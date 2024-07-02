import ast
import io
import os
from ast import AST, AnnAssign, Assign, ClassDef, Ellipsis, Expr, FunctionDef, Import, ImportFrom, Num, Str
from dataclasses import dataclass, field
from typing import Any, List, Union

import astunparse


@dataclass
class ModuleStubGenerator(ast.NodeVisitor):
    file_path: str
    buffer: io.TextIOWrapper
    stack: List[AST] = field(default_factory=list)

    def write_buffer(self, col_offset: int, content: str) -> None:
        for line in content.splitlines():
            self.buffer.write(" " * col_offset)
            self.buffer.write(line.strip())
            self.buffer.write("\n")

    def write_node(self, node: AST) -> None:
        content = astunparse.unparse(node)
        self.write_buffer(node.col_offset, content)

    def visit_nodes(self, *nodes: AST) -> None:
        for node in nodes:
            self.visit(node)

    def is_in_function(self) -> bool:
        for node in self.stack:
            if isinstance(node, FunctionDef):
                return True
        return False

    def convert_assign_value(self, node: Union[Assign, AnnAssign]) -> Any:
        if not isinstance(node.value, (Num, Str)):
            node.value = Ellipsis()

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        if self.is_in_function():
            return

        self.convert_assign_value(node)
        self.write_node(node)

    def visit_Assign(self, node: Assign) -> Any:
        if self.is_in_function():
            return

        self.convert_assign_value(node)
        self.write_node(node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.stack.append(node)

        first_statement = node.body[0]
        if not node.name.startswith("_"):
            node.body = []
            self.write_node(node)

            if isinstance(first_statement, Expr) and isinstance(first_statement.value, Str):
                self.write_buffer(node.col_offset + 1, f"'''\n{first_statement.value.s}'''")

            else:
                self.write_node(Ellipsis(col_offset=first_statement.col_offset))

        self.stack.pop()

    def visit_ClassDef(self, node: ClassDef) -> Any:
        body = node.body
        node.body = []

        self.write_node(node)
        self.visit_nodes(*body)

    def visit_Import(self, node: Import) -> Any:
        self.write_node(node)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        self.write_node(node)

    def generate(self) -> None:
        with open(self.file_path, "r") as fp:
            code = fp.read()

        module = ast.parse(code)
        self.visit(module)


@dataclass
class PackageStubGenerator:
    source_dir: str
    output_dir: str

    def generate(self) -> None:
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue

                source_path = os.path.join(root, file)
                output_path = os.path.join(self.output_dir, file.replace(".py", ".pyi"))

                with open(output_path, "w") as fp:
                    generator = ModuleStubGenerator(source_path, buffer=fp)
                    generator.generate()
