# UK VAT Identifier Discovery

Task: Can a dataset of UK company VAT numbers be built from the open web? This repository is my attempt to answer that on a random sample of 300 companies, and to be honest about where the idea works and where it breaks.

> **Status:** work in progress. Sections marked **TODO** are not done yet.

## Summary

> TODO: write last. 5–6 lines: what I tried, the main number, the conclusion.

---

## Part 1: Research

### Understanding the problem first

The problem has two separate questions:

1. **Should this company have a VAT number at all?** If not, "not found" is the right answer, not a failure.
2. **Is the number I found really this company's?** A wrong number is worse than a missing one, because nobody can see it is wrong.

#### Question 1: which companies should have a VAT number

Three rules decide it:

1. **Turnover.** A company must register when its taxable sales go over £90,000 in 12 months. Below that it can still register if it wants to.
2. **Exempt activity.** A company that only sells VAT-exempt things (insurance, finance, education, healthcare, membership subscriptions) cannot register at all, however big it is. Property is exempt too, but property companies can choose to pay VAT, and many do.
3. **VAT groups.** Companies owned by the same parent can share one VAT number. HMRC then shows the name of the main company of the group, not the one I was looking for.

#### Question 2: attaching a number to the right company

HMRC's checker shows the name and address behind a VAT number. I compare them with Companies House:

- **The name** is the main check. It must match after cleaning (removing dots, Ltd = Limited), against the current or a previous name.
- **The postcode** helps when two companies have similar names, like "J Smith Building Services Ltd" and "J Smith Builders Ltd".

But a postcode is only useful if few companies use it. If 3 companies share a postcode, a match is strong evidence. If 89,013 do (a virtual office in London), a match proves almost nothing. So for every company I count how many others share its postcode (`postcode_shared_by`).

It can also go wrong the other way. HMRC usually has the address where the company works. Companies House has the official address, which is often an accountant or a virtual office. So a correct number can come back with a different postcode. The postcode helps the name check. It never replaces it.

### What Companies House gives you, and what it doesn't

The free monthly file (`BasicCompanyDataAsOneFile-2026-11-01.csv`, 2.8 GB) has name, number, official address, SIC codes, accounts category, status, mortgages and previous names. It has **no websites, no turnover, no employee count and no VAT numbers**.

Things that were not obvious at the start:

- **The file has 5,711,779 companies, not ~4.2 million.** It also counts companies about to be closed (7.3%) and companies in liquidation (1.9%).
- **There is no turnover, so I could not filter on £90,000.** The closest thing is the accounts category, and it is only a rough sign: a very small company can choose to file bigger accounts.
- **Micro companies are the hardest part.** They are the biggest group (32.9% of all companies) and their sales can be anywhere from £0 to about £1 million. The £90,000 line is right in the middle, so the category tells you nothing.
- **SIC codes are chosen by the company and nobody checks them.** In one test a large charity with GROUP accounts had the code for "non-trading company". I only use SIC as a weak sign.

### Where a VAT number can be found

| Source | Has the VAT number? | Works for 40,000 companies? | Status |
|---|---|---|---|
| VAT registration certificate (VAT4) | Yes, but only the company has it | No | Ruled out |
| Invoices | Yes, but only the customer sees them | No | Ruled out (public PDFs not tested yet) |
| Company website | Sometimes | Partly | **Tested, see Part 2** |
| Amazon / eBay seller pages | Sometimes | Terms of use may forbid it | TODO |
| EORI number | Yes, it contains the VAT number | Unknown | TODO |
| findvatnumber.com | Claims to, for "6M+ companies", but does not say where its data comes from | Unknown | TODO |
| Common Crawl | Unknown | Yes | TODO |
| Public procurement and spend data | Unknown | Unknown | TODO |

**Why websites are the main source.** UK law requires a company that sells online to show its VAT number. It also requires every company to show its Companies House number on its website. That second rule was the most useful thing I found: it lets me **prove a website belongs to a company**, which a similar name cannot.

### Checking numbers: the HMRC API

HMRC's API confirms a VAT number and shows the name and address behind it. It cannot search by name. Getting access takes an approval of up to 10 working days, so for this project I used the free web checker (gov.uk/check-uk-vat-number) by hand. For Veridion this is a one-time setup: the limit is 3 checks per second, so 40,000 numbers take about 4 hours.

### Dead ends and ideas that did not hold

