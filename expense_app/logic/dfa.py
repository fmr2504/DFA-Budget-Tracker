"""Generalized text DFA for substring pattern detection.

Extends the algorithm from substring_dfa.py to support:
- Arbitrary text alphabets (not just '0' and '1').
- Case-insensitive matching via text normalization.
- Non-absorbing accept state for detecting ALL match positions
  (including overlapping matches).
- Characters absent from the pattern alphabet handled gracefully
  (they reset the automaton to state 0 — no crash, no false match).

The core construction algorithm is identical to the original: for each
(state, symbol) pair, find the longest suffix of
``pattern[:state] + symbol`` that is a prefix of the pattern.  This is
the classic KMP-style substring DFA, just generalized to an arbitrary
alphabet derived from the pattern itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Case-fold, strip, and collapse runs of whitespace to a single space.

    This function is applied to both patterns (at DFA build time) and
    descriptions (at scan time) so comparisons are always consistent.

    >>> normalize_text("  Water   Bill  ")
    'water bill'
    >>> normalize_text("")
    ''
    """
    return re.sub(r"\s+", " ", text.casefold().strip())


# ---------------------------------------------------------------------------
# DFA data structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TextDFA:
    """A compiled DFA for detecting a single substring pattern in text.

    Attributes:
        pattern:        The normalized pattern string (case-folded,
                        whitespace-collapsed).
        pattern_length: ``len(pattern)`` — also the accept-state index.
        transitions:    ``state -> {char -> next_state}`` mapping.
                        Characters absent from a state's dict default
                        to state 0 at scan time.
        alphabet:       The set of unique characters in the pattern.
    """

    pattern: str
    pattern_length: int
    transitions: dict  # dict[int, dict[str, int]]
    alphabet: frozenset


# ---------------------------------------------------------------------------
# DFA construction
# ---------------------------------------------------------------------------

def build_text_dfa(pattern: str) -> TextDFA:
    """Build a substring-detection DFA for *pattern*.

    The pattern is normalized (case-folded, stripped, whitespace-collapsed)
    before the DFA is constructed.

    Raises :class:`ValueError` if the pattern is empty after normalization.

    Algorithm (same as ``substring_dfa.build_dfa``, generalized):

    1. Create ``m + 1`` states where ``m = len(pattern)``.
    2. For every ``(state, symbol)`` pair (symbol drawn from the
       pattern's alphabet), form
       ``candidate = pattern[:state] + symbol``.
    3. Find the longest ``k`` such that ``candidate`` ends with
       ``pattern[:k]``.  That ``k`` is the next state.
    4. The accept state (``m``) is **not** absorbing — it falls back
       through the same suffix logic so overlapping matches are found.
    """
    normalized = normalize_text(pattern)
    if not normalized:
        raise ValueError(
            "Pattern must not be empty after normalization."
        )

    m = len(normalized)
    alphabet = frozenset(normalized)

    transitions: dict[int, dict[str, int]] = {}

    for state in range(m + 1):
        transitions[state] = {}
        for ch in alphabet:
            candidate = normalized[:state] + ch

            # Longest k where candidate ends with normalized[:k].
            k = min(m, len(candidate))
            while k > 0 and not candidate.endswith(normalized[:k]):
                k -= 1

            transitions[state][ch] = k

    return TextDFA(
        pattern=normalized,
        pattern_length=m,
        transitions=transitions,
        alphabet=alphabet,
    )


# ---------------------------------------------------------------------------
# DFA simulation
# ---------------------------------------------------------------------------

def find_matches_normalized(
    normalized_text: str, dfa: TextDFA
) -> list[int]:
    """Return starting positions of all pattern occurrences in
    *normalized_text*.

    The caller is responsible for normalizing the text with
    :func:`normalize_text` before calling this function.  Use
    :func:`find_matches` for the convenience wrapper that normalizes
    automatically.

    Overlapping matches are reported.
    """
    m = dfa.pattern_length
    state = 0
    positions: list[int] = []

    for i, ch in enumerate(normalized_text):
        # Characters not in the pattern alphabet can never advance the
        # match — they unconditionally reset to state 0.
        state = dfa.transitions[state].get(ch, 0)
        if state == m:
            positions.append(i - m + 1)

    return positions


def find_matches(text: str, dfa: TextDFA) -> list[int]:
    """Return starting positions of all pattern occurrences in *text*.

    Both *text* and the DFA's pattern are compared after normalization
    (case-folding + whitespace collapsing), so matching is
    case-insensitive and whitespace-tolerant.

    Overlapping matches are reported.

    >>> dfa = build_text_dfa("aba")
    >>> find_matches("ababa", dfa)
    [0, 2]
    """
    return find_matches_normalized(normalize_text(text), dfa)


def contains_pattern(text: str, dfa: TextDFA) -> bool:
    """Return ``True`` if the pattern occurs anywhere in *text*.

    A convenience wrapper around :func:`find_matches` that short-circuits
    on the first match.

    >>> dfa = build_text_dfa("hello")
    >>> contains_pattern("say hello world", dfa)
    True
    """
    normalized = normalize_text(text)
    m = dfa.pattern_length
    state = 0

    for ch in normalized:
        state = dfa.transitions[state].get(ch, 0)
        if state == m:
            return True

    return False

