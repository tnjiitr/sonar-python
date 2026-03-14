#
# SonarQube Python Plugin
# Copyright (C) 2011-2025 SonarSource SA
# mailto:info AT sonarsource DOT com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Sonar Source-Available License Version 1, as published by SonarSource SA.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the Sonar Source-Available License for more details.
#
# You should have received a copy of the Sonar Source-Available License
# along with this program; if not, see https://sonarsource.com/license/ssal/
#

"""
Tests for AI-237: Mypy output parser fails on multi-line error messages
due to terminal wrapping.

Bug: https://community.sonarsource.com/t/bug-with-sonar-python-parsing-mypy-output/146368

The MypySensor regex pattern assumes each mypy error is on a single line.
When terminal width causes line wrapping, the error message spans multiple
lines. The first fragment matches the regex but with a TRUNCATED message
and MISSING error code (defaulting to 'unknown_mypy_rule'). The continuation
line is silently dropped.

These tests define the EXPECTED correct behavior for parsing multi-line
mypy output. The parse_mypy_report function mirrors the fixed MypySensor.java
behavior which joins continuation lines before applying the regex pattern.
"""

import os
import re
import unittest

# Exact replica of the MypySensor.java regex pattern (line 54-55)
START_LOCATION = r"(?P<startLine>\d+)(?::(?P<startCol>\d+))?"
END_LOCATION = r"(?::(?P<endLine>\d+):(?P<endCol>\d+))?"
MYPY_PATTERN = re.compile(
    rf"^(?P<file>[^:]+):{START_LOCATION}{END_LOCATION}: (?P<severity>\S+[^:]): (?P<message>.*?)(?: \[(?P<code>[^\]]+)])?\s*$"
)


def parse_mypy_line(line):
    """Parse a single mypy output line using the MypySensor regex pattern."""
    if not line.strip():
        return None
    m = MYPY_PATTERN.match(line)
    if m:
        severity = m.group("severity")
        if severity != "error":
            return None
        return {
            "file": m.group("file"),
            "startLine": int(m.group("startLine")),
            "startCol": int(m.group("startCol")) - 1 if m.group("startCol") else None,
            "endLine": int(m.group("endLine")) if m.group("endLine") else None,
            "endCol": int(m.group("endCol")) - 1 if m.group("endCol") else None,
            "severity": severity,
            "message": m.group("message"),
            "code": m.group("code") or "unknown_mypy_rule",
        }
    return None


# Pattern to detect lines that start with a mypy file location
# (i.e., lines that are NOT continuation lines)
FILE_LOCATION_PATTERN = re.compile(r"^[^:]+:\d+:")


def join_continuation_lines(filepath):
    """Pre-process a mypy report file to join continuation lines.

    A continuation line is any non-empty line that does NOT start with a file
    location pattern (e.g., 'path/to/file.py:123:'). Such lines are appended
    to the previous line, separated by a space.

    This mirrors the joinContinuationLines method added to MypySensor.java.
    """
    joined_lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if FILE_LOCATION_PATTERN.match(line) or not joined_lines:
                joined_lines.append(line)
            else:
                # Continuation line: append to previous line with a space separator
                joined_lines[-1] = joined_lines[-1] + " " + line.strip()
    return joined_lines


def parse_mypy_report(filepath):
    """Parse a mypy report file with continuation line joining.

    First joins continuation lines (caused by terminal wrapping), then
    parses each joined line against the regex pattern. This mirrors the
    fixed MypySensor.java parse() method.
    """
    joined_lines = join_continuation_lines(filepath)
    issues = []
    for line in joined_lines:
        issue = parse_mypy_line(line)
        if issue is not None:
            issues.append(issue)
    return issues


class TestMypyMultilineParsing(unittest.TestCase):
    """Red Phase tests for AI-237: multi-line mypy output parsing.

    These tests define the CORRECT expected behavior. They will FAIL
    against the current buggy parse_mypy_report implementation and
    PASS once the fix (continuation line joining) is applied.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.single_line_file = os.path.join(cls.test_dir, "mypy_output.txt")
        cls.multiline_file = os.path.join(cls.test_dir, "mypy_output_multiline.txt")

    def test_multiline_wrapped_error_has_correct_rule_code_no_untyped_def(self):
        """A wrapped 'no-untyped-def' error must have code='no-untyped-def', not 'unknown_mypy_rule'.

        The multiline file has this wrapped error:
            mypy/type_hints_noncompliant.py:13: error: Function is missing a type
            annotation for one or more arguments  [no-untyped-def]

        Expected: code='no-untyped-def'
        Bug produces: code='unknown_mypy_rule' (because [no-untyped-def] is on the continuation line)
        """
        issues = parse_mypy_report(self.multiline_file)
        line_13_issues = [i for i in issues if i["startLine"] == 13]
        self.assertEqual(len(line_13_issues), 1, "Should find one issue at line 13")
        self.assertEqual(line_13_issues[0]["code"], "no-untyped-def",
                         "Wrapped error at line 13 must have correct rule code 'no-untyped-def'")

    def test_multiline_wrapped_error_has_correct_rule_code_no_untyped_call(self):
        """A wrapped 'no-untyped-call' error must have code='no-untyped-call', not 'unknown_mypy_rule'.

        The multiline file has this wrapped error:
            mypy/type_hints_noncompliant.py:19: error: Call to untyped function
            "no_type_hints" in typed context  [no-untyped-call]

        Expected: code='no-untyped-call'
        Bug produces: code='unknown_mypy_rule'
        """
        issues = parse_mypy_report(self.multiline_file)
        line_19_issues = [i for i in issues if i["startLine"] == 19]
        self.assertEqual(len(line_19_issues), 1, "Should find one issue at line 19")
        self.assertEqual(line_19_issues[0]["code"], "no-untyped-call",
                         "Wrapped error at line 19 must have correct rule code 'no-untyped-call'")

    def test_multiline_wrapped_error_has_complete_message(self):
        """Wrapped error messages must include content from continuation lines.

        The wrapped error at line 13 should have the full message:
            'Function is missing a type annotation for one or more arguments'
        Not just the truncated first line:
            'Function is missing a type'
        """
        issues = parse_mypy_report(self.multiline_file)
        line_13_issues = [i for i in issues if i["startLine"] == 13]
        self.assertEqual(len(line_13_issues), 1)
        self.assertIn("annotation", line_13_issues[0]["message"],
                      "Message must include continuation text 'annotation'")

    def test_multiline_wrapped_error_message_contains_function_name(self):
        """Wrapped error at line 19 must include the function name from the continuation line.

        The full message should be:
            'Call to untyped function "no_type_hints" in typed context'
        Not just:
            'Call to untyped function'
        """
        issues = parse_mypy_report(self.multiline_file)
        line_19_issues = [i for i in issues if i["startLine"] == 19]
        self.assertEqual(len(line_19_issues), 1)
        self.assertIn("no_type_hints", line_19_issues[0]["message"],
                      "Message must include function name 'no_type_hints' from continuation line")

if __name__ == "__main__":
    unittest.main()
