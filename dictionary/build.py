"""Build AskFish's semantic catalog from the data dictionary.

    python build.py           # write semantic-catalog.json
    python build.py --check   # exit 1 if semantic-catalog.json is out of date

Reads portal.odcs.json (the collections), metrics.json (the measures) and askfish.json
(what AskFish may query, its pages and limits). The catalog keeps the shape AskFish's
contract 1.0 validates, field for field. Standard library only.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "semantic-catalog.json"
ACROSS = {"month": "acrossTime", "district": "acrossDistrict", "gear": "acrossGear", "taxon": "acrossTaxon"}
COUNTS = {"landings", "trips"}


def load(name):
    return json.loads((HERE / name).read_text())


def custom(element, name, default=None):
    return next((c["value"] for c in element.get("customProperties", []) if c["property"] == name), default)


def discriminator(collection):
    """The property naming the measure in a long collection, or None for a wide one."""
    return next((p for p in collection["properties"] if "enum" in p), None)


def dimension_id(prop):
    return prop.get("businessName", prop["name"])


def metric_for(group, name):
    """The metric a collection's measure name stands for: its key, or its gear name."""
    if name in group:
        return name, group[name]
    return next((k, m) for k, m in group.items() if m.get("gear") == name)


def rollup(m, dim, weighted_by):
    if m["kind"] == "total":
        out = {"status": "allowed", "method": "sum"}
        if m["figure"] == "estimated":
            out["note"] = (
                "Adds up the district-months both methods estimate, as the pages do"
                " (every district-month this method estimates where the two share none)."
                if m.get("twin")
                else "Adds up only the district-months with an estimate."
            )
        return out
    if m["kind"] == "share":
        return {"status": "allowed", "method": "unweighted_mean", "note": m["caveats"][0]}
    if dim == "taxon":
        return {"status": "forbidden", "note": "Values of different taxa do not combine into one."}
    return {"status": "allowed", "method": f"weighted_mean_by_{m['weight']}", "note": weighted_by(m["weight"])}


def measure(m, dims, dictionary, weighted_by):
    label = m["label"]
    if m["figure"] == "estimated":
        label += f" ({dictionary['methods'][m['method']]['label']})"
    kind = "rate" if m["kind"] != "total" else "count" if m["unit"] in COUNTS else "total"
    return {
        "label": label,
        "aliases": m["synonyms"],
        "kind": kind,
        "unit": {"value": m["unit"], "status": "dictionary"},
        "nativeGrain": dims,
        "derivationStatus": "recorded" if m["figure"] == "recorded" else f"estimated_{m['method']}",
        "rollups": {ACROSS[d]: rollup(m, d, weighted_by) for d in dims},
    }


def dataset(collection, spec, contract, dictionary, ids):
    measured = discriminator(collection)
    keys = sorted((p for p in collection["properties"] if p.get("primaryKey")), key=lambda p: p["primaryKeyPosition"])
    grain = [dimension_id(p) for p in keys]
    dims = [d for d in grain if d != measured["name"]]
    group = dictionary["taxaMetrics" if collection["name"] == "taxa_summaries" else "metrics"]
    dimensions = {
        dimension_id(p): {"field": p["name"], "aliases": [s["synonym"] for s in p["synonyms"]]} for p in keys if p is not measured
    }
    dimensions[measured["name"]] = {"field": measured["name"], "aliases": ["metric", "measure", "indicator"]}

    def weighted_by(weight):
        w = dictionary["weights"][weight]
        source = ids[w["from"][collection["name"]]]
        keys = ", ".join(dims[:-1]) + " and " + dims[-1]
        return f"Weighted by {w['description']}: {w['measure']} of {source} at the same {keys}."

    return {
        "queryable": True,
        "lineage": "district",
        "collection": collection["physicalName"],
        "grain": grain,
        "layout": "long",
        "timeField": "date",
        "geographyKey": "gaul_2_name",
        "pageScopes": spec["pageScopes"],
        "access": spec["access"],
        "derivationStatus": "described_by_peskas_data_dictionary",
        "dimensions": dimensions,
        "measures": {
            e["value"]: measure(metric_for(group, e["value"])[1], dims, dictionary, weighted_by) for e in measured["enum"]
        },
        "bindings": {
            custom(s, "countryCode"): {
                "database": s["database"],
                "collection": collection["physicalName"],
                "status": "available",
                "observedDocuments": 0,
            }
            for s in contract["servers"]
        },
        "queryPolicy": {
            "maxRows": spec["maxRows"],
            "timeFilterStatus": "supported",
            "canonicalKey": grain,
            "duplicateResolution": "one_row_per_grain",
        },
        "caveats": custom(collection, "caveats", []),
    }


def build():
    contract, dictionary, askfish = load("portal.odcs.json"), load("metrics.json"), load("askfish.json")
    collections = {c["physicalName"]: c for c in contract["schema"]}
    ids = {spec["collection"]: name for name, spec in askfish["datasets"].items()}
    datasets = {
        name: dataset(collections[spec["collection"]], spec, contract, dictionary, ids)
        for name, spec in askfish["datasets"].items()
    }
    return {
        "catalogVersion": askfish["catalogVersion"],
        "contractVersion": "1.0",
        "status": "generated_from_peskas_data_dictionary",
        "sourceEvidence": {
            "repository": "peskas-context/dictionary",
            "liveMetadataAsOf": custom(contract, "checkedOnProd"),
            "limitations": custom(contract, "caveats")
            + [
                "Averages combine weighted, as the dashboard does: weighted_mean_by_landings and weighted_mean_by_catch name the weight in each rollup's note.",
                "observedDocuments is not maintained and reads 0.",
                "kenya_bmu_monthly and kenya_bmu_gear_monthly come from the Kenya BMU dashboard's own app database, outside the portal data dictionary.",
            ],
        },
        "scopeModes": askfish["scopeModes"],
        "countries": {
            custom(s, "countryCode"): {
                "name": custom(s, "countryName"),
                "iso3": custom(s, "iso3"),
                "currencyCode": custom(s, "currency"),
            }
            for s in contract["servers"]
        },
        "pageScopes": askfish["pageScopes"],
        "datasets": {**datasets, **askfish["extraDatasets"]},
        "discoveredSources": [],
        "geographicAlternatives": askfish["geographicAlternatives"],
    }


def render():
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    text = render()
    if sys.argv[1:] == ["--check"]:
        fresh = OUT.is_file() and OUT.read_text() == text
        print("semantic-catalog.json: " + ("up to date" if fresh else "out of date, run build.py"))
        sys.exit(0 if fresh else 1)
    OUT.write_text(text)
    print(f"wrote {OUT.name}")
