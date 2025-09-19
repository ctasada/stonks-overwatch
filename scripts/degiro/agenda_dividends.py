"""poetry run python -m scripts.degiro.agenda_dividends"""

# IMPORTATIONS
import json
from datetime import datetime, timedelta

from degiro_connector.trading.models.agenda import AgendaRequest, CalendarType

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# FETCH AGENDA
agenda = trading_api.get_agenda(
    agenda_request=AgendaRequest(
        calendar_type=CalendarType.DIVIDEND_CALENDAR,
        end_date=datetime.now() + timedelta(days=60),
        start_date=datetime.now() - timedelta(days=30),
        offset=0,
        limit=25,
        company_name="Coca-Cola",
    ),
    raw=True,
)

# {
#     "offset": 0,
#     "total": 1,
#     "items": [
#         {
#             "eventId": 16289953,
#             "isin": "US5949181045",
#             "ric": "MSFT.OQ",
#             "organizationName": "Microsoft Corp",
#             "dateTime": "2025-05-15T14:00:00+02:00",
#             "lastUpdate": "2025-05-14T20:17:18+02:00",
#             "countryCode": "US",
#             "eventType": "ExDividends",
#             "exDividendDate": "2025-05-15T14:00:00+02:00",
#             "paymentDate": "2025-06-12T14:00:00+02:00",
#             "dividend": 0.83,
#             "yield": 0.72066,
#             "currency": "USD",
#             "marketCap": "LARGE_CAP"
#         }
#     ]
# }

print(json.dumps(agenda, indent=4))
