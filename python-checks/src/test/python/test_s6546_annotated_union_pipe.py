"""
Tests for S6546: Union type expressions should be preferred over typing.Union.

This test file demonstrates the false positive where union pipe syntax (X | Y)
inside Annotated type hints that span multiple lines is incorrectly flagged
by rule S6546.

Bug reference: https://community.sonarsource.com/t/false-positive-for-python-s6546/179644

The rule should:
- Flag: Union[X, Y] usage (should use X | Y instead)
- NOT flag: X | Y usage (already using union pipe syntax)
- NOT flag: Annotated[X | Y, metadata] (already using union pipe syntax inside Annotated)
"""

import ast
import textwrap
import pytest


def check_s6546_issues(source_code: str) -> list[dict]:
    """
    Python implementation of the S6546 rule logic that mirrors the Java check
    in UnionTypeExpressionCheck.java.

    This function parses Python source code and identifies type annotations that
    use typing.Union instead of the X | Y union pipe syntax.

    The current (buggy) implementation does NOT properly handle the case where
    union pipe syntax is used inside Annotated[] type hints, especially when
    the Annotated expression spans multiple lines.

    Returns a list of dicts with 'line', 'col', and 'message' for each issue found.
    """
    tree = ast.parse(source_code)
    issues = []

    # Collect all imported names to resolve typing.Union and typing.Annotated
    typing_union_names = set()
    typing_annotated_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "typing":
                for alias in node.names:
                    if alias.name == "Union":
                        typing_union_names.add(alias.asname or alias.name)
                    elif alias.name == "Annotated":
                        typing_annotated_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "typing":
                    # Handle typing.Union and typing.Annotated via attribute access
                    pass

    def is_union_subscription(expr) -> bool:
        """Check if an expression is Union[X, Y] or typing.Union[X, Y]."""
        if isinstance(expr, ast.Subscript):
            value = expr.value
            # Direct name: Union[X, Y]
            if isinstance(value, ast.Name) and value.id in typing_union_names:
                return True
            # Attribute: typing.Union[X, Y]
            if isinstance(value, ast.Attribute) and value.attr == "Union":
                if isinstance(value.value, ast.Name) and value.value.id == "typing":
                    return True
        return False

    def is_annotated_subscription(expr) -> bool:
        """Check if an expression is Annotated[X, metadata]."""
        if isinstance(expr, ast.Subscript):
            value = expr.value
            # Direct name: Annotated[X, metadata]
            if isinstance(value, ast.Name) and value.id in typing_annotated_names:
                return True
            # Attribute: typing.Annotated[X, metadata]
            if isinstance(value, ast.Attribute) and value.attr == "Annotated":
                if isinstance(value.value, ast.Name) and value.value.id == "typing":
                    return True
        return False

    def is_bitwise_or(expr) -> bool:
        """Check if an expression is X | Y (bitwise or / union type)."""
        return isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr)

    def get_first_subscript_element(subscript_node):
        """
        Get the first element of a subscription expression.
        For Annotated[X | Y, metadata], this returns the X | Y part.
        Handles both Tuple slices and single element slices.
        """
        slice_node = subscript_node.slice
        if isinstance(slice_node, ast.Tuple):
            if slice_node.elts:
                return slice_node.elts[0]
        return slice_node

    def resolve_type_from_annotation(expr):
        """
        Resolve the effective type from a type annotation expression.
        Mirrors InferredTypes.fromTypeAnnotation() in the Java code.

        For Annotated[X, metadata], returns the resolved type of X.
        For Union[X, Y], returns 'typing.Union'.
        For X | Y, returns 'typing.Union' (as the Java code does).
        For plain names, returns the name.
        """
        if is_annotated_subscription(expr):
            first_arg = get_first_subscript_element(expr)
            return resolve_type_from_annotation(first_arg)
        if is_union_subscription(expr):
            return "typing.Union"
        if is_bitwise_or(expr):
            # The Java code's declaredUnionType returns typing.Union for X | Y
            return "typing.Union"
        if isinstance(expr, ast.Subscript):
            # Generic type like Dict[str, X]
            if isinstance(expr.value, ast.Name):
                return expr.value.id
        if isinstance(expr, ast.Name):
            return expr.id
        return None

    def check_type_annotation_buggy(annotation_expr, line):
        """
        BUGGY version: Mirrors the current Java UnionTypeExpressionCheck logic.

        Current logic:
        1. If the top-level expression is BITWISE_OR, return (no issue - already using |)
        2. Resolve the type via InferredTypes.fromTypeAnnotation
        3. If resolved type is typing.Union, raise issue

        BUG: When annotation is Annotated[X | Y, ...], the top-level is a SUBSCRIPTION
        (not BITWISE_OR), so step 1 does not return. Then step 2 resolves through
        Annotated to find X | Y, which resolves to typing.Union. Step 3 flags it.
        """
        # Step 1: Check if top-level expression is bitwise or (union pipe syntax)
        if is_bitwise_or(annotation_expr):
            return  # Already using union type expression - no issue

        # Step 2: Resolve the type
        resolved_type = resolve_type_from_annotation(annotation_expr)

        # Step 3: Check if it resolves to typing.Union
        if resolved_type == "typing.Union":
            issues.append({
                "line": line,
                "col": 0,
                "message": "Use a union type expression for this type hint."
            })

    # Walk the AST to find all type annotations
    for node in ast.walk(tree):
        annotation = None
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Check return type annotation
            if node.returns:
                check_type_annotation_buggy(node.returns, node.returns.lineno)
            # Check parameter type annotations
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.annotation:
                    check_type_annotation_buggy(arg.annotation, arg.annotation.lineno)
        elif isinstance(node, ast.AnnAssign):
            if node.annotation:
                check_type_annotation_buggy(node.annotation, node.annotation.lineno)

    return issues


