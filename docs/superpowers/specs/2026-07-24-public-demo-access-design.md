# Public Demo Access Design

**Date:** 2026-07-24
**Status:** Proposed for implementation
**Repository:** `YaoZeLiu0417/LLM_Psychometric`

## 1. Objective

Make the current Adolescent Big Five Workbench directly accessible to an
anonymous visitor from a CV or job-talk link without requiring GitHub or
Streamlit sign-in.

The repository and deployed application may be public. The primary security
requirement is that public browsing must not expose model credentials or
consume model tokens. Model-backed generation and every operation that mutates
research records must remain protected by a strong access code.

## 2. Confirmed Product Decisions

- Use one repository rather than maintaining a private source repository and a
  separate public mirror.
- Change the current GitHub repository to public only after a complete current
  tree and reachable-history security audit passes.
- Keep the current Streamlit URL when the platform permits it. Create a new URL
  only if the existing deployment cannot be changed from private to public.
- Anonymous visitors can navigate every page and inspect all reference content.
- Anonymous visitors can use Participant View; responses remain session-only.
- Reference-only JSON and CSV downloads remain available anonymously.
- Generate, Edit, Return, Approve, and Promote require Researcher Access.
- Public-demo changes are isolated to one Streamlit session and never modify
  the default project seen by another visitor.
- A public-demo session may initiate at most three candidate generations.
- No individual assessment result or personality interpretation is added.

## 3. Non-Goals

- Persistent multi-user research storage.
- User accounts, role administration, or OAuth.
- Durable export of live-generated candidates.
- Anonymous model generation.
- A validated personality assessment or diagnostic service.
- Rewriting the visual design of the existing workbench.

## 4. Deployment Architecture

```text
Public GitHub repository
        |
        v
Public Streamlit Community Cloud app
        |
        +-- anonymous visitor: read-only tour, zero model calls
        |
        +-- unlocked researcher: session-scoped generation and review
```

The codebase supports two explicit deployment modes:

- `research`: the current local/private research behavior and durable local
  JSON repository.
- `public_demo`: an isolated session repository and unified write gate.

`WORKBENCH_DEPLOYMENT` selects the mode. The safe default is `public_demo`.
Local and private research instructions explicitly configure `research`.
Unknown values fail configuration validation before a model call or repository
mutation can occur.

## 5. Components

### 5.1 Deployment Settings

A small configuration unit parses:

```dotenv
WORKBENCH_DEPLOYMENT=public_demo
PUBLIC_DEMO_GENERATION_LIMIT=3
```

The generation limit is fixed to three by default in public-demo mode. It is a
guard against accidental repeated clicks, not the primary cost boundary.

### 5.2 Unified Researcher Access

The current live-generation access mechanism becomes a shared Researcher
Access policy.

- The configured code remains in `LIVE_ACCESS_CODE` in Streamlit Secrets.
- The submitted value is compared with `hmac.compare_digest`.
- The raw submitted value is cleared immediately.
- Session state stores only a process-keyed HMAC fingerprint and an unlock
  boolean.
- A process restart, code rotation, session end, or missing code revokes the
  grant.
- Generation and Review use the same grant.

The UI gate is not the only enforcement point. `WorkbenchService` rejects
`save_generated_item` and `review_item` when mutations are not authorized.
This prevents a future UI regression from silently reopening writes.

### 5.3 Session Repository

Public-demo mode creates one `tempfile.TemporaryDirectory` for each Streamlit
session and stores its lifetime object in `st.session_state`. A
`JsonProjectRepository` rooted inside that directory seeds the existing demo
project.

This deliberately reuses the validated JSON repository and existing workbench
service rather than introducing a second storage implementation.

- Reruns in one browser session reuse the same temporary repository.
- Different browser sessions receive different paths and independent projects.
- Closing or expiring the session makes the temporary project disposable.
- Streamlit restarts discard all public-demo mutations.
- `workspace_data/v2/projects/` remains the repository only in `research` mode.

