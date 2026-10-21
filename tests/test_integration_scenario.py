"""End-to-end test suite validating the complete 10-step integration scenario from the development guide."""

from datetime import date
import pytest

from expense_app.data.database import init_database
from expense_app.data.repositories import (
    create_expense,
    delete_budget_for_category,
    delete_expense,
    get_budget,
    get_budgets_for_month,
    get_category_by_name,
    get_expense_by_id,
    get_expenses,
    load_categorizer_rules,
    set_budget,
    update_expense,
)
from expense_app.logic.categorizer import Categorizer
from expense_app.logic.money import format_amount, parse_amount
from expense_app.logic.reporting import (
    calculate_budget_progress,
    generate_monthly_report,
    month_range,
    shift_month,
    validate_date,
)


class TestFullGuideIntegrationScenario:
    """Automated execution of the 10-step integrated manual test scenario from Guide Section 14."""

    def test_complete_scenario_lifecycle(self, tmp_path):
        db_path = str(tmp_path / "scenario_expenses.db")
        conn = init_database(db_path)
        categorizer = Categorizer(load_categorizer_rules(conn), fallback_category="Other")

        today = date.today()
        current_month = today.strftime("%Y-%m")
        today_iso = today.isoformat()
        start_curr, end_curr = month_range(current_month)

        # -------------------------------------------------------------------
        # Step 1: Add ₱150.00 with description "Jollibee lunch" and accept Food.
        # -------------------------------------------------------------------
        res1 = categorizer.categorize("Jollibee lunch")
        assert res1.suggested_category == "Food"
        assert not res1.is_fallback
        cat_food = get_category_by_name(conn, "Food")
        exp1_id = create_expense(
            conn=conn,
            amount_centavos=parse_amount("150.00"),
            description="Jollibee lunch",
            occurred_on=today_iso,
            category_id=cat_food["id"],
            category_source="automatic",
            matched_pattern=res1.matches[0].rule.pattern,
        )
        assert exp1_id > 0
        exp1 = get_expense_by_id(conn, exp1_id)
        assert exp1["amount_centavos"] == 15000
        assert exp1["category_source"] == "automatic"

        # -------------------------------------------------------------------
        # Step 2: Add ₱80.00 with description "Jeepney fare" and accept Transportation.
        # -------------------------------------------------------------------
        res2 = categorizer.categorize("Jeepney fare")
        assert res2.suggested_category == "Transportation"
        cat_trans = get_category_by_name(conn, "Transportation")
        exp2_id = create_expense(
            conn=conn,
            amount_centavos=parse_amount("80.00"),
            description="Jeepney fare",
            occurred_on=today_iso,
            category_id=cat_trans["id"],
            category_source="automatic",
            matched_pattern=res2.matches[0].rule.pattern,
        )
        assert exp2_id > 0

        # -------------------------------------------------------------------
        # Step 3: Add ₱200.00 with an unmatched description; confirm fallback and manually choose a category.
        # -------------------------------------------------------------------
        unmatched_desc = "Antique brass keychain"
        res3 = categorizer.categorize(unmatched_desc)
        assert res3.is_fallback
        assert res3.suggested_category == "Other"

        # User overrides category to "Shopping"
        cat_shop = get_category_by_name(conn, "Shopping")
        exp3_id = create_expense(
            conn=conn,
            amount_centavos=parse_amount("200.00"),
            description=unmatched_desc,
            occurred_on=today_iso,
            category_id=cat_shop["id"],
            category_source="manual",
        )
        exp3 = get_expense_by_id(conn, exp3_id)
        assert exp3["category_name"] == "Shopping"
        assert exp3["category_source"] == "manual"

        # -------------------------------------------------------------------
        # Step 4: Edit one expense and verify that reports and budgets update.
        # -------------------------------------------------------------------
        # Edit exp2 amount from ₱80.00 to ₱100.00
        update_expense(conn, exp2_id, amount_centavos=parse_amount("100.00"))
        exp2_updated = get_expense_by_id(conn, exp2_id)
        assert exp2_updated["amount_centavos"] == 10000

        # Verify reports reflect updated total: 15000 + 10000 + 20000 = 45000 (₱450.00)
        report_s4 = generate_monthly_report(
            get_expenses(conn, start_date=start_curr, end_date_exclusive=end_curr),
            current_month,
        )
        assert report_s4.total_centavos == 45000
        assert report_s4.transaction_count == 3

        # -------------------------------------------------------------------
        # Step 5: Set a Food budget of ₱1,000.00 for the current month.
        # -------------------------------------------------------------------
        b_food_id = set_budget(conn, cat_food["id"], current_month, parse_amount("1000.00"))
        assert b_food_id > 0
        b_food = get_budget(conn, cat_food["id"], current_month)
        assert b_food["limit_centavos"] == 100000

        # -------------------------------------------------------------------
        # Step 6: Confirm Food spent is ₱150.00, remaining is ₱850.00, and progress is 15%.
        # -------------------------------------------------------------------
        month_expenses = get_expenses(conn, start_date=start_curr, end_date_exclusive=end_curr)
        status_s6 = calculate_budget_progress(b_food, month_expenses)
        assert status_s6.spent_centavos == 15000  # ₱150.00
        assert status_s6.remaining_centavos == 85000  # ₱850.00
        assert round(status_s6.progress_ratio * 100) == 15  # 15%
        assert status_s6.status_level == "normal"

        # -------------------------------------------------------------------
        # Step 7: Add enough Food expenses to exceed the limit, then confirm exceeded amount is visible and visual bar stays capped.
        # -------------------------------------------------------------------
        # Add ₱900.00 Food expense -> Total Food spent becomes ₱1,050.00 (> ₱1,000.00 limit)
        create_expense(
            conn=conn,
            amount_centavos=parse_amount("900.00"),
            description="Dinner buffet celebration",
            occurred_on=today_iso,
            category_id=cat_food["id"],
            category_source="manual",
        )
        month_expenses_s7 = get_expenses(conn, start_date=start_curr, end_date_exclusive=end_curr)
        status_s7 = calculate_budget_progress(b_food, month_expenses_s7)
        assert status_s7.spent_centavos == 105000  # ₱1,050.00
        assert status_s7.remaining_centavos == -5000  # -₱50.00 over budget!
        assert status_s7.progress_ratio == 1.05
        # Visual progress must be strictly capped to 1.0
        assert status_s7.visual_progress == 1.0
        assert status_s7.status_level == "exceeded"

        # -------------------------------------------------------------------
        # Step 8: Navigate to a different month and confirm report and budget values are isolated to that month.
        # -------------------------------------------------------------------
        next_month = shift_month(current_month, 1)
        start_next, end_next = month_range(next_month)

        # No expenses exist in next month
        report_next = generate_monthly_report(
            get_expenses(conn, start_date=start_next, end_date_exclusive=end_next),
            next_month,
        )
        assert report_next.total_centavos == 0
        assert report_next.transaction_count == 0

        # No budgets set for next month
        budgets_next = get_budgets_for_month(conn, next_month)
        assert len(budgets_next) == 0

        # -------------------------------------------------------------------
        # Step 9: Restart the app (re-open DB) and verify that saved expenses and budgets remain intact.
        # -------------------------------------------------------------------
        conn.close()
        new_conn = init_database(db_path)

        persisted_expenses = get_expenses(new_conn)
        assert len(persisted_expenses) == 4  # exp1, exp2, exp3, exp4

        persisted_food_budget = get_budget(new_conn, cat_food["id"], current_month)
        assert persisted_food_budget is not None
        assert persisted_food_budget["limit_centavos"] == 100000

        # -------------------------------------------------------------------
        # Step 10: Try blank/invalid amounts and delete cancellation; data remains unchanged.
        # -------------------------------------------------------------------
        with pytest.raises(ValueError):
            parse_amount("")
        with pytest.raises(ValueError):
            parse_amount("0")
        with pytest.raises(ValueError):
            parse_amount("-50")
        with pytest.raises(ValueError):
            parse_amount("not_a_number")

        assert validate_date("bad-date") is False

        # Verify row count is still 4
        assert len(get_expenses(new_conn)) == 4

        # Delete expense 1 and verify only it is removed
        assert delete_expense(new_conn, exp1_id) is True
        assert len(get_expenses(new_conn)) == 3
        assert get_expense_by_id(new_conn, exp1_id) is None

        new_conn.close()
