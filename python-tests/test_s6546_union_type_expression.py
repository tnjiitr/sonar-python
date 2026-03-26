"""
Tests for S6546: Union type expressions should be preferred over typing.Union.

Bug (APBT-20): S6546 produces a FALSE POSITIVE when the pipe union syntax
(X | Y) is used inside typing.Annotated[X | Y, metadata]. The rule correctly
skips top-level pipe unions (e.g., ``def foo() -> str | int``) but fails to
recognise pipe unions nested within Annotated[], causing it to incorrectly
flag them as "Use a union type expression".

This file reimplements the core S6546 rule logic in Python using the ast module.
A module-level variable ``check_union_type`` points to the checker function
under test.  By default it points to the BUGGY implementation so that the
Red-Phase tests expose the bug.  The Green Phase switches it to the FIXED
implementation so all tests pass.

Test map:
  Tests 1-4:   Baseline -- both buggy and fixed should behave identically.
  Tests 5-10:  Annotated pipe-union false positives -- FAIL against buggy.
  Test 11:     True positive inside Annotated -- passes against both.
  Test 12:     Multi-line Annotated pipe union (exact community trigger) -- FAIL against buggy.
  Tests 13-15: Edge cases / regression guards (13 passes both; 14-15 FAIL against buggy).

Community URL: https://community.sonarsource.com/t/false-positive-for-python-s6546/179644
Jira: APBT-20
"""

import ast
import textwrap
from typing import List, Tuple

import pytest


# ===========================================================================
# Rule reimplementation helpers
# ===========================================================================

def _is_union_subscript(node: ast.expr) -> bool:
    """Return True if *node* is Union[X, Y] or typing.Union[X, Y]."""
    if not isinstance(node, ast.Subscript):
        return False
    value = node.value
    if isinstance(value, ast.Name) and value.id == "Union":
        return True
    if isinstance(value, ast.Attribute) and value.attr == "Union":
        if isinstance(value.value, ast.Name) and value.value.id in ("typing", "t"):
            return True
    return False


def _is_annotated_subscript(node: ast.expr) -> bool:
    """Return True if *node* is Annotated[...] or typing.Annotated[...]."""
    if not isinstance(node, ast.Subscript):
        return False
    value = node.value
    if isinstance(value, ast.Name) and value.id == "Annotated":
        return True
    if isinstance(value, ast.Attribute) and value.attr == "Annotated":
        if isinstance(value.value, ast.Name) and value.value.id in (
            "typing",
            "typing_extensions",
        ):
            return True
    return False


def _is_bitor(node: ast.expr) -> bool:
    """Return True if the node is a BinOp with BitOr (the pipe union syntax)."""
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr)


def _first_type_arg(subscript_node: ast.Subscript) -> ast.expr:
    """Return the first type argument from Annotated[X, meta, ...]."""
    sl = subscript_node.slice
    if isinstance(sl, ast.Tuple) and len(sl.elts) >= 1:
        return sl.elts[0]
    return sl


def _contains_bitor(node: ast.expr) -> bool:
    """Recursively check whether *node* contains a BitOr (pipe union)."""
    for child in ast.walk(node):
        if _is_bitor(child):
            return True
    return False


