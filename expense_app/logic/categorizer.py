"""Multi-rule expense categorizer powered by the text DFA engine.

The categorizer accepts a list of :class:`CategoryRule` objects,
pre-builds a :class:`~expense_app.logic.dfa.TextDFA` for each enabled
rule, and evaluates all of them against a transaction description in a
single :meth:`Categorizer.categorize` call.

Conflict resolution policy (deterministic):

1. **No match** → suggest the fallback category (``Other``).
2. **One category matched** → suggest that category.
3. **Multiple categories matched, different priorities** → the highest
   priority wins.
4. **Multiple categories matched, same priority** → flag as ambiguous
   and return all tied categories so the UI can ask the user.

Each rule has a ``match_mode``:

- ``substring`` — the pattern may appear anywhere inside the
  description (the default).
- ``whole_word`` — the pattern must sit at word boundaries (the
  characters immediately before and after the match must be
  non-alphanumeric or at a string edge).  This prevents short
  patterns like ``gas`` from matching inside ``gasoline``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from expense_app.logic.dfa import (
    TextDFA,
    build_text_dfa,
    find_matches_normalized,
    normalize_text,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CategoryRule:
    """A single pattern-to-category mapping.

    Attributes:
        pattern:    The keyword or phrase to search for.
        category:   The expense category this rule suggests.
        priority:   Higher values win when rules from different
                    categories conflict.
        match_mode: ``"substring"`` (default) or ``"whole_word"``.
        is_enabled: Disabled rules are skipped during categorization.
    """

    pattern: str
    category: str
    priority: int
    match_mode: str = "substring"
    is_enabled: bool = True

    def __post_init__(self):
        if self.match_mode not in ("substring", "whole_word"):
            raise ValueError(
                f"match_mode must be 'substring' or 'whole_word', "
                f"got {self.match_mode!r}"
            )


@dataclass
class MatchDetail:
    """Information about a single rule that matched a description.

    Attributes:
        rule:      The :class:`CategoryRule` that fired.
        positions: Starting indices (in the *normalized* description)
                   where the pattern was found.
    """

    rule: CategoryRule
    positions: list[int] = field(default_factory=list)


@dataclass
class CategorizationResult:
    """The outcome of running all enabled rules against a description.

    Attributes:
        suggested_category: The recommended category (always populated).
        is_fallback:        ``True`` when no rule matched and the
                            suggestion is the fallback category.
        is_ambiguous:       ``True`` when equally-prioritized rules
                            from different categories matched.
        matches:            Details for every rule that matched.
        tied_categories:    Category names involved in the tie (only
                            populated when ``is_ambiguous`` is True).
    """

    suggested_category: str
    is_fallback: bool = False
    is_ambiguous: bool = False
    matches: list[MatchDetail] = field(default_factory=list)
    tied_categories: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Word-boundary helper
# ---------------------------------------------------------------------------

def _is_word_boundary(
    text: str, start: int, pattern_length: int
) -> bool:
    """Return ``True`` if the match at ``text[start:start+pattern_length]``
    is surrounded by non-alphanumeric characters (or string edges).

    This operates on *already-normalized* text.
    """
    # Character before the match must not be alphanumeric.
    if start > 0 and text[start - 1].isalnum():
        return False
    # Character after the match must not be alphanumeric.
    end = start + pattern_length
    if end < len(text) and text[end].isalnum():
        return False
    return True


# ---------------------------------------------------------------------------
# Categorizer
# ---------------------------------------------------------------------------

class Categorizer:
    """Evaluate multiple DFA-based rules against expense descriptions.

    Build a ``Categorizer`` once from the current rule set.  When rules
    change (add / remove / toggle), create a new ``Categorizer``.

    Parameters:
        rules:             Iterable of :class:`CategoryRule` objects.
        fallback_category: Category to suggest when no rule matches.
    """

    def __init__(
        self,
        rules: list[CategoryRule],
        fallback_category: str = "Other",
    ):
        self._fallback = fallback_category
        # Pre-build a DFA for each enabled rule.
        self._rule_dfas: list[tuple[CategoryRule, TextDFA]] = []
        for rule in rules:
            if rule.is_enabled:
                dfa = build_text_dfa(rule.pattern)
                self._rule_dfas.append((rule, dfa))

    # ---- public API -------------------------------------------------------

    def categorize(self, description: str) -> CategorizationResult:
        """Categorize *description* by running all enabled rules.

        Returns a :class:`CategorizationResult` with the suggested
        category, match details, and ambiguity flags.
        """
        normalized = normalize_text(description)
        if not normalized:
            return CategorizationResult(
                suggested_category=self._fallback,
                is_fallback=True,
            )

        matches = self._collect_matches(normalized)

        if not matches:
            return CategorizationResult(
                suggested_category=self._fallback,
                is_fallback=True,
            )

        return self._resolve(matches)

    # ---- internals --------------------------------------------------------

    def _collect_matches(
        self, normalized: str
    ) -> list[MatchDetail]:
        """Run every DFA against *normalized* and collect hits."""
        matches: list[MatchDetail] = []

        for rule, dfa in self._rule_dfas:
            positions = find_matches_normalized(normalized, dfa)

            # Apply word-boundary filter for whole_word rules.
            if rule.match_mode == "whole_word" and positions:
                positions = [
                    p
                    for p in positions
                    if _is_word_boundary(
                        normalized, p, dfa.pattern_length
                    )
                ]

            if positions:
                matches.append(
                    MatchDetail(rule=rule, positions=positions)
                )

        return matches

    def _resolve(
        self, matches: list[MatchDetail]
    ) -> CategorizationResult:
        """Apply the conflict-resolution policy to *matches*.

        1. Group matches by category, keeping the maximum priority
           observed for each category.
        2. Find the highest priority across all categories.
        3. If only one category has that priority → suggest it.
        4. If multiple categories share the top priority → ambiguous.
        """
        # category → best (highest) priority from its matching rules
        cat_priority: dict[str, int] = {}
        for m in matches:
            cat = m.rule.category
            if cat not in cat_priority:
                cat_priority[cat] = m.rule.priority
            else:
                cat_priority[cat] = max(
                    cat_priority[cat], m.rule.priority
                )

        # Single-category case: no conflict.
        if len(cat_priority) == 1:
            category = next(iter(cat_priority))
            return CategorizationResult(
                suggested_category=category,
                matches=matches,
            )

        # Multi-category: resolve by priority.
        max_pri = max(cat_priority.values())
        top = sorted(
            cat for cat, pri in cat_priority.items() if pri == max_pri
        )

        if len(top) == 1:
            return CategorizationResult(
                suggested_category=top[0],
                matches=matches,
            )

        # Ambiguous — tied priorities across different categories.
        return CategorizationResult(
            suggested_category=top[0],   # alphabetically first
            is_ambiguous=True,
            matches=matches,
            tied_categories=top,
        )

