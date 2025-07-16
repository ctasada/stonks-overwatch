from enum import Enum


class TransactionType(Enum):
    SELL = "sell"
    BUY = "buy"
    STAKING = "staking"
    FIXED_STAKING = "fixed_staking"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    AFFILIATE = "affiliate"
    DISTRIBUTION = "distribution"
    INTERNAL_TRANSFER = "internal_transfer"
    WITHDRAWAL_CANCELLED = "withdrawal_cancelled"
    REBATE = "rebate"
    LOAN = "loan"
    EXTERNAL_TRANSFERRED_FUNDS = "external_transferred_funds"
    MANUALLY_ASSIGNED_BITVAVO = "manually_assigned_bitvavo"
