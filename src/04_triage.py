from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPSHOT_DATE = pd.Timestamp("2026-11-01")
OVERDUE_GRACE = pd.Timedelta(days=90)

DORMANT_SIC = {"99999", "74990"}
HOLDING_SIC = {"70100", "64201", "64202", "64203", "64204", "64205", "64209"}
PROPERTY_MANAGEMENT_SIC = {"98000"}
EXEMPT_SIC_PREFIXES = ("64", "65", "66", "85", "86", "87", "88", "94")
EXEMPT_SIC_CODES = {"92000", "96030"}

LARGE_ACCOUNTS = {"FULL", "MEDIUM", "GROUP"}
SMALL_ACCOUNTS = {
    "SMALL",
    "AUDITED ABRIDGED",
    "AUDIT EXEMPTION SUBSIDIARY",
    "TOTAL EXEMPTION FULL",
    "TOTAL EXEMPTION SMALL",
    "UNAUDITED ABRIDGED",
    "PARTIAL EXEMPTION",
}
UNCERTAIN_ACCOUNTS = {"MICRO ENTITY", "NO ACCOUNTS FILED", "ACCOUNTS TYPE NOT AVAILABLE"}


def sic_codes(row):
    codes = []
    for column in ["sic_1", "sic_2", "sic_3", "sic_4"]:
        text = row[column].strip()
        if text[:5].isdigit():
            codes.append(text[:5])
    return codes


def sic_kind(code):
    if code in DORMANT_SIC:
        return "dormant"
    if code in HOLDING_SIC:
        return "holding"
    if code in PROPERTY_MANAGEMENT_SIC:
        return "property_management"
    if code in EXEMPT_SIC_CODES or code.startswith(EXEMPT_SIC_PREFIXES):
        return "exempt"
    return "taxable"


def is_overdue(date_text):
    due = pd.to_datetime(date_text, format="%d/%m/%Y", errors="coerce")
    return pd.notna(due) and due < SNAPSHOT_DATE - OVERDUE_GRACE


def collect_signals(row):
    hard_negative, soft_negative = [], []
    strong_positive, weak_positive = [], []
    notes = []

    accounts = row["accounts_category"].strip().upper()
    category = row["company_category"]
    status = row["company_status"]
    codes = sic_codes(row)
    kinds = {sic_kind(code) for code in codes}

    if accounts == "DORMANT":
        hard_negative.append("dormant")
    if accounts == "FILING EXEMPTION SUBSIDIARY":
        hard_negative.append("dormant_subsidiary")

    if accounts in LARGE_ACCOUNTS:
        strong_positive.append(f"accounts_{accounts.lower().replace(' ', '_')}")
    if category == "Public Limited Company":
        strong_positive.append("plc")

    if status != "Active":
        soft_negative.append("not_active")
    if kinds == {"dormant"}:
        soft_negative.append("dormant_sic")
    if kinds == {"holding"}:
        soft_negative.append("holding_company")
    elif kinds and kinds <= {"exempt", "holding"}:
        soft_negative.append("exempt_sic")
    if kinds == {"property_management"}:
        soft_negative.append("property_management")
    if "GUAR" in category.upper() or "LBG" in category.upper():
        soft_negative.append("guarantee_company")
    if "Charitable" in category:
        soft_negative.append("charity")
    if category == "Limited Partnership":
        soft_negative.append("limited_partnership")
    if category == "Overseas Entity":
        soft_negative.append("overseas_entity")
    if is_overdue(row["accounts_next_due"]) or is_overdue(row["confirmation_next_due"]):
        soft_negative.append("filings_overdue")

    if accounts in SMALL_ACCOUNTS:
        weak_positive.append(f"accounts_{accounts.lower().replace(' ', '_')}")
    if int(row["mortgage_charges"] or 0) > 0:
        weak_positive.append("has_mortgage")
    if category == "Limited Liability Partnership":
        weak_positive.append("llp")

    if accounts == "MICRO ENTITY":
        notes.append("micro")
    if accounts in {"NO ACCOUNTS FILED", "ACCOUNTS TYPE NOT AVAILABLE"}:
        notes.append("no_accounts_yet")
    if accounts == "AUDIT EXEMPTION SUBSIDIARY":
        notes.append("vat_group_risk")
    if not codes:
        notes.append("no_sic")

    return hard_negative, strong_positive, soft_negative, weak_positive, notes


def decide(row):
    hard_negative, strong_positive, soft_negative, weak_positive, notes = collect_signals(row)

    if hard_negative:
        group, decided_by = "unlikely", "hard_negative"
    elif strong_positive:
        group, decided_by = "likely", "strong_positive"
    elif soft_negative:
        group, decided_by = "unlikely", "soft_negative"
    elif weak_positive:
        group, decided_by = "likely", "weak_positive"
    else:
        group, decided_by = "uncertain", "no_signal"

    reasons = hard_negative + strong_positive + soft_negative + weak_positive + notes
    return pd.Series({"group": group, "decided_by": decided_by, "reasons": "; ".join(reasons)})


sample = pd.read_csv(DATA / "sample_300.csv", dtype=str, keep_default_na=False)
triaged = pd.concat([sample, sample.apply(decide, axis=1)], axis=1)

triaged.to_csv(DATA / "sample_triaged.csv", index=False)
for group in ["likely", "uncertain", "unlikely"]:
    triaged[triaged["group"] == group].to_csv(DATA / f"group_{group}.csv", index=False)

print("Companies per group:")
print(triaged["group"].value_counts().to_string())
print("\nWhich rule decided:")
print(triaged.groupby(["group", "decided_by"]).size().to_string())
print("\nMost common reasons:")
print(triaged["reasons"].str.split("; ").explode().value_counts().to_string())
print("\nGroup by accounts category:")
print(pd.crosstab(triaged["accounts_category"], triaged["group"]).to_string())
