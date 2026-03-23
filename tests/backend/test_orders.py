"""
Tests for orders API endpoints.
"""
import pytest


class TestOrdersEndpoints:
    """Test suite for order-related endpoints."""

    def test_get_all_orders(self, client):
        """Test getting all orders."""
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_orders_response_structure(self, client):
        """Test that orders have all required fields."""
        response = client.get("/api/orders")
        data = response.json()["items"]

        required_fields = [
            "id", "order_number", "customer", "items",
            "status", "order_date", "expected_delivery", "total_value"
        ]

        for order in data:
            for field in required_fields:
                assert field in order, f"Missing field: {field}"

    def test_orders_items_structure(self, client):
        """Test that order items have correct structure."""
        response = client.get("/api/orders")
        data = response.json()["items"]

        for order in data:
            assert isinstance(order["items"], list)
            assert len(order["items"]) > 0
            for item in order["items"]:
                assert "sku" in item
                assert "name" in item
                assert "quantity" in item
                assert "unit_price" in item

    def test_orders_data_types(self, client):
        """Test that order fields have correct data types."""
        response = client.get("/api/orders")
        data = response.json()["items"]

        for order in data:
            assert isinstance(order["id"], str)
            assert isinstance(order["order_number"], str)
            assert isinstance(order["customer"], str)
            assert isinstance(order["status"], str)
            assert isinstance(order["total_value"], (int, float))
            assert order["total_value"] >= 0

    def test_get_orders_filter_by_warehouse(self, client):
        """Test filtering orders by warehouse."""
        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert order["warehouse"] == "Tokyo"

    def test_get_orders_filter_by_category(self, client):
        """Test filtering orders by category."""
        response = client.get("/api/orders?category=Sensors")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert order["category"].lower() == "sensors"

    def test_get_orders_filter_by_status(self, client):
        """Test filtering orders by status."""
        response = client.get("/api/orders?status=Delivered")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert order["status"].lower() == "delivered"

    def test_get_orders_filter_by_month(self, client):
        """Test filtering orders by month."""
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert "2025-01" in order["order_date"]

    def test_get_orders_filter_by_quarter(self, client):
        """Test filtering orders by quarter."""
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        q1_months = ["2025-01", "2025-02", "2025-03"]
        for order in data:
            assert any(m in order["order_date"] for m in q1_months)

    def test_get_orders_combined_filters(self, client):
        """Test filtering orders by multiple filters simultaneously."""
        response = client.get(
            "/api/orders?warehouse=San Francisco&category=Sensors&status=Delivered"
        )
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert order["warehouse"] == "San Francisco"
            assert order["category"].lower() == "sensors"
            assert order["status"].lower() == "delivered"

    def test_get_orders_combined_filters_with_month(self, client):
        """Test filtering orders by all filters including month."""
        response = client.get(
            "/api/orders?warehouse=Tokyo&status=Delivered&month=2025-01"
        )
        assert response.status_code == 200

        data = response.json()["items"]
        assert isinstance(data, list)

        for order in data:
            assert order["warehouse"] == "Tokyo"
            assert order["status"].lower() == "delivered"
            assert "2025-01" in order["order_date"]

    def test_get_orders_all_filter_returns_all(self, client):
        """Test that 'all' filter values return all orders."""
        response_all = client.get(
            "/api/orders?warehouse=all&category=all&status=all&month=all"
        )
        response_no_filter = client.get("/api/orders")

        assert response_all.status_code == 200
        assert response_no_filter.status_code == 200

        assert len(response_all.json()["items"]) == len(response_no_filter.json()["items"])

    def test_get_orders_empty_results(self, client):
        """Test that filtering with invalid values returns 400."""
        response = client.get("/api/orders?warehouse=NonexistentWarehouse")
        assert response.status_code == 400

    def test_get_orders_filter_reduces_results(self, client):
        """Test that applying a filter returns fewer or equal results."""
        response_all = client.get("/api/orders")
        response_filtered = client.get("/api/orders?status=Delivered")

        all_count = len(response_all.json()["items"])
        filtered_count = len(response_filtered.json()["items"])

        assert filtered_count <= all_count


class TestOrderByIdEndpoints:
    """Test suite for getting a specific order by ID."""

    def test_get_order_by_valid_id(self, client):
        """Test getting a specific order by valid ID."""
        # First get all orders to find a valid ID
        response = client.get("/api/orders")
        all_orders = response.json()["items"]
        assert len(all_orders) > 0

        first_order_id = all_orders[0]["id"]

        # Now get that specific order
        response = client.get(f"/api/orders/{first_order_id}")
        assert response.status_code == 200

        order = response.json()
        assert order["id"] == first_order_id

    def test_get_order_by_id_returns_correct_order(self, client):
        """Test that fetching by ID returns the matching order data."""
        response = client.get("/api/orders")
        all_orders = response.json()["items"]

        target_order = all_orders[0]
        response = client.get(f"/api/orders/{target_order['id']}")
        assert response.status_code == 200

        fetched_order = response.json()
        assert fetched_order["order_number"] == target_order["order_number"]
        assert fetched_order["customer"] == target_order["customer"]
        assert fetched_order["total_value"] == target_order["total_value"]

    def test_get_order_by_id_has_all_fields(self, client):
        """Test that order retrieved by ID has all required fields."""
        response = client.get("/api/orders/1")
        assert response.status_code == 200

        order = response.json()
        required_fields = [
            "id", "order_number", "customer", "items",
            "status", "order_date", "expected_delivery", "total_value"
        ]

        for field in required_fields:
            assert field in order, f"Missing field: {field}"

    def test_get_order_by_invalid_id_returns_404(self, client):
        """Test that invalid order ID returns 404."""
        response = client.get("/api/orders/nonexistent-id-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_order_by_empty_string_id_returns_404(self, client):
        """Test that fetching order with unlikely ID returns 404."""
        response = client.get("/api/orders/00000")
        assert response.status_code == 404
