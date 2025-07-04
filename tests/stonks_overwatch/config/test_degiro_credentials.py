from stonks_overwatch.config.degiro import DegiroCredentials


def test_degiro_credentials_init():
    username = "testuser"
    password = "testpassword"
    int_account = 123456
    totp_secret_key = "ABCDEFGHIJKLMNOP"
    one_time_password = 123456

    credentials = DegiroCredentials(
        username=username,
        password=password,
        int_account=int_account,
        totp_secret_key=totp_secret_key,
        one_time_password=one_time_password,
    )

    assert credentials.username == username
    assert credentials.password == password
    assert credentials.int_account == int_account
    assert credentials.totp_secret_key == totp_secret_key
    assert credentials.one_time_password == one_time_password


def test_degiro_credentials_to_dict():
    credentials = DegiroCredentials(
        username="testuser",
        password="testpassword",
        int_account=123456,
        totp_secret_key="ABCDEFGHIJKLMNOP",
        one_time_password=123456,
    )

    credentials_dict = credentials.to_dict()

    assert credentials_dict["username"] == "testuser"
    assert credentials_dict["password"] == "testpassword"
    assert credentials_dict["int_account"] == 123456
    assert credentials_dict["totp_secret_key"] == "ABCDEFGHIJKLMNOP"
    assert credentials_dict["one_time_password"] == 123456


def test_degiro_credentials_from_dict():
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": "123456",
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": "123456",
    }

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account == "123456"
    assert credentials.totp_secret_key == "ABCDEFGHIJKLMNOP"
    assert credentials.one_time_password == "123456"


def test_degiro_credentials_from_empty_dict():
    credentials_dict = {}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == ""
    assert credentials.password == ""
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None


def test_degiro_credentials_from_minimum_dict():
    credentials_dict = {"username": "testuser", "password": "testpassword"}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None
