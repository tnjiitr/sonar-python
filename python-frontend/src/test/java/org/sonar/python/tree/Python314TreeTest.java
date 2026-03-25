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
package org.sonar.python.tree;

import org.junit.jupiter.api.Test;
import org.sonar.plugins.python.api.tree.ExceptClause;
import org.sonar.plugins.python.api.tree.Expression;
import org.sonar.plugins.python.api.tree.FileInput;
import org.sonar.plugins.python.api.tree.FormattedExpression;
import org.sonar.plugins.python.api.tree.StringElement;
import org.sonar.plugins.python.api.tree.StringLiteral;
import org.sonar.plugins.python.api.tree.Tree;
import org.sonar.plugins.python.api.tree.TryStatement;
import org.sonar.python.api.PythonGrammar;
import org.sonar.python.parser.RuleTest;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tests for the tree representation of Python 3.14 syntax features.
 * Verifies correct AST structure for:
 * - Template string literals (PEP 750) - isTemplate() flag, interpolation
 * - Simplified exception syntax (PEP 758) - multiple exceptions without parentheses
 * - Deferred annotations (PEP 649)
 */
class Python314TreeTest extends RuleTest {

  private final PythonTreeMaker treeMaker = new PythonTreeMaker();

  // ========== PEP 750: Template String Literals ==========

  @Test
  void tstring_is_template() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'Hello {name}'", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    assertThat(stringLiteral.stringElements()).hasSize(1);
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.isInterpolated()).isFalse();
    assertThat(element.prefix()).isEqualTo("t");
  }

  @Test
  void tstring_uppercase_is_template() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("T'Hello {name}'", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.isInterpolated()).isFalse();
    assertThat(element.prefix()).isEqualTo("T");
  }

  @Test
  void tstring_raw_is_template() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("tr'Hello {name}'", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.isInterpolated()).isFalse();
    assertThat(element.prefix()).isEqualTo("tr");
  }

  @Test
  void tstring_rt_prefix_is_template() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("rt'Hello {name}'", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.prefix()).isEqualTo("rt");
  }

  @Test
  void tstring_has_formatted_expressions() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'Hello {name}!'", treeMaker::expression);
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.formattedExpressions()).hasSize(1);
    FormattedExpression formattedExpression = element.formattedExpressions().get(0);
    assertThat(formattedExpression.expression()).isNotNull();
    assertThat(formattedExpression.expression().is(Tree.Kind.NAME)).isTrue();
  }

  @Test
  void tstring_multiple_interpolations() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'{x} and {y}'", treeMaker::expression);
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.formattedExpressions()).hasSize(2);
  }

  @Test
  void tstring_with_format_specifier() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'{value:.2f}'", treeMaker::expression);
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.formattedExpressions()).hasSize(1);
    FormattedExpression formattedExpression = element.formattedExpressions().get(0);
    assertThat(formattedExpression.formatSpecifier()).isNotNull();
  }

  @Test
  void tstring_with_conversion() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'{x!r}'", treeMaker::expression);
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.formattedExpressions()).hasSize(1);
  }

  @Test
  void tstring_empty() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t''", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.formattedExpressions()).isEmpty();
  }

  @Test
  void tstring_triple_quoted() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'''hello'''", treeMaker::expression);
    assertThat(expr.is(Tree.Kind.STRING_LITERAL)).isTrue();
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.isTemplate()).isTrue();
    assertThat(element.isTripleQuoted()).isTrue();
  }

  @Test
  void tstring_trimmed_quotes_value() {
    setRootRule(PythonGrammar.ATOM);
    Expression expr = parse("t'Hello {name}'", treeMaker::expression);
    StringLiteral stringLiteral = (StringLiteral) expr;
    StringElement element = stringLiteral.stringElements().get(0);
    assertThat(element.trimmedQuotesValue()).isEqualTo("Hello {name}");
  }

  @Test
  void tstring_is_not_fstring() {
    setRootRule(PythonGrammar.ATOM);
    Expression tExpr = parse("t'Hello {name}'", treeMaker::expression);
    StringElement tElement = ((StringLiteral) tExpr).stringElements().get(0);

    Expression fExpr = parse("f'Hello {name}'", treeMaker::expression);
    StringElement fElement = ((StringLiteral) fExpr).stringElements().get(0);

    assertThat(tElement.isTemplate()).isTrue();
    assertThat(tElement.isInterpolated()).isFalse();

    assertThat(fElement.isTemplate()).isFalse();
    assertThat(fElement.isInterpolated()).isTrue();
  }

  // ========== PEP 758: Simplified Exception Syntax ==========

  @Test
  void except_clause_multiple_unparenthesized_exceptions() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept ArithmeticError, ValueError:\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(1);
    ExceptClause exceptClause = tryStatement.exceptClauses().get(0);
    assertThat(exceptClause.exception()).isNotNull();
  }

  @Test
  void except_clause_single_exception() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept ValueError:\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(1);
    ExceptClause exceptClause = tryStatement.exceptClauses().get(0);
    assertThat(exceptClause.exception()).isNotNull();
    assertThat(exceptClause.starToken()).isNull();
  }

  @Test
  void except_clause_parenthesized_multiple() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept (ValueError, TypeError):\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(1);
    assertThat(tryStatement.exceptClauses().get(0).exception()).isNotNull();
  }

  @Test
  void except_clause_with_as() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept FileNotFoundError as e:\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(1);
    ExceptClause exceptClause = tryStatement.exceptClauses().get(0);
    assertThat(exceptClause.exception()).isNotNull();
    assertThat(exceptClause.exceptionInstance()).isNotNull();
  }

  @Test
  void except_star_clause() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept* ValueError:\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(1);
    ExceptClause exceptClause = tryStatement.exceptClauses().get(0);
    assertThat(exceptClause.starToken()).isNotNull();
  }

  @Test
  void multiple_except_clauses_traditional_and_pep758() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "try:\n    pass\nexcept FileNotFoundError as e:\n    pass\nexcept ArithmeticError, ValueError:\n    pass",
      treeMaker::fileInput);
    TryStatement tryStatement = (TryStatement) fileInput.statements().statements().get(0);
    assertThat(tryStatement.exceptClauses()).hasSize(2);
  }

  // ========== PEP 649: Deferred Annotations ==========

  @Test
  void function_annotation_forward_reference() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "def foo(x: MyClass) -> MyClass:\n    pass",
      treeMaker::fileInput);
    assertThat(fileInput.statements()).isNotNull();
    assertThat(fileInput.statements().statements()).hasSize(1);
  }

  @Test
  void class_with_self_referencing_annotation() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "class Node:\n    left: Node\n    right: Node",
      treeMaker::fileInput);
    assertThat(fileInput.statements()).isNotNull();
    assertThat(fileInput.statements().statements()).hasSize(1);
  }

  @Test
  void complex_type_annotation() {
    setRootRule(PythonGrammar.FILE_INPUT);
    FileInput fileInput = parse(
      "def foo(x: list[int | str]) -> dict[str, list[int]]:\n    pass",
      treeMaker::fileInput);
    assertThat(fileInput.statements()).isNotNull();
  }
}
