"""
Tests for restocking API endpoints.
"""
import pytest
from datetime import datetime, timedelta


class TestRestockingRecommendationsEndpoints:
    """Test suite for restocking recommendations endpoint."""

    def test_get_recommendations_basic(self, client):
        """Test getting restocking recommendations with a budget."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert "total_cost" in data
        assert "budget" in data
        assert "items_included" in data

    def test_recommendations_budget_1000(self, client):
        """Test recommendations with a small budget of $1000."""
        response = client.get("/api/restocking/recommendations?budget=1000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 1000
        assert data["total_cost"] <= 1000

    def test_recommendations_budget_50000(self, client):
        """Test recommendations with a medium budget of $50000."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 50000
        assert data["total_cost"] <= 50000

    def test_recommendations_budget_1000000(self, client):
        """Test recommendations with a large budget of $1000000."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        assert data["budget"] == 1000000
        assert data["total_cost"] <= 1000000

    def test_recommendations_sorted_by_demand_gap_descending(self, client):
        """Test that items are sorted by demand_gap in descending order."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        items = data["items"]
        demand_gaps = [item["demand_gap"] for item in items]

        assert demand_gaps == sorted(demand_gaps, reverse=True), \
            "Items should be sorted by demand_gap descending"

    def test_recommendations_total_cost_within_budget(self, client):
        """Test that total cost of included items does not exceed budget."""
        budget = 25000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()

        assert data["total_cost"] <= budget

        # Verify by summing included items
        included_cost = sum(
            item["restock_cost"] for item in data["items"] if item["included"]
        )
        assert abs(included_cost - data["total_cost"]) < 0.01

    def test_recommendations_included_items_count(self, client):
        """Test that items_included matches number of included items."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        included_count = sum(1 for item in data["items"] if item["included"])
        assert data["items_included"] == included_count

    def test_recommendations_excluded_items_exceed_remaining_budget(self, client):
        """Test that excluded items would exceed the remaining budget."""
        budget = 10000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()

        remaining_budget = budget - data["total_cost"]

        # Each excluded item's restock_cost should exceed remaining budget
        # (greedy algorithm: items are processed in order, so excluded items
        # would have exceeded the budget when encountered)
        running_total = 0.0
        for item in data["items"]:
            if item["included"]:
                running_total += item["restock_cost"]
            else:
                # This item was skipped because adding it would exceed budget
                assert running_total + item["restock_cost"] > budget, \
                    f"Item {item['item_sku']} could fit in budget but was excluded"

    def test_recommendations_item_structure(self, client):
        """Test that recommendation items have all required fields."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        required_fields = [
            "item_sku", "item_name", "current_demand",
            "forecasted_demand", "demand_gap", "unit_cost",
            "restock_cost", "included"
        ]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_recommendations_demand_gap_calculation(self, client):
        """Test that demand_gap equals forecasted_demand minus current_demand."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        for item in data["items"]:
            expected_gap = item["forecasted_demand"] - item["current_demand"]
            assert item["demand_gap"] == expected_gap, \
                f"Demand gap mismatch for {item['item_sku']}"

    def test_recommendations_only_positive_demand_gap(self, client):
        """Test that only items with positive demand gap are included."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        data = response.json()

        for item in data["items"]:
            assert item["demand_gap"] > 0, \
                f"Item {item['item_sku']} has non-positive demand gap"

    def test_recommendations_restock_cost_calculation(self, client):
        """Test that restock_cost equals demand_gap times unit_cost."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        for item in data["items"]:
            expected_cost = round(item["demand_gap"] * item["unit_cost"], 2)
            assert abs(item["restock_cost"] - expected_cost) < 0.01, \
                f"Restock cost mismatch for {item['item_sku']}"

    def test_recommendations_data_types(self, client):
        """Test that recommendation fields have correct data types."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        data = response.json()

        assert isinstance(data["total_cost"], (int, float))
        assert isinstance(data["budget"], (int, float))
        assert isinstance(data["items_included"], int)

        for item in data["items"]:
            assert isinstance(item["demand_gap"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["restock_cost"], (int, float))
            assert isinstance(item["included"], bool)


class TestRestockingOrdersEndpoints:
    """Test suite for restocking orders creation and retrieval."""

    def test_get_restocking_orders_initially(self, client):
        """Test getting restocking orders returns a list."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_restocking_order_valid(self, client):
        """Test creating a restocking order with valid data."""
        request_data = {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 100, "unit_price": 15.50}
            ],
            "budget": 5000
        }

        response = client.post("/api/restocking/orders", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_create_restocking_order_has_rst_prefix(self, client):
        """Test that created order number starts with RST-."""
        request_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget", "quantity": 50, "unit_price": 10.0}
            ],
            "budget": 1000
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        assert data["order_number"].startswith("RST-"), \
            f"Order number should start with RST-, got: {data['order_number']}"

    def test_create_restocking_order_status_is_processing(self, client):
        """Test that created order has Processing status."""
        request_data = {
            "items": [
                {"sku": "BRG-102", "name": "Bearing", "quantity": 20, "unit_price": 42.75}
            ],
            "budget": 2000
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        assert data["status"] == "Processing"

    def test_create_restocking_order_expected_delivery_14_days(self, client):
        """Test that expected delivery is approximately 14 days from now."""
        request_data = {
            "items": [
                {"sku": "GSK-203", "name": "Gasket", "quantity": 100, "unit_price": 8.25}
            ],
            "budget": 1500
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])

        days_diff = (expected_delivery - order_date).days
        assert days_diff == 14, \
            f"Expected delivery should be 14 days after order, got {days_diff} days"

    def test_create_restocking_order_total_value_calculation(self, client):
        """Test that total_value is calculated correctly from items."""
        request_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget A", "quantity": 10, "unit_price": 15.50},
                {"sku": "BRG-102", "name": "Bearing", "quantity": 5, "unit_price": 42.75}
            ],
            "budget": 5000
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        expected_value = round(10 * 15.50 + 5 * 42.75, 2)
        assert abs(data["total_value"] - expected_value) < 0.01

    def test_create_restocking_order_response_fields(self, client):
        """Test that created order has all expected fields."""
        request_data = {
            "items": [
                {"sku": "FLT-405", "name": "Filter", "quantity": 50, "unit_price": 12.50}
            ],
            "budget": 1000
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        required_fields = [
            "id", "order_number", "customer", "items",
            "status", "order_date", "expected_delivery", "total_value"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_create_restocking_order_appears_in_list(self, client):
        """Test that a created order appears in GET /api/restocking/orders."""
        # Get current count
        before_response = client.get("/api/restocking/orders")
        before_count = len(before_response.json())

        # Create a new order
        request_data = {
            "items": [
                {"sku": "VLV-506", "name": "Valve", "quantity": 30, "unit_price": 67.90}
            ],
            "budget": 3000
        }
        create_response = client.post("/api/restocking/orders", json=request_data)
        created_order = create_response.json()

        # Check it appears in the list
        after_response = client.get("/api/restocking/orders")
        after_data = after_response.json()

        assert len(after_data) == before_count + 1

        # Find the created order in the list
        order_ids = [o["id"] for o in after_data]
        assert created_order["id"] in order_ids

    def test_create_restocking_order_customer_is_restocking(self, client):
        """Test that restocking order customer is set to 'Restocking Order'."""
        request_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget", "quantity": 10, "unit_price": 15.50}
            ],
            "budget": 500
        }

        response = client.post("/api/restocking/orders", json=request_data)
        data = response.json()

        assert data["customer"] == "Restocking Order"
