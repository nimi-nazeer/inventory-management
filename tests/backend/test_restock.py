"""
Tests for the restocking endpoints: recommendations, order submission, order listing.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Submitted orders live in module memory; isolate each test."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


def _recommend(client, budget):
    response = client.get("/api/restock/recommendations", params={"budget": budget})
    assert response.status_code == 200
    return response.json()


class TestRecommendations:
    def test_zero_budget_returns_no_items(self, client):
        data = _recommend(client, 0)
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_rejected(self, client):
        response = client.get("/api/restock/recommendations", params={"budget": -1})
        assert response.status_code == 422

    def test_large_budget_covers_every_shortfall(self, client):
        data = _recommend(client, 1_000_000)
        expected = {
            f["item_sku"]: f["forecasted_demand"] - f["current_stock"]
            for f in main.demand_forecasts
            if f["forecasted_demand"] > f["current_stock"]
        }
        assert {i["sku"]: i["quantity"] for i in data["items"]} == expected

    @pytest.mark.parametrize("budget", [100, 1000, 2500, 5000, 12345.67])
    def test_never_exceeds_budget(self, client, budget):
        data = _recommend(client, budget)
        assert data["total_cost"] <= budget
        assert data["remaining_budget"] >= 0
        assert data["total_cost"] == pytest.approx(sum(i["line_cost"] for i in data["items"]))

    def test_ranked_by_forecast_growth(self, client):
        growth = [i["growth_percent"] for i in _recommend(client, 1_000_000)["items"]]
        assert growth == sorted(growth, reverse=True)

    def test_items_include_lead_time_and_cost(self, client):
        item = _recommend(client, 1_000_000)["items"][0]
        for key in ("sku", "name", "quantity", "unit_cost", "line_cost", "lead_time_days"):
            assert key in item


class TestCreateOrder:
    def test_happy_path_uses_longest_lead_time(self, client):
        payload = {
            "budget": 10000,
            "items": [{"sku": "WDG-001", "quantity": 10}, {"sku": "BRG-102", "quantity": 2}],
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 200
        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        # WDG-001 = 7 days, BRG-102 = 14 days
        assert order["lead_time_days"] == 14
        assert order["total_cost"] == pytest.approx(10 * 18.5 + 2 * 42.0)
        assert order["estimated_delivery"] > order["submitted_date"]

    def test_over_budget_rejected(self, client):
        payload = {"budget": 10, "items": [{"sku": "WDG-001", "quantity": 10}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 422

    def test_empty_items_rejected(self, client):
        assert client.post("/api/restock-orders", json={"budget": 100, "items": []}).status_code == 422

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        payload = {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": quantity}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 422

    def test_unknown_sku_not_found(self, client):
        payload = {"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 404


class TestListOrders:
    def test_empty_initially(self, client):
        assert client.get("/api/restock-orders").json() == []

    def test_submitted_orders_listed_newest_first(self, client):
        for sku in ("WDG-001", "GSK-203"):
            client.post("/api/restock-orders", json={"budget": 1000, "items": [{"sku": sku, "quantity": 1}]})
        orders = client.get("/api/restock-orders").json()
        assert [o["items"][0]["sku"] for o in orders] == ["GSK-203", "WDG-001"]
