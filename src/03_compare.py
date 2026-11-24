import pandas as pd

SOURCE = "BasicCompanyDataAsOneFile-2026-11-01.csv"

population = {}
total = 0

for chunk in pd.read_csv(SOURCE, dtype=str, chunksize=200_000, usecols=["Accounts.AccountCategory"]):
    for category in chunk["Accounts.AccountCategory"].fillna("(empty)"):
        population[category] = population.get(category, 0) + 1
        total += 1

sample = pd.read_csv("data/sample_300.csv", dtype=str).fillna("")
sample_counts = sample["accounts_category"].value_counts()

rows = []
for category, count in population.items():
    in_sample = sample_counts.get(category, 0)
    rows.append({
        "accounts_category": category,
        "population_count": count,
        "population_pct": round(count / total * 100, 1),
        "sample_count": in_sample,
        "sample_pct": round(in_sample / len(sample) * 100, 1),
    })

table = pd.DataFrame(rows).sort_values("population_count", ascending=False)
table.to_csv("data/population_vs_sample.csv", index=False)

print("Total companies:", total)
print(table.to_string(index=False))