- **"Companies at shared addresses are smaller."** I expected companies at busy postcodes (accountants, virtual offices) to be smaller and less likely to have VAT. On 300 companies the groups looked the same at busy and quiet postcodes, so I found no link.

> TODO: add the other sources as I test them, each with what I expected, what I ran and why it failed.

---

## Part 2: Proof of concept

### The sample

I drew **300 companies completely at random** from all 5,711,779 (`src/01_sample.py`). The seed is fixed (42), so anyone running the script gets the same 300.

I did **not** pick companies I knew published their VAT number, and I did not remove dormant or micro companies. The point is to measure everything, including the hard part.

| Accounts category | All companies | Sample |
|---|---|---|
| MICRO ENTITY | 32.9% | 31.7% |
| NO ACCOUNTS FILED | 25.7% | 23.7% |
| TOTAL EXEMPTION FULL | 23.5% | 21.0% |
| DORMANT | 10.9% | 16.7% |
| Others | under 3% each | |

Full table: `data/population_vs_sample.csv`.

- **There are more dormant companies than expected** (16.7% against 10.9%). With eight other seeds it came out between 8% and 13%, so seed 42 was just unlucky. I kept it, because changing the seed after seeing the result would mean picking the sample by its result.
- **Large companies are almost missing** (1 FULL, 0 MEDIUM). I think they are the easier case anyway: they publish their VAT number more often, and the customer probably has them already. TODO: test on 20–30 large companies.

### Triage: which companies should have a VAT number?

Before searching, I sorted the 300 companies into three groups (`src/04_triage.py`). I still search **all** of them. The groups show whether my expectations match the results.

| Group | Who is in it | Companies |
|---|---|---|
| likely | FULL / MEDIUM / GROUP accounts, PLC, small-company accounts, has a mortgage, LLP | 84 |
| uncertain | Micro companies, new companies with no accounts yet | 98 |
| unlikely | Dormant, only exempt SIC codes, holding company, not active, late filings, charity | 118 |


Decisions that can be argued with:
- TOTAL EXEMPTION FULL counts as "likely". This is the weakest rule: 53 of the 84 "likely" companies are here, and very small companies can file this way too.
- SIC 68 (property) is **not** treated as exempt, because property companies can choose to pay VAT.
- SIC 85 (education) **is** treated as exempt, although private training is often taxed.

### Finding websites automatically

`src/05_find_websites.py`, kept simple on purpose:

1. **Guess the domain from the name.** Remove words like ltd, limited, the, uk, and join the rest: `NIGHT EXCHANGE LIMITED` → `nightexchange.co.uk`, `nightexchange.com`.
2. **Take the first domain that answers.**
3. **Read six pages:** home, contact, contact-us, about-us, terms, privacy-policy.
4. **Check the site belongs to the company:** look for the company number (strong proof) or the postcode (good proof). Otherwise mark it `not_confirmed`.
5. **Look for a VAT number:** the word "VAT" followed by 9 digits.
6. **Run the HMRC checksum** to drop numbers that are not VAT numbers, like phone numbers.

### Results so far

```
300 companies
 └─ 126 had a guessed domain that answered            (42%)
     └─ 13 sites confirmed as the company's own        (4.3% of 300)
         └─ 2 of those showed a VAT number
     + 3 VAT numbers on sites that could not be confirmed
```

- **Most "found" websites are not the company's.** Only 13 of 126 showed the company number or postcode. The rest are parked domains, other companies with a similar name, or sites that don't show their company number. **Without the ownership check, about 9 in 10 found websites would be wrong or unproven.**
- **Even confirmed sites rarely show a VAT number:** 2 of 13.

| Company | Group | Site confirmed? | Checksum | What it means |
|---|---|---|---|---|
| MOORLAND ASSET FINANCE LTD | likely | Yes, company number | Pass | Best candidate |
| ORBITS IT GROUP EOT LIMITED | unlikely | Yes, postcode | Pass | Probably belongs to a sister company |
| IMPULSE SECURITY SYSTEMS LIMITED | unlikely | No | Pass | Probably belongs to someone else |
| WILLIAMS LETTINGS MERTHYR LTD | likely | No | Pass | The site may be another "Williams Lettings" |
| SERELLE GEMS LTD | uncertain | No | **Fail** | Dropped |

