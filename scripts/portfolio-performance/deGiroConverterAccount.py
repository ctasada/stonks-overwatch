import logging
import os
import sys

import pandas as pd
from currency_converter import CurrencyConverter
from util import CSV_DECIMAL, CSV_SEPARATOR, EXPORT_COLUMNS_ACCOUNT, convert_date

c = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
convert_isin_usd_to_euro = ["IE00B3RBWM25", "IE00B0M62Q58", "IE0031442068", "IE00BZ163M45"]


def convert_currency(isin: str, value: str, date):
    if isin in convert_isin_usd_to_euro:
        try:
            converted = c.convert(value, "USD", "EUR", date=date)
            return round(converted, 2)
        except Exception:
            logging.exception("message")
            print(isin + str(value) + str(date))
            return value
    return value


class DeGiroConverterAccount:
    def __init__(self, inputfile: str = None, data=None):
        self.outputdata = None
        if data is None:
            self.inputdata = pd.read_csv(inputfile, parse_dates=[0], date_format="%d-%m-%Y", decimal=",")
        else:
            self.inputdata = data
        self.df = self.inputdata

    def convert(self):
        self.outputdata = pd.DataFrame(index=self.inputdata.index, columns=EXPORT_COLUMNS_ACCOUNT, data=None)

        self.outputdata["Date"] = self.df["Datum"].apply(convert_date)
        self.outputdata["Time"] = self.df["Tijd"]
        self.outputdata["ISIN"] = self.df["ISIN"]
        self.df["Value"] = self.df.iloc[:, 8].astype(float)
        self.outputdata["Transaction Currency"] = self.df["Mutatie"]
        self.outputdata.loc[self.df["Omschrijving"].str.contains("Dividendbelasting", na=False), "Type"] = "Taxes"
        self.outputdata.loc[self.df["Omschrijving"].str.contains("iDEAL", na=False), "Type"] = "Deposit"
        # DeGiro has a weird issue in that some EUR funds pay out dividend in USD
        # This completely messes up the imports since pp does not expect that
        # Therefore we manually convert those funds to EUR. This will probably be off by some margin,
        # but I can live with that
        self.outputdata.loc[self.outputdata["ISIN"].isin(convert_isin_usd_to_euro), "Transaction Currency"] = "EUR"
        self.outputdata["Value"] = self.df.apply(
            lambda row: convert_currency(row["ISIN"], row["Value"], row["Datum"]), axis=1
        )

    def merge_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        koop_row = df[df["Omschrijving"].str.contains("Koop", na=False)]
        valuta_credit_row = df[df["Omschrijving"].str.contains("Valuta Creditering", na=False)]

        if not koop_row.empty and not valuta_credit_row.empty:
            koop_row = koop_row.iloc[0]
            koop_row["FX"] = valuta_credit_row["FX"].values[0]
            frame = pd.DataFrame([koop_row])
            print(frame)
            df.update(frame)

        return df

    def new_convert(self):
        # Reverse the lines, so we have it chronologically sorted
        df = self.df.iloc[::-1]

        grouped = df.groupby(
            ["Datum", "Tijd", "Valutadatum", "Product", "ISIN", "Order Id"], as_index=False, sort=False
        )
        merged_df = grouped.apply(self.merge_rows, include_groups=True)
        merged_df = merged_df.reset_index()
        merged_df = merged_df.drop(columns=["level_0", "level_1"])
        # df.update(merged_df)

        # Reverse again to keep the original order
        self.outputdata = df.reset_index().iloc[::-1]

    def write_outputfile(self, outputfile: str):
        self.outputdata.to_csv(outputfile, index=False, decimal=CSV_DECIMAL, sep=CSV_SEPARATOR)
        print("Wrote output to: " + outputfile)


if __name__ == "__main__":
    converter = DeGiroConverterAccount(os.path.dirname(sys.argv[0]) + "Account.csv")
    converter.convert()
    # converter.new_convert()
    filename = os.path.join(os.getcwd(), "degiro_account_converted.csv")
    converter.write_outputfile(filename)