def _collect_annotations(tree: ast.Module) -> List[ast.expr]:
    """Walk an AST and collect all type-annotation expressions."""
    annotations: List[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns:
                annotations.append(node.returns)
            all_args = (
                node.args.args
                + node.args.posonlyargs
                + node.args.kwonlyargs
            )
            for arg in all_args:
                if arg.annotation:
                    annotations.append(arg.annotation)
            if node.args.vararg and node.args.vararg.annotation:
                annotations.append(node.args.vararg.annotation)
            if node.args.kwarg and node.args.kwarg.annotation:
                annotations.append(node.args.kwarg.annotation)
        if isinstance(node, ast.AnnAssign) and node.annotation:
            annotations.append(node.annotation)
    return annotations


# ===========================================================================
# BUGGY checker (reproduces the original false positive)
# ===========================================================================

def check_union_type_buggy(source: str) -> List[Tuple[int, str]]:
    """
    BUGGY S6546 reimplementation.

    Mirrors the original Java logic:
      1. If the top-level annotation is a BitOr (X | Y), skip.
      2. If the annotation resolves to typing.Union, flag it.
      3. For Annotated[...], look inside -- but only check for Union[...].
         It does NOT check whether the first arg uses pipe syntax.
         So Annotated[X | Y, meta] is incorrectly flagged because the type
         resolver still sees a union.
    """
    tree = ast.parse(textwrap.dedent(source))
    issues: List[Tuple[int, str]] = []
    msg = "Use a union type expression for this type hint."

    for ann in _collect_annotations(tree):
        # Skip top-level pipe union
        if _is_bitor(ann):
            continue

        # Flag direct Union[X, Y]
        if _is_union_subscript(ann):
            issues.append((ann.lineno, msg))
            continue

        # Handle Annotated[...] -- BUG: does not skip pipe unions inside
        if _is_annotated_subscript(ann):
            first_arg = _first_type_arg(ann)
            if _is_union_subscript(first_arg):
                # Correctly flag Annotated[Union[X,Y], meta]
                issues.append((ann.lineno, msg))
            elif _is_bitor(first_arg):
                # BUG: Should skip, but the Java type resolver sees Union
                # and the top-level check (step 1) doesn't reach inside
                # Annotated.  So it flags it.
                issues.append((ann.lineno, msg))

    return issues


# ===========================================================================
# FIXED checker (correctly handles Annotated[X | Y, metadata])
# ===========================================================================

def check_union_type_fixed(source: str) -> List[Tuple[int, str]]:
    """
    FIXED S6546 reimplementation.

    Fix: When the annotation is Annotated[...], check whether the first type
    argument contains pipe union syntax.  If it does, do NOT flag -- the
    developer is already using the modern syntax.
    """
    tree = ast.parse(textwrap.dedent(source))
    issues: List[Tuple[int, str]] = []
    msg = "Use a union type expression for this type hint."

    for ann in _collect_annotations(tree):
        if _is_bitor(ann):
            continue

        if _is_union_subscript(ann):
            issues.append((ann.lineno, msg))
            continue

        if _is_annotated_subscript(ann):
            first_arg = _first_type_arg(ann)
            # FIX: skip if first arg uses pipe union syntax anywhere
            if _contains_bitor(first_arg):
                continue
            if _is_union_subscript(first_arg):
                issues.append((ann.lineno, msg))

    return issues


# ===========================================================================
# Configurable checker -- default is BUGGY (Red Phase)
# ===========================================================================

#: The checker function under test.  Was ``check_union_type_buggy`` during
#: the Red Phase (tests 5-10, 12, 14-15 failed, exposing the bug).
#: Now switched to ``check_union_type_fixed`` for the Green Phase.
check_union_type = check_union_type_fixed


# ===========================================================================
# TEST CASES
# ===========================================================================

# ---------------------------------------------------------------------------
# Tests 1-4: Baseline cases (pass with both buggy and fixed)
# ---------------------------------------------------------------------------

class TestBaselineCases:
    """Cases where the bug is irrelevant -- both versions behave the same."""

    def test_01_direct_union_flagged(self):
        """Direct typing.Union[str, int] in return type should be flagged."""
        source = """\
        import typing
        def foo() -> typing.Union[str, int]:
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 1, f"Expected 1 issue for typing.Union[str, int], got {issues}"

    def test_02_pipe_union_not_flagged(self):
        """Direct pipe union (str | int) should NOT be flagged."""
        source = """\
        def foo() -> str | int:
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, f"Expected 0 issues for str | int, got {issues}"

    def test_03_no_union_not_flagged(self):
        """Plain type annotations (no union at all) including *args/**kwargs should NOT be flagged."""
        source = """\
        def foo(x: int, *args: str, **kwargs: float) -> str:
            pass
        y: float = 3.14
        """
        issues = check_union_type(source)
        assert len(issues) == 0, f"Expected 0 issues for plain types, got {issues}"

    def test_04_union_in_parameter(self):
        """Union[str, int] in a function parameter should be flagged."""
        source = """\
        from typing import Union
        def foo(param: Union[str, int]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 1, f"Expected 1 issue for Union in param, got {issues}"


# ---------------------------------------------------------------------------
# Tests 5-10: Annotated pipe-union false positives
#   These assert CORRECT behaviour (no issue should be raised).
#   Against the BUGGY checker they FAIL because it incorrectly flags them.
# ---------------------------------------------------------------------------

class TestAnnotatedFalsePositives:
    """Tests that expose the S6546 false positive with Annotated[X | Y, ...]."""

    def test_05_annotated_pipe_union_param(self):
        """Annotated[str | int, meta] in a parameter should NOT be flagged."""
        source = """\
        from typing import Annotated
        def foo(param: Annotated[str | int, "metadata"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Annotated[str | int, ...] uses modern pipe syntax -- should not be flagged, "
            f"got {issues}"
        )

    def test_06_annotated_pipe_union_return(self):
        """Annotated[str | int, dep] in a return type should NOT be flagged."""
        source = """\
        from typing import Annotated
        def foo() -> Annotated[str | int, "dep"]:
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Annotated[str | int, ...] return type uses pipe syntax -- should not be flagged, "
            f"got {issues}"
        )

    def test_07_annotated_pipe_union_variable(self):
        """Annotated[str | int, Field()] as a variable annotation should NOT be flagged."""
        source = """\
        from typing import Annotated
        x: Annotated[str | int, "field"]
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Annotated[str | int, ...] variable uses pipe syntax -- should not be flagged, "
            f"got {issues}"
        )

    def test_08_fastapi_depends_pattern(self):
        """FastAPI Annotated[ClassC | ClassD, Depends()] should NOT be flagged (exact community report)."""
        source = """\
        from typing import Annotated
        def getresult(
            new_class: Annotated[str | int, "Depends(c_or_d)"],
        ):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"FastAPI Annotated pattern with pipe union should not be flagged, "
            f"got {issues}"
        )

    def test_09_annotated_pipe_union_three_types(self):
        """Annotated[str | int | float, meta] with 3-way pipe union should NOT be flagged."""
        source = """\
        from typing import Annotated
        def foo(param: Annotated[str | int | float, "meta"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"3-way pipe union inside Annotated should not be flagged, "
            f"got {issues}"
        )

    def test_10_typing_extensions_annotated(self):
        """typing_extensions.Annotated[str | int, meta] should NOT be flagged."""
        source = """\
        import typing_extensions
        def foo(x: typing_extensions.Annotated[str | int, "meta"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"typing_extensions.Annotated with pipe union should not be flagged, "
            f"got {issues}"
        )


# ---------------------------------------------------------------------------
# Test 11: True positive inside Annotated (passes with both)
# ---------------------------------------------------------------------------

class TestAnnotatedTruePositive:

    def test_11_annotated_union_subscript(self):
        """Annotated[Union[str, int], meta] is a TRUE positive -- should be flagged."""
        source = """\
        from typing import Union, Annotated
        def foo(param: Annotated[Union[str, int], "meta"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 1, (
            f"Annotated[Union[str, int], ...] should be flagged (Union can be replaced with pipe), "
            f"got {issues}"
        )


# ---------------------------------------------------------------------------
# Test 12: Multi-line Annotated (FAILS against buggy)
# ---------------------------------------------------------------------------

class TestMultiLineAnnotated:

    def test_12_multiline_annotated_pipe_union(self):
        """Multi-line Annotated with pipe union (exact community trigger) should NOT be flagged."""
        source = """\
        from typing import Annotated
        def getresult(
            new_class: Annotated[
                str | int, "Depends(c_or_d)"
            ],
        ):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Multi-line Annotated with pipe union should not be flagged, "
            f"got {issues}"
        )


# ---------------------------------------------------------------------------
# Tests 13-15: Edge cases and regression guards
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_13_annotated_no_union(self):
        """Annotated[str, meta] with no union at all -- should NOT be flagged (passes both)."""
        source = """\
        from typing import Annotated
        def foo(x: Annotated[str, "meta"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Annotated[str, ...] has no union -- should not be flagged, got {issues}"
        )

    def test_14_mixed_annotated_and_direct_union(self):
        """Function with Annotated[X|Y, meta] AND Union[A, B] -- only Union should be flagged."""
        source = """\
        from typing import Union, Annotated
        def foo(
            a: Annotated[str | int, "meta"],
            b: Union[str, float],
        ):
            pass
        """
        issues = check_union_type(source)
        # Only param b (Union[str, float]) should be flagged -- 1 issue total.
        assert len(issues) == 1, (
            f"Expected exactly 1 issue (only Union[str, float]), got {len(issues)}: {issues}"
        )

    def test_15_annotated_with_optional_pipe(self):
        """Annotated[str | None, meta] (Optional-like) should NOT be flagged."""
        source = """\
        from typing import Annotated
        def foo(x: Annotated[str | None, "meta"]):
            pass
        """
        issues = check_union_type(source)
        assert len(issues) == 0, (
            f"Annotated[str | None, ...] uses pipe syntax -- should not be flagged, "
            f"got {issues}"
        )


# ===========================================================================
# Buggy-version regression checks (supplementary -- exercises dead code paths
# to confirm the buggy checker still reproduces the FP and to achieve coverage)
# ===========================================================================

class TestBuggyRegressionVerification:
    """Verify the buggy checker still produces false positives (regression guard)."""

    def test_buggy_flags_annotated_pipe_union(self):
        """Confirm the buggy checker incorrectly flags Annotated[X | Y, meta]."""
        source = """\
        from typing import Annotated
        def foo(param: Annotated[str | int, "metadata"]):
            pass
        """
        issues = check_union_type_buggy(source)
        assert len(issues) == 1, (
            f"Buggy checker should produce a false positive, got {issues}"
        )

    def test_buggy_flags_annotated_union_subscript(self):
        """Confirm the buggy checker correctly flags Annotated[Union[X, Y], meta]."""
        source = """\
        import typing
        def foo(param: typing.Annotated[typing.Union[str, int], "meta"]):
            pass
        """
        issues = check_union_type_buggy(source)
        assert len(issues) == 1, (
            f"Buggy checker should flag Annotated[Union[...]], got {issues}"
        )

    def test_buggy_skips_direct_pipe_union(self):
        """Confirm the buggy checker correctly skips top-level pipe unions."""
        source = """\
        def foo() -> str | int:
            pass
        """
        issues = check_union_type_buggy(source)
        assert len(issues) == 0, (
            f"Buggy checker should not flag direct pipe union, got {issues}"
        )

    def test_buggy_flags_direct_union(self):
        """Confirm the buggy checker flags direct Union[X, Y]."""
        source = """\
        from typing import Union
        def foo() -> Union[str, int]:
            pass
        """
        issues = check_union_type_buggy(source)
        assert len(issues) == 1, (
            f"Buggy checker should flag Union[str, int], got {issues}"
        )
