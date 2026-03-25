/*
 * SonarQube Python Plugin
 * Copyright (C) 2011-2025 SonarSource Sarl
 * mailto:info AT sonarsource DOT com
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the Sonar Source-Available License Version 1, as published by SonarSource SA.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the Sonar Source-Available License for more details.
 *
 * You should have received a copy of the Sonar Source-Available License
 * along with this program; if not, see https://sonarsource.com/license/ssal/
 */
package org.sonar.python.parser;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

/**
 * Tests that verify the Python parser can successfully parse Python 3.14 syntax features.
 * These tests focus on:
 * - Template string literals (PEP 750)
 * - Simplified exception syntax (PEP 758)
 * - Control flow in finally blocks (PEP 765)
 * - Deferred annotations (PEP 649)
 */
class Python314SyntaxTest {

  private final PythonParser parser = PythonParser.create();

  // ========== PEP 750: Template String Literals (t-strings) ==========

  @Test
  void parse_basic_tstring() {
    assertDoesNotThrow(() -> parser.parse("x = t\"Hello {name}\""));
  }

  @Test
  void parse_tstring_empty() {
    assertDoesNotThrow(() -> parser.parse("x = t''"));
  }

  @Test
  void parse_tstring_empty_double_quote() {
    assertDoesNotThrow(() -> parser.parse("x = t\"\""));
  }

  @Test
  void parse_tstring_triple_quoted() {
    assertDoesNotThrow(() -> parser.parse("x = t'''hello'''"));
  }

  @Test
  void parse_tstring_triple_double_quoted() {
    assertDoesNotThrow(() -> parser.parse("x = t\"\"\"hello\"\"\""));
  }

  @Test
  void parse_tstring_with_interpolation() {
    assertDoesNotThrow(() -> parser.parse("x = t'hello {var}!'"));
  }

  @Test
  void parse_tstring_with_escaped_braces() {
    assertDoesNotThrow(() -> parser.parse("x = t'{{abc}}'"));
  }

  @Test
  void parse_tstring_with_escaped_and_interpolation() {
    assertDoesNotThrow(() -> parser.parse("x = t'{{abc}}{xyz}'"));
  }

  @Test
  void parse_tstring_with_format_specifier() {
    assertDoesNotThrow(() -> parser.parse("x = t'{today:%B %d, %Y}'"));
  }

  @Test
  void parse_tstring_with_conversion() {
    assertDoesNotThrow(() -> parser.parse("x = t'{x!a}'"));
  }

  @Test
  void parse_tstring_with_self_documenting() {
    assertDoesNotThrow(() -> parser.parse("x = t'{user=!s}'"));
  }

  @Test
  void parse_tstring_with_nested_format_specifier() {
    assertDoesNotThrow(() -> parser.parse("x = t'result: {value:{width}.{precision}}'"));
  }

  @Test
  void parse_tstring_uppercase_prefix() {
    assertDoesNotThrow(() -> parser.parse("x = T\"Hello {name}\""));
  }

  @Test
  void parse_tstring_raw_prefix_tr() {
    assertDoesNotThrow(() -> parser.parse("x = tr\"\\\\s*{var}\""));
  }

  @Test
  void parse_tstring_raw_prefix_rt() {
    assertDoesNotThrow(() -> parser.parse("x = rt\"\\\\s*{var}\""));
  }

  @Test
  void parse_tstring_raw_prefix_rT() {
    assertDoesNotThrow(() -> parser.parse("x = rT'\\\\\\\\'"));
  }

  @Test
  void parse_tstring_multiline() {
    assertDoesNotThrow(() -> parser.parse("x = t\"Foo {\n    h\n    }\""));
  }

  @Test
  void parse_tstring_with_nested_call() {
    assertDoesNotThrow(() -> parser.parse("x = t\"This is: {\"\\n\".join(songs)}\""));
  }

  @Test
  void parse_tstring_with_unicode_escape() {
    assertDoesNotThrow(() -> parser.parse("x = t'\\N{RIGHTWARDS ARROW}'"));
  }

