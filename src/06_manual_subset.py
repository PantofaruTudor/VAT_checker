import pandas as pd

PER_GROUP = 20

sample = pd.read_csv("data/sample_triaged.csv", dtype=str).fillna("")

parts = []
for group in ["likely", "uncertain", "unlikely"]:
    companies = sample[sample["group"] == group]
    parts.append(companies.sample(n=PER_GROUP, random_state=42))

subset = pd.concat(parts)
subset = subset[[
    "company_number", "name", "address_line1", "post_town", "postcode",
    "group", "accounts_category", "sic_1",
]]

for column in [
    "website_manual", "site_confirmed_by", "vat_manual", "vat_found_where",
    "hmrc_valid", "hmrc_name", "hmrc_postcode", "notes",
]:
    subset[column] = ""

subset.to_excel("data/manual_check.xlsx", index=False)
print("Saved", len(subset), "companies to data/manual_check.xlsx")
