from typing import Annotated, Union
from typing import Union as u
import typing
import typing as t

def function_return() -> Union[str, int]: # Noncompliant {{Use a union type expression for this type hint.}}
                        #^^^^^^^^^^^^^^^
    pass

def typing_union() -> typing.Union[int, str]: # Noncompliant
                     #^^^^^^^^^^^^^^^^^^^^^^
    pass

def from_import_alias() -> u[str, float]: # Noncompliant
                          #^^^^^^^^^^^^^
    pass

def import_alias() -> t.Union[float, int]: # Noncompliant
                     #^^^^^^^^^^^^^^^^^^^
    pass

def function_param(param: Union[str, int]): # Noncompliant
                         #^^^^^^^^^^^^^^^
    pass

def local_variable():
    variable : Union[int, str] # Noncompliant
              #^^^^^^^^^^^^^^^

top_level_variable : Union[int, str] # Noncompliant
                    #^^^^^^^^^^^^^^^

class MyClass:

    instance_variable: Union[int, str] # Noncompliant
                      #^^^^^^^^^^^^^^^

    def instance_method() -> Union[int, str]: # Noncompliant
                            #^^^^^^^^^^^^^^^
        pass


# There is no clear recommendation on this case, so we will just not handle them for the time being.
def union_in_generic_type() -> list[Union[int, str]]: # FN
    pass

def ok(param: int | str) -> int | str:
    variable : int | str
    variable = param
    return variable

def not_union_type() -> None:
    pass

def str_type() -> str:
    pass

def not_name_or_subscript() -> int or str:
    pass

def subscript_but_not_name() -> (int or str)[int, str]:
    pass

def unknown_return_type() -> unknown:
    pass

def unknown_return_type_subscript() -> unknown[int, str]:
    pass


# Compliant: Union pipe syntax inside Annotated should NOT trigger S6546
# Bug: https://community.sonarsource.com/t/false-positive-for-python-s6546/179644

class Depends:
    def __init__(self, func):
        self.func = func

class ClassC:
    pass

class ClassD:
    pass

def get_dep():
    return "dep"

# Compliant - union pipe syntax already used inside single-line Annotated
def annotated_union_pipe_single_line(param: Annotated[int | str, "metadata"]):
    pass

# Compliant - union pipe syntax already used inside multi-line Annotated (THE BUG)
def annotated_union_pipe_multiline(
    new_class: Annotated[
        ClassC | ClassD, Depends(get_dep)
    ],
):
    pass

# Compliant - union pipe in return type inside Annotated
def annotated_union_pipe_return() -> Annotated[
    int | str,
    "metadata"
]:
    pass

# Compliant - variable annotation with union pipe inside Annotated
annotated_var: Annotated[
    int | str,
    "metadata"
]

# Compliant - union pipe with None inside Annotated
def annotated_optional(param: Annotated[int | None, "optional"]):
    pass

# Compliant - multiple union pipe types inside Annotated
def annotated_multi_union(param: Annotated[int | str | float, "multi"]):
    pass