Best-effort temporary-directory cleanup is sufficient because the deployment
filesystem is ephemeral and the records contain no participant responses.

### 5.4 Public-Demo Generation Budget

Session state tracks generation starts, not only successful completions. The
counter increments immediately before the first model request. Once it reaches
three, Generate remains disabled for that session.

The real financial boundary is a separate demo API credential with a provider-
side spending or balance cap. The public demo must not reuse the researcher's
ordinary key.

## 6. Permission Matrix

| Capability | Anonymous | Researcher Access |
| --- | --- | --- |
| Open all pages | Allow | Allow |
| Inspect construct map and provenance | Allow | Allow |
| Change filters and load reference item | Allow | Allow |
| Participant View responses | Session only | Session only |
| Download reference-only JSON/CSV | Allow | Allow |
| Generate candidate | Deny | Allow within session limit |
| Edit item fields | Disabled | Allow |
| Return / Approve / Promote | Deny | Allow |
| Change another visitor's default project | Deny | Deny |

Review inputs remain visible while locked so a visitor can understand the
workflow, but they are disabled. Action buttons show a concise locked state and
do not submit. Reference downloads remain public because the current export
projection excludes live-generated candidates even after review or promotion.

## 7. Request and Data Flow

### 7.1 Anonymous Visit

1. Streamlit creates a new session.
2. The app creates and seeds a unique temporary repository.
3. The visitor navigates the full workbench and can load reference items.
4. Participant responses stay in `st.session_state`.
5. No model client is constructed and no model request is sent.

### 7.2 Researcher Unlock

1. The user submits the access code in the shared Researcher Access control.
2. The server compares the code and clears the input.
3. A valid code grants write access only to the current session.
4. Invalid input records a generic error and does not create a model client.

### 7.3 Generation

1. The app verifies model configuration, Researcher Access, and remaining
   session budget.
2. The generation counter increments before calling the model.
3. The existing structured pipeline generates and validates the candidate.
4. The candidate is saved only to the current session repository.
5. Review and Participant View in that session can observe later state changes.

### 7.4 Review

1. Locked visitors see disabled editor controls and actions.
2. An unlocked researcher edits and submits an action.
3. `WorkbenchService` independently verifies mutation authorization.
4. Existing validation, optimistic version checks, status transitions, and
   quality-check refresh continue unchanged.
5. The updated project remains inside the current session repository.

## 8. Token and Secret Security

Before changing repository visibility, inspect the complete reachable Git
history, not only the current working tree.

The release gate must check:

- credential-shaped values such as `sk-...`;
- non-empty API-key and access-code assignments;
- `.env`, `.streamlit/secrets.toml`, logs, exports, and workspace data in any
  reachable commit;
- local user paths and unintended personal files;
- binary assets and deleted historical paths that may contain sensitive data.

Every reachable blob is scanned with Git plumbing rather than relying only on
the checked-out files. Any discovered credential is rotated before the
repository becomes public. If sensitive content exists in history, history is
cleaned and verified before visibility changes.

The public Streamlit deployment stores only these values in platform Secrets:

- `WORKBENCH_DEPLOYMENT`: the literal value `public_demo`;
- `PUBLIC_DEMO_GENERATION_LIMIT`: the integer `3`;
- `OPENAI_API_KEY`: a dedicated capped demo credential;
- `LLM_MODEL`: the configured model identifier;
- `OPENAI_BASE_URL`: the compatible model endpoint;
- `LIVE_ACCESS_CODE`: a strong independent random code.

The demo key has a provider-side balance or spending cap. The access code is a
random secret rather than a personal password and can be rotated independently.

## 9. Error Handling and Fail-Closed Behavior

- Missing model configuration: all browsing works; generation stays disabled.
- Missing access code: the deployment is completely read-only.
- Invalid access code: generic rejection, cleared input, zero model calls.
- Exhausted session generation limit: Generate stays disabled with a concise
  remaining-limit message.
