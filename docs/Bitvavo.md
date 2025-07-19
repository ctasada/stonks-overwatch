# [Bitvavo](https://bitvavo.com/en/)

Bitvavo is a cryptocurrency exchange that **Stonks Overwatch** supports. It allows you to track your crypto investments, portfolio value, and growth.

## How to login to Bitvavo

To log in to Bitvavo, you need to create an API key and secret. Follow these steps:

1. [Bitvavo API Documentation](https://docs.bitvavo.com/docs/get-started/#create-an-api-key-and-secret) to understand how to create an API key.
2. Copy the file `config/config.json.template` to `config/config.json` if you don't have it already.

```json
{
    "bitvavo": {
        "enabled":"BOOLEAN (true by default)",
        "credentials": {
            "apikey": "BITVAVO API KEY",
            "apisecret": "BITVAVO API SECRET"
        },
        "update_frequency_minutes": "How frequently the data from Bitvavo should be updated. Defaults to 5 minutes"
    }
}
```

Only the `credentials` section is mandatory, put your credentials in the corresponding fields. Once the `credentials`
are provided, the integration will automatically fetch your portfolio from Bitvavo.

The `enabled` field is used to enable or disable the Bitvavo integration. If you set it to `false`, the application
will not show any Bitvavo data, and it will not try to connect to Bitvavo.

## Technical details

The application uses the official [Python Bitvavo API](https://github.com/bitvavo/python-bitvavo-api) to connect to Bitvavo. This
client is a Python wrapper around [Bitvavo's public API](https://docs.bitvavo.com/).

**Stonks Overwatch** uses the [Python Bitvavo API](https://github.com/bitvavo/python-bitvavo-api) to fetch data from Bitvavo and store it in a local database. The application
then uses this data to provide insights into your portfolio, including real-time access to your investments, portfolio.

The DB model reflects Bitvavo API and does the best effort to normalize the data and support the different features.

### DB Model

The DB model is defined at [`stonks_overwatch/stonks_overwatch/services/brokers/bitvavo/repositories/models.py`](https://github.com/ctasada/stonks-overwatch/blob/main/src/stonks_overwatch/repositories/bitvavo/models.py).

## Known issues

- When an asset is bought using RFQ (Request for Quote), the transaction doesn't appear in the transactions returned by the API
- When an asset uses some kind of blocking Staking, the Balance API returns only the available balance, not the total balance.
