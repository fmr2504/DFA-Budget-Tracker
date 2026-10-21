"""Tests for the text DFA engine (expense_app.logic.dfa).

Covers: normalization, DFA construction, match finding (including
edge cases, overlapping matches, case insensitivity, unknown
characters), and the convenience helpers.
"""

import pytest

from expense_app.logic.dfa import (
    TextDFA,
    build_text_dfa,
    contains_pattern,
    find_matches,
    find_matches_normalized,
    normalize_text,
)


# ===================================================================
# normalize_text
# ===================================================================


class TestNormalizeText:
    """Text normalization used by both DFA build and scan."""

    def test_casefold(self):
        assert normalize_text("Hello") == "hello"

    def test_strip(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapse_whitespace(self):
        assert normalize_text("water  bill") == "water bill"

    def test_tabs_and_newlines(self):
        assert normalize_text("water\t\nbill") == "water bill"

    def test_combined_normalization(self):
        assert normalize_text("  Water   Bill  ") == "water bill"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_whitespace_only(self):
        assert normalize_text("   ") == ""

    def test_single_character(self):
        assert normalize_text("A") == "a"

    def test_already_normalized(self):
        assert normalize_text("hello world") == "hello world"


# ===================================================================
# build_text_dfa
# ===================================================================


class TestBuildTextDFA:
    """DFA construction from a text pattern."""

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="empty"):
            build_text_dfa("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            build_text_dfa("   ")

    def test_returns_text_dfa(self):
        dfa = build_text_dfa("abc")
        assert isinstance(dfa, TextDFA)

    def test_pattern_is_casefolded(self):
        dfa = build_text_dfa("ABC")
        assert dfa.pattern == "abc"

    def test_pattern_is_whitespace_collapsed(self):
        dfa = build_text_dfa("water  bill")
        assert dfa.pattern == "water bill"

    def test_pattern_length(self):
        dfa = build_text_dfa("hello")
        assert dfa.pattern_length == 5

    def test_alphabet_from_pattern(self):
        dfa = build_text_dfa("abc")
        assert dfa.alphabet == frozenset("abc")

    def test_alphabet_includes_space(self):
        dfa = build_text_dfa("a b")
        assert " " in dfa.alphabet

    def test_state_count(self):
        """pattern_length + 1 states (q0 … q_m)."""
        dfa = build_text_dfa("abc")
        assert len(dfa.transitions) == 4  # states 0, 1, 2, 3

    def test_single_char_state_count(self):
        dfa = build_text_dfa("x")
        assert len(dfa.transitions) == 2  # states 0, 1


# ===================================================================
# find_matches — core matching
# ===================================================================


class TestFindMatchesSingleChar:
    """Patterns of length 1."""

    def test_match_at_start(self):
        dfa = build_text_dfa("a")
        assert find_matches("abc", dfa) == [0]

    def test_no_match(self):
        dfa = build_text_dfa("x")
        assert find_matches("abc", dfa) == []

    def test_every_char_matches(self):
        dfa = build_text_dfa("a")
        assert find_matches("aaa", dfa) == [0, 1, 2]


class TestFindMatchesPosition:
    """Pattern position within the text."""

    def test_at_start(self):
        dfa = build_text_dfa("hello")
        assert find_matches("hello world", dfa) == [0]

    def test_at_end(self):
        dfa = build_text_dfa("world")
        assert find_matches("hello world", dfa) == [6]

    def test_in_middle(self):
        dfa = build_text_dfa("lo wo")
        assert find_matches("hello world", dfa) == [3]

    def test_exact_match(self):
        """Pattern equals the entire text."""
        dfa = build_text_dfa("hello")
        assert find_matches("hello", dfa) == [0]

    def test_pattern_longer_than_text(self):
        dfa = build_text_dfa("hello world")
        assert find_matches("hello", dfa) == []


class TestFindMatchesCaseInsensitive:
    """Case-insensitive matching through normalization."""

    def test_upper_input(self):
        dfa = build_text_dfa("jollibee")
        assert find_matches("JOLLIBEE", dfa) == [0]

    def test_mixed_case(self):
        dfa = build_text_dfa("jollibee")
        assert find_matches("JoLlIbEe lunch", dfa) == [0]

    def test_upper_pattern(self):
        dfa = build_text_dfa("JOLLIBEE")
        assert find_matches("jollibee", dfa) == [0]


class TestFindMatchesRepeated:
    """Multiple and overlapping occurrences."""

    def test_non_overlapping(self):
        dfa = build_text_dfa("ab")
        assert find_matches("ababab", dfa) == [0, 2, 4]

    def test_overlapping(self):
        dfa = build_text_dfa("aba")
        assert find_matches("ababa", dfa) == [0, 2]

    def test_overlapping_aa(self):
        dfa = build_text_dfa("aa")
        assert find_matches("aaa", dfa) == [0, 1]

    def test_overlapping_aaa(self):
        dfa = build_text_dfa("aaa")
        assert find_matches("aaaa", dfa) == [0, 1]

    def test_multiple_separated(self):
        dfa = build_text_dfa("the")
        assert find_matches("the cat and the dog", dfa) == [0, 12]


class TestFindMatchesUnknownChars:
    """Characters not in the pattern alphabet."""

    def test_unknown_before_match(self):
        dfa = build_text_dfa("abc")
        assert find_matches("123abc", dfa) == [3]

    def test_unknown_after_match(self):
        dfa = build_text_dfa("abc")
        assert find_matches("abc456", dfa) == [0]

    def test_unknown_surrounding(self):
        dfa = build_text_dfa("abc")
        assert find_matches("123!@#abc456", dfa) == [6]

    def test_all_unknown_no_match(self):
        dfa = build_text_dfa("abc")
        assert find_matches("123!@#def456", dfa) == []

    def test_no_crash_on_empty_text(self):
        dfa = build_text_dfa("abc")
        assert find_matches("", dfa) == []


class TestFindMatchesMultiword:
    """Patterns containing spaces (multi-word keywords)."""

    def test_multi_word_match(self):
        dfa = build_text_dfa("water bill")
        assert find_matches("paid water bill today", dfa) == [5]

    def test_whitespace_normalized_in_text(self):
        """Double space in input is collapsed before scanning."""
        dfa = build_text_dfa("water bill")
        assert find_matches("paid water  bill today", dfa) == [5]

    def test_multi_word_no_match(self):
        dfa = build_text_dfa("water bill")
        assert find_matches("bill for water", dfa) == []

    def test_school_supplies(self):
        dfa = build_text_dfa("school supplies")
        assert find_matches("bought school supplies", dfa) == [7]


class TestFindMatchesUnicode:
    """Patterns and text containing non-ASCII characters."""

    def test_accented_characters(self):
        dfa = build_text_dfa("café")
        assert find_matches("I love café!", dfa) == [7]

    def test_peso_sign_in_text(self):
        """₱ in text does not crash even if pattern has no ₱."""
        dfa = build_text_dfa("lunch")
        positions = find_matches("₱150 lunch", dfa)
        assert positions == [5]


# ===================================================================
# contains_pattern (convenience)
# ===================================================================


class TestContainsPattern:
    def test_true(self):
        dfa = build_text_dfa("hello")
        assert contains_pattern("hello world", dfa) is True

    def test_false(self):
        dfa = build_text_dfa("xyz")
        assert contains_pattern("hello world", dfa) is False

    def test_case_insensitive(self):
        dfa = build_text_dfa("hello")
        assert contains_pattern("HELLO WORLD", dfa) is True

    def test_empty_text(self):
        dfa = build_text_dfa("hello")
        assert contains_pattern("", dfa) is False


# ===================================================================
# find_matches_normalized
# ===================================================================


class TestFindMatchesNormalized:
    """Verify the pre-normalized entry point works correctly."""

    def test_already_normalized_input(self):
        dfa = build_text_dfa("hello")
        positions = find_matches_normalized("hello world", dfa)
        assert positions == [0]

    def test_consistent_with_find_matches(self):
        """Both entry points must return the same positions."""
        dfa = build_text_dfa("water bill")
        text = "  Paid  Water   Bill  Today  "
        assert find_matches(text, dfa) == find_matches_normalized(
            normalize_text(text), dfa
        )

