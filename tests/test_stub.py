import ast
import io
from typing import Optional

from versifier.stub import ModuleStubGenerator


class TestModuleStubGenerator:
    def assert_generate_ast(self, source_code: str, expected_code: Optional[str] = None) -> None:
        if expected_code is None:
            expected_code = source_code

        source_buffer = io.StringIO(source_code)
        output_buffer = io.StringIO()

        generator = ModuleStubGenerator(source=source_buffer, output=output_buffer)
        generator.generate()

        output_code = output_buffer.getvalue()

        expected_ast = ast.parse(expected_code)
        output_ast = ast.parse(output_code)

        expected_dumped = ast.dump(expected_ast)
        output_dumped = ast.dump(output_ast)

        assert expected_dumped == output_dumped

    def test_import(self) -> None:
        self.assert_generate_ast(
            """
import foo
import bar as b
import a.b.c
            """
        )

    def test_import_from(self) -> None:
        self.assert_generate_ast(
            """
from foo import bar
from foo import bar as b
from a.b.c import d
            """
        )

    def test_assign(self) -> None:
        self.assert_generate_ast(
            """
int_value = 1
str_value = "foo"
bool_value = True
float_value = 1.0
tuple_value = (1, 2, 3)
list_value = [1, 2, 3]
set_value = {1, 2, 3}
dict_value = {"foo": 1, "bar": 2}
call = foo(1, 2, 3)
call_in_list = [foo(1, 2, 3)]
a = b = c = d
            """
        )

    def test_assign_private(self) -> None:
        self.assert_generate_ast(
            """
_value = 1
value = 2
x = _value = value
            """,
            """
value = 2
x = _value = value
            """,
        )

    def test_assign_attributes(self) -> None:
        self.assert_generate_ast("a.b = 1", "")

    def test_annotation_assign(self) -> None:
        self.assert_generate_ast(
            """
int_value: int = 1
str_value: str = "foo"
bool_value: bool = True
float_value: float = 1.0
tuple_value: Tuple[int, int, int] = (1, 2, 3)
list_value: List[int] = [1, 2, 3]
set_value: Set[int] = {1, 2, 3}
dict_value: Dict[str, int] = {"foo": 1, "bar": 2}
            """
        )

    def test_annotation_assign_private(self) -> None:
        self.assert_generate_ast(
            """
_value: int = 1
value: int = 2
            """,
            """
value: int = 2
            """,
        )

    def test_function_one_line(self) -> None:
        self.assert_generate_ast(
            """
def one_line():
    return 1
            """,
            """
def one_line():
    ...
            """,
        )

    def test_function_multi_lines(self) -> None:
        self.assert_generate_ast(
            """
def multi_lines():
    v = 1 + 1
    return v
            """,
            """
def multi_lines():
    ...
            """,
        )

    def test_function_with_args(self) -> None:
        self.assert_generate_ast(
            """
def add(a, b):
    return a + b
            """,
            """
def add(a, b):
    ...
            """,
        )

    def test_function_with_args_annotations(self) -> None:
        self.assert_generate_ast(
            """
def add(a: int, b: int) -> int:
    return a + b
            """,
            """
def add(a: int, b: int) -> int:
    ...
            """,
        )

    def test_function_with_one_line_docstring(self) -> None:
        self.assert_generate_ast(
            """
def add1(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b


def add2(a: int, b: int) -> int:
    '''
    Add two numbers.
    '''
    return a + b
            """,
            """
def add1(a: int, b: int) -> int:
    '''
    Add two numbers.
    '''

def add2(a: int, b: int) -> int:
    '''
    Add two numbers.
    '''
            """,
        )

    def test_function_with_multi_lines_docstring(self) -> None:
        self.assert_generate_ast(
            """
def add(a: int, b: int) -> int:
    '''
    This function adds two numbers, example:
    >>> add(1, 2)
    3
    '''
    return a + b
            """,
            """
def add(a: int, b: int) -> int:
    '''
    This function adds two numbers, example:
    >>> add(1, 2)
    3
    '''
            """,
        )

    def test_function_private(self) -> None:
        self.assert_generate_ast(
            """
def _add(a, b):
    return a + b
            """,
            "",
        )

    def test_function_with_decorators(self) -> None:
        self.assert_generate_ast(
            """
@decorator1
@decorator2
def add(a, b):
    return a + b
            """,
            """
@decorator1
@decorator2
def add(a, b):
    ...
            """,
        )

    def test_function_with_pass(self) -> None:
        self.assert_generate_ast(
            """
def foo():
    pass
            """,
            """
def foo():
    ...
            """,
        )

    def test_class_with_variable(self) -> None:
        self.assert_generate_ast(
            """
class NewStyle:
    a = 1

class OldStyle(object):
    a = 1

@dataclass
class DataClass:
    a: int
            """,
            """
class NewStyle:
    a = 1
    ...

class OldStyle(object):
    a = 1
    ...

@dataclass
class DataClass:
    a: int
    ...
            """,
        )

    def test_class_with_docstring(self) -> None:
        self.assert_generate_ast(
            """
class WithDocstring:
    '''
    This is a docstring.
    Over.
    '''
            """,
            """
class WithDocstring:
    '''
    This is a docstring.
    Over.
    '''
    ...
            """,
        )

    def test_class_with_private_variable_only(self) -> None:
        self.assert_generate_ast(
            """
class Foo:
    _a = 1
            """,
            """
class Foo:
    ...
            """,
        )

    def test_class_with_private_function_only(self) -> None:
        self.assert_generate_ast(
            """
class Foo:
    def _fun(self):
        return 1
            """,
            """
class Foo:
    ...
            """,
        )

    def test_class(self) -> None:
        self.assert_generate_ast(
            """
class Foo:
    '''
    This is a docstring.
    Over.
    '''

    a = 1
    b: int

    def __init__(self, v: int):
        self.b = v

    def _get_b(self):
        return self.b

    def get_b(self):
        '''
        Get b.
        '''
        return self._get_b()
            """,
            """
class Foo:
    '''
    This is a docstring.
    Over.
    '''

    a = 1
    b: int

    def get_b(self):
        '''
        Get b.
        '''
    ...
            """,
        )

    def test_class_with_var_docstring(self) -> None:
        self.assert_generate_ast(
            """
class Foo:
    a: int
    '''This is a docstring.'''
            """,
            """
class Foo:
    a: int
    '''
    This is a docstring.
    '''
    ...
            """,
        )

    def test_module_docstring(self) -> None:
        self.assert_generate_ast(
            """
'''
This is a module docstring.
Over.
'''
            """
        )

    def test_var_docstring(self) -> None:
        self.assert_generate_ast(
            """
a = 1
'''
This is a docstring.
Over.
'''
            """
        )

    def test_if_for_import(self) -> None:
        self.assert_generate_ast(
            """
if AUTH_USER_MODEL == settings.AUTH_USER_MODEL:
    from django.contrib import auth  # pylint: disable=ungrouped-imports
            """,
            """
if AUTH_USER_MODEL == settings.AUTH_USER_MODEL:
    from django.contrib import auth
    ...
            """,
        )

    def test_if_statements(self) -> None:
        self.assert_generate_ast(
            """
if True:
    call(1)
    v = call(1)
            """,
            """
if True:
    v = call(1)
    ...
            """,
        )

    def test_try_import(self) -> None:
        self.assert_generate_ast(
            """
try:
    import foo
except ImportError:
    foo = None
            """,
        )

    def test_try_call(self) -> None:
        self.assert_generate_ast(
            """
try:
    foo()
except ValueError:
    pass
            """,
            "",
        )

    def test_try_assign(self) -> None:
        self.assert_generate_ast(
            """
try:
    v = 1
except AttributeError:
    pass
            """,
        )

    def test_for_statements(self) -> None:
        self.assert_generate_ast(
            """
for i in range(10):
    call(i)
            """,
            "",
        )
