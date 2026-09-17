"""
Tests for reports API endpoints.
"""
import pytest

from main import quarter_of, quarter_sort_key


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        required_fields = [
            "quarter",
            "total_orders",
            "total_revenue",
            "delivered_orders",
            "avg_order_value",
            "fulfillment_rate"
        ]

        for row in data:
            for field in required_fields:
                assert field in row, f"Missing field: {field}"

    def test_fulfillment_rate_always_present_and_in_range(self, client):
        """Fulfillment rate must never be missing, so the client can't render 'undefined%'."""
        data = client.get("/api/reports/quarterly").json()

        for row in data:
            assert isinstance(row["fulfillment_rate"], (int, float))
            assert 0 <= row["fulfillment_rate"] <= 100

    def test_quarters_sorted_chronologically(self, client):
        """Quarters come back oldest first."""
        data = client.get("/api/reports/quarterly").json()
        keys = [quarter_sort_key(row) for row in data]
        assert keys == sorted(keys)

    def test_quarterly_respects_warehouse_filter(self, client):
        """Order totals must match /api/orders under the same filter."""
        expected = len(client.get("/api/orders?warehouse=Tokyo").json())

        data = client.get("/api/reports/quarterly?warehouse=Tokyo").json()
        assert sum(row["total_orders"] for row in data) == expected

    def test_quarterly_respects_status_filter(self, client):
        """A delivered-only report is 100% fulfilled by definition."""
        data = client.get("/api/reports/quarterly?status=delivered").json()
        assert len(data) > 0

        for row in data:
            assert row["total_orders"] == row["delivered_orders"]
            assert row["fulfillment_rate"] == 100.0

    def test_quarterly_respects_month_filter(self, client):
        """Filtering to a single month leaves only that month's quarter."""
        data = client.get("/api/reports/quarterly?month=2025-02").json()
        assert [row["quarter"] for row in data] == ["Q1-2025"]

    def test_quarterly_respects_quarter_filter(self, client):
        """The period filter also accepts a quarter key."""
        data = client.get("/api/reports/quarterly?month=Q3-2025").json()
        assert [row["quarter"] for row in data] == ["Q3-2025"]

    def test_quarterly_unmatched_filter_returns_empty(self, client):
        """A filter matching nothing yields an empty report, not an error."""
        response = client.get("/api/reports/quarterly?warehouse=Nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_quarterly_revenue_matches_orders(self, client):
        """Revenue is the sum of the same orders /api/orders returns."""
        orders = client.get("/api/orders?warehouse=London").json()
        expected = sum(order["total_value"] for order in orders)

        data = client.get("/api/reports/quarterly?warehouse=London").json()
        actual = sum(row["total_revenue"] for row in data)
        assert actual == pytest.approx(expected)


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for row in data:
            for field in ["month", "order_count", "revenue", "delivered_count"]:
                assert field in row, f"Missing field: {field}"

    def test_months_sorted_chronologically(self, client):
        """Months come back oldest first."""
        data = client.get("/api/reports/monthly-trends").json()
        months = [row["month"] for row in data]
        assert months == sorted(months)

    def test_monthly_respects_month_filter(self, client):
        """Filtering to a single month leaves exactly that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-04").json()
        assert [row["month"] for row in data] == ["2025-04"]

    def test_monthly_respects_warehouse_filter(self, client):
        """Order counts must match /api/orders under the same filter."""
        expected = len(client.get("/api/orders?warehouse=Tokyo").json())

        data = client.get("/api/reports/monthly-trends?warehouse=Tokyo").json()
        assert sum(row["order_count"] for row in data) == expected

    def test_monthly_respects_category_filter(self, client):
        """Category narrows the report the same way it narrows orders."""
        orders = client.get("/api/orders?category=sensors").json()
        expected = sum(order["total_value"] for order in orders)

        data = client.get("/api/reports/monthly-trends?category=sensors").json()
        actual = sum(row["revenue"] for row in data)
        assert actual == pytest.approx(expected)

    def test_monthly_unmatched_filter_returns_empty(self, client):
        """A filter matching nothing yields an empty report, not an error."""
        response = client.get("/api/reports/monthly-trends?warehouse=Nonexistent")
        assert response.status_code == 200
        assert response.json() == []


class TestQuarterOf:
    """Test suite for the quarter_of() date helper."""

    @pytest.mark.parametrize("order_date,expected", [
        ("2025-01-08T10:19:00", "Q1-2025"),
        ("2025-03-31", "Q1-2025"),
        ("2025-04-01", "Q2-2025"),
        ("2025-07-15", "Q3-2025"),
        ("2025-12-31", "Q4-2025"),
    ])
    def test_maps_month_to_quarter(self, order_date, expected):
        assert quarter_of(order_date) == expected

    @pytest.mark.parametrize("order_date,expected", [
        ("2024-02-10", "Q1-2024"),
        ("2026-11-02", "Q4-2026"),
    ])
    def test_handles_years_other_than_2025(self, order_date, expected):
        """Orders outside 2025 get their own quarter instead of being dropped."""
        assert quarter_of(order_date) == expected

    @pytest.mark.parametrize("order_date", ["", "2025", "not-a-date", "2025-13-01", "2025-00-01"])
    def test_returns_none_for_unparseable_dates(self, order_date):
        assert quarter_of(order_date) is None

    def test_sort_key_orders_across_years(self):
        """Lexicographic sorting would put Q1-2026 before Q4-2025."""
        labels = ["Q1-2026", "Q4-2025", "Q1-2025"]
        ordered = sorted(labels, key=lambda label: quarter_sort_key({"quarter": label}))
        assert ordered == ["Q1-2025", "Q4-2025", "Q1-2026"]
