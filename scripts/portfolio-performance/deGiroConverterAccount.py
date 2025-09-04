import logging
import os
import sys

import polars as pl
from currency_converter import CurrencyConverter
from util import CSV_SEPARATOR, EXPORT_COLUMNS_ACCOUNT, convert_date

c = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
convert_isin_usd_to_euro = ["IE00B3RBWM25", "IE00B0M62Q58", "IE0031442068", "IE00BZ163M45"]
TRANSACTION_CURRENCY = "Transaction Currency"


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
            # Read with polars
            self.inputdata = pl.read_csv(inputfile, separator=",", decimal_comma=True)
        else:
            self.inputdata = data if isinstance(data, pl.DataFrame) else pl.from_pandas(data)
        self.df = self.inputdata

    def convert(self):
        # Create base DataFrame with required columns and transformations
        self.outputdata = self.df.select(
            [
                # Basic column mappings
                pl.col("Datum").map_elements(convert_date, return_dtype=pl.String).alias("Date"),
                pl.col("Tijd").alias("Time"),
                pl.col("ISIN").alias("ISIN"),
                pl.nth(8).cast(pl.Float64).alias("Value"),  # 8th column as float
                pl.col("Mutatie").alias(TRANSACTION_CURRENCY),
                # Conditional Type assignment based on Omschrijving
                pl.when(pl.col("Omschrijving").str.contains("Dividendbelasting"))
                .then(pl.lit("Taxes"))
                .when(pl.col("Omschrijving").str.contains("iDEAL"))
                .then(pl.lit("Deposit"))
                .otherwise(None)
                .alias("Type"),
            ]
        ).with_columns(
            [
                # Currency conversion for specific ISINs
                pl.when(pl.col("ISIN").is_in(convert_isin_usd_to_euro))
                .then(pl.lit("EUR"))
                .otherwise(pl.col(TRANSACTION_CURRENCY))
                .alias(TRANSACTION_CURRENCY),
                # Apply currency conversion function
                pl.struct(["ISIN", "Value", "Datum"])
                .map_elements(
                    lambda row: convert_currency(row["ISIN"], row["Value"], row["Datum"]), return_dtype=pl.Float64
                )
                .alias("Value"),
            ]
        )

        # Add any missing columns from EXPORT_COLUMNS_ACCOUNT with null values
        existing_columns = set(self.outputdata.columns)
        for col in EXPORT_COLUMNS_ACCOUNT:
            if col not in existing_columns:
                self.outputdata = self.outputdata.with_columns(pl.lit(None).alias(col))

    def merge_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        # Filter for "Koop" and "Valuta Creditering" rows
        koop_rows = df.filter(pl.col("Omschrijving").str.contains("Koop"))
        valuta_credit_rows = df.filter(pl.col("Omschrijving").str.contains("Valuta Creditering"))

        if len(koop_rows) > 0 and len(valuta_credit_rows) > 0:
            # Get the first koop row and update its FX with valuta credit FX
            koop_row = koop_rows.slice(0, 1)
            fx_value = valuta_credit_rows.select("FX").item(0, 0)

            # Update the koop row with the FX value
            updated_koop = koop_row.with_columns(pl.lit(fx_value).alias("FX"))
            print(updated_koop)

            # Replace the original koop row in the dataframe
            # This is complex in polars, so we'll reconstruct the dataframe
            koop_filter = pl.col("Omschrijving").str.contains("Koop")
            koop_index = df.with_row_index().filter(koop_filter).select("index").item(0, 0)
            df = (
                df.with_row_index()
                .with_columns(pl.when(pl.col("index") == koop_index).then(fx_value).otherwise(pl.col("FX")).alias("FX"))
                .drop("index")
            )

        return df

    def new_convert(self):
        # Reverse the lines, so we have it chronologically sorted
        df = self.df.reverse()

        # Group by the specified columns and apply merge_rows to each group
        grouped_df = df.group_by(
            ["Datum", "Tijd", "Valutadatum", "Product", "ISIN", "Order Id"], maintain_order=True
        ).map_groups(self.merge_rows)

        # Reverse again to keep the original order
        self.outputdata = grouped_df.reverse()

    def write_outputfile(self, outputfile: str):
        self.outputdata.write_csv(outputfile, separator=CSV_SEPARATOR)
        print("Wrote output to: " + outputfile)


if __name__ == "__main__":
    converter = DeGiroConverterAccount(os.path.dirname(sys.argv[0]) + "Account.csv")
    converter.convert()
    # converter.new_convert()
    filename = os.path.join(os.getcwd(), "degiro_account_converted.csv")
    converter.write_outputfile(filename)
