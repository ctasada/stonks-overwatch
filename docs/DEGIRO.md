# DEGIRO

DEGIRO is the main tracker supported by **Stonks Overwatch**. It provides real-time access to your investments, portfolio value, growth, dividends, fees, deposits, and more.

## How to login to DEGIRO

You can log in to DEGIRO in two different ways

### Use the Login form

When you open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000) you will see a login form. Introduce
your credentials, including the OTP (One-Time-Password).

The first time, the application will retrieve all your portfolio from DEGIRO, and you are good to go

> Using this approach, no credentials are stored anywhere. You will need to repeat this step everytime

#### Automatic login

If you don't want to introduce your credentials everytime, it's possible to store them in a file, so login will be much
more comfortable and transparent.

Copy the file `config/config.json.template` to `config/config.json`

```json
{
    "degiro": {
        "enabled": "BOOLEAN (true by default)",
        "offline_mode": "BOOLEAN (false by default)",
        "credentials": {
            "username": "USERNAME",
            "password": "PASSWORD",
            "totp_secret_key": "See https://github.com/Chavithra/stonks_overwatch-connector#35-how-to-use-2fa-"
        },
        "base_currency": "EUR - Optional field. Uses DEGIRO base currency by default",
        "start_date": "PORTFOLIO CREATION DATE. Defaults to 2020-01-01",
        "update_frequency_minutes": "How frequently the data from DEGIRO should be updated. Defaults to 5 minutes"
    }
}
```

Only the `credentials` section is mandatory, put your credentials in the corresponding fields, and follow the instructions
to obtain your `totp_secret_key`. You can also skip it, and the application will ask for your OTP every time.

The `enabled` field is used to enable or disable the DEGIRO integration. If you set it to `false`, the application
will not show any DEGIRO data, and it will not try to connect to DEGIRO.

The `offline_mode` field is used to enable or disable the offline mode. If you set it to `true`, the application will
not try to connect to DEGIRO, and it will only use the data stored in the database. This is useful if you want to
work with the application without an internet connection or if you want to avoid hitting the DEGIRO API.

## Technical details

The application uses the [DEGIRO Connector](https://github.com/Chavithra/degiro-connector) to connect to DEGIRO. This
client is a Python wrapper around the non-publicly documented DEGIRO API.

**Stonks Overwatch** uses the connector to fetch data from DEGIRO and store it in a local database. The application
then uses this data to provide insights into your portfolio, including real-time access to your investments, portfolio.

The DB model reflects the DEGIRO API and does the best effort to normalize the data and support the different features.

### DB Model

The DB model is defined at [`stonks_overwatch/stonks_overwatch/services/brokers/degiro/repositories/models.py`](https://github.com/ctasada/stonks-overwatch/blob/main/src/stonks_overwatch/repositories/degiro/models.py).

### Test a new version of the connector

If you want to test a new version of the DEGIRO connector, you can do it by following these steps:

1. Clone the [DEGIRO Connector](https://github.com/Chavithra/degiro-connector) or your own fork
2. Modify the code in DEGIRO Connector as needed
3. In `pyproject.toml`, update the version to reflect the changes made

   ```toml
   [tool.poetry]
      version = "3.0.29.dev1"  # Update this to the new version
   ```

4. Use the new version in your project by running:

```bash
   poetry add path/to/your/degiro-connector/dist/degiro_connector-3.0.29.dev1-py3-none-any.whl
```
