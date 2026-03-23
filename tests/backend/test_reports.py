"""
Tests for reports API endpoints.
"""
import pytest


class TestQuarterlyReportsEndpoints:
    """Test suite for quarterly reports endpoint."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports returns a list."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_quarterly_reports_have_valid_quarter_names(self, client):
        """Test that quarter names follow Q{1-4}-YYYY format."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        valid_quarters = ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]

        for quarter in data:
            assert quarter["quarter"] in valid_quarters, \
                f"Unexpected quarter name: {quarter['quarter']}"

    def test_quarterly_reports_are_sorted(self, client):
        """Test that quarterly reports are sorted by quarter."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        quarter_names = [q["quarter"] for q in data]
        assert quarter_names == sorted(quarter_names)

    def test_quarterly_reports_required_fields(self, client):
        """Test that each quarter has all required fields."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        required_fields = [
            "quarter", "total_orders", "total_revenue",
            "avg_order_value", "fulfillment_rate"
        ]

        for quarter in data:
            for field in required_fields:
                assert field in quarter, f"Missing field: {field} in {quarter['quarter']}"

    def test_quarterly_reports_revenue_is_positive(self, client):
        """Test that revenue sums are positive for each quarter."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert quarter["total_revenue"] > 0, \
                f"Revenue should be positive for {quarter['quarter']}"

    def test_quarterly_reports_fulfillment_rate_range(self, client):
        """Test that fulfillment rate is between 0 and 100."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert 0 <= quarter["fulfillment_rate"] <= 100, \
                f"Fulfillment rate {quarter['fulfillment_rate']} out of range for {quarter['quarter']}"

    def test_quarterly_reports_total_orders_positive(self, client):
        """Test that total orders count is positive for each quarter."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert quarter["total_orders"] > 0, \
                f"Total orders should be positive for {quarter['quarter']}"

    def test_quarterly_reports_avg_order_value_calculation(self, client):
        """Test that avg_order_value equals total_revenue / total_orders."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            expected_avg = round(quarter["total_revenue"] / quarter["total_orders"], 2)
            assert abs(quarter["avg_order_value"] - expected_avg) < 0.01, \
                f"Avg order value mismatch for {quarter['quarter']}"

    def test_quarterly_reports_data_types(self, client):
        """Test that quarterly report fields have correct data types."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            assert isinstance(quarter["quarter"], str)
            assert isinstance(quarter["total_orders"], int)
            assert isinstance(quarter["total_revenue"], (int, float))
            assert isinstance(quarter["avg_order_value"], (int, float))
            assert isinstance(quarter["fulfillment_rate"], (int, float))


class TestMonthlyTrendsEndpoints:
    """Test suite for monthly trends endpoint."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends returns a list."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_monthly_trends_returns_12_months(self, client):
        """Test that monthly trends returns 12 months of data."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        assert len(data) == 12, f"Expected 12 months, got {len(data)}"

    def test_monthly_trends_are_sorted(self, client):
        """Test that months are sorted chronologically."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        months = [entry["month"] for entry in data]
        assert months == sorted(months), "Months should be sorted chronologically"

    def test_monthly_trends_required_fields(self, client):
        """Test that each month has required fields."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        required_fields = ["month", "order_count", "revenue"]

        for entry in data:
            for field in required_fields:
                assert field in entry, f"Missing field: {field} in {entry.get('month', 'unknown')}"

    def test_monthly_trends_revenue_is_positive(self, client):
        """Test that revenue values are positive for each month."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for entry in data:
            assert entry["revenue"] > 0, \
                f"Revenue should be positive for {entry['month']}"

    def test_monthly_trends_order_count_is_positive(self, client):
        """Test that order counts are positive for each month."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for entry in data:
            assert entry["order_count"] > 0, \
                f"Order count should be positive for {entry['month']}"

    def test_monthly_trends_month_format(self, client):
        """Test that month values follow YYYY-MM format."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for entry in data:
            month = entry["month"]
            assert len(month) == 7, f"Month should be YYYY-MM format, got: {month}"
            assert month[4] == "-", f"Month should have dash separator, got: {month}"
            year = int(month[:4])
            month_num = int(month[5:7])
            assert 2020 <= year <= 2030
            assert 1 <= month_num <= 12

    def test_monthly_trends_data_types(self, client):
        """Test that monthly trend fields have correct data types."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        for entry in data:
            assert isinstance(entry["month"], str)
            assert isinstance(entry["order_count"], int)
            assert isinstance(entry["revenue"], (int, float))

    def test_monthly_trends_consistent_with_orders(self, client):
        """Test that monthly trends total matches actual order count."""
        # Get monthly trends
        trends_response = client.get("/api/reports/monthly-trends")
        trends = trends_response.json()

        total_orders_from_trends = sum(entry["order_count"] for entry in trends)

        # Get all orders
        orders_response = client.get("/api/orders")
        all_orders = orders_response.json()["items"]

        # The total should match (orders with valid dates)
        orders_with_dates = [
            o for o in all_orders
            if o.get("order_date", "")[:7] in [t["month"] for t in trends]
        ]

        assert total_orders_from_trends == len(orders_with_dates)
