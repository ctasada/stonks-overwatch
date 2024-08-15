import sys
import os
import pandas as pd
from util import convert_date, EXPORT_COLUMNS_TRANSACTIONS, CSV_DECIMAL, CSV_SEPARATOR


class DeGiroConverterTrans:

    def __init__(self, inputfile: str = None, data=None):
        if data is None:
            self.inputdata = pd.read_csv(inputfile, parse_dates=[0], date_format="%d-%m-%Y")
        else:
            self.inputdata = data

        self.outputdata = pd.DataFrame(
            index=self.inputdata.index, columns=EXPORT_COLUMNS_TRANSACTIONS, data=None)

    def convert(self):
        self.outputdata['Date'] = self.inputdata['Datum'].apply(convert_date)
        self.outputdata['Time'] = self.inputdata['Tijd']
        self.outputdata['ISIN'] = self.inputdata['ISIN']
        self.outputdata['Shares'] = self.inputdata['Aantal']
        self.outputdata['Fees'] = self.inputdata.iloc[:, 14]
        self.outputdata['Value'] = self.inputdata['Waarde'].fillna(0.0)
        self.outputdata['Transaction Currency'] = self.inputdata.iloc[:, 10]
        self.outputdata['Exchange Rate'] = self.inputdata['Wisselkoers']

    def write_outputfile(self, outputfile: str):
        self.outputdata.to_csv(outputfile, index=False, decimal=CSV_DECIMAL, sep=CSV_SEPARATOR)
        print("Wrote output to: " + outputfile)


if __name__ == '__main__':
    converter = DeGiroConverterTrans(os.path.dirname(sys.argv[0]) + 'Transactions.csv')
    converter.convert()
    filename = os.path.join(os.getcwd(), 'degiro_portofolio_converted.csv')
    converter.write_outputfile(filename)
