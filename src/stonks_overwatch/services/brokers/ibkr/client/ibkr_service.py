import os
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from django.utils.timezone import is_naive, make_aware
from ibind import IbkrClient
from ibind.oauth.oauth1a import OAuth1aConfig

from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


@singleton
class IbkrService:
    @dataclass
    class IbkrAccount:
        account_id: str
        currency: str

    logger = StonksLogger.get_logger("stonks_overwatch.ibkr_service", "[IBKR|CLIENT]")
    client: IbkrClient = None
    account: IbkrAccount = None
    tzinfos = {
        "EST": ZoneInfo("America/New_York"),
        "EDT": ZoneInfo("America/New_York"),
        # add more if needed
    }

    def __init__(
        self,
        shutdown_oauth: bool = False,
        config: Optional[IbkrConfig] = None,
    ):
        # FIXME: The shutdown_oauth parameter is a workaround to avoid OAuth shutdown due to issues
        #  in the way SIGTERM is managed.
        #  The default value should be obtained checking if the service runs inside Django or not.

        # Use dependency injection if config is provided, otherwise fallback to global config
        if config:
            ibkr_config = config
        else:
            # Get IBKR configuration using unified BrokerFactory
            try:
                from stonks_overwatch.config.base_config import resolve_config_from_factory

                # Get and resolve IBKR configuration
                ibkr_config = resolve_config_from_factory(BrokerName.IBKR, IbkrConfig)
            except ImportError as e:
                raise ImportError(f"Failed to import BrokerFactory: {e}") from e

        ibkr_credentials = ibkr_config.get_credentials

        if ibkr_credentials:
            # Handle encryption key: prefer direct value over file path
            encryption_key_value = ibkr_credentials.encryption_key
            encryption_key_path = None
            if not encryption_key_value and ibkr_credentials.encryption_key_fp:
                # Expand paths to handle ~ and relative paths
                encryption_key_path = os.path.abspath(os.path.expanduser(ibkr_credentials.encryption_key_fp))
                # Validate file exists
                if not os.path.exists(encryption_key_path):
                    self.logger.warning(
                        f"Encryption key file not found: {encryption_key_path}. "
                        "Authentication may fail if the path is incorrect."
                    )

            # Handle signature key: prefer direct value over file path
            signature_key_value = ibkr_credentials.signature_key
            signature_key_path = None
            if not signature_key_value and ibkr_credentials.signature_key_fp:
                # Expand paths to handle ~ and relative paths
                signature_key_path = os.path.abspath(os.path.expanduser(ibkr_credentials.signature_key_fp))
                # Validate file exists
                if not os.path.exists(signature_key_path):
                    self.logger.warning(
                        f"Signature key file not found: {signature_key_path}. "
                        "Authentication may fail if the path is incorrect."
                    )

            self.client = IbkrClient(
                use_oauth=True,
                oauth_config=OAuth1aConfig(
                    access_token=ibkr_credentials.access_token,
                    access_token_secret=ibkr_credentials.access_token_secret,
                    consumer_key=ibkr_credentials.consumer_key,
                    dh_prime=ibkr_credentials.dh_prime,
                    encryption_key=encryption_key_value,
                    encryption_key_fp=encryption_key_path,
                    signature_key=signature_key_value,
                    signature_key_fp=signature_key_path,
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
        return dt.astimezone(dt_timezone.utc)
