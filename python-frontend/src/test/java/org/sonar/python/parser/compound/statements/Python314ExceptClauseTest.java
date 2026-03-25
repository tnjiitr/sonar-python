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
package org.sonar.python.parser.compound.statements;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.sonar.python.api.PythonGrammar;
import org.sonar.python.parser.RuleTest;

import static org.sonar.python.parser.PythonParserAssert.assertThat;

/**
 * Tests for PEP 758: Simplified Exception Syntax in Python 3.14.
 * Verifies the parser can handle:
 * - Multiple exceptions without parentheses: except ValueError, TypeError:
 * - except* with single exception
 * - Mixed parenthesized and unparenthesized
 * - Traditional parenthesized syntax continues to work
 */
class Python314ExceptClauseTest extends RuleTest {

  @BeforeEach
  void init() {
    setRootRule(PythonGrammar.EXCEPT_CLAUSE);
  }

  @Test
  void bare_except() {
    assertThat(p).matches("except");
  }

  @Test
  void single_exception() {
    assertThat(p).matches("except TEST");
  }

  @Test
  void except_star_single() {
    assertThat(p).matches("except* TEST");
  }

  @Test
  void exception_with_as() {
    assertThat(p).matches("except TEST as TEST");
  }

  @Test
  void old_python2_comma_syntax() {
    assertThat(p).matches("except TEST , TEST");
  }

  @Test
  void pep758_multiple_exceptions_without_parentheses() {
    assertThat(p).matches("except TEST , TEST , TEST");
  }

  @Test
  void pep758_two_exceptions_without_parentheses() {
    assertThat(p).matches("except TEST , TEST");
  }

  @Test
  void parenthesized_multiple_exceptions() {
    assertThat(p).matches("except ( TEST , TEST )");
  }

  @Test
  void parenthesized_with_as() {
    assertThat(p).matches("except ( TEST , TEST ) as TEST");
  }
}
