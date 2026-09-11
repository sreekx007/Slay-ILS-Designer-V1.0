"""Materialize an evidence-ranked candidate as an EDAS study layout."""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "knowledge/edas/standard_ils_layouts.json"

def patch(target, values):
    for key, value in values.items():
        if value is None:
            target.pop(key, None)
        else:
            target[key] = copy.deepcopy(value)

def materialize(solution, library=None):
    library = library or json.loads(LIBRARY.read_text(encoding="utf-8"))
    name = solution.get("recommendation", {}).get("recommended_candidate")
    anchors = {a["id"]: a for a in library["anchors"]}
    archetypes = {a["id"]: a for a in library["archetypes"]}
    key = name if name in anchors else "ILT-" + str(name)
    derived = name in ("L-ST-PS", "ILT-L-ST-PS")
    if derived:
        key = "ILT-L-FT-PS"
    anchor = anchors.get(key)
    if anchor is None:
        raise ValueError(f"No reviewed EDAS anchor mapping for candidate {name!r}")
    spec = copy.deepcopy(archetypes[anchor["archetype"]]["definition"])
    patch(spec["pipeline"], anchor.get("pipeline", {}))
    patch(spec["ils"], anchor.get("ils", {}))
    components = spec["components"]
    def part(ref):
        return components[ref] if isinstance(ref, int) else next(c for c in components if c["id"] == ref)
    patch(part(anchor.get("component", 0)), anchor.get("overrides", {}))
    for ref, values in anchor.get("parts", {}).items():
        patch(part(ref), values)
    if "associations" in anchor:
        spec["associations"] = copy.deepcopy(anchor["associations"])
    if derived:
        part("B")["support_connector"] = "S"
        for association in spec.get("associations", []):
            if association["from"]["component"] == "B":
                association["connection"] = "S"
                association["note"] = "Slotted branch support derived from EDAS FT/ST taxonomy."
    spec["ils"]["name"] = str(name) + " - EDAS study reconstruction"
    report = {
        "status": "emitted", "candidate": name, "source_anchor": key,
        "source_library": "knowledge/edas/standard_ils_layouts.json",
        "derived_changes": ["Branch support F -> S using EDAS FT/ST taxonomy"] if derived else [],
        "expert_review_required": True,
        "warnings": ["Study reconstruction uses EDAS anchor dimensions; EDPR constraints are not applied.",
                     "Implicit study connectors are retained; this is not a detailed fabrication assembly.",
                     "Solver evidence ranking is not a new structural analysis or design approval."],
        "errors": [], "recommendation": solution.get("recommendation"),
        "residual_risk": solution.get("residual_risk", [])
    }
    return spec, report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solution", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    paths = [Path(v).resolve() for v in (args.solution, args.output, args.report)]
    if len(set(paths)) != 3:
        parser.error("Solution, layout and report paths must differ.")
    try:
        spec, report = materialize(json.loads(paths[0].read_text(encoding="utf-8")))
        paths[1].parent.mkdir(parents=True, exist_ok=True)
        paths[1].write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, TypeError, StopIteration) as exc:
        report = {"status": "failed", "errors": [str(exc)], "warnings": [], "expert_review_required": True}
    paths[2].parent.mkdir(parents=True, exist_ok=True)
    paths[2].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if report["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
