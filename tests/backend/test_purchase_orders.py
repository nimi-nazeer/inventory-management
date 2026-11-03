"""
Tests for purchase order API endpoints (POST /api/purchase-orders, GET /api/purchase-orders/{backlog_item_id}).
"""
import pytest

import main


@pytest.fixture(autouse=True)
def isolated_purchase_orders(monkeypatch):
    """Start every test with no purchase orders.

    Purchase orders live in a shared module-level list (the backlog endpoint derives
    has_purchase_order from it) and cannot be deleted through the API, so each test
    works on its own empty list that is discarded afterwards.
    """
    monkeypatch.setattr(main, "purchase_orders", [])


@pytest.fixture
def backlog_item(client):
    """A real backlog item to attach purchase orders to."""
    items = client.get("/api/backlog").json()
    assert len(items) > 0
    return items[0]


def po_payload(backlog_item_id, **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "FilterMax Inc",
        "quantity": 350,
        "unit_cost": 4.2,
        "expected_delivery_date": "2025-10-20",
        "notes": "Rush order",
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client, backlog_item):
        """Test creating a purchase order returns 201 and the full structure."""
        response = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"]))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_item["id"]
        assert po["supplier_name"] == "FilterMax Inc"
        assert po["quantity"] == 350
        assert po["unit_cost"] == 4.2
        assert po["expected_delivery_date"] == "2025-10-20"
        assert po["status"] == "Pending"
        assert po["notes"] == "Rush order"
        # created_date is a plain ISO date
        assert len(po["created_date"]) == 10 and po["created_date"].count("-") == 2

    def test_create_purchase_order_notes_optional(self, client, backlog_item):
        """Test that notes can be omitted."""
        payload = po_payload(backlog_item["id"])
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_purchase_order_ids_are_unique(self, client):
        """Test that two purchase orders never share an id."""
        items = client.get("/api/backlog").json()
        assert len(items) >= 2

        first = client.post("/api/purchase-orders", json=po_payload(items[0]["id"])).json()
        second = client.post("/api/purchase-orders", json=po_payload(items[1]["id"])).json()
        assert first["id"] != second["id"]

    def test_get_purchase_order_by_backlog_item(self, client, backlog_item):
        """Test fetching a created purchase order by its backlog item id."""
        created = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"])).json()

        response = client.get(f"/api/purchase-orders/{backlog_item['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_purchase_order_none_exists(self, client, backlog_item):
        """Test that a backlog item without a purchase order returns 404."""
        response = client.get(f"/api/purchase-orders/{backlog_item['id']}")
        assert response.status_code == 404
        assert "no purchase order" in response.json()["detail"].lower()

    def test_create_purchase_order_updates_backlog_flag(self, client, backlog_item):
        """Test that /api/backlog reports has_purchase_order after a PO is created."""
        def flag():
            items = client.get("/api/backlog").json()
            return next(i for i in items if i["id"] == backlog_item["id"])["has_purchase_order"]

        assert flag() is False
        client.post("/api/purchase-orders", json=po_payload(backlog_item["id"]))
        assert flag() is True

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test that an unknown backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=po_payload("does-not-exist-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_duplicate(self, client, backlog_item):
        """Test that a backlog item can only have one purchase order."""
        first = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"]))
        assert first.status_code == 201

        second = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"]))
        assert second.status_code == 409
        assert "already has a purchase order" in second.json()["detail"].lower()

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("quantity", -5),
        ("unit_cost", 0),
        ("unit_cost", -1.5),
        ("supplier_name", ""),
    ])
    def test_create_purchase_order_invalid_values(self, client, backlog_item, field, value):
        """Test that non-positive numbers and an empty supplier fail validation."""
        response = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"], **{field: value}))
        assert response.status_code == 422

    def test_create_purchase_order_blank_supplier(self, client, backlog_item):
        """Test that a whitespace-only supplier is rejected."""
        response = client.post("/api/purchase-orders", json=po_payload(backlog_item["id"], supplier_name="   "))
        assert response.status_code == 400
        assert "supplier_name" in response.json()["detail"]

    def test_create_purchase_order_invalid_date(self, client, backlog_item):
        """Test that a malformed delivery date is rejected."""
        # "2025-1-5" is unpadded: strptime would accept it, but it is not YYYY-MM-DD
        for bad_date in ["tomorrow", "20/10/2025", "2025-13-01", "2025-1-5"]:
            response = client.post(
                "/api/purchase-orders",
                json=po_payload(backlog_item["id"], expected_delivery_date=bad_date),
            )
            assert response.status_code == 400, bad_date
            assert "expected_delivery_date" in response.json()["detail"]

    def test_create_purchase_order_missing_fields(self, client, backlog_item):
        """Test that required fields are enforced."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": backlog_item["id"]})
        assert response.status_code == 422
