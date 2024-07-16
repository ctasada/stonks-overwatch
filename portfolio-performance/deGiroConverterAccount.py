import datetime
import logging
import os
import sys

import pandas as pd
from currency_converter import CurrencyConverter

from util import *

c = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
convert_isin_usd_to_euro = ['IE00B3RBWM25', 'IE00B0M62Q58', 'IE0031442068', 'IE00BZ163M45']


def convert_currency(isin: str, value: str, date):
    if isin in convert_isin_usd_to_euro:
        try:
            converted = c.convert(value, 'USD', 'EUR', date=date)
            return round(converted, 2)
        except Exception as e:
            logging.exception("message")
            print(isin + str(value) + str(date))
            return value
    return value


class DeGiroConverterAccount:

    def __init__(self, inputfile: str = None, data=None):
        if data is None:
            self.inputdata = pd.read_csv(inputfile, parse_dates=[0], date_format="%d-%m-%Y", decimal=",")
        else:
            self.inputdata = data
        self.df = self.inputdata
        self.outputdata = pd.DataFrame(
            index=self.inputdata.index, columns=EXPORT_COLUMNS_ACCOUNT, data=None)

    def convert(self):
        self.outputdata['Date'] = self.df['Datum'].apply(convert_date)
        self.outputdata['Time'] = self.df['Tijd']
        self.outputdata['ISIN'] = self.df['ISIN']
        self.df['Value'] = self.df.iloc[:, 8].astype(float)
        self.outputdata['Transaction Currency'] = self.df['Mutatie']
        self.outputdata.loc[self.df['Omschrijving'].str.contains("Dividendbelasting", na=False), 'Type'] = 'Taxes'
        self.outputdata.loc[self.df['Omschrijving'].str.contains("iDEAL", na=False), 'Type'] = 'Deposit'
        # DeGiro has a weird issue in that some EUR funds pay out dividend in USD
        # This completely messes up the imports since pp does not expect that
        # Therefore we manually convert those funds to EUR. This will probably be off by some margin,
        # but I can live with that
        self.outputdata.loc[self.outputdata['ISIN'].isin(convert_isin_usd_to_euro), 'Transaction Currency'] = 'EUR'
        self.outputdata['Value'] = self.df.apply(lambda row: convert_currency(row['ISIN'], row['Value'], row['Datum']),
                                                 axis=1)

    def write_outputfile(self, outputfile: str):
        self.outputdata.to_csv(outputfile, index=False, decimal=CSV_DECIMAL, sep=CSV_SEPARATOR)
        print("Wrote output to: " + outputfile)

if __name__ == '__main__':
    converter = DeGiroConverterAccount(os.path.dirname(sys.argv[0]) + 'Account.csv')
    converter.convert()
    filename = os.path.join(os.getcwd(), "degiro_account_converted.csv")
    converter.write_outputfile(filename)