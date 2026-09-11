# ILS plotters

Build and draw conceptual ILS geometry in metres. The assembly view shows
an ILS and its header. Plots support design inspection, not FEA verification.

## Setup and repository-root execution

Use Python 3.10 or newer. In PowerShell, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r plotters/requirements.txt
$env:PYTHONPATH = (Resolve-Path plotters).Path
$env:MPLBACKEND = "Agg"
.\.venv\Scripts\python.exe
```

On macOS/Linux, use `.venv/bin/python` and
`export PYTHONPATH="$PWD/plotters" MPLBACKEND=Agg`.
The existing modules use top-level imports, so PYTHONPATH must include plotters.

## Component and assembly example

Run this Python code from the repository root in the configured environment:

```python
import json
from pathlib import Path
import matplotlib.pyplot as plt
from ils_builder import build_ils

layouts = json.loads(Path("knowledge/edas/standard_ils_layouts.json").read_text(encoding="utf-8"))
archetype = next(a for a in layouts["archetypes"] if a["id"] == "ILS-TP")
ils = build_ils(archetype["definition"])
for finding in ils.findings:
    print(finding)
assert not any(f.severity == "error" for f in ils.findings), "Resolve assembly errors before plotting"
output = Path("runs/plotter_smoke")
output.mkdir(parents=True, exist_ok=True)
plt.close(ils.plot(path=str(output / "ils_tp.png")))
plt.close(ils.plot_component(0, path=str(output / "gd_tp.png")))
```

Select other layouts by `archetypes[].id` and pass their `definition` to
`build_ils`; the collection itself is not a buildable definition.
Inspect `ils.findings` even when construction succeeds: engineering errors may
be returned as findings. Omitted geometry parameters use model defaults;
preserve omissions rather than writing resolved defaults back into a design.

## Modules

| File | Role |
| --- | --- |
| `component_spec.py` | Component geometry, engineering rules and connection systems |
| `ils_builder.py` | Definition-to-assembly conversion, validation and reports |
| `component_plotter.py` | Component detail rendering and shared drawing functions |
| `ils_plotter.py` | Assembly rendering, contact envelope and parameter panels |
| `config.py` | Loads and validates the adjacent YAML configuration |
| `slay_config.yaml` | Shared toolchain defaults; required at import time |
| `requirements.txt` | Python plotting dependencies |

Both plotting functions return a Matplotlib figure and accept an optional
`path` for export. Close figures after batch rendering. Geometry uses positive
y downwards and plots preserve equal x/y scale.

Command-line wrappers are available as described below. Basic plot QA is implemented; label/legend correction remains pending. GD-BOSS is registered as a coaxial sleeve; see Phase 6 below. See
[the restructuring plan](../docs/PLOTTER_RESTRUCTURE_PLAN.md) for subsequent phases.


## Phase 2 command-line tools

These commands configure imports and the headless Matplotlib backend themselves;
no PYTHONPATH or display configuration is required. Run from the repository root:

```powershell
.\.venv\Scripts\python.exe tools/plot_design.py --input knowledge/edas/standard_ils_layouts.json --archetype ILS-ILT --output runs/ilt.png --report runs/ilt.report.json
.\.venv\Scripts\python.exe tools/plot_design.py --input plotters/examples/example_valve_layout.json --output runs/valve.png
.\.venv\Scripts\python.exe tools/plot_component.py --component GD-TP --set centre_x=0.0 --set t_comp=0.042 --output runs/gd_tp.png
```

`example_ilt_layout.json` is the ILS-ILT definition copied from the standard
archetype library, including its provenance. `example_valve_layout.json` is an
illustrative valve using model defaults, not a verified design.

Both commands accept `--title`, `--output` (PNG, SVG, or PDF), and `--report`.
The report defaults to the image stem plus `.report.json`. Paths are relative
to the current working directory; absolute paths also work. Existing output
files at the requested destinations are replaced. Input and output/report paths
must be distinct. On failure, a prior image at that path may remain; use the
current report and exit code rather than image existence to determine success.

Component overrides use repeated `--set NAME=VALUE` arguments. Use
`--pipeline-set OD_pipe=0.508 --pipeline-set t_pipe=0.025` for pipeline changes
and `--system F2` for an ILS connection system. JSON arrays are supported, e.g.
`--set 'top_connector_x=[-1.0,1.0]'`; strings such as `variant=L` are accepted.
The component command defaults centre_x to zero and pipeline dimensions to the
shared configuration. Geometry defaults and provenance come from the model.
Unknown parameters, unsupported codes, invalid geometry,
and assembly error findings stop image export. Standalone components are built
in a single-component assembly, so assembly context warnings can still appear.

The JSON report records findings, resolved component/pipeline defaults, assembly
settings, errors, and export status. Input definitions are never rewritten.
`plot_status=passed` means build, export and implemented basic QA checks succeeded.
It does not certify full visual quality. `plot_qa_status` records basic QA results;
it is `not_applicable` if construction/export never reaches the checker. ILT may return `warning` because its simplified archetype has no
explicit GD-Con parts; that builder warning is retained in the report.

Exit codes: 0 for an exported image (including warnings), 1 for execution, validation or
QA failure, and 2 for command-line syntax errors. Argparse errors and
unsafe input/output path collisions do not produce a report. Stdout contains a
compact JSON result for normal execution. Use `--help` for argument details.

Run CLI integration checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tools -p test_plot_cli.py
```


