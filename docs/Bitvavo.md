# [Bitvavo](https://bitvavo.com/en/)

Bitvavo is a cryptocurrency exchange that **Stonks Overwatch** supports. It allows you to track your crypto investments, portfolio value, and growth.

## How to login to Bitvavo

To log in to Bitvavo, you need to create an API key and secret. Follow these steps:

1. [Bitvavo API Documentation](https://docs.bitvavo.com/docs/get-started/#create-an-api-key-and-secret) to understand how to create an API key.
2. Copy the file `config/config.json.template` to `config/config.json` if you don't have it already.

```json
{
    "bitvavo": {
        "enabled": true,
        "credentials": {
            "apikey": "BITVAVO API KEY",
            "apisecret": "BITVAVO API SECRET"
        }
    }
}
```

Only the `credentials` section is mandatory, put your credentials in the corresponding fields. Once the `credentials`
are provided, the integration will automatically fetch your portfolio from Bitvavo. If needed, the integration can
be easily disabled with `"enabled": false`.

## Technical details

The application uses the [Python Bitvavo API](https://github.com/bitvavo/python-bitvavo-api) to connect to Bitvavo. This
client is a Python wrapper around [Bitvavo's public API](https://docs.bitvavo.com/).

At the time of writing, **Stonks Overwatch** doesn't store any data from Bitvavo in the database. Instead, it fetches
the data in real-time from Bitvavo's API. This means that the data is always up to date, but it also means that when
Bitvavo is down, the application won't be able to show the data.
