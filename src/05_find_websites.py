import re
import time

import pandas as pd
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (student research project on UK VAT numbers)"}
TIMEOUT = 8
ENDINGS = [".co.uk", ".com"]
PAGES = ["", "/contact", "/contact-us", "/about-us", "/terms", "/privacy-policy"]
REMOVE_WORDS = {"ltd", "limited", "plc", "llp", "uk", "the", "and", "co", "company", "group"}
VAT_PATTERN = re.compile(r"VAT[^0-9]{0,40}((?:GB)?\s?\d{3}\s?\d{4}\s?\d{2})", re.IGNORECASE)


def clean_words(name):
    name = name.lower().replace("&", " ")
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return [word for word in name.split() if word not in REMOVE_WORDS]


def candidate_domains(name):
    words = clean_words(name)
    if not words:
        return []

    bases = ["".join(words)]
    if len(words) > 2:
        bases.append("".join(words[:2]))

    domains = []
    for base in bases:
        for ending in ENDINGS:
            domains.append(base + ending)
    return domains


def download(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return ""


def page_text(html):
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def find_vat_numbers(text):
    numbers = []
    for match in VAT_PATTERN.findall(text):
        digits = re.sub(r"\D", "", match)
        if len(digits) == 9 and digits not in numbers:
            numbers.append(digits)
    return numbers


def checksum_ok(vat):
    weights = [8, 7, 6, 5, 4, 3, 2]
    total = 0
    for digit, weight in zip(vat[:7], weights):
        total += int(digit) * weight
    total += int(vat[7:])
    return total % 97 == 0 or (total + 55) % 97 == 0


def number_on_page(compact, company_number):
    without_zeros = company_number.lstrip("0")
    versions = [company_number]
    if len(without_zeros) >= 6:
        versions.append(without_zeros)

    for version in versions:
        if re.search(r"(?<!\d)" + version + r"(?!\d)", compact):
            return True
    return False


def check_site(text, company_number, postcode):
    compact = text.upper().replace(" ", "")
    if company_number and number_on_page(compact, company_number):
        return "company_number"
    if postcode and postcode.upper().replace(" ", "") in compact:
        return "postcode"
    return "not_confirmed"


sample = pd.read_csv("data/sample_triaged.csv", dtype=str).fillna("")
results = []

for index, company in sample.iterrows():
    print(f"{index + 1}/{len(sample)} {company['name']}")

    result = {
        "name": company["name"],
        "company_number": company["company_number"],
        "group": company["group"],
        "website": "",
        "site_check": "",
        "vat_numbers": "",
        "vat_checksum_ok": "",
        "vat_page": "",
    }

    for domain in candidate_domains(company["name"]):
        url = "https://www." + domain
        if download(url):
            result["website"] = url
            break

    if result["website"]:
        all_text = ""
        for page in PAGES:
            text = page_text(download(result["website"] + page))
            all_text += " " + text

            numbers = find_vat_numbers(text)
            if numbers and not result["vat_numbers"]:
                result["vat_numbers"] = "; ".join(numbers)
                result["vat_checksum_ok"] = "; ".join(str(checksum_ok(n)) for n in numbers)
                result["vat_page"] = result["website"] + page
            time.sleep(0.5)

        result["site_check"] = check_site(all_text, company["company_number"], company["postcode"])

    results.append(result)

table = pd.DataFrame(results)
table.to_csv("data/websites_auto.csv", index=False)

print("\nWebsite found:", (table["website"] != "").sum())
print("Website confirmed:", table["site_check"].isin(["company_number", "postcode"]).sum())
print("VAT number found:", (table["vat_numbers"] != "").sum())
print("\nBy group:")
print(table.assign(
    site_found=table["website"] != "",
    vat_found=table["vat_numbers"] != "",
).groupby("group")[["site_found", "vat_found"]].sum())
