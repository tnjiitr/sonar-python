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
package org.sonar.python.lexer;

import com.google.common.collect.ImmutableSet;
import com.sonar.sslr.api.GenericTokenType;
import com.sonar.sslr.api.Token;
import com.sonar.sslr.impl.Lexer;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.sonar.python.api.PythonPunctuator;
import org.sonar.python.api.PythonTokenType;

import static com.sonar.sslr.test.lexer.LexerMatchers.hasToken;
import static org.hamcrest.Matchers.allOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Tests for t-string (template string literal) lexing (PEP 750).
 * Verifies that the lexer correctly tokenizes t-strings with TSTRING_START token type.
 */
class TStringLexerTest {

  private static TestLexer lexer;

  @BeforeAll
  static void init() {
    lexer = new TestLexer();
  }

  private static class TestLexer {
    private LexerState lexerState = new LexerState();
    private Lexer lexer = PythonLexer.create(lexerState);

    List<Token> lex(String code) {
      lexerState.reset();
      return lexer.lex(code);
    }
  }

  @Test
  void tstring_prefixes() {
    Set<String> tstringPrefixes = ImmutableSet.of(
      "T",
      "t",
      "tr",
      "Tr",
      "tR",
      "TR",
      "rt",
      "rT",
      "Rt",
      "RT");
    for (String prefix : tstringPrefixes) {
      assertTrue(allOf(
        hasToken(prefix + "'", PythonTokenType.TSTRING_START),
        hasToken("'", PythonTokenType.FSTRING_END)).matches(lexer.lex(prefix + "''")),
        "Failed for prefix: " + prefix);
    }
  }

  @Test
  void tstring_empty() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"\"")));
  }

  @Test
  void tstring_no_code() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken(" te st ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\" te st \"")));
  }

  @Test
  void tstring_code_only() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("+", PythonPunctuator.PLUS),
      hasToken("b", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"{a + b}\"")));
  }

  @Test
  void tstring_with_text_and_code() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("test ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("+", PythonPunctuator.PLUS),
      hasToken("b", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken(" foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"test {a + b} foo\"")));
  }

  @Test
  void tstring_multiple_interpolations() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken(" + ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("b", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"{a } + { b }\"")));
  }

  @Test
  void tstring_single_quote() {
    assertTrue(allOf(
      hasToken("t'", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken(" foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("'", PythonTokenType.FSTRING_END)).matches(lexer.lex("t'{a} foo'")));
  }

  @Test
  void tstring_triple_single_quote() {
    assertTrue(allOf(
      hasToken("t'''", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken(" foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("'''", PythonTokenType.FSTRING_END)).matches(lexer.lex("t'''{a} foo'''")));
  }

  @Test
  void tstring_triple_double_quote() {
    assertTrue(allOf(
      hasToken("t\"\"\"", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken(" foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"\"\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"\"\"{a} foo\"\"\"")));
  }

  @Test
  void tstring_with_escaped_braces() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("abc{{a}} ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("b", GenericTokenType.IDENTIFIER),
      hasToken("+", PythonPunctuator.PLUS),
      hasToken("3", PythonTokenType.NUMBER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"abc{{a}} { b + 3}\"")));
  }

  @Test
  void tstring_format_specifier() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("abc ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("+", PythonPunctuator.PLUS),
      hasToken("b", GenericTokenType.IDENTIFIER),
      hasToken(":", PythonPunctuator.COLON),
      hasToken(".3f", PythonTokenType.FSTRING_MIDDLE),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"abc {a + b:.3f}\"")));
  }

  @Test
  void tstring_with_unicode_escape() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("\\N{RIGHTWARDS ARROW} foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"\\N{RIGHTWARDS ARROW} foo\"")));
  }

  @Test
  void tstring_with_escaped_quotes() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("\\\"", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\\\" foo", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"\\\"{a}\\\" foo\"")));
  }

  @Test
  void tstring_uppercase_prefix() {
    assertTrue(allOf(
      hasToken("T\"", PythonTokenType.TSTRING_START),
      hasToken("hello ", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("name", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("T\"hello {name}\"")));
  }

  @Test
  void tstring_raw_prefix_tr() {
    assertTrue(allOf(
      hasToken("tr\"", PythonTokenType.TSTRING_START),
      hasToken("\\s*", PythonTokenType.FSTRING_MIDDLE),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("42", PythonTokenType.NUMBER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("tr\"\\s*{42}\"")));
  }

  @Test
  void tstring_raw_prefix_rt() {
    assertTrue(allOf(
      hasToken("rt'", PythonTokenType.TSTRING_START),
      hasToken("\\\\", PythonTokenType.FSTRING_MIDDLE),
      hasToken("'", PythonTokenType.FSTRING_END)).matches(lexer.lex("rt'\\\\'")));
  }

  @Test
  void tstring_double_backslash() {
    assertTrue(allOf(
      hasToken("t\"", PythonTokenType.TSTRING_START),
      hasToken("{", PythonPunctuator.LCURLYBRACE),
      hasToken("a", GenericTokenType.IDENTIFIER),
      hasToken("}", PythonPunctuator.RCURLYBRACE),
      hasToken("\\\\", PythonTokenType.FSTRING_MIDDLE),
      hasToken("\"", PythonTokenType.FSTRING_END)).matches(lexer.lex("t\"{a}\\\\\"")));
  }
}
