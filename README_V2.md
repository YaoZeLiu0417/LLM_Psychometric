# Adolescent Big Five Research Workbench V2

V2 is a research/demo workbench for developing and reviewing situational judgment items for Mainland Chinese adolescents aged 12-15. It is not a validated assessment product.

## Run the workbench

```powershell
python -m pip install -r requirements-v2.txt
powershell -ExecutionPolicy Bypass -File .\run_v2.ps1
```

Open `http://localhost:8501`. CURATED DEMO works without credentials and is the stable presentation path.

## Optional live generation

Set these environment variables before launching the app:

- `OPENAI_API_KEY`: API credential.
- `LLM_MODEL`: model identifier.
- `OPENAI_BASE_URL`: optional OpenAI-compatible endpoint.

Live generation requires `OPENAI_API_KEY` and `LLM_MODEL`. It is not required for CURATED DEMO.

## Verification

```powershell
python -m pytest
```

## 6-8 minute demo flow

1. Open PROJECT and explain the 2023 research lineage.
2. Select a domain and facet, then inspect source anchors and behavioral indicators.
3. Confirm the 12-15 age range and context constraints.
4. Show a curated or live-generated scenario blueprint.
5. Inspect the four behavioral options.
6. Review provenance and quality flags.
7. Make one visible human edit and mark the item reviewed.
8. Open the five-item participant preview.
9. Close with the future construct-module roadmap.

## Evidence boundary

V2 is a research/demo workbench. It has not completed psychometric validation and must not be used for diagnosis or individual personality inference. Candidate items require expert review, pilot testing, and empirical validation before research deployment.
