from stonks_overwatch.services.brokers.metatrader4.utilities.parser import parse_mt4_html

SAMPLE_HTML = """
<html>
<body>
<table>
    <tr><td>Account: 123456</td></tr>
    <tr>
        <td><b>Closed Transactions:</b></td>
    </tr>
    <tr align="right">
        <td>Ticket</td><td>Open Time</td><td>Type</td><td>Size</td><td>Item</td><td>Open Price</td><td>S / L</td>
        <td>T / P</td><td>Close Time</td><td>Close Price</td><td>Commission</td><td>Taxes</td><td>Swap</td>
        <td>Profit</td>
    </tr>
    <tr align="right">
        <td>12345678</td><td>2023.01.01 10:00:00</td><td>buy</td><td>0.10</td><td>EURUSD</td><td>1.1000</td>
        <td>1.0900</td><td>1.1100</td><td>2023.01.01 12:00:00</td><td>1.1050</td><td>-0.50</td><td>0.00</td>
        <td>0.00</td><td>50.00</td>
    </tr>
    <tr align="right">
        <td>12345679</td><td>2023.01.01 13:00:00</td><td>balance</td><td colspan=11>Deposit</td><td>1000.00</td>
    </tr>
    <tr>
        <td><b>Open Trades:</b></td>
    </tr>
    <tr align="right">
        <td>Ticket</td><td>Open Time</td><td>Type</td><td>Size</td><td>Item</td><td>Price</td><td>S / L</td>
        <td>T / P</td><td></td><td>Market Price</td><td>Commission</td><td>Taxes</td><td>Swap</td><td>Profit</td>
    </tr>
    <tr align="right">
        <td>12345680</td><td>2023.01.01 14:00:00</td><td>sell</td><td>0.20</td><td>GBPUSD</td><td>1.2500</td>
        <td>0.0000</td><td>0.0000</td><td>&nbsp;</td><td>1.2450</td><td>-1.00</td><td>0.00</td><td>0.00</td><td>100.00</td>
    </tr>
    <tr>
        <td><b>Working Orders:</b></td>
    </tr>
    <tr>
        <td><b>Summary:</b></td>
    </tr>
    <tr>
        <td>Deposit/Withdrawal:</td><td>1000.00</td><td>Credit Facility:</td><td>0.00</td>
    </tr>
</table>
</body>
</html>
"""


def test_parse_mt4_html_closed_transactions():
    result = parse_mt4_html(SAMPLE_HTML)

    assert len(result.closed_transactions) == 2

    trade = result.closed_transactions[0]
    assert trade["Ticket"] == "12345678"
    assert trade["Item"] == "EURUSD"
    # Note: Values are strings in parsing result
    assert trade["Profit"] == "50.00"

    # Check Price columns which we renamed via header fix
    assert trade["Open Price"] == "1.1000"
    assert trade["Close Price"] == "1.1050"


def test_parse_mt4_html_balance():
    result = parse_mt4_html(SAMPLE_HTML)
    balance_row = result.closed_transactions[1]

    assert balance_row["Type"] == "balance"
    assert balance_row["Profit"] == "1000.00"
    assert balance_row["Description"] == "Deposit"


def test_parse_mt4_html_open_trades():
    result = parse_mt4_html(SAMPLE_HTML)

    assert len(result.open_trades) == 1
    trade = result.open_trades[0]
    assert trade["Ticket"] == "12345680"
    assert trade["Item"] == "GBPUSD"
    assert trade["Size"] == "0.20"
    # Market Price is at index 9?
    # In SAMPLE_HTML I tried to mimic column structure broadly.
    # Parser relies on index map.
    # OPEN_HEADERS_MAP: {0: Ticket, ..., 5: Price, 9: Market Price}
    # My sample row has:
    # 0: Ticket, 1: Open Time, 2: Type, 3: Size, 4: Item, 5: Price, 6: SL, 7: TP, 8: nbsp, 9: Market Price ...
    assert trade["Market Price"] == "1.2450"


def test_parse_mt4_html_summary():
    result = parse_mt4_html(SAMPLE_HTML)
    assert result.summary["Deposit/Withdrawal"] == "1000.00"
