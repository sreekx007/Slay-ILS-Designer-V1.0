# Slay-ILS Pending Runtime Batch

Upload these files to the repository root preserving the paths below.

## Root manifest

- `framework_manifest.json`
- `framework_manifest_v0_3.json`

After upload, `framework_manifest.json` should be treated as the latest active manifest.

## EDPR Examples

- `knowledge/edpr/examples/EDPR_EXAMPLE_ILT_L_BRANCH_MIN_STRAIN.json`
- `knowledge/edpr/examples/EDPR_EXAMPLE_GDVLV_NO_ROLLER_CONTACT.json`
- `knowledge/edpr/examples/EDPR_EXAMPLE_GDSH_GDTP_MIN_STRAIN.json`
- `knowledge/edpr/examples/EDPR_EXAMPLE_EAST_EASB_CONNECTION_COMPARISON.json`

## Runtime Tools

- `tools/retrieve_context.py`
- `tools/run_edpr_pipeline.py`
- `tools/solve_problem.py`

## Quick Test

From the repository root:

```bash
python tools/EDPR_VALIDATOR.py --schema schemas/EDPR_METASCHEMA.json knowledge/edpr/examples/*.json
python tools/run_edpr_pipeline.py --edpr-json knowledge/edpr/examples/EDPR_EXAMPLE_ILT_L_BRANCH_MIN_STRAIN.json --output-dir runs/test_ilt --solution-format md
```

Expected first-pass numeric recommendation for the ILT L-branch example:

```text
L-ST-PS
```
