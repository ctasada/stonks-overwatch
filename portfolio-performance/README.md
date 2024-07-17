# Portfolio Performance

This folder contains some scripts to help exporting the data to Portfolio Performance

> Stil WIP

* `deGiroAnalysis.py`: Using the `Transactions.csv` file, calculates the total costs of the Portfolio
* `deGiroConverterAccount.py`: Converts the `Accounts.csv` file to a format that can be directly imported by Portfolio Performance
* `deGiroConverterTrans.py`: Converts the `Transactions.csv` file to a format that can be directly imported by Portfolio Performance

## TODO

* Review the expected format to properly import the data
* Fix import of Dividends: Ignore 'Valuta Creditering' and convert USD to Euro. Review the currencyconverter values if match