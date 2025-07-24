def is_non_tradeable_product(product: dict) -> bool:
    """Check if the product is non-tradeable.

    This method checks if the product is a non-tradeable product.
    Non-tradeable products are identified by the presence of "Non-tradeable" in the name.

    If the product is NOT tradable, we shouldn't consider it for Growth.

    The 'tradable' attribute identifies old Stocks, like the ones that are
    renamed for some reason, and it's not good enough to identify stocks
    that are provided as dividends, for example.
    """
    if product["symbol"].endswith(".D"):
        # This is a DeGiro-specific symbol, which is not tradeable
        return True

    return "Non tradeable" in product["name"]