  @Test
  void parse_tstring_with_backslash() {
    assertDoesNotThrow(() -> parser.parse("x = t\" \\\\\""));
  }

  @Test
  void parse_tstring_with_type_annotation() {
    assertDoesNotThrow(() -> parser.parse("from string.templatelib import Template\ntemplate: Template = t\"Hello {name}\""));
  }

  // ========== PEP 758: Simplified Exception Syntax ==========

  @Test
  void parse_except_multiple_exceptions_without_parentheses() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept ArithmeticError, ValueError:\n    print(\"caught\")"));
  }

  @Test
  void parse_except_multiple_exceptions_with_parentheses_traditional() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept (ValueError, TypeError):\n    print(\"caught\")"));
  }

  @Test
  void parse_except_star_single_exception() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept* ValueError:\n    print(\"caught\")"));
  }

  @Test
  void parse_except_single_exception_with_as() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept FileNotFoundError as e:\n    print(e)"));
  }

  @Test
  void parse_except_parenthesized_with_as() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept (BrokenPipeError, BufferError) as e:\n    print(e)"));
  }

  @Test
  void parse_except_mixed_parenthesized_and_unparenthesized() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept (MemoryError, OverflowError), TypeError:\n    print(\"mixed\")"));
  }

  @Test
  void parse_except_old_python2_syntax_still_works() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept OSError, e:\n    print(e)"));
  }

  @Test
  void parse_except_multiple_except_clauses_mixed_syntax() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept FileNotFoundError as e:\n    print(e)\nexcept ArithmeticError, ValueError:\n    print(\"new syntax\")"));
  }

  @Test
  void parse_except_three_exceptions_without_parentheses() {
    assertDoesNotThrow(() -> parser.parse(
      "try:\n    foo()\nexcept ValueError, TypeError, KeyError:\n    print(\"three\")"));
  }

  // ========== PEP 765: Control Flow in Finally Blocks ==========

  @Test
  void parse_return_in_finally() {
    assertDoesNotThrow(() -> parser.parse(
      "def f():\n    try:\n        pass\n    finally:\n        return 1"));
  }

  @Test
  void parse_break_in_finally() {
    assertDoesNotThrow(() -> parser.parse(
      "for i in range(3):\n    try:\n        pass\n    finally:\n        break"));
  }

  @Test
  void parse_continue_in_finally() {
    assertDoesNotThrow(() -> parser.parse(
      "for i in range(3):\n    try:\n        pass\n    finally:\n        continue"));
  }

  @Test
  void parse_nested_try_finally_with_return() {
    assertDoesNotThrow(() -> parser.parse(
      "def f():\n    try:\n        try:\n            pass\n        finally:\n            return 1\n    finally:\n        return 2"));
  }

  // ========== PEP 649: Deferred Annotations ==========

  @Test
  void parse_function_with_forward_reference_annotation() {
    assertDoesNotThrow(() -> parser.parse(
      "def foo(x: MyClass) -> MyClass:\n    pass"));
  }

  @Test
  void parse_class_with_forward_reference_annotation() {
    assertDoesNotThrow(() -> parser.parse(
      "class Node:\n    left: Node\n    right: Node"));
  }

  @Test
  void parse_function_with_complex_annotation() {
    assertDoesNotThrow(() -> parser.parse(
      "def foo(x: list[int | str]) -> dict[str, list[int]]:\n    pass"));
  }

  @Test
  void parse_variable_annotation_with_expression() {
    assertDoesNotThrow(() -> parser.parse(
      "x: int | str = 42\ny: list[tuple[int, ...]] = []"));
  }

  @Test
  void parse_annotation_with_string_literal() {
    assertDoesNotThrow(() -> parser.parse(
      "def foo(x: 'MyClass') -> 'MyClass':\n    pass"));
  }

  @Test
  void parse_annotation_with_union_types() {
    assertDoesNotThrow(() -> parser.parse(
      "def foo(x: int | str | None) -> int | None:\n    pass"));
  }
}