def check_s6546_issues_fixed(source_code: str) -> list[dict]:
    """
    FIXED version of the S6546 rule logic.

    The fix adds an additional check: if the expression is an Annotated subscription
    whose first type argument is a BITWISE_OR (union pipe syntax), we should NOT
    flag it because the user is already using the correct X | Y syntax.
    """
    tree = ast.parse(source_code)
    issues = []

    typing_union_names = set()
    typing_annotated_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "typing":
                for alias in node.names:
                    if alias.name == "Union":
                        typing_union_names.add(alias.asname or alias.name)
                    elif alias.name == "Annotated":
                        typing_annotated_names.add(alias.asname or alias.name)

    def is_union_subscription(expr) -> bool:
        if isinstance(expr, ast.Subscript):
            value = expr.value
            if isinstance(value, ast.Name) and value.id in typing_union_names:
                return True
            if isinstance(value, ast.Attribute) and value.attr == "Union":
                if isinstance(value.value, ast.Name) and value.value.id == "typing":
                    return True
        return False

    def is_annotated_subscription(expr) -> bool:
        if isinstance(expr, ast.Subscript):
            value = expr.value
            if isinstance(value, ast.Name) and value.id in typing_annotated_names:
                return True
            if isinstance(value, ast.Attribute) and value.attr == "Annotated":
                if isinstance(value.value, ast.Name) and value.value.id == "typing":
                    return True
        return False

    def is_bitwise_or(expr) -> bool:
        return isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr)

    def get_first_subscript_element(subscript_node):
        slice_node = subscript_node.slice
        if isinstance(slice_node, ast.Tuple):
            if slice_node.elts:
                return slice_node.elts[0]
        return slice_node

    def resolve_type_from_annotation(expr):
        if is_annotated_subscription(expr):
            first_arg = get_first_subscript_element(expr)
            return resolve_type_from_annotation(first_arg)
        if is_union_subscription(expr):
            return "typing.Union"
        if is_bitwise_or(expr):
            return "typing.Union"
        if isinstance(expr, ast.Subscript):
            if isinstance(expr.value, ast.Name):
                return expr.value.id
        if isinstance(expr, ast.Name):
            return expr.id
        return None

    def contains_bitwise_or_in_annotation(expr) -> bool:
        """
        FIX: Check if the expression contains a bitwise or (union pipe syntax)
        at the type level within an Annotated subscription.

        This handles:
        - Annotated[X | Y, metadata] -> True (first type arg is X | Y)
        - Annotated[Dict[str, X | Y], metadata] -> True (nested union pipe)
        """
        if is_bitwise_or(expr):
            return True
        if is_annotated_subscription(expr):
            first_arg = get_first_subscript_element(expr)
            return contains_bitwise_or_in_annotation(first_arg)
        if isinstance(expr, ast.Subscript):
            # Check inside generic types like Dict[str, X | Y]
            slice_node = expr.slice
            if isinstance(slice_node, ast.Tuple):
                return any(contains_bitwise_or_in_annotation(elt) for elt in slice_node.elts)
            return contains_bitwise_or_in_annotation(slice_node)
        return False

    def check_type_annotation_fixed(annotation_expr, line):
        """
        FIXED version: adds check for union pipe syntax inside Annotated wrappers.
        """
        # Step 1: Check if top-level expression is bitwise or
        if is_bitwise_or(annotation_expr):
            return

        # Step 1b (FIX): Check if expression contains bitwise or inside Annotated
        if contains_bitwise_or_in_annotation(annotation_expr):
            return  # Already using union pipe syntax inside Annotated - no issue

        # Step 2: Resolve the type
        resolved_type = resolve_type_from_annotation(annotation_expr)

        # Step 3: Check if it resolves to typing.Union
        if resolved_type == "typing.Union":
            issues.append({
                "line": line,
                "col": 0,
                "message": "Use a union type expression for this type hint."
            })

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if node.returns:
                check_type_annotation_fixed(node.returns, node.returns.lineno)
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.annotation:
                    check_type_annotation_fixed(arg.annotation, arg.annotation.lineno)
        elif isinstance(node, ast.AnnAssign):
            if node.annotation:
                check_type_annotation_fixed(node.annotation, node.annotation.lineno)

    return issues


