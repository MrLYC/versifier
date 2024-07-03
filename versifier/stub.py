import ast
import io
import os
from ast import (AST, AnnAssign, Assign, ClassDef, Ellipsis, Expr, FunctionDef,
                 If, Import, ImportFrom, Name, Pass, Str, Try, stmt)
from contextlib import contextmanager
from dataclasses import dataclass, field
from subprocess import check_call
from textwrap import dedent, indent
from typing import Any, Generator, Iterable, List, Tuple

import astunparse


@dataclass
class ModuleStubGenerator(ast.NodeVisitor):
    source: io.TextIOWrapper
    output: io.TextIOWrapper
    stack: List[AST] = field(default_factory=list)

    def write_buffer(
        self, col_offset: int, content: str, pre_newline: bool = False, post_newline: bool = False
    ) -> None:
        if pre_newline:
            self.output.write("\n")

        self.output.write(indent(content, " " * col_offset))

        if post_newline:
            self.output.write("\n")

    def write_node(self, node: AST, pre_newline: bool = False, post_newline: bool = True) -> None:
        content = astunparse.unparse(node)
        self.write_buffer(node.col_offset, content, pre_newline, post_newline)

    def write_docstring(self, parent: AST, value: Str) -> None:
        if value.col_offset < 0:
            value.col_offset = parent.col_offset + 4

        cleaned = dedent(value.s).strip()
        lines = cleaned.splitlines()

        col_offset = value.col_offset
        self.write_buffer(col_offset, "'''", post_newline=True)

        for line in lines:
            self.write_buffer(col_offset, line, post_newline=True)

        self.write_buffer(col_offset, "'''", post_newline=True)

    def write_ellipsis(self, col_offset: int = 0, parent_col_offset: int = 0) -> None:
        self.write_node(Ellipsis(col_offset=col_offset or parent_col_offset + 4))

    @contextmanager
    def scope(self, node: AST) -> Generator:
        self.stack.append(node)
        yield
        self.stack.pop()

    def get_parent_node(self) -> AST:
        return self.stack[-2]

    def filter_nodes(self, nodes: Iterable[stmt], allowed_types: Tuple = ()) -> Generator[stmt, None, None]:
        if not allowed_types:
            allowed_types = (stmt,)

        for node in nodes:
            if isinstance(node, allowed_types):
                yield node

    def visit_nodes(self, nodes: Iterable[stmt], allowed_types: Tuple = ()) -> None:
        for node in self.filter_nodes(nodes, allowed_types):
            self.visit(node)

    def is_in_function(self) -> bool:
        for node in self.stack:
            if isinstance(node, FunctionDef):
                return True
        return False

    def visit_Expr(self, node: Expr) -> Any:
        if not isinstance(node.value, Str) or self.is_in_function():
            return self.generic_visit(node)

        parent = self.get_parent_node()
        docstring = node.value
        if node.col_offset >= 0:
            docstring.col_offset = node.col_offset
        elif docstring.col_offset < 0:
            docstring.col_offset = getattr(parent, "col_offset", 0)

        self.write_docstring(parent, docstring)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        if self.is_in_function():
            return

        if not isinstance(node.target, Name) or node.target.id.startswith("_"):
            return

        self.write_node(node)

    def visit_Assign(self, node: Assign) -> Any:
        if self.is_in_function():
            return

        target = node.targets[0]
        if not isinstance(target, Name) or target.id.startswith("_"):
            return

        self.write_node(node)

    def visit_If(self, node: If) -> None:
        if self.is_in_function():
            return

        body = node.body
        node.body = []
        self.write_node(node)
        self.visit_nodes(body, (Import, ImportFrom, Assign, AnnAssign))
        self.write_ellipsis(parent_col_offset=node.col_offset)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        if node.name.startswith("_"):
            return

        first_statement = node.body[0]
        node.body = []
        self.write_node(node, True, False)

        if isinstance(first_statement, Expr) and isinstance(first_statement.value, Str):
            self.write_docstring(node, first_statement.value)

        else:
            self.write_ellipsis(col_offset=first_statement.col_offset)

    def visit_Pass(self, node: Pass) -> Any:
        self.write_ellipsis(col_offset=node.col_offset)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        body = node.body
        node.body = []
        first_statement = body[0]

        self.write_node(node, True, False)

        if isinstance(first_statement, Expr) and isinstance(first_statement.value, Str):
            self.write_docstring(node, first_statement.value)
            body = body[1:]

        self.visit_nodes(body, (Import, ImportFrom, Assign, AnnAssign, If, FunctionDef, Expr, Pass, Ellipsis))
        self.write_ellipsis(parent_col_offset=node.col_offset)

    def visit_Import(self, node: Import) -> Any:
        self.write_node(node)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        self.write_node(node)

    def visit_Try(self, node: Try) -> Any:
        allowed_types = (Import, ImportFrom, Assign, AnnAssign, Pass)
        node.body = list(self.filter_nodes(node.body, allowed_types))
        node.orelse = list(self.filter_nodes(node.orelse, allowed_types))
        node.finalbody = list(self.filter_nodes(node.finalbody, allowed_types))

        if node.body:
            self.write_node(node)

    def visit(self, node: AST) -> None:
        with self.scope(node):
            super().visit(node)

    def generate(self) -> None:
        module = ast.parse(self.source.read())
        self.visit(module)


@dataclass
class PackageStubGenerator:
    output_dir: str

    def generate(self, source_dir: str, packages: Iterable[str]) -> None:
        for package in packages:
            package_dir = os.path.join(source_dir, package)
            output_dir = os.path.join(self.output_dir, f"{package}-stubs")

            for root, _, files in os.walk(package_dir):
                for file in files:
                    if not file.endswith(".py"):
                        continue

                    source_path = os.path.join(root, file)
                    target_dir = root.replace(package_dir, output_dir)
                    os.makedirs(target_dir, exist_ok=True)

                    with open(source_path) as source_file, open(
                        os.path.join(target_dir, f"{file}i"), "w"
                    ) as output_file:
                        generator = ModuleStubGenerator(source=source_file, output=output_file)
                        generator.generate()
