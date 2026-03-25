# PEP 649: Deferred Evaluation of Annotations
# These test cases verify the parser handles all annotation patterns correctly.
# Under PEP 649, annotations are no longer evaluated at function/class definition time.
# The parser should handle forward references without issues.

# Forward reference in function parameter and return type
class MyClass:
    def method(self) -> MyClass:
        return self

# Forward reference in variable annotations
class Node:
    left: Node
    right: Node
    value: int

# Complex type annotations with unions and generics
def process(items: list[int | str]) -> dict[str, list[int]]:
    pass

# Type alias with forward reference
type TreeNode = Node | None

# Annotation with string literal (traditional way before PEP 649)
def old_style(x: 'MyClass') -> 'MyClass':
    pass

# Nested type annotations
def nested_generics(data: dict[str, list[tuple[int, ...]]]) -> list[dict[str, int]]:
    pass

# Lambda in default with annotation
def with_default(x: int = 42, y: str = "hello") -> bool:
    pass

# Class with complex annotations
class Container:
    items: list[int]
    metadata: dict[str, list[str]]
    parent: Container | None = None

# Function with keyword-only and positional-only parameters with annotations
def mixed_params(x: int, /, y: str, *, z: float) -> None:
    pass

# Annotations in for loops and comprehensions (not affected by PEP 649, but should parse)
x: int
for x in range(10):
    pass

# Multiple annotations on one line
a: int = 1
b: str = "hello"
c: list[int] = [1, 2, 3]
