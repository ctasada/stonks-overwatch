"""Alpaca portfolio service implementation."""

from collections import defaultdict
from typing import Dict, List, Optional

from django.utils import timezone

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces import PortfolioServiceInterface
from stonks_overwatch.services.brokers.alpaca.client.alpaca_client import AlpacaClient
from stonks_overwatch.services.brokers.alpaca.repositories.orders_repository import OrdersRepository
from stonks_overwatch.services.brokers.alpaca.repositories.positions_repository import PositionsRepository
from stonks_overwatch.services.brokers.alpaca.services.alpaca_base_service import AlpacaBaseService
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType


class PortfolioService(AlpacaBaseService, PortfolioServiceInterface):
    """
    Portfolio service for Alpaca Markets.

    Reads positions from the local DB (synced by UpdateService) and
    fetches latest prices from the Market Data API via AlpacaClient.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.portfolio", "[ALPACA|PORTFOLIO]")

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the portfolio service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
        """
        super().__init__(config)
        self.alpaca_client = AlpacaClient()

    @property
    def get_portfolio(self) -> List[PortfolioEntry]:
        """
        Retrieve portfolio entries from the stored positions.

        Returns:
            List of PortfolioEntry objects, one per open position
        """
        self.logger.debug("Getting Alpaca portfolio")
        positions = PositionsRepository.get_all_positions()

        symbols = [p.symbol for p in positions]
        try:
            latest_prices = self.alpaca_client.get_latest_prices(symbols)
        except Exception as e:
            self.logger.warning(f"Could not fetch latest prices, using stored prices: {e}")
            latest_prices = {}

        portfolio: List[PortfolioEntry] = []
        for position in positions:
            qty = float(position.qty)
            if qty == 0:
                continue

            avg_entry = float(position.avg_entry_price or 0)
            current_price = latest_prices.get(position.symbol) or float(position.current_price or 0)
            market_value = qty * current_price if current_price else float(position.market_value or 0)
            unrealized_gain = (
                (current_price - avg_entry) * qty if current_price and avg_entry else float(position.unrealized_pl or 0)
            )

            portfolio.append(
                PortfolioEntry(
                    symbol=position.symbol,
                    name=position.symbol,
                    shares=qty,
                    product_type=ProductType.STOCK,
                    product_currency=position.currency,
                    is_open=True,
                    price=current_price,
                    value=market_value,
                    base_currency_price=self._to_base(current_price),
                    base_currency=self.base_currency,
                    base_currency_value=self._to_base(market_value),
                    break_even_price=avg_entry,
                    base_currency_break_even_price=self._to_base(avg_entry),
                    unrealized_gain=self._to_base(unrealized_gain),
                )
            )

        # Add a cash entry for the USD balance held at Alpaca so it appears
        # as a "Cash" row in the portfolio dashboard (same pattern as DEGIRO).
        try:
            account = self.alpaca_client.get_account()
            cash_usd = float(account.cash or 0)
            if cash_usd:
                portfolio.append(
                    PortfolioEntry(
                        symbol=self.BROKER_CURRENCY,
                        name=f"Cash Balance {self.BROKER_CURRENCY}",
                        product_type=ProductType.CASH,
                        product_currency=self.BROKER_CURRENCY,
                        value=cash_usd,
                        base_currency_value=self._to_base(cash_usd),
                        base_currency=self.base_currency,
                        is_open=True,
                    )
                )
        except Exception as e:
            self.logger.warning(f"Could not fetch account cash balance for portfolio entry: {e}")

        try:
            portfolio.extend(self._compute_closed_positions())
        except Exception as e:
            self.logger.warning(f"Could not compute closed positions: {e}")

        return sorted(portfolio, key=lambda k: k.symbol)

    @staticmethod
    def _fifo_realized_gain(orders: list) -> tuple:
        """
        Compute realized gain and total cost basis for a single symbol via FIFO.

        Args:
            orders: Chronologically sorted AlpacaOrder objects for one symbol.

        Returns:
            (realized_gain_usd, total_costs_usd) as floats.
        """
        buy_queue = [
            {"qty": float(o.filled_qty or 0), "price": float(o.filled_avg_price or 0)}
            for o in orders
            if o.side == "buy" and float(o.filled_avg_price or 0) > 0
        ]
        total_costs_usd = sum(b["qty"] * b["price"] for b in buy_queue)
        realized_gain_usd = 0.0

        for o in orders:
            if o.side != "sell":
                continue
            sell_qty = float(o.filled_qty or 0)
            sell_price = float(o.filled_avg_price or 0)
            for buy in buy_queue:
                if sell_qty <= 0:
                    break
                match_qty = min(sell_qty, buy["qty"])
                realized_gain_usd += match_qty * (sell_price - buy["price"])
                buy["qty"] -= match_qty
                sell_qty -= match_qty
            buy_queue = [b for b in buy_queue if b["qty"] > 1e-9]

        return realized_gain_usd, total_costs_usd

    def _compute_closed_positions(self) -> List[PortfolioEntry]:
        """
        Derive closed positions from filled order history using FIFO cost basis.

        A position is considered closed when the net filled quantity across all
        orders for a symbol is approximately zero and the symbol no longer
        appears in the live positions table (i.e. it has been fully sold).

        Uses FIFO matching to compute the realized gain: each sell lot is
        matched against the oldest unexhausted buy lot.

        Returns:
            List of PortfolioEntry objects with is_open=False, one per closed
            symbol, carrying realized_gain and total_costs in base currency.
        """
        open_symbols = set(PositionsRepository.get_symbols())
        orders = OrdersRepository.get_filled_orders_chronological()

        if not orders:
            return []

        # Group orders by symbol, preserving chronological order within each group
        by_symbol: Dict[str, list] = defaultdict(list)
        for order in orders:
            by_symbol[order.symbol].append(order)

        closed_entries: List[PortfolioEntry] = []

        for symbol, sym_orders in by_symbol.items():
            if symbol in open_symbols:
                # Position is still (at least partially) open — skip
                continue

            # Net quantity: positive means net long, 0 means fully closed
            net_qty = 0.0
            for o in sym_orders:
                qty = float(o.filled_qty or 0)
                net_qty += qty if o.side == "buy" else -qty

            # Only emit a closed entry when the position is fully liquidated
            if abs(net_qty) > 1e-6:
                continue

            realized_gain_usd, total_costs_usd = self._fifo_realized_gain(sym_orders)

            closed_entries.append(
                PortfolioEntry(
                    symbol=symbol,
                    name=symbol,
                    shares=0.0,
                    product_type=ProductType.STOCK,
                    product_currency=self.BROKER_CURRENCY,
                    is_open=False,
                    price=0.0,
                    value=0.0,
                    base_currency_price=0.0,
                    base_currency=self.base_currency,
                    base_currency_value=0.0,
                    break_even_price=0.0,
                    base_currency_break_even_price=0.0,
                    unrealized_gain=0.0,
                    realized_gain=self._to_base(realized_gain_usd),
                    total_costs=self._to_base(total_costs_usd),
                )
            )

        return sorted(closed_entries, key=lambda e: e.symbol)

    def calculate_historical_value(self) -> List[DailyValue]:
        """
        Calculate historical portfolio value.

        Alpaca does not expose a historical portfolio-value endpoint, so this
        returns a single data point for today using the current portfolio total.
        This is enough for the dashboard to render and for the TWR engine to
        have a baseline, matching the same approach used by IBKR.

        Returns:
            List with one DailyValue entry for today's portfolio value
        """
        self.logger.debug("Calculating historical value for Alpaca (today only)")
        try:
            portfolio_total = self.get_portfolio_total()
            today = timezone.now().strftime("%Y-%m-%d")
            return [DailyValue(x=today, y=portfolio_total.current_value)]
        except Exception as e:
            self.logger.error(f"Error calculating historical value for Alpaca: {e}")
            return []

    def calculate_product_growth(self) -> dict:
        """
        Calculate growth history per product.

        Not implemented for Alpaca yet — returns an empty dict.

        Returns:
            Empty dict (product growth data not yet supported)
        """
        self.logger.debug("Product growth calculation not yet implemented for Alpaca")
        return {}

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        """
        Calculate total portfolio value.

        Args:
            portfolio: Optional pre-fetched portfolio entries (fetches if not provided)

        Returns:
            TotalPortfolio with aggregated totals
        """
        self.logger.debug("Getting Alpaca portfolio total")
        if portfolio is None:
            portfolio = self.get_portfolio  # noqa: E501 — property access()

        # Cash entry is included in the portfolio list (ProductType.CASH).
        # Split it out so total_cash and total_pl can be computed separately,
        # but include cash in current_value (consistent with DEGIRO behaviour).
        stock_entries = [e for e in portfolio if e.is_open and e.product_type != ProductType.CASH]
        cash_entries = [e for e in portfolio if e.is_open and e.product_type == ProductType.CASH]

        cash = sum(e.base_currency_value for e in cash_entries)
        current_value = sum(e.base_currency_value for e in stock_entries) + cash

        # Delegate to DepositService so the deposit definition and FX conversion
        # logic stays in one place.  Both services share the same config so
        # base_currency and historical rates are consistent.
        from stonks_overwatch.services.brokers.alpaca.services.deposit_service import DepositService

        deposits = DepositService(config=self.config).get_cash_deposits()
        total_deposit_withdrawal = sum(d.change for d in deposits)

        # Total P/L = current portfolio value minus total deposited.
        # This mirrors DEGIRO's approach and correctly includes realized gains:
        # when a position is sold the cash proceeds flow into account.cash,
        # which is already part of current_value via the CASH entry.
        total_pl = current_value - total_deposit_withdrawal

        if total_deposit_withdrawal > 0:
            total_roi = (current_value / total_deposit_withdrawal - 1) * 100
        else:
            total_roi = 0.0

        return TotalPortfolio(
            base_currency=self.base_currency,
            current_value=current_value,
            total_cash=cash,
            total_pl=total_pl,
            total_roi=total_roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )
