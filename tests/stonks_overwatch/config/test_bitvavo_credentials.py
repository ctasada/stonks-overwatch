from stonks_overwatch.config.bitvavo import BitvavoCredentials


def test_bitvavo_credentials_init():
    api_key = "testapikey"
    api_secret = "testapisecret"

    credentials = BitvavoCredentials(
        apikey=api_key,
        apisecret=api_secret,
    )

    assert credentials.apikey == api_key
    assert credentials.apisecret == api_secret


def test_bitvavo_credentials_to_dict():
    credentials = BitvavoCredentials(
        apikey="testapikey",
        apisecret="testapisecret",
    )

    credentials_dict = credentials.to_dict()

    assert credentials_dict["apikey"] == "testapikey"
    assert credentials_dict["apisecret"] == "testapisecret"


def test_bitvavo_credentials_from_dict():
    credentials_dict = {
        "apikey": "testapikey",
        "apisecret": "testapisecret",
    }

    credentials = BitvavoCredentials.from_dict(credentials_dict)

    assert credentials.apikey == "testapikey"
    assert credentials.apisecret == "testapisecret"
