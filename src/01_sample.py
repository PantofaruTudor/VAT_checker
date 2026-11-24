import random

import pandas as pd

SOURCE = "BasicCompanyDataAsOneFile-2026-11-01.csv"
SAMPLE_SIZE = 300

COLUMNS = {
    "CompanyName": "name",
    "CompanyNumber": "company_number",
    "RegAddress.CareOf": "care_of",
    "RegAddress.AddressLine1": "address_line1",
    "RegAddress.PostTown": "post_town",
    "RegAddress.PostCode": "postcode",
    "CompanyCategory": "company_category",
    "CompanyStatus": "company_status",
    "IncorporationDate": "incorporation_date",
    "Accounts.AccountCategory": "accounts_category",
    "Accounts.NextDueDate": "accounts_next_due",
    "ConfStmtNextDueDate": "confirmation_next_due",
    "Mortgages.NumMortCharges": "mortgage_charges",
    "SICCode.SicText_1": "sic_1",
    "SICCode.SicText_2": "sic_2",
    "SICCode.SicText_3": "sic_3",
    "SICCode.SicText_4": "sic_4",
    "PreviousName_1.CompanyName": "previous_name",
}


def is_wanted(column_name):
    return column_name.strip() in COLUMNS


random.seed(42)
winners = None

for chunk in pd.read_csv(SOURCE, dtype=str, chunksize=200_000, usecols=is_wanted):
    chunk.columns = chunk.columns.str.strip()
    chunk["ticket"] = [random.random() for _ in range(len(chunk))]

    if winners is None:
        pool = chunk
    else:
        pool = pd.concat([winners, chunk])

    winners = pool.nsmallest(SAMPLE_SIZE, "ticket")

sample = winners.sort_values("ticket")
sample = sample.drop(columns="ticket")
sample = sample.rename(columns=COLUMNS)
sample = sample.fillna("")

sample.to_csv("data/sample_300.csv", index=False)
print("Saved", len(sample), "companies to data/sample_300.csv")
