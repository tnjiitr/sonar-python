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
 * Tests that Python 3.14 deferred annotations (PEP 649) can be parsed without errors.
 * PEP 649 changes when annotations are evaluated (deferred instead of eager), but
 * the syntax itself does not change. These tests verify the parser handles all
 * annotation patterns correctly, including forward references and complex type expressions.
 */
class Python314DeferredAnnotationsParsingTest {

  @Test
  void test_pep649_annotation_patterns_parse_without_errors() {
    PythonCheckVerifier.verifyNoIssue("src/test/resources/checks/python314/deferredAnnotationsPep649.py", new ParsingErrorCheck());
  }
}
