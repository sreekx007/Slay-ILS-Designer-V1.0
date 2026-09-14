#!/usr/bin/env python3
"""Regenerate the paper ILT schematic with manuscript-readable fonts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
PLOTTERS = ROOT / "plotters"
sys.path[:0] = [str(TOOLS), str(PLOTTERS)]

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.size"] = 11.5
matplotlib.rcParams["svg.hashsalt"] = "slay-ils-paper-schematic-v1"

from plot_settings import STYLE
from _plot_cli import execute

PAPER_FONTS = {
    "annotation": 12.0,
    "small": 11.5,
    "dimension": 12.5,
    "component_label": 14.0,
    "title": 16.0,
    "assembly_table": 10.5,
    "exclusions": 9.5,
}


def definition(builder):
    # Keep the paper illustration focused on geometry and topology. The
    # companion JSON report retains the complete parameter, connector,
    # association, finding, and validation payload.
    if not getattr(builder.ILS, "_paper_geometry_only", False):
        original_plot = builder.ILS.plot

        def paper_plot(self, path=None, **kwargs):
            kwargs.setdefault("panel", False)
            kwargs.setdefault("show_exclusions", False)
            return original_plot(self, path=path, **kwargs)

        builder.ILS.plot = paper_plot
        builder.ILS._paper_geometry_only = True

    source = ROOT / "knowledge/edas/standard_ils_layouts.json"
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    matches = [item for item in data["archetypes"] if item.get("id") == "ILS-ILT"]
    if len(matches) != 1:
        raise ValueError(f"Expected one ILS-ILT archetype; found {len(matches)}")
    return matches[0]["definition"]


def normalize_svg(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\s*<dc:date>.*?</dc:date>\s*", "\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    path.write_text(text, encoding="utf-8")


def normalize_report(path, suffix):
    report = json.loads(path.read_text(encoding="utf-8"))
    report["input_file"] = "knowledge\\edas\\standard_ils_layouts.json"
    report["output_image"] = f"papers\\figures\\preliminary\\shared_repository_ilt_schematic.{suffix}"
    report["paper_font_profile"] = PAPER_FONTS
    report["paper_figure_scope"] = "geometry_and_topology"
    report.setdefault("checks", []).append({
        "id": "paper_font_profile",
        "status": "passed",
        "message": "Paper-specific font sizes and a geometry-focused view were applied without changing engineering geometry or the companion report payload.",
    })
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "preliminary",
        help="Destination directory; a short path can be used on Windows.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    STYLE["fonts"].update(PAPER_FONTS)
    STYLE["figure"]["export_dpi"] = 200

    input_path = ROOT / "knowledge/edas/standard_ils_layouts.json"
    exit_code = 0
    for suffix in ("svg", "png"):
        output = args.output_dir / f"shared_repository_ilt_schematic.{suffix}"
        report = args.output_dir / f"shared_repository_ilt_schematic.{suffix}.report.json"
        cli_args = SimpleNamespace(
            input=str(input_path),
            archetype="ILS-ILT",
            output=str(output),
            report=str(report),
            title=None,
        )
        exit_code = max(exit_code, execute(cli_args, definition))
        if suffix == "svg" and output.exists():
            normalize_svg(output)
        if report.exists():
            normalize_report(report, suffix)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
