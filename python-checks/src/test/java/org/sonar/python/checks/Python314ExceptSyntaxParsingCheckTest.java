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
package org.sonar.python.checks;

import org.junit.jupiter.api.Test;
import org.sonar.python.checks.utils.PythonCheckVerifier;

/**
 * Tests that Python files using PEP 758 (simplified exception syntax) can be parsed without errors.
 * Uses the ParsingErrorCheck to verify no parsing errors occur when analyzing files with
 * the new unparenthesized multiple exception syntax.
 */
class Python314ExceptSyntaxParsingCheckTest {

  @Test
  void test_pep758_exception_syntax_parses_without_errors() {
    PythonCheckVerifier.verifyNoIssue("src/test/resources/checks/python314/exceptSyntaxPep758.py", new ParsingErrorCheck());
  }
}
