"""
Tests for data-quality regressions: text encoding and spending percentages.
"""
import pytest


class TestTextEncoding:
    """Non-ASCII characters in the JSON data must survive loading intact."""

    def test_inventory_has_no_mojibake(self, client):
        """Test that inventory text has no cp1252-misdecoded UTF-8 (e.g. 'Â±' instead of '±')."""
        data = client.get("/api/inventory").json()

        for item in data:
            for field in ("name", "category", "location", "sku"):
                assert "Â" not in item[field], f"Mojibake in {item['sku']} {field}: {item[field]!r}"
                assert "Ã" not in item[field], f"Mojibake in {item['sku']} {field}: {item[field]!r}"

    def test_plus_minus_sign_is_decoded(self, client):
        """Test that the '±' in PSU-504's name is decoded correctly."""
        data = client.get("/api/inventory").json()
        psu_504 = next((item for item in data if item["sku"] == "PSU-504"), None)

        assert psu_504 is not None, "PSU-504 missing from inventory"
        assert "±15V" in psu_504["name"]

    def test_json_data_files_are_valid_utf8(self):
        """Test that every data file decodes as strict UTF-8 (the loader assumes it)."""
        from pathlib import Path

        data_dir = Path(__file__).parent.parent.parent / "server" / "data"
        files = list(data_dir.glob("*.json"))
        assert files, "No data files found"

        for path in files:
            path.read_bytes().decode("utf-8")  # raises UnicodeDecodeError if not UTF-8


class TestCategorySpendingPercentages:
    """The 'percentage of total' shown for each spending category must be coherent."""

    def test_percentages_sum_to_100(self, client):
        """Test that category percentages add up to 100 (allowing for 1-decimal rounding)."""
        data = client.get("/api/spending/categories").json()
        assert len(data) > 0

        total = sum(category["percentage"] for category in data)
        assert abs(total - 100) <= 0.2, f"Percentages sum to {total}, expected ~100"

    def test_percentages_match_amounts(self, client):
        """Test that each percentage is that category's share of the total amount."""
        data = client.get("/api/spending/categories").json()
        total_amount = sum(category["amount"] for category in data)

        for category in data:
            expected = category["amount"] / total_amount * 100
            assert abs(category["percentage"] - expected) <= 0.05, category["category"]

    def test_percentages_within_range(self, client):
        """Test that no category exceeds 100% or goes negative."""
        for category in client.get("/api/spending/categories").json():
            assert 0 <= category["percentage"] <= 100
