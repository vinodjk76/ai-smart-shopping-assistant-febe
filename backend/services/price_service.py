"""Price-source abstraction.

A PriceProvider returns real prices from an identified source. Only the
StoredPriceProvider (reads prices already in SQLite, including seeded SAMPLE
prices) ships with this project. To add a live retailer API, subclass
PriceProvider, implement `fetch_prices`, and register it in `PROVIDERS`.

Never fabricate prices, discounts, links or availability here.
"""
from abc import ABC, abstractmethod

NO_LIVE_PROVIDER_NOTE = (
    "No live retailer API is configured, so only sample (demo) price comparison "
    "is available. Sample prices are not current market prices."
)


class PriceProvider(ABC):
    name = "base"
    is_live = False

    @abstractmethod
    def fetch_prices(self, product) -> list[dict]:
        """Return a list of dicts: amount, currency, source, source_url,
        is_verified, is_sample, retrieved_at (ISO string)."""


class StoredPriceProvider(PriceProvider):
    """Reads prices already stored in the database."""
    name = "stored"
    is_live = False

    def fetch_prices(self, product):
        return [p.to_dict() for p in product.prices]


PROVIDERS: list[PriceProvider] = [StoredPriceProvider()]


def get_price_comparison(product):
    """Compare prices that came from identified sources.

    Returns a dict with all prices (each labelled), the cheapest one, and a
    note explaining whether any live/verified data is present.
    """
    prices = []
    for provider in PROVIDERS:
        prices.extend(provider.fetch_prices(product))
    # Only prices with an identified source are comparable.
    prices = [p for p in prices if p.get("source")]
    prices.sort(key=lambda p: p["amount"])

    has_verified = any(p["is_verified"] and not p["is_sample"] for p in prices)
    if not prices:
        note = "No price data is available for this product."
    elif has_verified:
        note = "Verified prices are shown with their source and retrieval time."
    else:
        note = NO_LIVE_PROVIDER_NOTE
    cheapest = prices[0] if prices else None
    spread = (prices[-1]["amount"] - prices[0]["amount"]) if len(prices) > 1 else 0
    return {
        "prices": prices,
        "cheapest": cheapest,
        "max_difference": round(spread, 2),
        "has_verified_prices": has_verified,
        "note": note,
    }
