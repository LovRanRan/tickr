"""Tests for tickr.portfolio.Portfolio and tickr.storage round-trip."""

import pytest

from tickr.models import PortfolioEntry
from tickr.portfolio import Portfolio
from tickr.storage import load_portfolio, save_portfolio


# -------- helpers --------

def make_entries() -> list[PortfolioEntry]:
    return [
        PortfolioEntry(symbol="btc", quantity=1.0, avg_cost=20000),
        PortfolioEntry(symbol="eth", quantity=5.0, avg_cost=2000),
    ]


# -------- construction --------

class TestPortfolioConstruction:
    def test_empty_portfolio(self):
        p = Portfolio()
        assert len(p) == 0
        assert list(p) == []

    def test_with_entries(self):
        p = Portfolio(make_entries())
        assert len(p) == 2

    def test_init_makes_defensive_copy(self):
        # Mutating the original list should NOT affect the Portfolio
        original = make_entries()
        p = Portfolio(original)
        original.clear()
        assert len(p) == 2


# -------- dunder methods --------

class TestDunders:
    def test_repr(self):
        p = Portfolio(make_entries())
        assert "Portfolio(" in repr(p)
        assert "2 holdings" in repr(p)
        assert "btc" in repr(p)
        assert "eth" in repr(p)

    def test_len(self):
        assert len(Portfolio()) == 0
        assert len(Portfolio(make_entries())) == 2

    def test_iter(self):
        p = Portfolio(make_entries())
        symbols = [e.symbol for e in p]
        assert symbols == ["btc", "eth"]

    def test_iter_returns_portfolio_entries(self):
        p = Portfolio(make_entries())
        for entry in p:
            assert isinstance(entry, PortfolioEntry)


# -------- __add__ merging --------

class TestAdd:
    def test_disjoint_symbols(self):
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1)])
        p2 = Portfolio([PortfolioEntry(symbol="eth", quantity=5)])
        merged = p1 + p2
        assert len(merged) == 2

    def test_same_symbol_quantity_sums(self):
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1.0, avg_cost=20000)])
        p2 = Portfolio([PortfolioEntry(symbol="btc", quantity=2.0, avg_cost=30000)])
        merged = p1 + p2
        assert len(merged) == 1
        entry = list(merged)[0]
        assert entry.quantity == 3.0

    def test_same_symbol_avg_cost_weighted_average(self):
        # (1 * 20000 + 2 * 30000) / 3 = 26666.67
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1.0, avg_cost=20000)])
        p2 = Portfolio([PortfolioEntry(symbol="btc", quantity=2.0, avg_cost=30000)])
        merged = p1 + p2
        entry = list(merged)[0]
        assert entry.avg_cost == pytest.approx(26666.666666, rel=1e-4)

    def test_one_side_has_no_avg_cost(self):
        # When only one side provides avg_cost, use that one
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1, avg_cost=20000)])
        p2 = Portfolio([PortfolioEntry(symbol="btc", quantity=1)])
        merged = p1 + p2
        entry = list(merged)[0]
        assert entry.avg_cost == 20000

    def test_neither_has_avg_cost(self):
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1)])
        p2 = Portfolio([PortfolioEntry(symbol="btc", quantity=1)])
        merged = p1 + p2
        entry = list(merged)[0]
        assert entry.avg_cost is None

    def test_does_not_mutate_originals(self):
        p1 = Portfolio([PortfolioEntry(symbol="btc", quantity=1)])
        p2 = Portfolio([PortfolioEntry(symbol="btc", quantity=2)])
        _ = p1 + p2
        # Originals should be untouched
        assert list(p1)[0].quantity == 1
        assert list(p2)[0].quantity == 2


# -------- JSON persistence --------

class TestJSONRoundTrip:
    def test_save_load_round_trip(self, tmp_path):
        path = tmp_path / "portfolio.json"
        original = Portfolio(make_entries())
        original.save_json(path)
        loaded = Portfolio.from_json(path)

        assert len(loaded) == len(original)
        original_dicts = [e.model_dump() for e in original]
        loaded_dicts = [e.model_dump() for e in loaded]
        assert loaded_dicts == original_dicts

    def test_save_creates_valid_json(self, tmp_path):
        path = tmp_path / "portfolio.json"
        Portfolio([PortfolioEntry(symbol="btc", quantity=1)]).save_json(path)
        text = path.read_text()
        assert "btc" in text
        assert "quantity" in text


# -------- storage layer --------

class TestStorage:
    def test_load_missing_file_returns_empty(self, tmp_path):
        # storage.load_portfolio gracefully handles missing files
        missing = tmp_path / "nope.json"
        p = load_portfolio(missing)
        assert len(p) == 0

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "portfolio.json"
        original = Portfolio(make_entries())
        save_portfolio(original, path)
        loaded = load_portfolio(path)
        assert len(loaded) == 2
