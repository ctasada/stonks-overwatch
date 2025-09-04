import os
import sys

import polars as pl
from util import CSV_SEPARATOR, EXPORT_COLUMNS_TRANSACTIONS, convert_date


class DeGiroConverterTrans:
    def __init__(self, inputfile: str = None, data=None):
        if data is None:
            # Read with polars
            self.inputdata = pl.read_csv(inputfile)
        else:
            self.inputdata = data if isinstance(data, pl.DataFrame) else pl.from_pandas(data)

        # Create empty polars DataFrame with the required columns
        self.outputdata = pl.DataFrame({col: [] for col in EXPORT_COLUMNS_TRANSACTIONS})

    def convert(self):
        # Use polars operations to create the output DataFrame
        self.outputdata = self.inputdata.select(
            [
                pl.col("Datum").map_elements(convert_date, return_dtype=pl.String).alias("Date"),
                pl.col("Tijd").alias("Time"),
                pl.col("ISIN").alias("ISIN"),
                pl.col("Aantal").alias("Shares"),
                pl.nth(14).alias("Fees"),  # 14th column (0-indexed)
                pl.col("Waarde").fill_null(0.0).alias("Value"),
                pl.nth(10).alias("Transaction Currency"),  # 10th column (0-indexed)
                pl.col("Wisselkoers").alias("Exchange Rate"),
            ]
        )

    def write_outputfile(self, outputfile: str):
        self.outputdata.write_csv(outputfile, separator=CSV_SEPARATOR)
        print("Wrote output to: " + outputfile)


if __name__ == "__main__":
    converter = DeGiroConverterTrans(os.path.dirname(sys.argv[0]) + "Transactions.csv")
    converter.convert()
    filename = os.path.join(os.getcwd(), "degiro_portofolio_converted.csv")
    converter.write_outputfile(filename)
