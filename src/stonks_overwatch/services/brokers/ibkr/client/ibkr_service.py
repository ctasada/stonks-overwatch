from dataclasses import dataclass
from datetime import datetime

from dateutil.parser import parse
from dateutil.tz import gettz
from django.utils.timezone import is_naive, make_aware
from ibind import IbkrClient
from ibind.oauth.oauth1a import OAuth1aConfig
from pytz import utc

from stonks_overwatch.config.config import Config
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


@singleton
class IbkrService:
    @dataclass
    class IbkrAccount:
        account_id: str
        currency: str

    logger = StonksLogger.get_logger("stocks_portfolio.ibkr_service", "[IBKR|CLIENT]")
    client: IbkrClient = None
    account: IbkrAccount = None
    tzinfos = {
        "EST": gettz("America/New_York"),
        "EDT": gettz("America/New_York"),
        # add more if needed
    }

    def __init__(
        self,
        shutdown_oauth: bool = False,
    ):
        # FIXME: The shutdown_oauth parameter is a workaround to avoid OAuth shutdown due to issues
        #  in the way SIGTERM is managed.
        #  The default value should be obtained checking if the service runs inside Django or not.
        ibkr_config = Config.get_global().registry.get_broker_config("ibkr")
        ibkr_credentials = ibkr_config.credentials

        if ibkr_credentials:
            self.client = IbkrClient(
                use_oauth=True,
                oauth_config=OAuth1aConfig(
                    access_token=ibkr_credentials.access_token,
                    access_token_secret=ibkr_credentials.access_token_secret,
                    consumer_key=ibkr_credentials.consumer_key,
                    dh_prime=ibkr_credentials.dh_prime,
                    encryption_key_fp=ibkr_credentials.encryption_key_fp,
                    signature_key_fp=ibkr_credentials.signature_key_fp,
                    # Disable OAuth shutdown due to issues in the way SIGTERM is managed.
                    # The StonksOverwatchConfig is registering the SIGTERM signal and shutting down the OAuth
                    shutdown_oauth=shutdown_oauth,
                ),
            )
            self.__update_account()

    def __update_account(self):
        portfolio_accounts = self.get_portfolio_accounts()
        self.account = self.IbkrAccount(
            account_id=portfolio_accounts[0]["id"], currency=portfolio_accounts[0]["currency"]
        )

    def get_client(self) -> IbkrClient:
        return self.client

    def get_portfolio_accounts(self) -> dict:
        self.logger.debug("Accounts")
        return self.client.portfolio_accounts().data

    def get_account_summary(self) -> dict:
        self.logger.debug("Account Summary")
        return self.client.account_summary(self.account.account_id).data

    def get_open_positions(self) -> list[dict]:
        self.logger.debug("Open Positions")
        return self.client.positions(self.account.account_id).data

    def transaction_history(self, conid: str, currency: str) -> dict:
        self.logger.debug("Transaction History")
        return self.client.transaction_history(
            account_ids=self.account.account_id, conids=conid, currency=currency
        ).data

    def get_default_currency(self) -> str:
        return self.account.currency

    def get_currency_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        self.logger.debug(f"Exchange Rate from '{from_currency}' to '{to_currency}'")
        return self.client.currency_exchange_rate(from_currency, to_currency).data["rate"]

    def convert_to_default_currency(self, from_currency: str, amount: float) -> float:
        if from_currency == self.account.currency:
            return amount

        exchange_rate = self.get_currency_exchange_rate(from_currency, self.get_default_currency())
        return amount * exchange_rate

    @staticmethod
    def convert_date(date: str) -> datetime:
        dt = None
        for tz_abbr, tz in IbkrService.tzinfos.items():
            if tz_abbr in date:
                dt = parse(date, tzinfos={tz_abbr: tz})
        if dt is None:
            dt = parse(date)

        if is_naive(dt):
            dt = make_aware(dt)
        return dt.astimezone(utc)
