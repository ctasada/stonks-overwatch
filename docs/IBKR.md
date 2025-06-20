# IBKR (Interactive Brokers)

### How to login to IBR (Interactive Brokers)
Follow instructions at https://github.com/Voyz/ibind/wiki/OAuth-1.0a

Copy the generated files to a folder, for example `config/ibkr_certs`. Now you can update your `config.json` file with
the new values:

```json
{
    "ibkr": {
        "enabled": "BOOLEAN (true by default)",
        "credentials": {
            "access_token": "IBKR ACCESS TOKEN",
            "access_token_secret": "IBKR ACCESS TOKEN SECRET",
            "consumer_key": "IBKR CONSUMER KEY",
            "dh_prime": "IBKR DH PRIME",
            "encryption_key_fp": "PATH to IBKR private_encryption.pem",
            "signature_key_fp": "PATH to IBKR private_signature.pem"
        },
        "start_date": "PORTFOLIO CREATION DATE. Defaults to 2020-01-01",
        "update_frequency_minutes": "How frequently the data from IBKR should be updated. Defaults to 15 minutes"
  }
}
```
Only the `credentials` section is mandatory, put your credentials in the corresponding fields, and follow the instructions
to obtain your `totp_secret_key`. You can also skip it, and the application will ask for your OTP everytime.

The `enabled` field is used to enable or disable the IBKR integration. If you set it to `false`, the application
will not show any IBKR data, and it will not try to connect to IBKR.

## Technical details

The application uses the [iBind](https://github.com/Voyz/ibind) client. This is a Python client using IBKR [Web API](https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/)

**Stonks Overwatch** uses this client to fetch data from IBKR and store it in a local database. The application
then uses this data to provide insights into your portfolio, including real-time access to your investments.

The DB model reflects the IBKR API and does the best effort to normalize the data and support the different features.

> IBKR API has many limitations, like only providing the transactions for the last 90 days or not
> providing Deposits/Withdrawals or fees information.

### DB Model

The DB model is defined at [`stonks_overwatch/stonks_overwatch/services/brokers/ibkr/repositories/models.py`](https://github.com/ctasada/stonks-overwatch/blob/main/src/stonks_overwatch/repositories/degiro/models.py).

### Test a new version of iBind

If you want to test a new version of iBind, you can do it by following these steps:

1. Clone the [iBind](https://github.com/Voyz/ibind) or your own fork
2. Modify the code in iBind as needed
3. In `pyproject.toml`, update the version to reflect the changes made
   ```toml
   [tool.poetry]
   version = "0.1.15.dev1"  # Update this to the new version
   ```
4. Use the new version in your project by running:
   ```bash
   poetry add path/to/your/ibind/dist/ibind-0.1.15.dev1-py3-none-any.whl
   ```
