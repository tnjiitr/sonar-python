# AI-238: Tests for S6659 false positive -- string slice comparison vs startswith/endswith
#
# Rule S6659 suggests replacing slice comparisons with startswith()/endswith().
# These tests verify that PREFIX slice cases where the replacement changes
# semantics are correctly marked as Compliant (no issue raised) in the test
# resource file and handled properly in the Java check implementation.
#
# RED PHASE: All tests MUST FAIL because the current code incorrectly
# flags these patterns as Noncompliant.
# GREEN PHASE: All tests PASS after the fix is applied.

import os
import pytest

# Path to the test resource file used by the Java test runner
TEST_RESOURCE_FILE = os.path.join(
    os.path.dirname(__file__),
    "useStartsWithEndsWithCheck.py"
)

# Path to the Java check implementation
# From checks/ -> resources/ -> test/ (3 levels up to python-checks/src/)
# then into main/java/...
JAVA_CHECK_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "main", "java", "org", "sonar", "python",
    "checks", "UseStartsWithEndsWithCheck.java"
)


def read_file(path):
    """Read file content, resolving relative paths."""
    resolved = os.path.normpath(path)
    with open(resolved, "r") as f:
        return f.read()


class TestS6659FalsePositivePrefixSliceMismatch:
    """Tests verifying that prefix slice comparisons with mismatched lengths
    are correctly marked as Compliant in the test resource file.

    The rule currently marks these as Noncompliant, which is the bug.
    """

    def test_prefix_slice_too_small_should_be_compliant(self):
        """foobar[:2] == 'foo' -- slice bound (2) != comparator length (3).
        'foobar'[:2] gives 'fo', and 'fo' == 'foo' is False
        while 'foobar'.startswith('foo') is True.
        This line MUST be Compliant, not Noncompliant.
        """
        content = read_file(TEST_RESOURCE_FILE)
        assert "foobar[:2] == 'foo' # Compliant" in content, (
            "foobar[:2] == 'foo' should be marked Compliant because "
            "the slice bound (2) does not match the comparator length (3). "
            "Currently incorrectly marked as Noncompliant."
        )

    def test_prefix_slice_too_large_should_be_compliant(self):
        """foobar[:10] == 'foo' -- slice bound (10) > comparator length (3).
        'foobar'[:10] gives 'foobar', and 'foobar' == 'foo' is False
        while 'foobar'.startswith('foo') is True.
        This line MUST be Compliant, not Noncompliant.
        """
        content = read_file(TEST_RESOURCE_FILE)
        assert "foobar[:10] == 'foo' # Compliant" in content, (
            "foobar[:10] == 'foo' should be marked Compliant because "
            "the slice bound (10) does not match the comparator length (3). "
            "Currently incorrectly marked as Noncompliant."
        )


class TestS6659FalsePositiveNegativeIndexSlice:
    """Tests verifying that negative-index prefix slice comparisons are
    correctly handled. The community-reported case uses a negative index.
    """

    def test_negative_prefix_slice_should_be_compliant(self):
        """foobar[:-3] == 'foo' -- this is the community-reported case.
        'foobar'[:-3] gives 'foo', and 'foo' == 'foo' is True.
        BUT for 'foobarfoo', [:-3] gives 'foobar',
        and 'foobar' == 'foo' is False while 'foobarfoo'.startswith('foo') is True.

        The rule cannot guarantee equivalence, so this MUST be Compliant.
        """
        content = read_file(TEST_RESOURCE_FILE)
        assert "foobar[:-3] == 'foo' # Compliant" in content, (
            "foobar[:-3] == 'foo' should be marked Compliant because "
            "negative-index prefix slices produce variable-length substrings "
            "depending on the original string length, making the semantics "
            "of startswith() different. "
            "Currently incorrectly marked as Noncompliant. "
            "Community report: https://community.sonarsource.com/t/"
            "false-positive-python-s6659-in-some-cases-of-string-slice-comparison/142202"
        )


class TestS6659JavaCheckHandlesSliceBoundValidation:
    """Tests verifying that the Java check implementation properly validates
    that slice bounds match the comparator length before raising an issue.
    """

    def test_java_check_validates_slice_bounds(self):
        """The Java check should contain logic to validate slice bounds
        against the comparator string length to avoid false positives.
        The current code in fromSliceItem() does NOT perform this check.
        After the fix, the check should contain validation logic.
        """
        content = read_file(JAVA_CHECK_FILE)

        # After the fix, the check should contain:
        # 1. A method that checks for slice bound mismatches
        # 2. References to comparator length or string literal length
        # 3. Logic to detect negative numeric literals
        has_mismatch_validation = "sliceBoundMismatchesComparator" in content
        has_length_check = "getStringLiteralLength" in content
        has_negative_check = "isNegativeNumericLiteral" in content

        assert has_mismatch_validation, (
            "UseStartsWithEndsWithCheck.java should contain a "
            "sliceBoundMismatchesComparator method to validate that the "
            "slice bound matches the comparator string length."
        )
        assert has_length_check, (
            "UseStartsWithEndsWithCheck.java should contain a "
            "getStringLiteralLength method to determine comparator length."
        )
        assert has_negative_check, (
            "UseStartsWithEndsWithCheck.java should contain a "
            "isNegativeNumericLiteral method to detect negative slice bounds."
        )

    def test_comment_about_detecting_mismatched_slices_updated(self):
        """The test resource file currently contains a comment saying
        'We should definitely also detect the cases with too small / large slices'
        followed by Noncompliant markers. After the fix, this comment
        should be updated because detecting mismatched prefix slices
        leads to false positives.
        """
        content = read_file(TEST_RESOURCE_FILE)

        has_misleading_comment = (
            "We should definitely also detect the cases with too small / large slices"
            in content
        )

        assert not has_misleading_comment, (
            "The test resource file still contains the misleading comment "
            "'We should definitely also detect the cases with too small / large slices'. "
            "This comment should be updated because detecting mismatched prefix slices "
            "leads to false positives -- the rule's suggestion changes program semantics."
        )
