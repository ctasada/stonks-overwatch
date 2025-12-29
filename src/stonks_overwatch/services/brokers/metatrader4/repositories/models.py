from django.db import models
from django.utils import timezone


class Metatrader4Trade(models.Model):
    """
    Stores all MT4 trades, transactions, and orders (pending, open, and closed).

    This unified model handles:
    - Pending orders (working orders that haven't been executed)
    - Open trades (active positions)
    - Closed trades (completed positions)
    - Balance/deposit entries
    """

    # Order/Trade status choices
    STATUS_PENDING = "pending"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Order"),
        (STATUS_OPEN, "Open Trade"),
        (STATUS_CLOSED, "Closed Trade"),
    ]

    class Meta:
        db_table = '"metatrader4_trade"'
        indexes = [
            models.Index(fields=["ticket"]),
            models.Index(fields=["open_time"]),
            models.Index(fields=["close_time"]),
            models.Index(fields=["item"]),
            models.Index(fields=["trade_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            # Composite indexes for common query patterns
            models.Index(fields=["status", "item", "open_time"], name="mt4_status_item_time_idx"),
            models.Index(fields=["status", "profit"], name="mt4_status_profit_idx"),
            models.Index(fields=["trade_type", "open_time"], name="mt4_type_time_idx"),
        ]
        constraints = [
            # Ensure ticket uniqueness
            models.UniqueConstraint(fields=["ticket"], name="unique_mt4_ticket"),
            # Ensure closed trades have close_time
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "open"]) | models.Q(close_time__isnull=False),
                name="closed_trades_have_close_time",
            ),
            # Ensure positive size for actual trades (balance entries can have zero size)
            models.CheckConstraint(
                condition=models.Q(trade_type="balance") | models.Q(size__gt=0),
                name="positive_trade_size",
            ),
        ]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now, help_text="When this record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated")

    # Core trade/order data
    ticket = models.CharField(max_length=50, unique=True, help_text="MT4 ticket number")
    open_time = models.DateTimeField(null=True, blank=True, help_text="When position was opened or order placed")
    close_time = models.DateTimeField(null=True, blank=True, help_text="When position was closed")
    trade_type = models.CharField(max_length=20, help_text="Type: buy, sell, balance, buy limit, sell stop, etc.")
    size = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Position size/lots")
    item = models.CharField(max_length=50, null=True, blank=True, help_text="Symbol/instrument")

    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Order/trade status: pending, open, or closed",
    )

    # Pricing data
    open_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Entry price")
    close_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Exit price")
    market_price = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True, help_text="Current market price"
    )
    # For pending orders, open_price represents the order price

    # Stop Loss / Take Profit
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Stop loss level")
    take_profit = models.DecimalField(
        max_digits=20, decimal_places=8, null=True, blank=True, help_text="Take profit level"
    )

    # Financial data (only applicable to executed trades, not pending orders)
    commission = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, help_text="Commission charged")
    taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, help_text="Taxes charged")
    swap = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, help_text="Swap/rollover charges")
    profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, help_text="Profit/loss")

    # Special fields
    description = models.TextField(null=True, blank=True, help_text="Description for balance/deposit entries")
    comment = models.TextField(null=True, blank=True, help_text="Order/trade comment")

    # Raw data for debugging
    raw_data = models.JSONField(null=True, blank=True, help_text="Original parsed row data")

    def __str__(self):
        status_display = self.get_status_display()
        if self.trade_type == "balance":
            return f"Balance: {self.profit} ({self.open_time}) [{status_display}]"
        price = self.current_price or "N/A"
        return f"{self.trade_type} {self.item} {self.size} @ {price} (Ticket: {self.ticket}) [{status_display}]"

    @property
    def current_price(self):
        """Get the current relevant price based on status."""
        if self.status == self.STATUS_PENDING:
            return self.open_price  # For pending orders, this is the order price
        elif self.status == self.STATUS_OPEN:
            return self.market_price or self.open_price
        else:  # STATUS_CLOSED
            return self.close_price or self.open_price

    @property
    def is_pending(self):
        """Check if this is a pending order."""
        return self.status == self.STATUS_PENDING

    @property
    def is_open(self):
        """Check if this is an open trade."""
        return self.status == self.STATUS_OPEN

    @property
    def is_closed(self):
        """Check if this is a closed trade."""
        return self.status == self.STATUS_CLOSED


class Metatrader4Summary(models.Model):
    """
    Stores summary/account information from MT4 reports.

    This includes account balance, equity, margin, and other summary statistics.
    Only the latest summary is kept (records are replaced on each update).
    """

    class Meta:
        db_table = '"metatrader4_summary"'
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now, help_text="When this record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated")

    # Account identification (kept at beginning as requested)
    account = models.CharField(max_length=100, null=True, blank=True, help_text="Account number/identifier")
    currency = models.CharField(max_length=10, null=True, blank=True, help_text="Account currency")

    # MT4 summary fields in typical HTML report order
    deposit_withdrawal = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Total deposits minus withdrawals"
    )
    credit_facility = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Available credit facility"
    )
    closed_trade_pl = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Profit/Loss from closed trades"
    )
    floating_pl = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Unrealized profit/loss from open positions"
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Account balance")
    equity = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Account equity")
    margin = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Used margin")
    free_margin = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Free margin")

    # Raw summary data for any additional fields
    raw_summary = models.JSONField(null=True, blank=True, help_text="Complete summary data from report")
