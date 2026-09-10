# Manual Upload Map

Updated: 2026-09-10
Repository: sreekx007/Slay-ILS-Designer-V1.0
Target branch: main
Baseline commit: 152887a (Plotter Restructuring plan)

This map tracks local changes made after the baseline. Paths are relative to
the repository root. The previous runtime-batch checklist described files
already present in the baseline; those unchanged files do not need re-uploading.

## Pending batch: Plotter Phase 1 packaging

Status: implemented and checked locally; not committed or pushed by the assistant.

| Action | Repository path | Reason |
| --- | --- | --- |
| Update | `.gitignore` | Ignore the local Python environment; preserve cache and run-output exclusions. |
| Update | `framework_manifest.json` | Correct plotter paths and configuration filename; update obsolete folder guidance. |
| Update | `UPLOAD_MAP.md` | Keep this manual upload checklist alongside the changes. |
| Add | `plotters/README.md` | Setup instructions, module guide, and repository-root plotting example. |
| Add | `plotters/requirements.txt` | Declare NumPy, Matplotlib, and PyYAML dependencies. |
| Add / rename destination | `plotters/slay_config.yaml` | Configuration under the filename required by config.py; contents unchanged. |
| Delete / rename source | `plotters/slay_config.yaml.txt` | Replaced by slay_config.yaml. |
| Delete | `plotters/plotting tools and spec` | Empty placeholder replaced by README.md. |

## Manual upload procedure

1. Upload the added and updated files to the exact paths above, preserving folders.
2. Delete the two obsolete paths listed above. Uploading replacements through
   GitHub's web interface does not remove the old files automatically.
3. Confirm the final file set, then record the resulting GitHub commit below.

If committing from this local checkout instead, stage additions, modifications,
and deletions together. Inspect the staged diff before committing and pushing.

## Keep local; do not upload

- `.venv/` — installed Python environment.
- `runs/plotter_smoke/` — generated baseline PNGs.
- `__pycache__/` and `*.pyc` — generated Python caches.
- `.git/` — local Git metadata; never upload through GitHub's file uploader.

No changes were made to the five existing Python plotter/builder modules.
Historical manifest contents are preserved; their locations change as listed below.

## Verification recorded for this batch

- All five plotter/builder modules imported from the repository root with PYTHONPATH=plotters.
- ILS-TP built from standard_ils_layouts.json with no validation findings.
- Assembly and component PNGs exported, decoded successfully, and visually inspected.
- All six plotter artifact paths in the active manifest resolved to local files.
- Git diff whitespace check passed.
- Existing assembly annotation overlap near the x-axis remains for the later label-correction phase.

## Upload record

- GitHub commit: pending
- Upload date: pending

Keep this map current as further local batches are added. Mark a batch uploaded
only after its remote commit is confirmed.

## Pending batch: Manifest archive and registration

Status: local only; pending manual upload.

The root `framework_manifest.json` remains the only active manifest. It now
registers the plotter README, dependencies, upload map, restructuring plan, and
archive policy, and records the local Phase 1 verification status.

| Action | Old path (delete after upload) | New path (upload) |
| --- | --- | --- |
| Move | `framework_manifest_v0_1.json` | `superseded/framework_manifest_v0_1.json` |
| Move | `framework_manifest_v0_2.json` | `superseded/framework_manifest_v0_2.json` |
| Move | `framework_manifest_v0_3.json` | `superseded/framework_manifest_v0_3.json` |
| Move | `framework_manifest_v0_4.json` | `superseded/framework_manifest_v0_4.json` |

Also upload the updated `framework_manifest.json` and `UPLOAD_MAP.md`.
The pre-existing `superseded/framework_manifest.json` is retained unchanged.
Archived manifest contents describe historical states and must not be used as
current repository instructions. When using GitHub web uploads, upload all four
archive destinations and remove all four old root paths.

## Pending batch: Plotter Phase 2 command-line tools

Status: implemented and verified locally; not committed or pushed.

| Action | Repository path | Reason |
| --- | --- | --- |
| Add | `tools/plot_design.py` | Plot direct layout JSON or a selected archetype. |
| Add | `tools/plot_component.py` | Plot a component using defaults and parameter overrides. |
| Add | `tools/_plot_cli.py` | Shared input validation, headless setup, default reporting, and export. Required by both commands. |
| Add | `tools/test_plot_cli.py` | Integration checks for CLI behavior and failure handling. |
| Add | `plotters/examples/example_ilt_layout.json` | Direct ILS-ILT definition copied from the archetype library. |
| Add | `plotters/examples/example_valve_layout.json` | Illustrative default valve definition. |
| Update | `plotters/README.md` | CLI commands, options, exit codes, report scope, and tests. |
| Update | `framework_manifest.json` | Register the tools/examples and record Phase 2 status. |
| Update | `UPLOAD_MAP.md` | Include this batch in the manual upload checklist. |

Verification: five integration tests passed, including six invalid-request
subcases. Tests cover PNG and SVG exports, direct inputs, archetype selection,
parameter overrides, defaults, warning propagation, geometry errors, and input
protection. Tests run from a separate directory without PYTHONPATH. Repository-root
component, ILT, and valve PNGs also exported successfully; ILT and valve images
were visually inspected.

Reports describe build/export results, not automated visual QA. The ILT retains
the existing warning about absent explicit GD-Con parts in its simplified
archetype. Existing label/annotation overlaps remain for the later correction
phase. The valve example demonstrates current geometry rendering; it does not
implement a roller-contact exclusion rule.

Do not upload `runs/phase2/` or other generated run outputs. All batches above
remain pending; upload the latest copy of each file listed more than once.
