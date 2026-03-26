from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService

from unittest.mock import Mock, patch


class TestGetCorrelatedProducts:
    """Tests for PortfolioService._get_correlated_products.

    The key invariant: calling get_products_info_raw_by_symbol([""]) would return ALL
    products stored with an empty symbol (i.e. every WARRANT/LEVERAGED product), treating
    them all as correlated to one another and corrupting realized P&L calculations.
    """

    def test_empty_symbol_returns_empty_list(self):
        """_get_correlated_products('') must return [] immediately.
        WARRANT/LEVERAGED products have no meaningful correlated products."""
        service = PortfolioService.__new__(PortfolioService)
        service.product_info = Mock()

        result = service._get_correlated_products("")

        assert result == []

    def test_empty_symbol_does_not_query_the_database(self):
        """No DB query must be made for an empty symbol — querying '' would return
        all other empty-symbol products, not just the one we care about."""
        service = PortfolioService.__new__(PortfolioService)
        service.product_info = Mock()

        service._get_correlated_products("")

        service.product_info.get_products_info_raw_by_symbol.assert_not_called()

    def test_normal_symbol_queries_db_and_returns_ids(self):
        """A regular symbol should still query the DB and return matching product IDs."""
        service = PortfolioService.__new__(PortfolioService)
        service.product_info = Mock()
        service.product_info.get_products_info_raw_by_symbol.return_value = {
            332111: {"id": 332111, "name": "Microsoft Corp"},
            999: {"id": 999, "name": "Microsoft Corp Non tradeable"},
        }

        result = service._get_correlated_products("MSFT")

        service.product_info.get_products_info_raw_by_symbol.assert_called_once_with(["MSFT"])
        # Non-tradeable variants must be excluded
        assert 332111 in result
        assert 999 not in result


class TestCreateStockPortfolioEntries:
    """Tests for PortfolioService._create_stock_portfolio_entries.

    Focuses on WARRANT/LEVERAGED products whose DeGiro API response omits the 'symbol' key.
    Previously this caused KeyError: 'symbol' at product_info["symbol"].
    """

    # Minimal product data as returned by the live DeGiro API for a WARRANT —
    # note the intentional absence of the 'symbol' key.
    WARRANT_PRODUCT_INFO = {
        "id": "18960776",
        "name": "MiniS O.End DAX 17230",
        "isin": "DE000VP4KR02",
        "productType": "WARRANT",
        "currency": "EUR",
        "active": False,
        "tradable": False,
        # 'symbol' key is intentionally absent — reproduces the crash scenario
    }

    def setup_method(self):
        self.service = PortfolioService.__new__(PortfolioService)
        self.service.product_info = Mock()
        self.service.product_info.get_products_info_raw_by_symbol.return_value = {}

    def test_product_missing_symbol_key_does_not_raise(self):
        """A product dict without a 'symbol' key must not raise KeyError.
        Previously product_info["symbol"] crashed; now it uses .get("symbol", "")."""
        portfolio_products = [{"productId": "18960776", "size": 1.0, "value": 10.0, "breakEvenPrice": 5.0}]
        products_info = {"18960776": self.WARRANT_PRODUCT_INFO}

        mock_entry = Mock()
        mock_entry.symbol = ""
        with patch.object(self.service, "_create_portfolio_entry", return_value=mock_entry):
            # Must not raise KeyError: 'symbol'
            result = self.service._create_stock_portfolio_entries(portfolio_products, products_info, {})

        assert len(result) == 1

    def test_product_missing_symbol_passes_empty_correlated_list(self):
        """When symbol is '' the correlated products list passed to _create_portfolio_entry
        must be empty — not a list of all other WARRANT products from the DB."""
        portfolio_products = [{"productId": "18960776", "size": 1.0, "value": 10.0, "breakEvenPrice": 5.0}]
        products_info = {"18960776": self.WARRANT_PRODUCT_INFO}

        mock_entry = Mock()
        mock_entry.symbol = ""
        with patch.object(self.service, "_create_portfolio_entry", return_value=mock_entry) as mock_create:
            self.service._create_stock_portfolio_entries(portfolio_products, products_info, {})

        # correlated_products is the 4th positional argument
        correlated_products = mock_create.call_args[0][3]
        assert correlated_products == []

    def test_product_with_symbol_passes_correlated_list_from_db(self):
        """Normal products must still look up correlated products in the DB."""
        self.service.product_info.get_products_info_raw_by_symbol.return_value = {
            332111: {"id": 332111, "name": "Microsoft Corp"},
        }
        portfolio_products = [{"productId": "332111", "size": 10.0, "value": 1000.0, "breakEvenPrice": 90.0}]
        products_info = {
            "332111": {
                "id": "332111",
                "name": "Microsoft Corp",
                "isin": "US5949181045",
                "symbol": "MSFT",
                "productType": "STOCK",
                "currency": "USD",
            }
        }

        mock_entry = Mock()
        mock_entry.symbol = "MSFT"
        with patch.object(self.service, "_create_portfolio_entry", return_value=mock_entry) as mock_create:
            self.service._create_stock_portfolio_entries(portfolio_products, products_info, {})

        correlated_products = mock_create.call_args[0][3]
        assert 332111 in correlated_products