## Phase 3: editable presentation

- `config/plot_style.yaml`: colors, connector glyph text/foreground/background,
  line widths, font sizes, figure widths, export DPI, and label format.
- `config/component_catalog.json`: display names, ontology paths, component
  families, style keys, renderer/support declarations, and label priority.
- `plot_settings.py`: loads and validates configuration once per process.
- `_plot_defaults.py`: frozen legacy defaults used when files or keys are missing.

Restart the CLI after editing. No engineering dimensions belong in these files.
The adjacent `config.py` still loads engineering defaults from `slay_config.yaml`;
`config/` is a presentation-data directory, not a Python package.

For example, set `figure.export_dpi` to 200, `fonts.title` to 12, or
`component_colors.GD-TP` to another Matplotlib color. Set `labels.format` to
`display_name` or `code_and_name` to use catalog names (default: `code`).
`default_style_key` maps a catalog entry to a component color. Missing component
colors retain the renderer's legacy gray fallback. Stroke keys such as
`stroke_1_9` identify legacy 1.9-point drawing widths; their values are editable.
Connector glyph text can change, while the engineering-specific connector shapes
and meanings remain in the renderer. Higher label priority gets first placement
in assembly label separation; equal priorities preserve component order.

Both plotters use the existing shared `accessor_renderer`; catalog entries do
not create geometry classes. GD-BOSS is supported as a coaxial sleeve. Missing catalog
entries for existing components retain legacy metadata. An unknown renderer,
invalid color, nonpositive font/figure setting, or malformed configuration fails
explicitly. Missing files emit warnings and use defaults; omitted keys also use
defaults. Explicit Python plot width arguments take precedence over configured
widths. CLI export DPI and direct Python export DPI use the same setting.

