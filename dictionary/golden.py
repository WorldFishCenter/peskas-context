"""Ask AskFish a few questions whose answers the dashboard's own pages show, and compare.

    python golden.py                          # the dashboard at http://localhost:3001
    python golden.py --url https://...        # another dashboard that has AskFish
    python golden.py --page-only              # only the page's figures, no AskFish call

Read-only: the page's figures come from the dashboard's public summaries procedures,
AskFish's answers from its askfish.ask procedure (one AI call per question). A question
passes when AskFish names the page's top group, or gives the page's figure within 2%.
Exit 1 if any fails. Standard library only.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

MONTHS = 12


def trpc(url, procedure, payload, post=False):
    body = json.dumps({"json": payload})
    if post:
        req = urllib.request.Request(f"{url}/api/trpc/{procedure}", body.encode(), {"content-type": "application/json"})
    else:
        req = urllib.request.Request(f"{url}/api/trpc/{procedure}?input={urllib.parse.quote(body)}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["result"]["data"]["json"]


def headline(metric):
    return lambda url: trpc(url, "summaries.headline", {"months": MONTHS})["metrics"][metric]["value"]


def top_district(metric):
    def page(url):
        rows = [r for r in trpc(url, "summaries.byDistrict", {"months": MONTHS}) if r[metric] is not None]
        return max(rows, key=lambda r: r[metric])["district"]

    return page


def top_taxon(url):
    rows = [r for r in trpc(url, "summaries.composition", {"months": MONTHS, "metric": "catch_kg"}) if r["taxon"]]
    return rows[0]["taxon"]


QUESTIONS = [
    ("Which district had the highest catch per unit effort over the last 12 months?", top_district("mean_cpue")),
    ("Which district had the highest revenue per unit effort over the last 12 months?", top_district("mean_rpue")),
    ("What was the average price per kg over the last 12 months?", headline("mean_price_kg")),
    ("What was the total estimated catch over the last 12 months?", headline("estimated_catch_tn")),
    ("How many landings were surveyed over the last 12 months?", headline("n_submissions")),
    ("Which species had the highest recorded catch over the last 12 months?", top_taxon),
]


def matches(answer, expected):
    if isinstance(expected, str):
        named = [answer["headline"]] + [s["label"] for s in answer["statistics"][:1]]
        return any(expected.lower() in text.lower() for text in named)
    return any(s["value"] is not None and abs(s["value"] - expected) <= 0.02 * abs(expected) for s in answer["statistics"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:3001")
    ap.add_argument("--page-only", action="store_true")
    args = ap.parse_args()
    url = args.url.rstrip("/")
    failed = 0
    for question, page in QUESTIONS:
        expected = page(url)
        print(f"{question}\n  page: {expected}")
        if args.page_only:
            continue
        try:
            answer = trpc(url, "askfish.ask", {"districts": [], "months": MONTHS, "lang": "en", "question": question}, post=True)
        except Exception as e:
            print(f"  AskFish: no answer ({e})\n  FAIL")
            failed += 1
            continue
        ok = matches(answer, expected)
        failed += not ok
        print(f"  AskFish: {answer['headline']}\n  {'ok' if ok else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