Two of these are exactly the hidden error the task warns about:
- **ORBITS IT GROUP EOT LIMITED** is a holding company that does not trade. The website is at the same address, but the VAT number almost certainly belongs to the company that does the actual work.
- **IMPULSE SECURITY SYSTEMS LIMITED** is dormant, yet a website with the same name shows a VAT number. The number probably belongs to someone else using the same name.

My triage had put both in "unlikely".

| Group | Companies | Domain answered | VAT candidate |
|---|---|---|---|
| likely | 84 | 28 (33%) | 2 (2.4%) |
| uncertain | 98 | 50 (51%) | 1 (1.0%) |
| unlikely | 118 | 48 (41%) | 2 (1.7%) |

These numbers are too small to draw conclusions yet.

> TODO: HMRC results for the four candidates that passed the checksum.

### Matching a VAT number to the right company

When HMRC shows a name and address for a number:

1. **Accept** if the cleaned name is the same as the current or a previous Companies House name.
2. **Accept** if the name is very similar, the postcode matches, at most 20 companies use that postcode, and no other company there has a similar name. Above 20, the postcode stops helping: 30% of my sample companies at such postcodes had a similar-named company at the same address, against 9% below 20. There, only rule 1 applies.
3. **Check by hand** if the name is only partly similar (trading names, extra words).
4. **Flag as a possible VAT group** if HMRC shows another company with the same root name (ABC Holdings for ABC Manufacturing). Do not attach it.
5. **Reject** if both the name and the postcode are different. The number belongs to someone else, like the accountant or the web agency.

Two safety rules:
- If two companies match equally well, leave it empty.
- Never copy a VAT number to a sister company with a similar name at the same address.

### Manual search: measuring the automatic method

> TODO: 60 companies (20 per group, `data/manual_check.xlsx`) searched by hand, 4 minutes max per company. Then compare with the script: websites found, wrong websites, VAT numbers found, HMRC confirmations, time per company.

### False-positive rate

> TODO: every accepted number checked with HMRC, then a hand check of accepted matches. Report the rate, how it was measured and on how many companies.

### What these numbers don't capture

> TODO

---

## Part 3: What I would do with real resources

> TODO. Notes so far:
> - HMRC API: one-time approval, 3 checks per second, about 4 hours for 40,000 numbers.
> - Guessing domains is free but finds a confirmed website for only 4.3% of companies. A search API would find more, at a cost per search (TODO: price it).
> - The time per company from the manual test gives the cost of a team doing it by hand.
> - First thing to ask the customer: the third of suppliers they already have VAT numbers for. It shows what their suppliers look like, and gives us known answers to test against.

---

## Debate topics

**Trying every valid number on HMRC's checker.** A UK VAT number has 9 digits, and the last 2 are check digits, so only 7 are free: about 10 million numbers, or up to about 20 million with both checksum formulas. At 3 checks per second that is about 39 days non-stop (77 days for both). So it is possible, but a bad idea. HMRC can block access, and then we lose the only way to check our data. It would also build a list of names and addresses that includes sole traders, which is a data protection problem for a company that sells data.

**Keeping the dataset current.** TODO

**Knowing the dataset is wrong at scale.** TODO

**Sources I would not be comfortable using in a product.** TODO (marketplace terms of use, sources that don't say where their data comes from, like findvatnumber.com)

## Beyond the UK

> TODO (optional)

---

## How to run

Download `BasicCompanyDataAsOneFile-2026-11-01.zip` from Companies House (download.companieshouse.gov.uk/en_output.html) and unzip it in the repository folder. It is not in the repository because it is 2.8 GB.

```
pip3 install pandas requests openpyxl
python3 src/01_sample.py
python3 src/02_postcodes.py
python3 src/03_compare.py
python3 src/04_triage.py
python3 src/05_find_websites.py
python3 src/06_manual_subset.py
```

| Script | What it does | Output |
|---|---|---|
| `01_sample.py` | Picks 300 random companies (seed 42) | `data/sample_300.csv` |
| `02_postcodes.py` | Counts how many companies share each postcode | adds `postcode_shared_by` |
| `03_compare.py` | Compares the sample with all companies | `data/population_vs_sample.csv` |
| `04_triage.py` | Sorts companies into likely / uncertain / unlikely | `data/sample_triaged.csv`, `data/group_*.csv` |
| `05_find_websites.py` | Guesses domains, checks ownership, looks for VAT numbers | `data/websites_auto.csv` |
| `06_manual_subset.py` | Picks 60 companies for the manual search | `data/manual_check.xlsx` |
