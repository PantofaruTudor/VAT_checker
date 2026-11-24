import pandas as pd

SOURCE = "BasicCompanyDataAsOneFile-2026-11-01.csv"


def clean_postcode(postcode):
    return postcode.upper().replace(" ", "")


sample = pd.read_csv("data/sample_300.csv", dtype=str).fillna("")
sample_postcodes = [clean_postcode(p) for p in sample["postcode"]]

counts = {}
for postcode in sample_postcodes:
    if postcode != "":
        counts[postcode] = 0

for chunk in pd.read_csv(SOURCE, dtype=str, chunksize=200_000, usecols=["RegAddress.PostCode"]):
    for postcode in chunk["RegAddress.PostCode"].fillna(""):
        postcode = clean_postcode(postcode)
        if postcode in counts:
            counts[postcode] += 1

sample["postcode_shared_by"] = [counts.get(p, 0) for p in sample_postcodes]
sample.to_csv("data/sample_300.csv", index=False)

print("Companies sharing the same postcode:")
print(sample["postcode_shared_by"].describe())
