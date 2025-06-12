from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService
from stonks_overwatch.services.models import DepositType

import pook

@pook.on
def test_get_cash_deposits():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    pook.get("https://api.bitvavo.com/v2/depositHistory").reply(200).json(
        [
            {
                "timestamp": 1739024620000,
                "symbol": "EUR",
                "amount": "500",
                "fee": "0",
                "status": "completed",
                "address": "BACKACCOUNTNUMBER"
            },
        ]
    )
    pook.get("https://api.bitvavo.com/v2/withdrawalHistory").reply(200).json(
        [
            {
                "timestamp": 1738476376,
                "symbol": "EUR",
                "amount": "100",
                "fee": "0",
                "status": "completed",
                "address": "BACKACCOUNTNUMBER"
            },
        ]
    )

    deposits = DepositsService().get_cash_deposits()

    assert len(deposits) == 2
    assert deposits[0].type == DepositType.DEPOSIT
    assert deposits[0].change == 500.0
    assert deposits[1].type == DepositType.WITHDRAWAL
    assert deposits[1].change == -100.0
