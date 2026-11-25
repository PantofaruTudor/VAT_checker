# UK VAT Identifier Discovery

Task: Can a dataset of UK company VAT numbers be built from the open web? This repository is my attempt to answer that on a random sample of 300 companies, and to be honest about where the idea works and where it breaks.


## Summary

I took 300 random UK companies from Companies House and tried to find their VAT numbers on their websites, first with a script and then by hand for 60 of them. Every number found was checked on the HMRC website.

- **The script** found a correct VAT number for **1 company in 300**. **Searching by hand** found **1 in 60**.
- **The problem is the source, not the method.** Most small companies don't put their VAT number on their website, so a better script, a search API or a team of people all hit the same limit. Even an improved method would find a number for only about 5–15% of companies.
- **A valid number is often not the company's own.** 3 of the 5 valid numbers I found belonged to other companies (one with a similar name in another town, two using a brand name), and 1 was the number of a VAT group. Comparing the name HMRC gives back catches these mistakes.

My conclusion: a VAT dataset for small UK companies can't be built well from the open web. Websites can fill a small part of the problem, but most of it needs other sources, like asking the customer directly.

---

## Part 1: Research

### Understanding the problem first

The problem has two sides:

1. **Should this company have a VAT number at all?** If not, "not found" is the right answer, not a failure.
2. **Is the number I found really this company's?** A wrong number is worse than a missing one, because nobody can see it is wrong.

#### Question 1: which companies should have a VAT number

Three rules decide it:

1. **Turnover.** A company must register when its taxable sales go over £90,000 in 12 months. Below that it can still register if it wants to.
2. **Exempt activity.** A company that only sells VAT-exempt things (insurance, finance, education, healthcare, membership subscriptions) cannot register at all, however big it is. Property is exempt too, but property companies can choose to pay VAT
3. **VAT groups.** Companies owned by the same parent can share one VAT number. HMRC then shows the name of the main company of the group, not the one I was looking for.

#### Question 2: attaching a number to the right company

HMRC's checker shows the name and address behind a VAT number. I compare them with Companies House:

- **The name** is the main check. It must match after cleaning (removing dots, Ltd = Limited), against the active or the previous name.
- **The postcode** helps when two companies have similar names, like "J Smith Building Services Ltd" and "J Smith Builders Ltd".

But a postcode is only useful if few companies use it. If 3 companies share a postcode, a match is strong evidence. If 89,013 do (a virtual office in London), a match proves almost nothing. So for every company I count how many others share its postcode (`postcode_shared_by`).

It can also go wrong the other way. HMRC usually has the address where the company works. Companies House has the official address, which is often an accountant or a virtual office. So a correct number can come back with a different postcode. The postcode helps the name check. It never replaces it.

### What Companies House gives you, and what it doesn't

The free monthly file (`BasicCompanyDataAsOneFile-2026-11-01.csv`, 2.8 GB) has name, number, official address, SIC codes, accounts category, status, mortgages and previous names. It has **no websites, no turnover, no employee count and no VAT numbers**.

Things that were not obvious at the start:

- **The file has 5,711,779 companies, not ~4.2 million.** It also counts companies about to be closed (7.3%) and companies in liquidation (1.9%).
- **There is no turnover, so I could not filter on £90,000.** The closest thing is the accounts category, and it is only a rough sign: a very small company can choose to file bigger accounts.
- **Micro companies are the hardest part.** They are the biggest group (32% of all companies) and their sales can be anywhere from £0 to about £1 million. The £90,000 line is right in the middle, so the category tells me nothing.
- **SIC codes are chosen by the company and nobody checks them.** In one test a large charity with GROUP accounts had the code for "non-trading company". I only use SIC as a weak sign.

### Where a VAT number can be found

| Source | Has the VAT number? | Works for 40,000 companies? | Status |
|---|---|---|---|
| VAT registration certificate (VAT4) | Yes, but only the company has it | No | Ruled out |
| Invoices | Yes, but only the customer sees them | No | Ruled out - public PDFs not tested yet |
| Company website | Sometimes | Partly | **Tested, see Part 2** |
| Amazon / eBay seller pages | Sometimes | Terms of use may make it illegal | Not tested: their terms don't allow collecting data automatically, so it can't be used in a product |
| EORI number | Yes, it contains the VAT number | No | Not useful: the EORI checker also needs the number first, so it can only confirm, not find |
| findvatnumber.com | Claims to, for "6M+ companies", but does not say where its data comes from | Unknown | Not tested: excluded because the source of its data is unknown |

