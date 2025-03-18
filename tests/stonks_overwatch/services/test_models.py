from stonks_overwatch.services.models import PortfolioId

def test_generate_list_of_portfolio_ids():
    assert PortfolioId.values() == [PortfolioId.ALL, PortfolioId.DEGIRO, PortfolioId.BITVAVO]