- Temporary repository creation failure: stop before rendering mutation
  controls and show a generic unavailable message; do not fall back to the
  shared research repository.
- Unauthorized service mutation: raise a dedicated permission error and show a
  generic locked-state message.
- Model timeout or invalid model output: preserve the existing public error
  boundary and charge the attempted generation against the session limit.
- Streamlit restart: start each new session from the immutable demo seed.

No error surface includes secrets, endpoint credentials, local paths, raw
model responses, or stack traces.

## 10. Documentation Changes

The root README will be updated after public access is verified:

- replace the private-access caveat with the anonymous Live Workbench link;
- explain that anonymous browsing consumes no model tokens;
- document the Researcher Access boundary and session generation limit;
- describe public-demo session isolation and non-persistence;
- preserve the reference-only export and psychometric evidence boundaries.

The repository remains without an open-source license unless the owner makes a
separate license decision. Public visibility alone does not grant reuse rights.

## 11. Test Strategy

### Unit and Service Tests

- deployment mode parsing and safe default;
- invalid deployment values;
- Researcher Access success, failure, rotation, and cleared raw input;
- service-level denial of unauthorized generation save and review mutation;
- independent temporary repositories for independent session-state mappings;
- repository reuse across reruns in one session;
- generation budget increments before a request and blocks attempt four;
- missing secrets produce read-only behavior;
- locked flows never construct or call the model client.

### Streamlit Smoke Tests

- all five pages render while anonymous;
- Generation and Review mutation controls are disabled while locked;
- reference-item loading, downloads, and Participant View remain usable;
- one unlock enables both Generation and Review for the same session;
- generated and reviewed content remains in the current session only.

### Security and Release Tests

- current-tree credential and local-path scan;
- every-reachable-blob history scan;
- ignored-secret-path assertions;
- full `python -m pytest` suite;
- anonymous HTTP request must not redirect to `/-/login`;
- anonymous browser must render the real Project page without GitHub sign-in;
- anonymous navigation must not generate model-provider traffic;
- a second fresh browser session must show the original default project.

## 12. Rollout

1. Implement and verify public-demo mode on an isolated branch.
2. Configure the existing private Streamlit deployment with explicit
   `WORKBENCH_DEPLOYMENT=research` before merging the new safe default.
3. Merge the tested feature through a pull request.
4. Run the current-tree and complete-history security audit.
5. Create and cap a dedicated demo API credential; rotate any previously shared
   credential if its status is uncertain.
6. Configure public-demo Streamlit Secrets.
7. Change the GitHub repository visibility to public.
8. Change Streamlit sharing to public or redeploy from the now-public
   repository if the platform requires it.
9. Verify anonymous desktop and mobile access, session isolation, disabled
   writes, and zero-token browsing.
10. Update the README/CV link only after anonymous verification passes.

## 13. Rollback

If public verification fails:

1. Return the Streamlit app to private access.
2. Change the GitHub repository back to private.
3. Revoke or rotate the demo API key and access code.
4. Diagnose in the private deployment and repeat the release gate.

Repository visibility is not a reversible confidentiality control after public
release because clones, caches, and forks may persist. The complete-history
audit is therefore mandatory before the first visibility change.

## 14. Acceptance Criteria

- A signed-out visitor can open the workbench without GitHub or Streamlit login.
- All five pages and default reference content are visible anonymously.
- Anonymous actions cause zero model API requests.
- Every persistent or model-backed mutation is denied until Researcher Access.
- An unlocked public-demo session cannot affect a second fresh session.
- The fourth generation attempt in one session is blocked before any model call.
- Secrets are absent from the current tree and every reachable Git blob.
- The complete automated test suite passes.
- The repository and Streamlit app are public only after all release gates pass.
- The final anonymous URL is recorded in the README and provided to the owner.
