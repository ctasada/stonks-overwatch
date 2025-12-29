from stonks_overwatch.config.metatrader4 import Metatrader4Credentials


def test_metatrader4_credentials_init():
    ftp_server = "ftp.example.com"
    username = "testuser"
    password = "testpassword"
    path = "/path/to/data"

    credentials = Metatrader4Credentials(
        ftp_server=ftp_server,
        username=username,
        password=password,
        path=path,
    )

    assert credentials.ftp_server == ftp_server
    assert credentials.username == username
    assert credentials.password == password
    assert credentials.path == path


def test_metatrader4_credentials_to_dict():
    credentials = Metatrader4Credentials(
        ftp_server="ftp.example.com",
        username="testuser",
        password="testpassword",
        path="/path/to/data",
    )

    credentials_dict = credentials.to_dict()

    assert credentials_dict["ftp_server"] == "ftp.example.com"
    assert credentials_dict["username"] == "testuser"
    assert credentials_dict["password"] == "testpassword"
    assert credentials_dict["path"] == "/path/to/data"


def test_metatrader4_credentials_from_dict():
    credentials_dict = {
        "ftp_server": "ftp.example.com",
        "username": "testuser",
        "password": "testpassword",
        "path": "/path/to/data",
    }

    credentials = Metatrader4Credentials.from_dict(credentials_dict)

    assert credentials.ftp_server == "ftp.example.com"
    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.path == "/path/to/data"


def test_metatrader4_credentials_from_empty_dict():
    credentials_dict = {}

    credentials = Metatrader4Credentials.from_dict(credentials_dict)

    assert credentials.ftp_server == ""
    assert credentials.username == ""
    assert credentials.password == ""
    assert credentials.path == ""


def test_has_minimal_credentials():
    # All required fields present
    credentials = Metatrader4Credentials(
        ftp_server="ftp.example.com",
        username="user",
        password="pass",
        path="/path",
    )
    assert credentials.has_minimal_credentials() is True

    # Missing ftp_server
    credentials = Metatrader4Credentials(
        ftp_server="",
        username="user",
        password="pass",
        path="/path",
    )
    assert credentials.has_minimal_credentials() is False

    # Missing username
    credentials = Metatrader4Credentials(
        ftp_server="ftp.example.com",
        username="",
        password="pass",
        path="/path",
    )
    assert credentials.has_minimal_credentials() is False

    # Missing password
    credentials = Metatrader4Credentials(
        ftp_server="ftp.example.com",
        username="user",
        password="",
        path="/path",
    )
    assert credentials.has_minimal_credentials() is False

    # Missing path
    credentials = Metatrader4Credentials(
        ftp_server="ftp.example.com",
        username="user",
        password="pass",
        path="",
    )
    assert credentials.has_minimal_credentials() is False
