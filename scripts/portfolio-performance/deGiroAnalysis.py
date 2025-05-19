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

import numpy as np
import pandas as pd

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
df = pd.read_csv(csv_file)

# define Kosten column (fee cost init)
fc = df["Transactiekosten en/of"]

# turn negative into positive
df["AbsKosten"] = fc.abs()

# generate sum + round to 2 decimals
fc_sum = df["AbsKosten"].sum()
fcf = round(fc_sum, 2)

# set beginning & end date
dbeg = df["Datum"].tail(1).to_string(index=False).strip()
dend = df["Datum"].head(1).to_string(index=False).strip()

# define Totaal column (portofolio cost init)
pc = df["Totaal"]

# cherry pick positives (portofolio sale init)
ps = []
for line in pc:
    # if not line.startswith('-'):
    if line > 0:
        ps.append(line)

# convert str + int to float (sales)
ps = np.array(ps, float)

ps = sum(ps)
ps = round(ps, 2)

# turn str to float (portofolio costs)
pc = pc.astype(float)

# turn negatives into positive
df["AbsTotaal"] = pc.abs()

# generate sum + round to 2 decimals
pc_sum = df["AbsTotaal"].sum()
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