**Why websites are the main source.** UK law requires a company that sells online to show its VAT number. It also requires every company to show its Companies House number on its website. That second rule was the most useful thing I found: it lets me **prove a website belongs to a company**, which a similar name cannot.

### Checking numbers: the HMRC API

HMRC's API confirms a VAT number and shows the name and address behind it. It cannot search by name. Getting access takes an approval of up to 10 working days, so for this project I used the free web checker (gov.uk/check-uk-vat-number) by hand. For Veridion this is a one-time setup: the limit is 3 checks per second, so 40,000 numbers take about 4 hours.

### Dead ends and ideas that did not hold

- **Company websites as the main source of VAT numbers.** I expected websites to be the best source, because UK law requires online sellers to show their VAT number. In practice, of 17 company websites that I could link to a company by hand, only 1 showed a VAT number. Most small companies don't show it, or don't sell online. The law only requires the VAT number from VAT-registered companies that sell or offer services online, many small companies only have a simple website, and the rule is rarely seen in action. Even the company number, which every company website must show, appeared on only 4 of the 17 sites I could link to a company. See Part 2.
- **"Companies at shared addresses are smaller."** I expected companies at busy postcodes to be smaller and less likely to have VAT. On 300 companies the groups looked the same at busy and quiet postcodes.

---

## Part 2: Proof of concept

### The sample

I drew **300 companies completely at random** from all 5 million (`src/01_sample.py`). The seed is fixed (42), so anyone running the script gets the same 300.

I did **not** pick companies I knew published their VAT number, and I did not remove dormant or micro companies. The point is to measure everything.
| Accounts category | All companies | Sample |
|---|---|---|
| MICRO ENTITY | 32.9% | 31.7% |
| NO ACCOUNTS FILED | 25.7% | 23.7% |
| TOTAL EXEMPTION FULL | 23.5% | 21.0% |
| DORMANT | 10.9% | 16.7% |
| Others | under 3% each | |

Full table: `data/population_vs_sample.csv`.

- **There are more dormant companies than expected** (16.7% against 10.9%). With eight other seeds it came out between 8% and 13%, so seed 42 was just unlucky. I kept it, because changing the seed after seeing the result would mean picking the sample by its result.
- **Large companies are almost missing** (1 FULL, 0 MEDIUM). I think they are the easier case anyway: they publish their VAT number more often, and the customer probably has them already (see "What these numbers don't capture").

### Triage: which companies should have a VAT number?

Before searching, I sorted the 300 companies into three groups (`src/04_triage.py`). I still search **all** of them. The groups show whether my expectations match the results.

| Group | Who is in it | Companies |
|---|---|---|
| likely | FULL / MEDIUM / GROUP accounts, PLC, small-company accounts, has a mortgage, LLP | 84 |
| uncertain | Micro companies, new companies with no accounts yet | 98 |
| unlikely | Dormant, only exempt SIC codes, holding company, not active, late filings, charity | 118 |


### Finding websites automatically

`src/05_find_websites.py`, a simple web scraper:

1. **Guess the domain from the name.** Remove words like ltd, limited, the, uk, and join the rest: `NIGHT EXCHANGE LIMITED` → `nightexchange.co.uk`, `nightexchange.com`.
2. **Take the first domain that answers.**
3. **Read six pages:** home, contact, contact-us, about-us, terms, privacy-policy.
4. **Check the site belongs to the company:** look for the company number (strong proof) or the postcode (good proof). Otherwise mark it `not_confirmed`.
5. **Look for a VAT number:** the word "VAT" followed by 9 digits.
6. **Run the HMRC check** to drop numbers that are not VAT numbers, like phone numbers.

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

| Group | Companies | Domain answered | VAT candidate |
|---|---|---|---|
| likely | 84 | 28 (33%) | 2 (2.4%) |
| uncertain | 98 | 50 (51%) | 1 (1.0%) |
| unlikely | 118 | 48 (41%) | 2 (1.7%) |

These numbers are too small to draw conclusions yet.

I checked the four numbers that passed the checksum on the HMRC website:

| Company in my sample | HMRC says the number belongs to | Result |
|---|---|---|
| MOORLAND ASSET FINANCE LTD | MOORLAND ASSET FINANCE LIMITED | Correct |
| WILLIAMS LETTINGS MERTHYR LTD | WILLIAMS LETTINGS LIMITED (a different company in Rhyl) | Wrong company |
| IMPULSE SECURITY SYSTEMS LIMITED | SPY ALARMS LIMITED ("Impulse Security Systems" is their brand) | Wrong company |
| ORBITS IT GROUP EOT LIMITED | ORIGINAL BUSINESS IT SOLUTIONS LTD ("ORBITS" is their short name) | Wrong company |

