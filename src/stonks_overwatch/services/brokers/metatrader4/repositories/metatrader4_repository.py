from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from stonks_overwatch.services.brokers.metatrader4.repositories.models import Metatrader4Summary, Metatrader4Trade
from stonks_overwatch.services.brokers.metatrader4.utilities.parser import ParseResult
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class Metatrader4Repository:
    """
    Repository for storing and retrieving Metatrader4 data from the database.

    This class handles the conversion between parsed MT4 data and Django models,
    providing a clean interface for data persistence.
    """

    def __init__(self):
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|REPOSITORY]")

    def store_parsed_report(self, parse_result: ParseResult, file_path: str) -> bool:
        """
        Store a complete parsed MT4 report in the database using optimized upsert strategy.

        Args:
            parse_result: The parsed MT4 report data
            file_path: FTP path of the source file

        Returns:
            bool: True if successful
        """
        self.logger.info(
            f"Storing MT4 report from {file_path} with {len(parse_result.closed_transactions)} closed transactions, "
            f"{len(parse_result.open_trades)} open trades, {len(parse_result.working_orders)} working orders"
        )

        try:
            with transaction.atomic():
                # Store closed transactions as closed trades
                self._store_trades(parse_result.closed_transactions, Metatrader4Trade.STATUS_CLOSED)

                # Store open trades
                self._store_trades(parse_result.open_trades, Metatrader4Trade.STATUS_OPEN)

                # Store working orders as pending trades
                self._store_trades(parse_result.working_orders, Metatrader4Trade.STATUS_PENDING)

                # Store/update summary data
                self._store_summary(parse_result.summary)

                self.logger.info("Successfully stored MT4 report data using optimized upsert strategy")
                return True
        except Exception as e:
            self.logger.error(f"Failed to store MT4 report data: {e}", exc_info=True)
            return False

    def get_latest_trades(self, limit: Optional[int] = None) -> List[Metatrader4Trade]:
        """
        Get the most recent trades/orders with optimized query.

        Args:
            limit: Maximum number of records to return

        Returns:
            List[Metatrader4Trade]: List of recent trades/orders
        """
        queryset = Metatrader4Trade.objects.select_related().order_by("-created_at")
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    def get_open_trades(self) -> List[Metatrader4Trade]:
        """
        Get all currently open trades.

        Returns:
            List[Metatrader4Trade]: List of open trades
        """
        return list(
            Metatrader4Trade.objects.filter(status=Metatrader4Trade.STATUS_OPEN)
            .exclude(trade_type="balance")
            .order_by("-open_time")
        )

    def get_closed_trades(self, limit: Optional[int] = None) -> List[Metatrader4Trade]:
        """
        Get closed trades.

        Args:
            limit: Maximum number of trades to return

        Returns:
            List[Metatrader4Trade]: List of closed trades
        """
        queryset = (
            Metatrader4Trade.objects.filter(status=Metatrader4Trade.STATUS_CLOSED)
            .exclude(trade_type="balance")
            .order_by("-close_time")
        )
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    def get_pending_orders(self) -> List[Metatrader4Trade]:
        """
        Get all pending orders.

        Returns:
            List[Metatrader4Trade]: List of pending orders
        """
        return list(
            Metatrader4Trade.objects.filter(status=Metatrader4Trade.STATUS_PENDING)
            .exclude(trade_type="balance")
            .order_by("-open_time")
        )

    def get_latest_summary(self) -> Optional[Metatrader4Summary]:
        """
        Get the most recent summary.

        Returns:
            Metatrader4Summary or None: The latest summary if any exist
        """
        return Metatrader4Summary.objects.order_by("-updated_at").first()

    def get_balance_entries(self, limit: Optional[int] = None) -> List[Metatrader4Trade]:
        """
        Get balance entries (deposits/withdrawals).

        Args:
            limit: Maximum number of entries to return

        Returns:
            List[Metatrader4Trade]: List of balance entries
        """
        queryset = Metatrader4Trade.objects.filter(trade_type="balance").order_by("-open_time")
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    def get_account_currency(self) -> str:
        """
        Get the account currency from the latest summary.

        Returns:
            str: Account currency code (e.g., 'USD', 'EUR'), defaults to 'USD' if not found
        """
        try:
            summary = self.get_latest_summary()
            if summary and summary.currency:
                self.logger.debug(f"Retrieved currency from summary: {summary.currency}")
                return summary.currency
            else:
                self.logger.warning("No currency found in summary table, using USD as fallback")
                return "USD"
        except Exception as e:
            self.logger.warning(f"Failed to retrieve currency from summary: {e}, using USD as fallback")
            return "USD"

    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse MT4 datetime string to datetime object."""
        if not time_str or time_str.strip() == "":
            return None
        try:
            # Convert MT4 format (YYYY.MM.DD HH:MM:SS) to standard format
            normalized_str = time_str.replace(".", "-")
            dt = LocalizationUtility.convert_string_to_datetime(normalized_str)
            # Make timezone-aware if it's naive
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            return dt
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse datetime '{time_str}': {e}")
            return None

    def _parse_decimal(self, value_str: str) -> Optional[float]:
        """Parse a string value to decimal, handling empty/invalid values."""
        if not value_str or value_str.strip() == "":
            return None
        try:
            return float(value_str.replace(" ", ""))
        except (ValueError, TypeError):
            return None

    def _store_trades(self, trades_data: List[Dict], status: str, batch_size: int = 100) -> None:  # noqa: C901
        """
        Optimized trade storage using upsert strategy with batch processing.
        Only updates records when there are actual differences.

        Args:
            trades_data: List of trade data dictionaries
            status: Trade status (pending, open, closed)
            batch_size: Number of records to process in each batch
        """
        if not trades_data:
            self.logger.debug(f"No {status} trades to process")
            return

        total_processed = 0
        total_updated = 0
        total_created = 0

        # Process in batches to avoid memory issues and improve performance
        for i in range(0, len(trades_data), batch_size):
            batch = trades_data[i : i + batch_size]

            with transaction.atomic():
                # Get existing tickets in this batch
                tickets_in_batch = [t.get("Ticket", "") for t in batch if t.get("Ticket")]
                existing_trades = {
                    trade.ticket: trade for trade in Metatrader4Trade.objects.filter(ticket__in=tickets_in_batch)
                }

                updates = []
                creates = []

                for trade_data in batch:
                    ticket = trade_data.get("Ticket", "")
                    if not ticket:
                        self.logger.warning(f"Skipping trade with missing ticket: {trade_data}")
                        continue

                    try:
                        parsed_data = self._parse_trade_data(trade_data, status)

                        if ticket in existing_trades:
                            existing_trade = existing_trades[ticket]
                            if self._needs_update(existing_trade, parsed_data):
                                # Update existing record
                                for field, value in parsed_data.items():
                                    setattr(existing_trade, field, value)
                                updates.append(existing_trade)
                                total_updated += 1
                        else:
                            # Create new record
                            creates.append(Metatrader4Trade(ticket=ticket, **parsed_data))
                            total_created += 1

                        total_processed += 1

                    except Exception as e:
                        self.logger.warning(f"Failed to process trade {ticket}: {e}")
                        continue

                # Perform bulk operations
                if updates:
                    update_fields = list(parsed_data.keys()) + ["updated_at"]
                    Metatrader4Trade.objects.bulk_update(updates, fields=update_fields, batch_size=batch_size)

                if creates:
                    Metatrader4Trade.objects.bulk_create(creates, batch_size=batch_size)

        self.logger.info(
            f"Processed {total_processed} {status} trades: {total_created} created, {total_updated} updated"
        )

    def _parse_trade_data(self, trade_data: Dict, status: str) -> Dict:
        """
        Parse trade data dictionary into model field values.

        Args:
            trade_data: Raw trade data from parser
            status: Trade status (pending, open, closed)

        Returns:
            Dict: Parsed field values for model creation/update
        """
        parsed = {
            "status": status,
            "open_time": self._parse_datetime(trade_data.get("Open Time", "")),
            "trade_type": trade_data.get("Type", ""),
            "size": self._parse_decimal(trade_data.get("Size", "")),
            "item": trade_data.get("Item", ""),
            "commission": self._parse_decimal(trade_data.get("Commission", "0")) or 0.0,
            "taxes": self._parse_decimal(trade_data.get("Taxes", "0")) or 0.0,
            "swap": self._parse_decimal(trade_data.get("Swap", "0")) or 0.0,
            "profit": self._parse_decimal(trade_data.get("Profit", "0")) or 0.0,
            "stop_loss": self._parse_decimal(trade_data.get("S / L", "")),
            "take_profit": self._parse_decimal(trade_data.get("T / P", "")),
            "raw_data": trade_data,
        }

        # Status-specific fields
        if status == Metatrader4Trade.STATUS_CLOSED:
            close_time = self._parse_datetime(trade_data.get("Close Time", ""))

            # Special handling for balance entries - they might use open_time instead
            if close_time is None and parsed.get("trade_type") == "balance":
                close_time = parsed.get("open_time")

            # Validate: closed trades MUST have a close_time (database constraint)
            if close_time is None:
                raise ValueError(
                    f"Closed trade must have a valid close_time. "
                    f"Ticket: {trade_data.get('Ticket', 'unknown')}, "
                    f"Type: {parsed.get('trade_type', 'unknown')}, "
                    f"Close Time raw: '{trade_data.get('Close Time', '')}', "
                    f"Open Time raw: '{trade_data.get('Open Time', '')}'"
                )

            parsed.update(
                {
                    "close_time": close_time,
                    "open_price": self._parse_decimal(trade_data.get("Open Price", "")),
                    "close_price": self._parse_decimal(trade_data.get("Close Price", "")),
                    "market_price": None,  # Not applicable for closed trades
                    "description": trade_data.get("Description", ""),
                    "comment": "",
                }
            )
        elif status == Metatrader4Trade.STATUS_OPEN:
            parsed.update(
                {
                    "close_time": None,  # Open trades don't have close time
                    "open_price": self._parse_decimal(trade_data.get("Price", "")),
                    "close_price": None,  # Not applicable for open trades
                    "market_price": self._parse_decimal(trade_data.get("Market Price", "")),
                    "description": "",  # Open trades don't have descriptions
                    "comment": "",
                }
            )
        elif status == Metatrader4Trade.STATUS_PENDING:
            parsed.update(
                {
                    "close_time": None,  # Pending orders don't have close time
                    "open_price": self._parse_decimal(trade_data.get("Price", "")),  # Order price
                    "close_price": None,
                    "market_price": self._parse_decimal(trade_data.get("Market Price", "")),
                    "description": "",
                    "comment": trade_data.get("Comment", ""),
                    # Reset financial data for pending orders
                    "commission": 0.0,
                    "taxes": 0.0,
                    "swap": 0.0,
                    "profit": 0.0,
                }
            )

        return parsed

    def _needs_update(self, existing: Metatrader4Trade, new_data: Dict) -> bool:
        """
        Compare existing record with new data to determine if update is needed.
        Only compares fields that can actually change to avoid unnecessary updates.

        Args:
            existing: Existing Metatrader4Trade instance
            new_data: New parsed data dictionary

        Returns:
            bool: True if update is needed, False otherwise
        """
        # Fields that can change and should trigger updates
        comparable_fields = [
            "status",
            "close_time",
            "close_price",
            "market_price",
            "stop_loss",
            "take_profit",
            "commission",
            "taxes",
            "swap",
            "profit",
            "comment",
            "description",
        ]

        for field in comparable_fields:
            if field not in new_data:
                continue

            existing_value = getattr(existing, field)
            new_value = new_data[field]

            # Handle None comparisons
            if existing_value is None and new_value is None:
                continue
            if existing_value is None or new_value is None:
                return True

            # Handle decimal comparison with tolerance for floating point precision
            if isinstance(existing_value, Decimal) and isinstance(new_value, (float, Decimal, int)):
                new_decimal = Decimal(str(new_value))
                if abs(existing_value - new_decimal) > Decimal("0.00001"):
                    return True
            elif isinstance(existing_value, datetime) and isinstance(new_value, datetime):
                # Compare datetime objects (both should be timezone-aware)
                if existing_value != new_value:
                    return True
            elif existing_value != new_value:
                return True

        return False

    def _store_summary(self, summary_data: Dict):  # noqa: C901
        """
        Store/update summary data using upsert strategy.

        Args:
            summary_data: Dictionary containing summary information
        """
        if not summary_data:
            self.logger.debug("No summary data to store")
            return

        try:
            # Parse summary data
            parsed_summary = {
                "account": summary_data.get("Account"),
                "currency": summary_data.get("Currency"),
                "balance": self._parse_decimal(summary_data.get("Balance", "")),
                "equity": self._parse_decimal(summary_data.get("Equity", "")),
                "margin": self._parse_decimal(summary_data.get("Margin", "")),
                "free_margin": self._parse_decimal(summary_data.get("Free Margin", "")),
                "deposit_withdrawal": self._parse_decimal(summary_data.get("Deposit/Withdrawal", "")),
                "credit_facility": self._parse_decimal(summary_data.get("Credit Facility", "")),
                "closed_trade_pl": self._parse_decimal(summary_data.get("Closed Trade P/L", "")),
                "floating_pl": self._parse_decimal(summary_data.get("Floating P/L", "")),
                "raw_summary": summary_data,
            }

            # Get existing summary (there should only be one)
            existing_summary = Metatrader4Summary.objects.first()

            if existing_summary:
                # Check if update is needed
                needs_update = False
                for field, value in parsed_summary.items():
                    if field == "raw_summary":
                        continue  # Skip raw data comparison

                    existing_value = getattr(existing_summary, field)

                    # Handle None comparisons
                    if existing_value is None and value is None:
                        continue
                    if existing_value is None or value is None:
                        needs_update = True
                        break

                    # Handle decimal comparison with tolerance
                    if (
                        isinstance(existing_value, Decimal)
                        and isinstance(value, (float, Decimal, int))
                        and value is not None
                    ):
                        new_decimal = Decimal(str(value))
                        if abs(existing_value - new_decimal) > Decimal("0.01"):  # 1 cent tolerance
                            needs_update = True
                            break
                    elif existing_value != value:
                        needs_update = True
                        break

                if needs_update:
                    # Update existing summary
                    for field, value in parsed_summary.items():
                        setattr(existing_summary, field, value)
                    existing_summary.save()
                    self.logger.debug("Updated existing summary data")
                else:
                    self.logger.debug("Summary data unchanged, skipping update")
            else:
                # Create new summary
                Metatrader4Summary.objects.create(**parsed_summary)
                self.logger.debug("Created new summary data")

        except Exception as e:
            self.logger.warning(f"Failed to store summary data {summary_data}: {e}")

    def cleanup_orphaned_trades(self) -> int:
        """
        Clean up any orphaned or duplicate trades that might exist.
        This is a maintenance method that can be called periodically.

        Returns:
            int: Number of records cleaned up
        """
        try:
            # Find duplicate tickets (shouldn't happen with unique constraint, but just in case)
            from django.db.models import Count

            duplicates = Metatrader4Trade.objects.values("ticket").annotate(count=Count("ticket")).filter(count__gt=1)

            cleaned_count = 0
            for duplicate in duplicates:
                ticket = duplicate["ticket"]
                # Keep the most recent record, delete others
                trades = Metatrader4Trade.objects.filter(ticket=ticket).order_by("-updated_at")
                if trades.count() > 1:
                    trades_to_delete = trades[1:]  # Keep first (most recent), delete rest
                    delete_count = len(trades_to_delete)
                    for trade in trades_to_delete:
                        trade.delete()
                    cleaned_count += delete_count
                    self.logger.info(f"Cleaned up {delete_count} duplicate records for ticket {ticket}")

            if cleaned_count > 0:
                self.logger.info(f"Cleanup completed: removed {cleaned_count} orphaned/duplicate records")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup orphaned trades: {e}")
            return 0

    def get_trade_by_ticket(self, ticket: str) -> Optional[Metatrader4Trade]:
        """
        Get a specific trade by its ticket number.

        Args:
            ticket: MT4 ticket number

        Returns:
            Metatrader4Trade or None: The trade if found
        """
        try:
            return Metatrader4Trade.objects.get(ticket=ticket)
        except Metatrader4Trade.DoesNotExist:
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving trade by ticket {ticket}: {e}")
            return None

    def get_trades_by_symbol(self, symbol: str, limit: Optional[int] = None) -> List[Metatrader4Trade]:
        """
        Get trades for a specific symbol/instrument.

        Args:
            symbol: Symbol/instrument name (e.g., 'EURUSD', 'GOLD')
            limit: Maximum number of records to return

        Returns:
            List[Metatrader4Trade]: List of trades for the symbol
        """
        queryset = Metatrader4Trade.objects.filter(item=symbol).order_by("-open_time")
        if limit:
            queryset = queryset[:limit]
        return list(queryset)

    def get_trades_by_date_range(
        self, start_date: datetime, end_date: datetime, status: Optional[str] = None
    ) -> List[Metatrader4Trade]:
        """
        Get trades within a specific date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            status: Optional status filter (pending, open, closed)

        Returns:
            List[Metatrader4Trade]: List of trades in date range
        """
        queryset = Metatrader4Trade.objects.filter(open_time__gte=start_date, open_time__lte=end_date)

        if status:
            queryset = queryset.filter(status=status)

        return list(queryset.order_by("-open_time"))

    def get_profit_summary(self) -> Dict[str, float]:
        """
        Get profit summary statistics.

        Returns:
            Dict: Summary statistics including total profit, open P&L, etc.
        """
        from django.db.models import Count, Sum

        try:
            # Get closed trades profit
            closed_stats = Metatrader4Trade.objects.filter(status=Metatrader4Trade.STATUS_CLOSED).aggregate(
                total_profit=Sum("profit"),
                total_commission=Sum("commission"),
                total_swap=Sum("swap"),
                trade_count=Count("id"),
            )

            # Get open trades profit
            open_stats = Metatrader4Trade.objects.filter(status=Metatrader4Trade.STATUS_OPEN).aggregate(
                floating_profit=Sum("profit"), open_count=Count("id")
            )

            return {
                "total_closed_profit": float(closed_stats["total_profit"] or 0),
                "total_commission": float(closed_stats["total_commission"] or 0),
                "total_swap": float(closed_stats["total_swap"] or 0),
                "closed_trades_count": closed_stats["trade_count"] or 0,
                "floating_profit": float(open_stats["floating_profit"] or 0),
                "open_trades_count": open_stats["open_count"] or 0,
            }
        except Exception as e:
            self.logger.error(f"Failed to calculate profit summary: {e}")
            return {
                "total_closed_profit": 0.0,
                "total_commission": 0.0,
                "total_swap": 0.0,
                "closed_trades_count": 0,
                "floating_profit": 0.0,
                "open_trades_count": 0,
            }
