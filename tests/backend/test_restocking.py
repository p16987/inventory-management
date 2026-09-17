"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockRecommendationEndpoints:
    """Test suite for the budget-based restocking recommendations."""

    def test_get_recommendations_default_budget(self, client):
        """Test getting recommendations without specifying a budget."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "budget" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert "items" in data
        assert "skipped_count" in data
        assert isinstance(data["items"], list)

    def test_recommendation_item_structure(self, client):
        """Test that recommended items have the full expected structure."""
        response = client.get("/api/restock/recommendations?budget=50000")
        data = response.json()
        assert len(data["items"]) > 0

        for item in data["items"]:
            assert "item_sku" in item
            assert "item_name" in item
            assert "category" in item
            assert "unit_cost" in item
            assert "quantity_on_hand" in item
            assert "forecasted_demand" in item
            assert "shortfall" in item
            assert "recommended_quantity" in item
            assert "line_total" in item
            assert "lead_time_days" in item
            assert "trend" in item
            assert "fully_covered" in item

    def test_recommendation_types_and_ranges(self, client):
        """Test that recommendation numeric fields have valid types and ranges."""
        response = client.get("/api/restock/recommendations?budget=50000")
        data = response.json()

        for item in data["items"]:
            assert isinstance(item["quantity_on_hand"], int)
            assert isinstance(item["forecasted_demand"], int)
            assert isinstance(item["shortfall"], int)
            assert isinstance(item["recommended_quantity"], int)
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["line_total"], (int, float))
            assert isinstance(item["lead_time_days"], int)
            assert isinstance(item["fully_covered"], bool)

            assert item["shortfall"] > 0
            assert item["recommended_quantity"] > 0
            assert item["unit_cost"] > 0
            assert item["lead_time_days"] > 0

    def test_recommendations_stay_within_budget(self, client):
        """Test that the plan total never exceeds the requested budget."""
        for budget in [500, 2500, 10000, 29000, 50000]:
            response = client.get(f"/api/restock/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["total_cost"] <= budget
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_line_totals_match_quantity_times_cost(self, client):
        """Test that each line total equals quantity multiplied by unit cost."""
        response = client.get("/api/restock/recommendations?budget=50000")
        data = response.json()

        for item in data["items"]:
            expected = item["recommended_quantity"] * item["unit_cost"]
            assert abs(item["line_total"] - expected) < 0.01

    def test_total_cost_matches_sum_of_lines(self, client):
        """Test that the plan total equals the sum of its line totals."""
        response = client.get("/api/restock/recommendations?budget=15000")
        data = response.json()

        calculated_total = sum(item["line_total"] for item in data["items"])
        assert abs(data["total_cost"] - calculated_total) < 0.01

    def test_recommendations_sorted_by_urgency(self, client):
        """Test that items are returned most urgent (largest shortfall) first."""
        response = client.get("/api/restock/recommendations?budget=50000")
        data = response.json()

        shortfalls = [item["shortfall"] for item in data["items"]]
        assert shortfalls == sorted(shortfalls, reverse=True)

    def test_recommended_quantity_never_exceeds_shortfall(self, client):
        """Test that the plan never orders more than the forecast gap."""
        response = client.get("/api/restock/recommendations?budget=50000")
        data = response.json()

        for item in data["items"]:
            assert item["recommended_quantity"] <= item["shortfall"]

    def test_fully_covered_flag_is_accurate(self, client):
        """Test that fully_covered reflects whether the shortfall was fully funded."""
        response = client.get("/api/restock/recommendations?budget=3000")
        data = response.json()

        for item in data["items"]:
            expected = item["recommended_quantity"] == item["shortfall"]
            assert item["fully_covered"] == expected

    def test_large_budget_covers_every_shortfall(self, client):
        """Test that a large enough budget fully covers all candidates."""
        response = client.get("/api/restock/recommendations?budget=1000000")
        data = response.json()

        assert data["skipped_count"] == 0
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["fully_covered"] is True
            assert item["recommended_quantity"] == item["shortfall"]

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget returns an empty plan with items skipped."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["skipped_count"] > 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget returns a 400 error."""
        response = client.get("/api/restock/recommendations?budget=-100")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_recommendations_match_inventory_and_forecast_data(self, client):
        """Test that recommendations cross-check against inventory and demand data."""
        inventory = client.get("/api/inventory").json()
        forecasts = client.get("/api/demand").json()
        data = client.get("/api/restock/recommendations?budget=50000").json()

        forecast_by_sku = {f["item_sku"]: f for f in forecasts}

        for item in data["items"]:
            sku_rows = [row for row in inventory if row["sku"] == item["item_sku"]]
            assert len(sku_rows) > 0

            # Stock is aggregated across warehouses and priced at the highest unit cost.
            assert item["quantity_on_hand"] == sum(r["quantity_on_hand"] for r in sku_rows)
            assert item["unit_cost"] == max(r["unit_cost"] for r in sku_rows)

            forecast = forecast_by_sku[item["item_sku"]]
            assert item["forecasted_demand"] == forecast["forecasted_demand"]
            assert item["shortfall"] == forecast["forecasted_demand"] - item["quantity_on_hand"]


class TestRestockOrderEndpoints:
    """Test suite for submitting and listing restocking orders."""

    def test_get_restock_orders_returns_list(self, client):
        """Test that submitted restocking orders are returned as a list."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_restock_order(self, client):
        """Test submitting a restocking order."""
        plan = client.get("/api/restock/recommendations?budget=10000").json()
        items = [
            {"item_sku": item["item_sku"], "quantity": item["recommended_quantity"]}
            for item in plan["items"][:2]
        ]

        response = client.post(
            "/api/restock-orders",
            json={"budget": plan["budget"], "items": items}
        )
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["id"].startswith("RO-")
        assert order["order_number"].startswith("RESTOCK-")
        assert len(order["items"]) == len(items)
        assert order["total_cost"] <= plan["budget"]

    def test_created_order_priced_from_catalogue(self, client):
        """Test that the server prices submitted lines from inventory data."""
        inventory = client.get("/api/inventory").json()
        sku = inventory[0]["sku"]
        expected_cost = max(row["unit_cost"] for row in inventory if row["sku"] == sku)

        response = client.post(
            "/api/restock-orders",
            json={"budget": 100000, "items": [{"item_sku": sku, "quantity": 3}]}
        )
        assert response.status_code == 201

        line = response.json()["items"][0]
        assert line["unit_cost"] == expected_cost
        assert abs(line["line_total"] - 3 * expected_cost) < 0.01

    def test_order_lead_time_is_slowest_line(self, client):
        """Test that the order lead time is the longest of its item lead times."""
        response = client.post(
            "/api/restock-orders",
            json={
                "budget": 100000,
                "items": [
                    {"item_sku": "PSU-505", "quantity": 2},
                    {"item_sku": "SRV-301", "quantity": 1}
                ]
            }
        )
        assert response.status_code == 201

        order = response.json()
        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])

    def test_order_expected_delivery_follows_lead_time(self, client):
        """Test that expected delivery is the created date plus the lead time."""
        from datetime import datetime, timedelta

        response = client.post(
            "/api/restock-orders",
            json={"budget": 100000, "items": [{"item_sku": "PSU-505", "quantity": 1}]}
        )
        order = response.json()

        created = datetime.strptime(order["created_date"], "%Y-%m-%d")
        expected = created + timedelta(days=order["lead_time_days"])
        assert order["expected_delivery"] == expected.strftime("%Y-%m-%d")

    def test_submitted_order_appears_in_list(self, client):
        """Test that a submitted order is returned by the list endpoint."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 100000, "items": [{"item_sku": "PSU-505", "quantity": 1}]}
        )
        order_id = response.json()["id"]

        listed = client.get("/api/restock-orders").json()
        assert any(o["id"] == order_id for o in listed)

    def test_restock_orders_newest_first(self, client):
        """Test that the list returns the most recently submitted order first."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 100000, "items": [{"item_sku": "PSU-507", "quantity": 1}]}
        )
        newest_id = response.json()["id"]

        listed = client.get("/api/restock-orders").json()
        assert listed[0]["id"] == newest_id

    def test_order_over_budget_rejected(self, client):
        """Test that an order costing more than the budget is rejected."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 1, "items": [{"item_sku": "SRV-302", "quantity": 5}]}
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "budget" in data["detail"].lower()

    def test_order_with_unknown_sku_rejected(self, client):
        """Test that an order referencing an unknown SKU returns 404."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 10000, "items": [{"item_sku": "NOT-A-SKU", "quantity": 1}]}
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_empty_order_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 10000, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_zero_quantity_rejected(self, client):
        """Test that a line with a non-positive quantity is rejected."""
        response = client.post(
            "/api/restock-orders",
            json={"budget": 10000, "items": [{"item_sku": "PSU-505", "quantity": 0}]}
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_missing_fields_rejected(self, client):
        """Test that a malformed request body returns a validation error."""
        response = client.post("/api/restock-orders", json={"items": []})
        assert response.status_code == 422
