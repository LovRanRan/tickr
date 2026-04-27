"""Tests for tickr.models — Quote and PortfolioEntry."""

import pytest
from pydantic import ValidationError

from tickr.exceptions import RateLimitError, TickrError
from tickr.models import PortfolioEntry, Quote


# -------- Quote --------

class TestQuote:
    def test_basic_construction(self):
        q = Quote(symbol="btc", price=50000)
        assert q.symbol == "btc"
        assert q.price == 50000.0
        assert q.currency == "usd"        # default
        assert q.change_pct is None       # default
        assert q.fetched_at is not None   # default_factory ran

    def test_symbol_normalized_to_lowercase(self):
        q = Quote(symbol="BTC", price=50000)
        assert q.symbol == "btc"

    def test_price_must_be_positive(self):
        with pytest.raises(ValidationError):
            Quote(symbol="btc", price=-100)

    def test_price_zero_rejected(self):
        # gt=0 means strictly greater than zero
        with pytest.raises(ValidationError):
            Quote(symbol="btc", price=0)

    def test_change_pct_optional(self):
        q = Quote(symbol="btc", price=50000)
        assert q.change_pct is None

        q2 = Quote(symbol="btc", price=50000, change_pct=2.5)
        assert q2.change_pct == 2.5

    # -------- from_api_response (CoinGecko shape) --------

    def test_from_api_response_full(self):
        data = {"usd": 67234.5, "usd_24h_change": 2.34}
        q = Quote.from_api_response("BTC", data)
        assert q.symbol == "btc"
        assert q.price == 67234.5
        assert q.change_pct == 2.34
        assert q.currency == "usd"

    def test_from_api_response_missing_change_pct(self):
        # API returns only the price, no 24h change field
        data = {"usd": 67234.5}
        q = Quote.from_api_response("btc", data)
        assert q.change_pct is None

    def test_from_api_response_custom_currency(self):
        data = {"eur": 60000, "eur_24h_change": 1.0}
        q = Quote.from_api_response("btc", data, currency="eur")
        assert q.price == 60000
        assert q.currency == "eur"

    # -------- __lt__ sorting --------

    def test_lt_sorts_by_change_pct_ascending(self):
        a = Quote(symbol="a", price=1, change_pct=5.0)
        b = Quote(symbol="b", price=1, change_pct=-2.0)
        c = Quote(symbol="c", price=1, change_pct=10.0)

        sorted_quotes = sorted([a, b, c])
        assert [q.symbol for q in sorted_quotes] == ["b", "a", "c"]

    def test_lt_none_treated_as_smallest(self):
        with_change = Quote(symbol="a", price=1, change_pct=-100.0)
        no_change = Quote(symbol="b", price=1, change_pct=None)

        # None should sort BEFORE even -100 (treated as -inf)
        sorted_quotes = sorted([with_change, no_change])
        assert [q.symbol for q in sorted_quotes] == ["b", "a"]


# -------- PortfolioEntry --------

class TestPortfolioEntry:
    def test_basic_construction(self):
        e = PortfolioEntry(symbol="btc", quantity=1.5, avg_cost=25000)
        assert e.symbol == "btc"
        assert e.quantity == 1.5
        assert e.avg_cost == 25000.0

    def test_symbol_normalized_to_lowercase(self):
        e = PortfolioEntry(symbol="BTC", quantity=1)
        assert e.symbol == "btc"

    def test_quantity_must_be_positive(self):
        with pytest.raises(ValidationError):
            PortfolioEntry(symbol="btc", quantity=-1)

    def test_quantity_zero_rejected(self):
        with pytest.raises(ValidationError):
            PortfolioEntry(symbol="btc", quantity=0)

    def test_avg_cost_optional(self):
        e = PortfolioEntry(symbol="btc", quantity=1)
        assert e.avg_cost is None

    def test_avg_cost_must_be_positive_if_provided(self):
        with pytest.raises(ValidationError):
            PortfolioEntry(symbol="btc", quantity=1, avg_cost=-100)


# -------- exception tree --------

class TestExceptionTree:
    def test_rate_limit_is_tickr_error(self):
        # The whole point of the exception hierarchy: callers can catch the base class.
        with pytest.raises(TickrError):
            raise RateLimitError("limited")
