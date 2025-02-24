"""poetry run python ./scripts/exchanges.py"""

from iso10383 import MIC

for exchange in MIC:
    print(exchange)
