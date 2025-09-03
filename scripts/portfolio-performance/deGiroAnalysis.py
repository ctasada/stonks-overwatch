#!/usr/bin/env python3
#
# Degiro trading tracker:
# Simplified tracking of your investments
#
# Blog post: https://foolcontrol.org/?p=3614
# GitHub: https://github.com/AdnanHodzic/degiro-trading-tracker
#
# Copyleft: Adnan Hodzic <adnan@hodzic.org>
# License: GPLv3

# FIXME: Numbers do not seem to match. Needs to be reviewed

import sys

import polars as pl

sepup = "\n" + 6 * "----" + " Degiro trading tracker " + 6 * "---" + "\n"
sep = "\n" + 22 * "---" + "\n"

if len(sys.argv) <= 1:
    print(sepup)
    print("ERROR:\nSecond argument should be path to file you want to analyze\n")
    print("Example:\npython3 degiro-trading-tracker.py ~/Documents/Transactions.xls")
    print(sep)
    sys.exit()

# excel loc/file setup
csv_file = sys.argv[1]
df = pl.read_csv(csv_file)

# define Kosten column (fee cost init)
fc = df.select("Transactiekosten en/of").to_series()

# turn negative into positive
df = df.with_columns(pl.col("Transactiekosten en/of").abs().alias("AbsKosten"))

# generate sum + round to 2 decimals
fc_sum = df.select("AbsKosten").sum().item()
fcf = round(fc_sum, 2)

# set beginning & end date
dbeg = df.select("Datum").tail(1).item()
dend = df.select("Datum").head(1).item()

# define Totaal column (portofolio cost init)
pc = df.select("Totaal").to_series()

# cherry pick positives (portofolio sale init) and sum them
ps = df.filter(pl.col("Totaal") > 0).select("Totaal").sum().item()
ps = round(ps, 2)

# turn negatives into positive
df = df.with_columns(pl.col("Totaal").abs().alias("AbsTotaal"))

# generate sum + round to 2 decimals
pc_sum = df.select("AbsTotaal").sum().item()
pcf = pc_sum - ps
pcf = round(pcf - ps, 2)

# Define a format string for 3 columns, each 20 characters wide, left-aligned
format_str = "{:<20}{:<20}{:<20}"

# output
print(sepup)
print("Analysis made by using:", csv_file)
print("\nTotal Degiro portofolio investment ...")
print("\nfrom:", dbeg, "\nto:  ", dend, "\n")
print(format_str.format("Stock costs", "Stock sales", "Fee costs"))
formatted_row = [f"€{num:,}" for num in (pcf, ps, fcf)]
print(format_str.format(*formatted_row))
print(sep)
