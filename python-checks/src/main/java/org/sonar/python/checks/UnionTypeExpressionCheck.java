/*
 * SonarQube Python Plugin
 * Copyright (C) 2011-2025 SonarSource Sàrl
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
package org.sonar.python.checks;

import java.util.Optional;
import org.sonar.check.Rule;
import org.sonar.plugins.python.api.PythonSubscriptionCheck;
import org.sonar.plugins.python.api.PythonVersionUtils;
import org.sonar.plugins.python.api.SubscriptionContext;
import org.sonar.plugins.python.api.symbols.Symbol;
import org.sonar.plugins.python.api.tree.Expression;
import org.sonar.plugins.python.api.tree.SubscriptionExpression;
import org.sonar.plugins.python.api.tree.Tree;
import org.sonar.plugins.python.api.tree.TypeAnnotation;
import org.sonar.plugins.python.api.types.InferredType;
import org.sonar.python.tree.TreeUtils;
import org.sonar.python.types.InferredTypes;

@Rule(key = "S6546")
public class UnionTypeExpressionCheck extends PythonSubscriptionCheck {

  private static final String MESSAGE = "Use a union type expression for this type hint.";

  @Override
  public void initialize(Context context) {
    context.registerSyntaxNodeConsumer(Tree.Kind.PARAMETER_TYPE_ANNOTATION, UnionTypeExpressionCheck::checkTypeAnnotation);
    context.registerSyntaxNodeConsumer(Tree.Kind.RETURN_TYPE_ANNOTATION, UnionTypeExpressionCheck::checkTypeAnnotation);
    context.registerSyntaxNodeConsumer(Tree.Kind.VARIABLE_TYPE_ANNOTATION, UnionTypeExpressionCheck::checkTypeAnnotation);
  }

  private static void checkTypeAnnotation(SubscriptionContext ctx) {
    if (!supportsUnionTypeExpressions(ctx)) {
      return;
    }

    TypeAnnotation typeAnnotation = (TypeAnnotation) ctx.syntaxNode();
    Expression expression = typeAnnotation.expression();
    if (expression.is(Tree.Kind.BITWISE_OR)) {
      return;
    }

    if (containsBitwiseOrInAnnotated(expression)) {
      return;
    }

    InferredType type = InferredTypes.fromTypeAnnotation(typeAnnotation);
    String fqn = InferredTypes.fullyQualifiedTypeName(type);
    if ("typing.Union".equals(fqn)) {
      ctx.addIssue(expression, MESSAGE);
    }
  }

  /**
   * Checks if the expression is an Annotated subscription whose first type argument
   * uses bitwise OR (union pipe syntax). This prevents false positives where
   * Annotated[X | Y, metadata] is incorrectly flagged as needing union type expression,
   * even though X | Y IS the union type expression.
   *
   * @see <a href="https://community.sonarsource.com/t/false-positive-for-python-s6546/179644">Community report</a>
   */
  private static boolean containsBitwiseOrInAnnotated(Expression expression) {
    if (expression.is(Tree.Kind.SUBSCRIPTION)) {
      SubscriptionExpression subscription = (SubscriptionExpression) expression;
      Optional<Symbol> objectSymbol = TreeUtils.getSymbolFromTree(subscription.object());
      if (objectSymbol.isPresent() && "typing.Annotated".equals(objectSymbol.get().fullyQualifiedName())) {
        var subscripts = subscription.subscripts().expressions();
        if (!subscripts.isEmpty()) {
          Expression firstArg = subscripts.get(0);
          return containsBitwiseOrExpression(firstArg);
        }
      }
    }
    return false;
  }

  /**
   * Recursively checks if an expression contains a bitwise OR (union pipe syntax),
   * including within nested subscription expressions like Dict[str, X | Y].
   */
  private static boolean containsBitwiseOrExpression(Expression expression) {
    if (expression.is(Tree.Kind.BITWISE_OR)) {
      return true;
    }
    if (expression.is(Tree.Kind.SUBSCRIPTION)) {
      SubscriptionExpression subscription = (SubscriptionExpression) expression;
      return subscription.subscripts().expressions().stream()
        .anyMatch(UnionTypeExpressionCheck::containsBitwiseOrExpression);
    }
    return false;
  }

  private static boolean supportsUnionTypeExpressions(SubscriptionContext ctx) {
    return PythonVersionUtils.areSourcePythonVersionsGreaterOrEqualThan(ctx.sourcePythonVersions(), PythonVersionUtils.Version.V_310);
  }
}
