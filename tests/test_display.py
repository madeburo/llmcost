from llm_cost.display import format_price_per_million


def test_format_price_per_million_uses_standard_currency_precision():
    assert format_price_per_million(0.20) == "$0.20"
    assert format_price_per_million(5.0) == "$5.00"
