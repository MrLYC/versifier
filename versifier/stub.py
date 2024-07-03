import ast
import io
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Any, Generator, Iterable, List, Tuple, Union

import astunparse


@dataclass
class ModuleStubGenerator(ast.NodeVisitor):
    source: io.TextIOWrapper
    output: io.TextIOWrapper
    stack: List[ast.AST] = field(default_factory=list)
    write_disabled: bool = False

    @contextmanager
    def scope(self, node: ast.AST) -> Generator:
        self.stack.append(node)
        yield
        self.stack.pop()

    @contextmanager
    def disable_write(self) -> Generator:
        self.write_disabled = True
        yield
        self.write_disabled = False

    def write_buffer(self, col_offset: int, content: str, keep_newline: bool = True) -> None:
        if self.write_disabled:
            return

        content = indent(content, " " * col_offset)
        if not keep_newline:
            content = content.strip("\n")

        self.output.write(content)

        if not keep_newline:
            self.output.write("\n")

    def write_node(self, node: ast.AST, keep_newline: bool = False) -> None:
        content = astunparse.unparse(node)
        self.write_buffer(node.col_offset, content, keep_newline)

    def write_docstring(self, parent: ast.AST, value: ast.Str) -> None:
        if value.col_offset < 0:
            value.col_offset = parent.col_offset + 4

        cleaned = dedent(value.s).strip("\n")
        lines = cleaned.splitlines()

        col_offset = value.col_offset
        self.write_buffer(col_offset, "'''\n")

        for line in lines:
            self.write_buffer(col_offset, line, False)

        self.write_buffer(col_offset, "'''\n")

    def write_ellipsis(self, col_offset: int = 0, parent_col_offset: int = 0) -> None:
        self.write_node(ast.Ellipsis(col_offset=col_offset or parent_col_offset + 4))

    def write_node_and_extra_body(self, node: ast.AST) -> Iterable[ast.stmt]:
        body = getattr(node, "body", [])
        if not body:
            return []

        setattr(node, "body", [])
        self.write_node(node)

        first_statement = body[0]
        if isinstance(first_statement, ast.Expr) and isinstance(first_statement.value, ast.Str):
            self.write_docstring(node, first_statement.value)
            body = body[1:]
        else:
            self.write_ellipsis(col_offset=first_statement.col_offset, parent_col_offset=node.col_offset)

        return body

    def get_parent_node(self) -> ast.AST:
        return self.stack[-2]

    def filter_nodes(self, nodes: Iterable[ast.stmt], allowed_types: Tuple = ()) -> Generator[ast.stmt, None, None]:
        if not allowed_types:
            allowed_types = (ast.stmt,)

        for node in nodes:
            if isinstance(node, allowed_types):
                yield node

    def visit_nodes(self, nodes: Iterable[ast.stmt], allowed_types: Tuple = ()) -> None:
        for node in self.filter_nodes(nodes, allowed_types):
            self.visit(node)

    def is_in_function(self) -> bool:
        for node in self.stack:
            if isinstance(node, ast.FunctionDef):
                return True
        return False

    def hide_assign_value(self, node: Union[ast.Assign, ast.AnnAssign]) -> bool:
        value = node.value
        if isinstance(value, (ast.Call, ast.Name, ast.Attribute, ast.NameConstant)):
            return False

        node.value = ast.Ellipsis()

        return False

    def visit_Expr(self, node: ast.Expr) -> Any:
        if not isinstance(node.value, ast.Str) or self.is_in_function():
            return self.generic_visit(node)

        parent = self.get_parent_node()
        docstring = node.value
        if node.col_offset >= 0:
            docstring.col_offset = node.col_offset
        elif docstring.col_offset < 0:
            docstring.col_offset = getattr(parent, "col_offset", 0)

        self.write_docstring(parent, docstring)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.is_in_function():
            return

        if not isinstance(node.target, ast.Name) or node.target.id.startswith("_"):
            return

        node.value = None
        self.write_node(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        if self.is_in_function():
            return

        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id.startswith("_"):
            return

        self.hide_assign_value(node)
        self.write_node(node)

    def visit_If(self, node: ast.If) -> None:
        if self.is_in_function():
            return

        body = node.body
        node.body = []
        self.write_node(node)
        self.write_ellipsis(col_offset=body[0].col_offset)
        self.visit_nodes(body, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if node.name.startswith("_"):
            return

        self.write_node_and_extra_body(node)

    def visit_Pass(self, node: ast.Pass) -> Any:
        self.write_ellipsis(col_offset=node.col_offset)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        body = self.write_node_and_extra_body(node)

        self.visit_nodes(
            body, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.If, ast.FunctionDef, ast.Expr, ast.Pass)
        )

    def visit_Import(self, node: ast.Import) -> Any:
        self.write_node(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        self.write_node(node)

    def visit_Try(self, node: ast.Try) -> Any:
        allowed_types = (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.Pass)
        node.body = list(self.filter_nodes(node.body, allowed_types))
        node.orelse = list(self.filter_nodes(node.orelse, allowed_types))
        node.finalbody = list(self.filter_nodes(node.finalbody, allowed_types))

        if not node.body:
            return

        with self.disable_write():
            self.visit_nodes(node.body)
            self.visit_nodes(node.orelse)
            self.visit_nodes(node.finalbody)

        self.write_node(node)

    def visit(self, node: ast.AST) -> None:
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
