# DEGIRO

DEGIRO is the main tracker supported by **Stonks Overwatch**. It provides real-time access to your investments, portfolio value, growth, dividends, fees, deposits, and more.

## How to login to DEGIRO

You can log in to DEGIRO using different authentication methods that DEGIRO supports. The application automatically detects which method your account requires and guides you through the appropriate flow.

### Authentication Methods

DEGIRO supports three authentication methods, which the application handles automatically:

1. **Username/Password Only**: Basic authentication (less common)
2. **TOTP (Two-Factor Authentication)**: Requires 6-digit code from authenticator app
3. **In-App Authentication**: Requires confirmation through DEGIRO mobile app (New 2025)

### Use the Login form

When you open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000) you will see a login form. The login process varies based on your DEGIRO account security settings:

#### Basic Login Flow

1. Enter your DEGIRO username and password
2. Click "Login"
3. The application will automatically detect which additional authentication is required

#### TOTP (2FA) Flow

If your account has traditional 2FA enabled:
1. Enter username and password
2. You'll be redirected to a 2FA code input screen
3. Enter the 6-digit code from your authenticator app
4. Authentication completes and portfolio loads

#### In-App Authentication Flow (New 2025)

If your account uses In-App authentication (automatically enabled when 2FA is not configured):
1. Enter username and password
2. You'll see "Open the DEGIRO app" message with a loading spinner
3. Open the DEGIRO mobile app on your phone
4. Approve the login notification in the app
5. The browser will automatically detect approval and proceed to the dashboard

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

## Authentication Troubleshooting

### Common Authentication Issues

#### In-App Authentication Issues

- **Stuck on "Open the DEGIRO app" screen**:
  - Check that you have the official DEGIRO mobile app installed
  - Look for a notification in the app about approving the login
  - Make sure you're logged into the correct account in the mobile app
  - Try refreshing the browser page if the notification was missed

- **No notification in mobile app**:
  - Ensure your mobile app is updated to the latest version
  - Check notification settings are enabled for the DEGIRO app
  - Try logging out and back into the mobile app

#### TOTP (2FA) Issues

- **Invalid 2FA code errors**:
  - Ensure your authenticator app's time is synchronized
  - Try generating a new code and entering it quickly
  - Verify you're using the correct account in your authenticator app

#### General Login Issues

- **Wrong authentication method shown**:
  - The application auto-detects your account's security settings
  - If you recently changed your DEGIRO security settings, it may take time to reflect
  - Try clearing browser cache and cookies for the application

### Authentication Method Detection

The application automatically detects which authentication method your DEGIRO account requires:

- **Basic Login**: No additional security configured
- **TOTP Required**: Traditional 2FA with authenticator app is enabled
- **In-App Authentication**: Automatically enabled when 2FA is not configured (DEGIRO's newer security method)

You cannot manually choose the authentication method - it's determined by your DEGIRO account security configuration.

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
      version = "3.0.30.dev1"  # Update this to the new version
   ```

4. Build the package by running:

    ```bash
       poetry build
    ```

5. Use the new version in your project by running:

    ```bash
       poetry add path/to/your/degiro-connector/dist/degiro_connector-3.0.30.dev1-py3-none-any.whl
    ```
