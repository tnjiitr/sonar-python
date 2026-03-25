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
 * Tests for JumpInFinallyCheck (S1143) with Python 3.14 specific patterns.
 * PEP 765 makes return/break/continue in finally blocks a SyntaxWarning in 3.14
 * (and will be SyntaxError in future Python).
 * These tests verify that the existing check correctly detects all PEP 765 violations,
 * including in combination with PEP 758 exception syntax.
 */
class Python314JumpInFinallyCheckTest {

  @Test
  void test_pep765_jump_in_finally_patterns() {
    PythonCheckVerifier.verify("src/test/resources/checks/python314/jumpInFinallyPep765.py", new JumpInFinallyCheck());
  }
}