After fixing the leading-zero check (websites often write `8756469` for company `08756469`), a second full run confirmed 14 sites instead of 13. The other results were the same. One limit remains: it only tries `https://www.`, so sites that work only without `www` are missed.

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

I searched 60 companies by hand (20 per group, `data/manual_check.xlsx`): Google search, open the most likely site, check it belongs to the company, look for a VAT number. It took 124 minutes, about **2 minutes per company**. Then I compared my results with the script (first run) on the same 60 companies.

| | By hand | Script |
|---|---|---|
| Websites found | 32 | 23 domains answered |
| Really the company's | 17 with some proof (7 strong, 10 name + activity) | 6, the same sites I found |
| Wrong websites | – | 17, all marked `not_confirmed` |
| VAT numbers found | 1 (RMS) | 0 |

**A person is much better at finding the site.** The script found the right website for only 6 of my 32. It cannot guess brand names (RMS Estate Agents uses `rookmatthewssayer.co.uk`), small changes (`desmouk.co.uk`, `dreamhome4u.co.uk`), hyphens (`esi-building.co.uk`), abbreviations (`seschester.co.uk`) or other endings (`structify.ai`, `.org.uk`).

**The script is better and more consistent at checking it.** It never accepted a wrong website: all 17 were marked `not_confirmed`. On the same site it was sometimes more careful than me: it found the company number on Haywood Recruitment's site, which I missed, and confirmed two sites by postcode that I had only matched by name. It reads the same pages every time; a person in a hurry does not.

So the best method combines them: a search (by a person or a search API) to find the site, then an automatic check of company number, postcode and VAT number.

**The most important finding: even with the right website, the VAT number is rarely there.** I had 17 sites with some proof of ownership and found only 1 VAT number among them. In the script's first run, 2 of 13 confirmed sites had one. **Small UK companies mostly don't put their VAT number on their website, whoever does the search.** For the small companies the customer is missing, websites are a weak source.

**Would a better script help?** About 7 of the 26 websites I found and the script missed could be caught with simple extra rules (no `www`, hyphens, "uk" added to the name, dropping the last word). The other 18 use trading names or abbreviations that can't be guessed. So better guessing could roughly double the websites found, but because so few small company websites show a VAT number, it would add only 1–2 VAT numbers on 300 companies. **The limit is the source, not the script.**

The triage also held up: websites with strong proof (company number or directors) were found for 6 of 20 "likely" companies, 1 of 20 "uncertain" and 0 of 20 "unlikely".

### False-positive rate

I found 6 VAT numbers in total: 5 by the script and 1 by hand. With so few, I checked every one by hand on the HMRC website.

- 1 failed the checksum, so it was not a real VAT number.
- The other 5 were all valid at HMRC.
- But only **1** of them belonged to the company I was looking for (Moorland).
- **3** belonged to other companies: a company with almost the same name in another town, and two companies whose brand name matched my company's name.
- **1** (RMS) is the number of a VAT group. It is the right number to use for RMS invoices, but HMRC shows the group's name, not RMS.

So if I had trusted every valid number found on a matching website, **3 of 5 would have been wrong**. After comparing the name HMRC gives back, **none of the wrong ones get through**.

The lesson: **"valid at HMRC" does not mean "belongs to this company".** The name check is what stops the hidden mistakes. Even a website the script had confirmed (Orbits IT) showed another company's number.

This is only 5 numbers, so the exact percentage means little. What matters is that the mistake and easy to catch.

### What these numbers don't capture

- **Large companies.** My random sample has almost none (1 FULL, 0 MEDIUM). I think this is fine: large companies publish their VAT number more often, and the customer probably already has them. The real problem is the small and medium companies, and that is what the sample covers.
- **"Not found" is still two things.** It can mean "not registered for VAT" or "registered, but not published anywhere I looked". From the outside there is no way to tell them apart.
- **Only one source was tested properly: websites.** The other ways to get the number are official documents (invoices, contracts), which are not public and hard to find, or asking each company directly. Asking works best for the customer, who already works with these suppliers and gets a reply.
- **Small numbers.** 300 companies, 60 searched by hand, 6 VAT numbers found. The percentages are only a rough guide, but the result is clear: small company websites rarely show a VAT number, and a valid number is often not the company's own.

---

## Part 3: What I would do with real resources

