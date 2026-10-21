"""Tests for the expense categorizer (expense_app.logic.categorizer).

Covers: single-rule matching, fallback/unmatched behavior, multi-rule
same category, priority-based conflict resolution, ambiguity detection,
whole-word boundary filtering, disabled rules, case insensitivity, and
practical expense descriptions from the development guide.
"""

import pytest

from expense_app.logic.categorizer import (
    Categorizer,
    CategorizationResult,
    CategoryRule,
    MatchDetail,
)


# ===================================================================
# Fixtures — reusable rules
# ===================================================================


@pytest.fixture
def food_rule():
    return CategoryRule(
        pattern="jollibee", category="Food", priority=10
    )


@pytest.fixture
def transport_rule():
    return CategoryRule(
        pattern="jeepney", category="Transportation", priority=10
    )


@pytest.fixture
def gas_whole_word():
    return CategoryRule(
        pattern="gas",
        category="Transportation",
        priority=10,
        match_mode="whole_word",
    )


# ===================================================================
# Single-rule matching
# ===================================================================


class TestSingleRuleMatch:
    def test_returns_correct_category(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("Jollibee lunch")
        assert result.suggested_category == "Food"
        assert not result.is_fallback
        assert not result.is_ambiguous

    def test_match_includes_positions(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("Jollibee lunch")
        assert len(result.matches) == 1
        assert 0 in result.matches[0].positions

    def test_match_detail_references_rule(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("Jollibee")
        assert result.matches[0].rule is food_rule


# ===================================================================
# No match / fallback
# ===================================================================


class TestNoMatch:
    def test_returns_fallback_category(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("bought new shoes")
        assert result.suggested_category == "Other"
        assert result.is_fallback

    def test_custom_fallback(self, food_rule):
        cat = Categorizer(
            [food_rule], fallback_category="Uncategorized"
        )
        result = cat.categorize("bought new shoes")
        assert result.suggested_category == "Uncategorized"

    def test_empty_description(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("")
        assert result.is_fallback

    def test_whitespace_only_description(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("   ")
        assert result.is_fallback

    def test_no_matches_list_is_empty(self, food_rule):
        cat = Categorizer([food_rule])
        result = cat.categorize("bought shoes")
        assert result.matches == []

    def test_no_rules_always_fallback(self):
        cat = Categorizer([])
        result = cat.categorize("anything")
        assert result.is_fallback


# ===================================================================
# Multiple rules, same category
# ===================================================================


class TestSameCategoryMultipleRules:
    def test_two_food_rules_both_match(self):
        rules = [
            CategoryRule("jollibee", "Food", 10, "substring"),
            CategoryRule("lunch", "Food", 10, "whole_word"),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("Jollibee lunch")
        assert result.suggested_category == "Food"
        assert not result.is_ambiguous
        assert len(result.matches) == 2

    def test_one_of_two_matches(self):
        rules = [
            CategoryRule("jollibee", "Food", 10),
            CategoryRule("mcdonalds", "Food", 10),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("Jollibee lunch")
        assert result.suggested_category == "Food"
        assert len(result.matches) == 1


# ===================================================================
# Priority-based conflict resolution
# ===================================================================


class TestPriorityResolution:
    def test_higher_priority_wins(self):
        rules = [
            CategoryRule("jollibee", "Food", 20),
            CategoryRule("shopee", "Shopping", 10),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("jollibee shopee promo")
        assert result.suggested_category == "Food"
        assert not result.is_ambiguous

    def test_lower_priority_loses(self):
        rules = [
            CategoryRule("grab", "Transportation", 5, "whole_word"),
            CategoryRule("food", "Food", 15, "whole_word"),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("grab food delivery")
        assert result.suggested_category == "Food"

    def test_max_priority_per_category(self):
        """When a category has multiple rules, use its best priority."""
        rules = [
            CategoryRule("jollibee", "Food", 5),
            CategoryRule("lunch", "Food", 20, "whole_word"),
            CategoryRule("shopee", "Shopping", 15),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("jollibee lunch on shopee")
        # Food's max priority is 20 > Shopping's 15
        assert result.suggested_category == "Food"
        assert not result.is_ambiguous


# ===================================================================
# Ambiguity (tied priority, different categories)
# ===================================================================


class TestAmbiguity:
    def test_same_priority_different_categories(
        self, food_rule, transport_rule
    ):
        cat = Categorizer([food_rule, transport_rule])
        result = cat.categorize("jollibee near jeepney stop")
        assert result.is_ambiguous
        assert len(result.tied_categories) == 2
        assert "Food" in result.tied_categories
        assert "Transportation" in result.tied_categories

    def test_ambiguous_still_suggests_a_category(
        self, food_rule, transport_rule
    ):
        cat = Categorizer([food_rule, transport_rule])
        result = cat.categorize("jollibee near jeepney stop")
        # Must still provide a suggestion (alphabetically first).
        assert result.suggested_category in (
            "Food",
            "Transportation",
        )

    def test_tied_categories_sorted(self):
        rules = [
            CategoryRule("bus", "Transportation", 10, "whole_word"),
            CategoryRule("clinic", "Health", 10),
            CategoryRule("lunch", "Food", 10, "whole_word"),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("bus to clinic after lunch")
        assert result.is_ambiguous
        assert result.tied_categories == [
            "Food",
            "Health",
            "Transportation",
        ]
        # Alphabetically first wins the suggestion.
        assert result.suggested_category == "Food"


# ===================================================================
# Whole-word mode
# ===================================================================


class TestWholeWordMode:
    def test_matches_standalone(self, gas_whole_word):
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("gas")
        assert result.suggested_category == "Transportation"

    def test_matches_at_start_with_space(self, gas_whole_word):
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("gas station")
        assert result.suggested_category == "Transportation"

    def test_matches_at_end_with_space(self, gas_whole_word):
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("bought gas")
        assert result.suggested_category == "Transportation"

    def test_matches_surrounded_by_spaces(self, gas_whole_word):
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("the gas pump")
        assert result.suggested_category == "Transportation"

    def test_matches_with_punctuation(self, gas_whole_word):
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("bought gas!")
        assert result.suggested_category == "Transportation"

    def test_rejects_inside_word(self, gas_whole_word):
        """'gas' must NOT match inside 'gasoline'."""
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("gasoline purchase")
        assert result.is_fallback

    def test_rejects_suffix(self, gas_whole_word):
        """'gas' must NOT match at the end of 'biogas'."""
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("biogas plant")
        assert result.is_fallback

    def test_rejects_madagascar(self, gas_whole_word):
        """'gas' must NOT match inside 'Madagascar'."""
        cat = Categorizer([gas_whole_word])
        result = cat.categorize("Madagascar trip")
        assert result.is_fallback

    def test_substring_mode_would_match_gasoline(self):
        """Contrast: substring mode DOES match inside 'gasoline'."""
        rule = CategoryRule(
            "gas", "Transportation", 10, "substring"
        )
        cat = Categorizer([rule])
        result = cat.categorize("gasoline purchase")
        assert result.suggested_category == "Transportation"


# ===================================================================
# Disabled rules
# ===================================================================


class TestDisabledRule:
    def test_disabled_rule_skipped(self):
        rule = CategoryRule(
            "jollibee", "Food", 10, is_enabled=False
        )
        cat = Categorizer([rule])
        result = cat.categorize("Jollibee lunch")
        assert result.is_fallback

    def test_disabled_among_enabled(self):
        rules = [
            CategoryRule("jollibee", "Food", 10, is_enabled=False),
            CategoryRule("lunch", "Food", 10, "whole_word"),
        ]
        cat = Categorizer(rules)
        result = cat.categorize("Jollibee lunch")
        assert result.suggested_category == "Food"
        assert len(result.matches) == 1  # only 'lunch' matched


# ===================================================================
# Case insensitivity
# ===================================================================


class TestCaseInsensitive:
    def test_mixed_case_descriptions(self, food_rule):
        cat = Categorizer([food_rule])
        for desc in ["JOLLIBEE", "jollibee", "JoLlIbEe", "Jollibee"]:
            result = cat.categorize(desc)
            assert (
                result.suggested_category == "Food"
            ), f"Failed for '{desc}'"


# ===================================================================
# Invalid rule construction
# ===================================================================


class TestCategoryRuleValidation:
    def test_invalid_match_mode_raises(self):
        with pytest.raises(ValueError, match="match_mode"):
            CategoryRule("test", "Cat", 10, match_mode="regex")


# ===================================================================
# Real expense descriptions from the development guide
# ===================================================================


class TestRealExpenseDescriptions:
    """Practical scenarios using the starter rule set from the guide."""

    @pytest.fixture
    def categorizer(self):
        rules = [
            CategoryRule("jollibee", "Food", 10, "substring"),
            CategoryRule("restaurant", "Food", 10, "substring"),
            CategoryRule("lunch", "Food", 10, "whole_word"),
            CategoryRule("dinner", "Food", 10, "whole_word"),
            CategoryRule("coffee", "Food", 10, "substring"),
            CategoryRule("grab", "Transportation", 10, "whole_word"),
            CategoryRule("jeepney", "Transportation", 10, "substring"),
            CategoryRule("bus", "Transportation", 10, "whole_word"),
            CategoryRule("train", "Transportation", 10, "whole_word"),
            CategoryRule("gas", "Transportation", 10, "whole_word"),
            CategoryRule("parking", "Transportation", 10, "substring"),
            CategoryRule("electricity", "Bills", 10, "substring"),
            CategoryRule("water bill", "Bills", 10, "substring"),
            CategoryRule("internet", "Bills", 10, "substring"),
            CategoryRule("mobile load", "Bills", 10, "substring"),
            CategoryRule("lazada", "Shopping", 10, "substring"),
            CategoryRule("shopee", "Shopping", 10, "substring"),
            CategoryRule("clothing", "Shopping", 10, "substring"),
            CategoryRule("tuition", "Education", 10, "substring"),
            CategoryRule("textbook", "Education", 10, "substring"),
            CategoryRule(
                "school supplies", "Education", 10, "substring"
            ),
            CategoryRule("pharmacy", "Health", 10, "substring"),
            CategoryRule("clinic", "Health", 10, "substring"),
            CategoryRule("medicine", "Health", 10, "substring"),
        ]
        return Categorizer(rules)

    def test_jollibee_lunch(self, categorizer):
        result = categorizer.categorize("Jollibee lunch")
        assert result.suggested_category == "Food"
        assert not result.is_ambiguous

    def test_jeepney_fare(self, categorizer):
        result = categorizer.categorize("Jeepney fare to school")
        assert result.suggested_category == "Transportation"

    def test_grab_ride(self, categorizer):
        result = categorizer.categorize("Grab ride to work")
        assert result.suggested_category == "Transportation"

    def test_electricity_bill(self, categorizer):
        result = categorizer.categorize("Electricity bill for October")
        assert result.suggested_category == "Bills"

    def test_water_bill(self, categorizer):
        result = categorizer.categorize("Water bill payment")
        assert result.suggested_category == "Bills"

    def test_lazada_order(self, categorizer):
        result = categorizer.categorize("Lazada order - phone case")
        assert result.suggested_category == "Shopping"

    def test_pharmacy_purchase(self, categorizer):
        result = categorizer.categorize("Pharmacy - vitamins")
        assert result.suggested_category == "Health"

    def test_school_supplies(self, categorizer):
        result = categorizer.categorize("School supplies for semester")
        assert result.suggested_category == "Education"

    def test_gas_station(self, categorizer):
        result = categorizer.categorize("Gas station fill up")
        assert result.suggested_category == "Transportation"

    def test_gasoline_no_match(self, categorizer):
        """'gas' in whole_word mode must NOT match 'gasoline'."""
        result = categorizer.categorize("Gasoline purchase")
        assert result.is_fallback

    def test_unmatched_falls_back(self, categorizer):
        result = categorizer.categorize("Birthday gift for mom")
        assert result.is_fallback
        assert result.suggested_category == "Other"

    def test_coffee_shop(self, categorizer):
        result = categorizer.categorize("Coffee shop with friends")
        assert result.suggested_category == "Food"

    def test_parking_fee(self, categorizer):
        result = categorizer.categorize("Parking fee at mall")
        assert result.suggested_category == "Transportation"

    def test_internet_subscription(self, categorizer):
        result = categorizer.categorize("Internet monthly subscription")
        assert result.suggested_category == "Bills"

    def test_mobile_load(self, categorizer):
        result = categorizer.categorize("Mobile load top up")
        assert result.suggested_category == "Bills"


# ===================================================================
# Expanded keyword library tests
# ===================================================================


class TestExpandedKeywordLibrary:
    """Tests covering the expanded keyword collection from config.DEFAULT_RULES."""

    @pytest.fixture
    def default_categorizer(self):
        from expense_app.config import DEFAULT_RULES
        rules = [
            CategoryRule(pattern=p, category=c, priority=pr, match_mode=m)
            for p, c, pr, m in DEFAULT_RULES
        ]
        return Categorizer(rules)

    def test_category_rule_counts(self):
        """Ensure each major category meets the 40+ rules threshold."""
        from collections import Counter
        from expense_app.config import DEFAULT_RULES

        counts = Counter(cat for _, cat, _, _ in DEFAULT_RULES)
        major_categories = [
            "Food",
            "Transportation",
            "Bills",
            "Shopping",
            "Education",
            "Health",
            "Household",
            "Entertainment",
        ]
        for cat in major_categories:
            assert counts[cat] >= 40, f"Category '{cat}' has only {counts[cat]} rules, expected >= 40"

        assert counts["Other"] >= 10, f"Category 'Other' has only {counts['Other']} rules, expected >= 10"

    def test_no_duplicate_patterns_in_default_rules(self):
        """Ensure all rule patterns in DEFAULT_RULES are distinct."""
        from collections import Counter
        from expense_app.config import DEFAULT_RULES

        patterns = [p.strip().lower() for p, _, _, _ in DEFAULT_RULES]
        dupes = [pat for pat, cnt in Counter(patterns).items() if cnt > 1]
        assert not dupes, f"Found duplicate patterns in DEFAULT_RULES: {dupes}"

    @pytest.mark.parametrize(
        "desc,expected_cat",
        [
            # Food
            ("Chickenjoy with rice and iced tea", "Food"),
            ("Mang Inasal merienda with friends", "Food"),
            ("Almusal tapsilog and pandesal", "Food"),
            ("Tanghalian sa karinderya", "Food"),
            ("Hapunan sinigang na baboy", "Food"),
            ("Order food via Foodpanda delivery", "Food"),
            ("Milk tea with pearls", "Food"),
            ("Starbucks cafe latte", "Food"),
            ("KFC burger and french fries", "Food"),
            ("Bumili ng ulam sa carinderia", "Food"),
            ("Buy groceries for meals", "Food"),
            # Transportation
            ("Pamasahe sa jeep papuntang MRT", "Transportation"),
            ("Biyahe pauwi via UV Express", "Transportation"),
            ("Sakay ng tricycle sa kanto", "Transportation"),
            ("Gasolina sa Shell refuel", "Transportation"),
            ("Book a ride with Angkas", "Transportation"),
            ("JoyRide motorcycle taxi fare", "Transportation"),
            ("Autosweep RFID toll fee", "Transportation"),
            ("Car wash and tire repair", "Transportation"),
            ("Airplane ticket for Cebu trip", "Transportation"),
            # Bills
            ("Meralco electric bill payment", "Bills"),
            ("Maynilad water utility bill", "Bills"),
            ("Bayad sa kuryente at ilaw", "Bills"),
            ("Bayad sa tubig payment", "Bills"),
            ("PLDT fiber internet bill", "Bills"),
            ("Prepaid mobile load promo", "Bills"),
            ("Monthly house rent payment", "Bills"),
            ("Condo dues and HOA dues", "Bills"),
            ("GCash load topup", "Bills"),
            # Shopping
            ("Shopee 10.10 checkout shoes", "Shopping"),
            ("Lazada online shopping bag", "Shopping"),
            ("Bumili ng tsinelas sa tiangge", "Shopping"),
            ("Ukay-ukay jacket and denim jeans", "Shopping"),
            ("Department store cosmetic makeup", "Shopping"),
            ("Smartphone powerbank and charger", "Shopping"),
            ("Zalora dress and heels", "Shopping"),
            # Education
            ("Matrikula payment for second semester", "Education"),
            ("College tuition fee payment", "Education"),
            ("Review center enrollment fee", "Education"),
            ("Yellow pad paper and ballpen", "Education"),
            ("Photocopy of reading modules", "Education"),
            ("Gamit sa eskwela notebooks", "Education"),
            ("Scientific calculator for class", "Education"),
            # Health
            ("Bumili ng gamot sa Mercury Drug", "Health"),
            ("Biogesic paracetamol for headache", "Health"),
            ("Doctor's consultation fee payment", "Health"),
            ("Dental clinic checkup and cleaning", "Health"),
            ("Flu shot vaccine injection", "Health"),
            ("Prescription vitamins at Watsons", "Health"),
            ("Hospital bill for inpatient care", "Health"),
            # Household
            ("Bumili ng detergent sabong panlaba", "Household"),
            ("Zonrox bleach at dishwashing liquid", "Household"),
            ("Walis tambo and dustpan for cleaning", "Household"),
            ("Aircon cleaning and maintenance service", "Household"),
            ("Repair ng gripo sa lababo", "Household"),
            ("Light bulb replacement and led bulb", "Household"),
            ("Ace Hardware nails and screwdriver", "Household"),
            # Entertainment
            ("Cinema ticket for evening movie", "Entertainment"),
            ("Concert ticket live band gig", "Entertainment"),
            ("Netflix subscription monthly payment", "Entertainment"),
            ("Spotify premium music streaming", "Entertainment"),
            ("Enchanted Kingdom theme park tickets", "Entertainment"),
            ("Arcade Timezone tokens", "Entertainment"),
            ("Karaoke KTV night with friends", "Entertainment"),
            ("Valorant points codashop topup", "Entertainment"),
            # Other
            ("Miscellaneous sundry items", "Other"),
            ("Petty cash extra expense", "Other"),
            ("Uncategorized general expense", "Other"),
            ("Unspecified random expense", "Other"),
        ],
    )
    def test_expanded_rules_match_expected_category(
        self, default_categorizer, desc, expected_cat
    ):
        result = default_categorizer.categorize(desc)
        assert (
            result.suggested_category == expected_cat
        ), f"Failed for '{desc}': got {result.suggested_category}, ambiguous={result.is_ambiguous}"

    def test_case_insensitivity_and_punctuation(self, default_categorizer):
        """Matching works with all-uppercase, punctuation, and extra whitespace."""
        res1 = default_categorizer.categorize("BAYAD SA KURYENTE!")
        assert res1.suggested_category == "Bills"

        res2 = default_categorizer.categorize("   meralco   power    bill...  ")
        assert res2.suggested_category == "Bills"

        res3 = default_categorizer.categorize("JOLLIBEE (CHICKENJOY) - DINNER.")
        assert res3.suggested_category == "Food"

    def test_whole_word_matching_prevents_partial_collisions(
        self, default_categorizer
    ):
        """Whole-word rules must not match unrelated words containing the keyword."""
        # 'fare' should not match 'farewell' or 'warfare'
        res1 = default_categorizer.categorize("Attended farewell party for colleague")
        # should fall back to Other or match party/colleague, not Transportation via 'fare'
        assert not any(
            m.rule.pattern == "fare" for m in res1.matches
        )

        # 'rice' should not match 'price'
        res2 = default_categorizer.categorize("Asked about the total price of the item")
        assert not any(
            m.rule.pattern == "rice" for m in res2.matches
        )

        # 'soap' / 'mop' should not match partial words
        res3 = default_categorizer.categorize("Atmosphere was pleasant")
        assert not any(
            m.rule.pattern == "mop" for m in res3.matches
        )

    def test_unrelated_description_falls_back(self, default_categorizer):
        """Arbitrary unrelated text with no keywords falls back to Other."""
        result = default_categorizer.categorize("Xy789 Qqzz completely unknown")
        assert result.is_fallback
        assert result.suggested_category == "Other"

    def test_ambiguity_flagged_for_tied_priorities(self, default_categorizer):
        """When keywords from multiple categories tie at top priority, flag ambiguous."""
        # "movie" (Entertainment, pri=10) and "pizza" (Food, pri=10)
        result = default_categorizer.categorize("movie and pizza night")
        assert result.is_ambiguous
        assert "Entertainment" in result.tied_categories
        assert "Food" in result.tied_categories


