"""
Tests for edge cases and error handling across API endpoints.
"""
import pytest


class TestInvalidFilterValues:
    """Test suite for invalid and edge-case filter values."""

    def test_orders_nonexistent_warehouse(self, client):
        """Test orders with an invalid warehouse returns 400."""
        response = client.get("/api/orders?warehouse=Atlantis")
        assert response.status_code == 400

    def test_orders_nonexistent_category(self, client):
        """Test orders with an invalid category returns 400."""
        response = client.get("/api/orders?category=Unicorns")
        assert response.status_code == 400

    def test_orders_nonexistent_status(self, client):
        """Test orders with an invalid status returns 400."""
        response = client.get("/api/orders?status=Exploded")
        assert response.status_code == 400

    def test_inventory_nonexistent_warehouse(self, client):
        """Test inventory with an invalid warehouse returns 400."""
        response = client.get("/api/inventory?warehouse=Mars")
        assert response.status_code == 400

    def test_inventory_nonexistent_category(self, client):
        """Test inventory with an invalid category returns 400."""
        response = client.get("/api/inventory?category=MagicBeans")
        assert response.status_code == 400

    def test_dashboard_nonexistent_warehouse(self, client):
        """Test dashboard summary with invalid warehouse returns 400."""
        response = client.get("/api/dashboard/summary?warehouse=Nowhere")
        assert response.status_code == 400


class TestEmptyStringFilters:
    """Test suite for empty string filter values."""

    def test_orders_empty_warehouse_filter(self, client):
        """Test orders with empty warehouse filter."""
        response = client.get("/api/orders?warehouse=")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

    def test_orders_empty_category_filter(self, client):
        """Test orders with empty category filter."""
        response = client.get("/api/orders?category=")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

    def test_orders_empty_status_filter(self, client):
        """Test orders with empty status filter."""
        response = client.get("/api/orders?status=")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

    def test_inventory_empty_filters(self, client):
        """Test inventory with empty filter values."""
        response = client.get("/api/inventory?warehouse=&category=")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)


class TestMonthFilterFormats:
    """Test suite for various month filter formats."""

    def test_orders_month_yyyy_mm(self, client):
        """Test month filter with YYYY-MM format."""
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)
        for order in data:
            assert "2025-01" in order["order_date"]

    def test_orders_month_quarter_format(self, client):
        """Test month filter with quarter format Q1-2025."""
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        q1_months = ["2025-01", "2025-02", "2025-03"]
        for order in data:
            assert any(m in order["order_date"] for m in q1_months)

    def test_orders_month_nonexistent_month(self, client):
        """Test month filter with an invalid month returns 400."""
        response = client.get("/api/orders?month=2020-01")
        assert response.status_code == 400

    def test_orders_month_invalid_quarter(self, client):
        """Test month filter with an invalid quarter returns 400."""
        response = client.get("/api/orders?month=Q5-2025")
        assert response.status_code == 400

    def test_orders_month_all_returns_everything(self, client):
        """Test that month=all returns all orders."""
        response_all = client.get("/api/orders?month=all")
        response_none = client.get("/api/orders")

        assert len(response_all.json()["items"]) == len(response_none.json()["items"])

    def test_dashboard_month_filter(self, client):
        """Test dashboard with specific month filter."""
        response = client.get("/api/dashboard/summary?month=2025-06")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "total_orders_value" in data


class TestNotFoundErrors:
    """Test suite for 404 error responses."""

    def test_inventory_item_not_found(self, client):
        """Test that nonexistent inventory item ID returns 404."""
        response = client.get("/api/inventory/nonexistent-id-12345")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_order_not_found(self, client):
        """Test that nonexistent order ID returns 404."""
        response = client.get("/api/orders/nonexistent-order-99999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_inventory_item_numeric_nonexistent_id(self, client):
        """Test that a numeric ID that doesn't exist returns 404."""
        response = client.get("/api/inventory/99999")
        assert response.status_code == 404

    def test_order_numeric_nonexistent_id(self, client):
        """Test that a numeric order ID that doesn't exist returns 404."""
        response = client.get("/api/orders/99999")
        assert response.status_code == 404


class TestRestockingEdgeCases:
    """Test suite for restocking endpoint edge cases."""

    def test_recommendations_budget_zero(self, client):
        """Test recommendations with budget of 0 returns 400."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 400

    def test_recommendations_very_large_budget(self, client):
        """Test that a very large budget includes all items."""
        response = client.get("/api/restocking/recommendations?budget=10000000")
        assert response.status_code == 200

        data = response.json()

        # All items should be included with a very large budget
        for item in data["items"]:
            assert item["included"] is True, \
                f"Item {item['item_sku']} should be included with large budget"

        assert data["items_included"] == len(data["items"])

    def test_recommendations_very_small_budget(self, client):
        """Test that a very small budget includes few or no items."""
        response = client.get("/api/restocking/recommendations?budget=1")
        assert response.status_code == 200

        data = response.json()
        assert data["total_cost"] <= 1
        # With $1 budget, likely no items can be restocked
        assert data["items_included"] <= 1

    def test_recommendations_budget_equals_cheapest_item(self, client):
        """Test budget that exactly matches cheapest item cost."""
        # First get all items to find the cheapest
        response = client.get("/api/restocking/recommendations?budget=10000000")
        data = response.json()

        if len(data["items"]) > 0:
            # Find item with lowest restock cost
            cheapest = min(data["items"], key=lambda x: x["restock_cost"])
            exact_budget = cheapest["restock_cost"]

            # Request with exact budget for cheapest item
            response2 = client.get(
                f"/api/restocking/recommendations?budget={exact_budget}"
            )
            data2 = response2.json()

            assert data2["total_cost"] <= exact_budget
            assert data2["items_included"] >= 1

    def test_recommendations_negative_budget_handled(self, client):
        """Test that negative budget returns 400."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 400


class TestCaseSensitivityEdgeCases:
    """Test suite for case sensitivity in filters."""

    def test_category_filter_valid_value(self, client):
        """Test that category filter works with valid value."""
        response = client.get("/api/inventory?category=Sensors")
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) > 0
        for item in data:
            assert item["category"].lower() == "sensors"

    def test_status_filter_valid_value(self, client):
        """Test that status filter works with valid value."""
        response = client.get("/api/orders?status=Delivered")
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "delivered"

    def test_warehouse_filter_valid_value(self, client):
        """Test that warehouse filter works with valid value."""
        response = client.get("/api/inventory?warehouse=San Francisco")
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) > 0
        for item in data:
            assert item["warehouse"] == "San Francisco"