Run both CLI and style tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tools -p 'test_plot*.py'
```


## Phase 4: basic plot QA

Both CLI commands automatically call `checkers/plot_checker.py` after export.
Reports include checks for file existence, PNG decoding and pixel variation,
visible content in the geometry axes, finite nonzero axis bounds, geometry
clipping, and equal physical scale (1% tolerance). Inverted y axes are supported.
Geometry bounds include accessor nodes/extents and 241 contact samples per
component; this is a sampled check, not an exhaustive geometry proof.

Clipping and unequal scale produce warnings. Missing/corrupt/blank outputs and
empty geometry axes fail QA and return exit code 1. Failed or warning figures
may remain on disk for inspection; consult the report and exit code.
The checker changes no engineering geometry and applies no automatic corrections.

SVG is parsed as XML. PDF receives header/EOF checks only, not full decoding.
Neither vector format is independently rasterized; its `export_nonblank` check
is `not_applicable`, while the live Matplotlib geometry axes are still checked.
Pixel variation is a basic empty-image heuristic, not recognition of correct
engineering content. Label/legend overlap and iterative corrections remain Phase 5.

Direct Python callers can use `check_plot(fig, components, output_path)` after
saving a figure. The first axes must be the geometry axes, as in both current
plotters. It returns QA status, checks, warnings, errors and an empty corrections
list. Direct plotting APIs do not automatically invoke QA.

## Phase 5: rendered layout correction

The CLI runs checkers/label_overlap_checker.py before exporting. It measures
annotation boxes after rendering, checks labels against other labels, structure
paths, symbols and axis text, then tries up to 100 positions per label. Moved
text gets a leader to its original anchor. Engineering model data is untouched.

The pass may expand vertical view margins, wrap the title, wrap table cells,
allocate row heights from measured text, increase figure height (capped at
36 inches), and relocate the legend. Large parameter tables can still create
tall figures; whitespace is checked separately without cropping the header.
The correction pass is bounded, not a guarantee that every layout is resolvable.

Reports include layout_qa.initial_issues, remaining_issues, the search limit,
and structured corrections with original/final positions and coordinate systems.
passed_with_corrections means the implemented checks found no remaining issues;
warning means collisions or other warnings remain. Leaders may cross other
leaders; leader routing is not checked. Artist-path checks are conservative
approximations, not a replacement for visual inspection.

For direct Python use, call correct_layout(fig) before saving, followed by
check_plot(fig, components, output_path). Both functions expect the first axes
to be the geometry view. The CLI runs both automatically.


## Phase 6: Boss sleeve and component coverage

GD-BOSS surrounds the thick header coaxially; it does not replace header material.
ID_boss = OD_boss - 2*t_boss must strictly exceed the actual enclosed header
section OD across the full sleeve span. The builder checks section breakpoints
and both sides of each interval, so short thick sections are not skipped.

Standalone inputs require OD_boss and t_boss. L_boss defaults to 3*OD_boss.
Optionally, source_pip names a GD-PIP component in the same definition; the builder
takes its OD_outer and t_outer and rejects conflicting explicit dimensions.
Omitted dimensions remain omitted in serialized definitions. Reference order
does not matter. The source PiP itself needs valid explicit junction/wall inputs.

Example:
python tools/plot_design.py --input plotters/examples/example_boss_layout.json --output runs/boss.png
python tools/plot_component.py --component GD-BOSS --set OD_boss=0.6 --set t_boss=0.025 --output runs/boss_detail.png

The illustrative assembly has a 0.55 m boss bore over a 0.4484 m thick header OD.
Use ownership=lowest for the overlapping contact envelopes. The sleeve owns a
separate structural line and mass, with no automatic header junction. endL/endR
are sleeve ends; conMid is its attachment station on the sleeve beam axis.
The boss is excluded from header weld_chain and leaves section_at unchanged.
Reports include sleeve_steel_kg separately, including its contribution to CoG.

Sleeve-to-header attachment and load transfer remain unspecified. Every Boss
assembly emits that warning; contact is a geometric envelope, not proof of a
complete load path. The hollow rendering shows two wall strips and a clear bore.

Coverage now exercises component and assembly rendering for all 12 EDES codes.
GD-BrPipe remains a pipe part (explicit L_pipe, no roller contact); GD-B remains
the multi-member branch assembly. GD-PIP requires an interior junction position
and an outer wall that clears its thick inner body.


## Phase 7 solver plotting

Use the pipeline --plot option. See [workflow](../docs/PHASE7_SOLVER_PLOTTING.md).