# =============================================================================
# TEST CASES
# =============================================================================

class TestS6546BuggyBehavior:
    """
    Tests that demonstrate the BUGGY behavior of the current S6546 rule.
    These tests show that the current implementation incorrectly flags
    union pipe syntax inside Annotated type hints.
    """

    def test_union_in_annotated_multiline_is_false_positive(self):
        """
        CORE BUG: When Annotated[ClassC | ClassD, Depends(c_or_d)] spans
        multiple lines, the rule incorrectly flags it as needing union type
        expression, even though X | Y IS the union type expression.

        This test MUST FAIL with the buggy implementation to prove the bug exists.
        Expected: 0 issues (union pipe syntax is already used)
        Buggy actual: 1 issue (false positive)
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def get_dep():
                return "dep"

            class Depends:
                def __init__(self, func):
                    self.func = func

            class ClassC:
                pass

            class ClassD:
                pass

            def getresult(
                new_class: Annotated[
                    ClassC | ClassD, Depends(get_dep)
                ],
            ):
                pass
        """)
        issues = check_s6546_issues(code)
        # BUG: This should find 0 issues but the buggy implementation finds 1
        assert len(issues) == 0, (
            f"FALSE POSITIVE: Rule S6546 incorrectly flagged union pipe syntax "
            f"inside multi-line Annotated. Found {len(issues)} issue(s): {issues}"
        )

    def test_union_in_annotated_single_line_no_issue(self):
        """
        Single-line Annotated with union pipe inside a generic type (Dict[str, X | Y])
        does NOT trigger the false positive because the first Annotated argument
        resolves to Dict, not typing.Union.
        """
        code = textwrap.dedent("""\
            from typing import Annotated, Dict

            class Depends:
                def __init__(self, func):
                    self.func = func

            class ClassA:
                pass

            class ClassB:
                pass

            def get_dep():
                return "dep"

            def getresult(
                regular_class: Annotated[Dict[str, ClassA | ClassB], Depends(get_dep)],
            ):
                pass
        """)
        issues = check_s6546_issues(code)
        # This correctly finds 0 issues because Dict[...] is the first arg, not X | Y
        assert len(issues) == 0, (
            f"Expected 0 issues for Dict[str, ClassA | ClassB] inside Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_union_in_annotated_multiline_direct_pipe(self):
        """
        Another false positive case: Annotated[int | str, "metadata"] on multiple lines.
        The union pipe is directly the first argument of Annotated.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func(
                param: Annotated[
                    int | str, "some metadata"
                ],
            ):
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 0, (
            f"FALSE POSITIVE: Rule S6546 incorrectly flagged int | str "
            f"inside multi-line Annotated. Found {len(issues)} issue(s): {issues}"
        )

    def test_union_in_annotated_return_type_multiline(self):
        """
        False positive in return type annotation with Annotated and union pipe
        across multiple lines.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func() -> Annotated[
                int | str,
                "metadata"
            ]:
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 0, (
            f"FALSE POSITIVE: Rule S6546 incorrectly flagged int | str "
            f"in return type Annotated across multiple lines. "
            f"Found {len(issues)} issue(s): {issues}"
        )

    def test_union_in_annotated_variable_annotation(self):
        """
        False positive in variable type annotation with Annotated and union pipe.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            my_var: Annotated[
                int | str,
                "metadata"
            ]
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 0, (
            f"FALSE POSITIVE: Rule S6546 incorrectly flagged int | str "
            f"in variable annotation with Annotated. "
            f"Found {len(issues)} issue(s): {issues}"
        )


class TestS6546CorrectBehavior:
    """
    Tests that verify the rule CORRECTLY flags typing.Union usage.
    These tests should pass with BOTH the buggy and fixed implementations.
    """

    def test_union_import_flagged(self):
        """Union[str, int] in a function return type should be flagged."""
        code = textwrap.dedent("""\
            from typing import Union

            def func() -> Union[str, int]:
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 1, (
            f"Expected 1 issue for Union[str, int]. Found {len(issues)}: {issues}"
        )

    def test_union_in_parameter(self):
        """Union[str, int] in a parameter type should be flagged."""
        code = textwrap.dedent("""\
            from typing import Union

            def func(param: Union[str, int]):
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 1, (
            f"Expected 1 issue for Union[str, int] in parameter. "
            f"Found {len(issues)}: {issues}"
        )

    def test_union_in_variable(self):
        """Union[int, str] in a variable annotation should be flagged."""
        code = textwrap.dedent("""\
            from typing import Union

            my_var: Union[int, str]
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 1, (
            f"Expected 1 issue for Union[int, str] in variable. "
            f"Found {len(issues)}: {issues}"
        )

    def test_pipe_syntax_not_flagged(self):
        """int | str should NOT be flagged (already using union type expression)."""
        code = textwrap.dedent("""\
            def func(param: int | str) -> int | str:
                variable: int | str
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 0, (
            f"Expected 0 issues for int | str pipe syntax. "
            f"Found {len(issues)}: {issues}"
        )

    def test_union_inside_annotated_should_be_flagged(self):
        """Union[X, Y] inside Annotated should still be flagged."""
        code = textwrap.dedent("""\
            from typing import Annotated, Union

            def func(
                param: Annotated[
                    Union[int, str], "metadata"
                ],
            ):
                pass
        """)
        issues = check_s6546_issues(code)
        assert len(issues) == 1, (
            f"Expected 1 issue for Union[int, str] inside Annotated. "
            f"Found {len(issues)}: {issues}"
        )


class TestS6546FixedBehavior:
    """
    Tests that verify the FIXED implementation correctly handles
    union pipe syntax inside Annotated type hints.
    """

    def test_fixed_union_in_annotated_multiline_no_issue(self):
        """
        FIXED: Annotated[ClassC | ClassD, Depends(c_or_d)] across multiple lines
        should NOT be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            class Depends:
                def __init__(self, func):
                    self.func = func

            class ClassC:
                pass

            class ClassD:
                pass

            def get_dep():
                return "dep"

            def getresult(
                new_class: Annotated[
                    ClassC | ClassD, Depends(get_dep)
                ],
            ):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for union pipe in multi-line Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_union_in_annotated_single_line_no_issue(self):
        """
        FIXED: Annotated[int | str, "metadata"] on a single line should NOT be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func(param: Annotated[int | str, "metadata"]):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for union pipe in single-line Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_union_in_annotated_return_type(self):
        """
        FIXED: Return type Annotated[int | str, "meta"] should NOT be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func() -> Annotated[
                int | str,
                "metadata"
            ]:
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for union pipe in return type Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_union_in_annotated_variable(self):
        """
        FIXED: Variable Annotated[int | str, "meta"] should NOT be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            my_var: Annotated[
                int | str,
                "metadata"
            ]
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for union pipe in variable Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_still_flags_typing_union(self):
        """
        FIXED: typing.Union should still be flagged even after the fix.
        """
        code = textwrap.dedent("""\
            from typing import Union

            def func() -> Union[str, int]:
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 1, (
            f"FIXED: Expected 1 issue for Union[str, int]. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_still_flags_union_inside_annotated(self):
        """
        FIXED: Union[X, Y] inside Annotated should still be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated, Union

            def func(
                param: Annotated[
                    Union[int, str], "metadata"
                ],
            ):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 1, (
            f"FIXED: Expected 1 issue for Union[int, str] inside Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_community_reported_example(self):
        """
        FIXED: The exact code from the community report should not trigger any issues.
        https://community.sonarsource.com/t/false-positive-for-python-s6546/179644
        """
        code = textwrap.dedent("""\
            from typing import Annotated, Dict

            class Database:
                pass

            class ClassA:
                pass

            class ClassB:
                pass

            class ClassC:
                pass

            class ClassD:
                pass

            class Depends:
                def __init__(self, func):
                    self.func = func

            def current_database():
                return Database()

            def a_or_b():
                return ClassA()

            def c_or_d():
                return ClassC()

            def getresult(
                my_env: str,
                database: Annotated[Database, Depends(current_database)],
                regular_class: Annotated[Dict[str, ClassA | ClassB], Depends(a_or_b)],
                new_class: Annotated[
                    ClassC | ClassD, Depends(c_or_d)
                ],
            ):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Community-reported example should have 0 issues. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_pipe_syntax_still_ok(self):
        """
        FIXED: Plain pipe syntax (not inside Annotated) should still be fine.
        """
        code = textwrap.dedent("""\
            def func(param: int | str) -> int | str:
                variable: int | str
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for plain pipe syntax. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_multiple_union_pipes_in_annotated(self):
        """
        FIXED: Multiple union pipe arguments inside Annotated should not be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func(
                param: Annotated[
                    int | str | float, "metadata"
                ],
            ):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for multiple union pipes in Annotated. "
            f"Found {len(issues)}: {issues}"
        )

    def test_fixed_none_union_in_annotated(self):
        """
        FIXED: Annotated[int | None, metadata] should not be flagged.
        """
        code = textwrap.dedent("""\
            from typing import Annotated

            def func(
                param: Annotated[
                    int | None, "optional int"
                ],
            ):
                pass
        """)
        issues = check_s6546_issues_fixed(code)
        assert len(issues) == 0, (
            f"FIXED: Expected 0 issues for int | None in Annotated. "
            f"Found {len(issues)}: {issues}"
        )
