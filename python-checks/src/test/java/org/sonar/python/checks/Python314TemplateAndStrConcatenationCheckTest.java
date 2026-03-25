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

import java.util.EnumSet;
import org.junit.jupiter.api.Test;
import org.sonar.plugins.python.api.ProjectPythonVersion;
import org.sonar.plugins.python.api.PythonVersionUtils;
import org.sonar.python.checks.utils.PythonCheckVerifier;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tests for TemplateAndStrConcatenationCheck with advanced Python 3.14 t-string patterns.
 * Verifies that the check correctly detects t-string + regular string concatenation
 * for various t-string prefix forms (t, T, tr, rt, tR, rT, Tr, RT).
 */
class Python314TemplateAndStrConcatenationCheckTest {

  @Test
  void test_advanced_tstring_concatenation_patterns() {
    ProjectPythonVersion.setCurrentVersions(EnumSet.of(PythonVersionUtils.Version.V_314));
    PythonCheckVerifier.verify("src/test/resources/checks/python314/tStringAdvancedPatterns.py", new TemplateAndStrConcatenationCheck());
  }

  @Test
  void test_tstring_concatenation_not_detected_on_older_python() {
    ProjectPythonVersion.setCurrentVersions(EnumSet.of(PythonVersionUtils.Version.V_313, PythonVersionUtils.Version.V_314));
    var issues = PythonCheckVerifier.issues("src/test/resources/checks/python314/tStringAdvancedPatterns.py", new TemplateAndStrConcatenationCheck());
    assertThat(issues).isEmpty();
  }
}
