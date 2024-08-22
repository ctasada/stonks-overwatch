"""
poetry run python ./scripts/agenda_dividends.py
"""
# IMPORTATIONS
import common
import json

from datetime import datetime, timedelta

from degiro_connector.trading.models.agenda import AgendaRequest, CalendarType

trading_api = common.connectToDegiro()

# FETCH AGENDA
agenda = trading_api.get_agenda(
    agenda_request=AgendaRequest(
        calendar_type=CalendarType.DIVIDEND_CALENDAR,
        end_date=datetime.now() + timedelta(days=30),
        start_date=datetime.now() - timedelta(days=30),
        offset=0,
        limit=25,
        company_name='IBERDROLA',
    ),
    raw=True,
)

# {
#     "offset": 0,
#     "total": 1,
#     "items": [
#         {
#             "eventId": 15833294,
#             "isin": "ES0144580Y14",
#             "ric": "IBE.MC",
#             "organizationName": "Iberdrola SA",
#             "dateTime": "2024-01-09T12:00:00Z",
#             "lastUpdate": "2024-01-09T09:48:13Z",
#             "countryCode": "ES",
#             "eventType": "ExDividends",
#             "exDividendDate": "2024-01-09T12:00:00Z",
#             "paymentDate": "2024-01-31T12:00:00Z",
#             "dividend": 0.0,
#             "yield": 4.62955,
#             "currency": "EUR",
#             "marketCap": "LARGE_CAP"
#         }
#     ]
# }

print(json.dumps(agenda, indent=4))
