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

Command-line wrappers are available as described below. Automated visual QA is not yet implemented. GD-BOSS is not yet
registered as a buildable component. See
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
Unknown parameters, unsupported codes (including GD-BOSS), invalid geometry,
and assembly error findings stop image export. Standalone components are built
in a single-component assembly, so assembly context warnings can still appear.

The JSON report records findings, resolved component/pipeline defaults, assembly
settings, errors, and export status. Input definitions are never rewritten.
`plot_status=passed` means build/export succeeded, not that the image passed
visual inspection. `plot_qa_status=not_applicable` explicitly marks deferred
visual QA. ILT may return `warning` because its simplified archetype has no
explicit GD-Con parts; that builder warning is retained in the report.

Exit codes: 0 for an exported image (including warnings), 1 for execution or
validation failure, and 2 for command-line syntax errors. Argparse errors and
unsafe input/output path collisions do not produce a report. Stdout contains a
compact JSON result for normal execution. Use `--help` for argument details.

Run CLI integration checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tools -p test_plot_cli.py
```