### Coverage and accuracy

My test showed that the biggest problem is not the script but the source: most small companies don't put their VAT number on their website. So with more resources, my first step would be to find **better sources** for websites and VAT numbers, and only then improve the scripts and the manual checks.

On websites alone, the ceiling is low. If a search API found the right website for 75% of companies, and 6–8% of confirmed websites show a correct VAT number (as in my test), I would find a number for about 0.75 × 6–8% ≈ **5–6% of companies**. With a better scraper and a paid team checking more carefully, I think it could reach **at most about 15%**.

Accuracy is easier to keep high. The checks I already use (checksum, then comparing the HMRC name and postcode) stopped all 3 wrong numbers out of 5 in my test. At scale they would run automatically, with a person only for the unclear cases.

### Rough cost per company

The cost per company is: search API + downloading the pages + HMRC check (free) + a person checking the unclear cases. Prices used: a search API at about $5 (€4.3) per 1,000 searches (Brave), a team in Romania paid between the minimum wage (about €5 per hour) and about €10 per hour, and 2 minutes per company, which is what my manual search took. The customer is missing VAT numbers for about 26,700 suppliers.

*With my current method.* The script costs under 1 cent per company (about €300 in total) but finds a correct VAT number for only 0.3% of companies, about €3 per number. Searching by hand finds 1.7%, but costs €4,500–8,800, or €10–20 per number.

*With an improved method.* At about €0.05–0.09 per company (€1,300–2,400 in total) and 5–15% of companies found, that is €0.30–2 per number.

So better tools make each number much cheaper, but even the improved method finds a VAT number for only 5–15% of the missing suppliers. The cost is not the problem. The source is. For the rest, the customer needs other sources: the invoices they already received from these suppliers, or simply asking the suppliers directly.

### What breaks first

1. **Matching numbers to companies.** It is the most dangerous, because the mistake is hard to see: in my test 3 of 5 valid numbers belonged to other companies (sister companies, brand names, VAT groups). At scale there will be many more of these cases.
2. **Finding the website.** It is the biggest loss: the script found the right website for only 6 of the 32 I found by hand.
3. **The search API limits.** These can be solved with money.

### What I would monitor in production

Mainly the accuracy of the data:
- how many numbers pass every check (checksum, HMRC name and postcode)
- how many numbers match a parent or sister company instead of the company itself
- how many numbers become invalid at the monthly recheck
- how many web requests fail, because a lost connection looks exactly like "no website found"

## Debate topics

**Trying every valid number on HMRC's checker.** A UK VAT number has 9 digits, and the last 2 are check digits, so only 7 are free: about 10 million numbers, or up to about 20 million with both checksum formulas. At 3 checks per second that is about 39 days non-stop (77 days for both). So it is possible, but a bad idea. HMRC can block access, and then we lose the only way to check our data. 

**Keeping the dataset current.**
Once a month I would check all 40,000 numbers again with the HMRC API. A full check takes about 4 hours (3 checks per second), so doing it monthly costs almost nothing. I used the HMRC website by hand in this project because getting API access takes up to 10 working days, but at scale the API is the right tool.

Every change goes into a separate table first, not straight into the main dataset. I look at the changes there and then decide what to do:
- the number is no longer valid → the company stopped being VAT registered, so I remove the number
- HMRC shows a new name → I check the match again
- a company now has a website → I search it again, maybe the VAT number is there now

New companies from the monthly Companies House file go on a separate list. I search them again after a few months, because a new company usually registers for VAT only when its sales grow, and its website comes later too.

**Knowing the dataset is wrong at scale.**
There is no complete list to compare with, except one: the customer already has VAT numbers for about a third of their suppliers. I would run my method on those suppliers too, without looking at their numbers, and then compare. Where my number differs from theirs, one of us is wrong, and I can check by hand which one. This is the only real test with known answers, and I would repeat it every time the method changes.

**Sources I would not use in a product.**
- **findvatnumber.com.** It does not say where its data comes from. I can't sell data when I don't know its source or whether it is allowed to be reused.
- **Amazon and eBay seller pages.** Their terms usually don't allow collecting data automatically.



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


Use of AI. I used Claude throughout this project: to help with writing some parts of the scripts, to look up for rules and prices, to double check informations, and to visually improve this README so it could be easier to read. The approach and the decisions are mine: what to sample and how to group it, searching 60 companies by hand to measure the script, the rules used to match a VAT to a company, which sources to drop, and the conclusion that the source, not the script, is the limit. I checked every number in this README against the data.
