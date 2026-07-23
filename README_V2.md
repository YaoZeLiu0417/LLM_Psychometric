# Adolescent Big Five Research Workbench V2

V2 is a research/demo workbench for developing and reviewing situational judgment items for Mainland Chinese adolescents aged 12-15. It is not a validated assessment product.

## Run the workbench

```powershell
python -m pip install -r requirements-v2.txt
powershell -ExecutionPolicy Bypass -File .\run_v2.ps1
```

Open `http://localhost:8501`. Public reference items are available without model credentials or an access code and are the stable presentation path.

## Runtime boundary

Use one Streamlit server process per workspace. Manual or direct JSON edits and additional processes sharing a workspace are unsupported in demo V2; atomic file replacement does not provide cross-process transaction isolation.

## Optional live generation

Set these root-level environment variables before launching the app:

- `OPENAI_API_KEY`: API credential.
- `LLM_MODEL`: model identifier.
- `OPENAI_BASE_URL`: optional OpenAI-compatible endpoint.
- `LIVE_ACCESS_CODE`: access code used to unlock live generation for the current Streamlit session.

Live generation requires both model configuration (`OPENAI_API_KEY` and `LLM_MODEL`) and a session access-code unlock. The unlock applies only to the current Streamlit session and does not itself trigger a model call.

## Verification

```powershell
python -m pytest
```

## 6-8 minute demo flow

1. Open PROJECT and explain the 2023 research lineage.
2. Select a domain and facet, then inspect source anchors and behavioral indicators.
3. Confirm the 12-15 age range and context constraints.
4. Show a reference or live-generated scenario blueprint.
5. Inspect the four behavioral options.
6. Review provenance and quality flags.
7. Make one visible human edit and mark the item reviewed.
8. Open the five-item participant preview.
9. Close with the future construct-module roadmap.

## Evidence boundary

V2 is a research/demo workbench. It has not completed psychometric validation and must not be used for diagnosis or individual personality inference. Candidate items require expert review, pilot testing, and empirical validation before research deployment.
