"""Check the data dictionary, and that the dashboard agrees with it.

    uv run --with jsonschema check.py                      # dashboard next to peskas-context
    uv run --with jsonschema check.py --dashboard PATH     # dashboard checked out elsewhere
    uv run --with jsonschema check.py --self-test

Checks that portal.odcs.json is valid ODCS v3.2.0 and metrics.json valid against
metrics.schema.json; that every measure a collection carries has a definition and the
reverse; that semantic-catalog.json is up to date; and that the dashboard's metrics.ts
(read with Node) and English locale texts match the metrics. Exit 1 on any problem.
"""

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

import build

HERE = Path(__file__).resolve().parent


def schema_problems(contract, metrics):
    odcs = json.loads((HERE / "odcs-json-schema-v3.2.0.json").read_text())
    own = json.loads((HERE / "metrics.schema.json").read_text())
    found = [("portal.odcs.json", e) for e in jsonschema.Draft201909Validator(odcs).iter_errors(contract)]
    found += [("metrics.json", e) for e in jsonschema.Draft202012Validator(own).iter_errors(metrics)]
    return [f"{name} {'/'.join(map(str, e.path))}: {e.message[:200]}" for name, e in found]


def dictionary_problems(contract, metrics):
    problems = []
    shared, used = {}, {"metrics": set(), "taxaMetrics": set()}
    for c in contract["schema"]:
        for p in c["properties"]:
            if "businessName" not in p:
                continue
            p = {k: v for k, v in p.items() if k not in ("primaryKey", "primaryKeyPosition")}
            if p["name"] in shared and shared[p["name"]] != p:
                problems.append(f"{c['name']}.{p['name']} is defined differently in another collection")
            shared.setdefault(p["name"], p)
        measured = build.discriminator(c)
        if not measured:
            continue
        group = "taxaMetrics" if c["name"] == "taxa_summaries" else "metrics"
        for e in measured["enum"]:
            try:
                key, m = build.metric_for(metrics[group], e["value"])
            except StopIteration:
                problems.append(f"{c['name']} carries {e['value']}, which {group} does not define")
                continue
            used[group].add(key)
            if m.get("weight") and c["name"] not in metrics["weights"][m["weight"]]["from"]:
                problems.append(f"{key}: weight {m['weight']} names no source for {c['name']}")
    for group, defined in metrics.items():
        if group not in used:
            continue
        for key, m in defined.items():
            if key not in used[group]:
                problems.append(f"{group}.{key} is in no collection")
            if m.get("weight") and m["weight"] not in metrics["weights"]:
                problems.append(f"{key}: unknown weight {m['weight']}")
            if m.get("method") and m["method"] not in metrics["methods"]:
                problems.append(f"{key}: unknown method {m['method']}")
            twin = defined.get(m.get("twin", ""), {})
            if m.get("twin") and (twin.get("twin") != key or twin.get("unit") != m["unit"] or twin.get("method") == m.get("method")):
                problems.append(f"{key}: twin {m['twin']} must point back, share its unit and use the other method")
    return problems


def dashboard_problems(dashboard, contract, metrics):
    dashboard = dashboard.resolve()
    source = dashboard / "packages/domain/src/metrics.ts"
    locale = dashboard / "apps/isomorphic-i18n/src/i18n/locales/en/common.json"
    if not source.is_file():
        return [f"no dashboard at {dashboard}"]
    script = f"const m = await import({json.dumps(source.as_uri())}); console.log(JSON.stringify({{metrics: m.METRICS, taxa: m.TAXA_METRICS}}))"
    ts = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
    texts = json.loads(locale.read_text())
    monthly = {e["value"] for c in contract["schema"] if c["name"] == "monthly_summaries" for e in build.discriminator(c)["enum"]}
    problems = []

    def compare(where, key, spec, m):
        combine = "sum" if m["kind"] == "total" else "mean"
        expected = {
            "overMonths": combine,
            "overDistricts": combine,
            "estimated": m["figure"] == "estimated" or None,
            "artfish": m.get("method") == "fao_artfish" or None,
            "twin": m.get("twin"),
        }
        if where == "METRICS":
            expected["gearIndicator"] = m.get("gear") if m.get("gear") != key else None
            expected["districtsOnly"] = key not in monthly or None
        for field, value in expected.items():
            if spec.get(field) != value:
                problems.append(f"metrics.ts {where}.{key}.{field} is {spec.get(field)!r}, the dictionary says {value!r}")

    dictionary = {k: m for k, m in metrics["metrics"].items() if m["kind"] != "share"}
    for where, theirs, ours in (("METRICS", ts["metrics"], dictionary), ("TAXA_METRICS", ts["taxa"], metrics["taxaMetrics"])):
        for key in sorted(set(theirs) ^ set(ours)):
            problems.append(f"{key} is in {'metrics.ts ' + where if key in theirs else 'the dictionary'} only")
        for key in sorted(set(theirs) & set(ours)):
            compare(where, key, theirs[key], ours[key])
    for key, m in dictionary.items():
        title, unit = texts.get(f"metric-{key}-title"), texts.get(f"metric-{key}-unit")
        if title != m["label"]:
            problems.append(f"locale metric-{key}-title is {title!r}, the dictionary's label {m['label']!r}")
        if unit and unit != m["unit"].replace("{currency}", "{{currency}}"):
            problems.append(f"locale metric-{key}-unit is {unit!r}, the dictionary's unit {m['unit']!r}")
    return problems


def run(contract, metrics, dashboard):
    problems = schema_problems(contract, metrics) + dictionary_problems(contract, metrics)
    if (HERE / "semantic-catalog.json").read_text() != build.render():
        problems.append("semantic-catalog.json is out of date: run build.py")
    if dashboard:
        problems += dashboard_problems(dashboard, contract, metrics)
    return problems


def self_test():
    contract, metrics = build.load("portal.odcs.json"), build.load("metrics.json")
    assert dictionary_problems(contract, metrics) == []
    broken = copy.deepcopy(metrics)
    del broken["metrics"]["mean_cpue"]
    broken["metrics"]["estimated_catch_tn"]["twin"] = "estimated_revenue_fao"
    found = dictionary_problems(contract, broken)
    assert any("carries mean_cpue" in p for p in found), found
    assert any("twin" in p for p in found), found
    broken = copy.deepcopy(contract)
    broken["schema"][0]["properties"][0]["description"] = "changed"
    assert any("defined differently" in p for p in dictionary_problems(broken, metrics))
    assert schema_problems(contract, {**metrics, "extra": 1})
    print("self-test ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dashboard", type=Path, default=HERE.parent.parent / "peskas.dashboard")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    problems = run(build.load("portal.odcs.json"), build.load("metrics.json"), args.dashboard)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)" if problems else "dictionary ok, dashboard agrees")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
