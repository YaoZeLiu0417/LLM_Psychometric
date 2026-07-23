# Formal Release Polish and Protected Live Generation

**Date:** 2026-07-23
**Status:** Approved design

## Context

The workbench is now deployed as a public Streamlit Community Cloud app. Its
research pages should remain openly viewable for demonstrations, while model
generation must not be available to anonymous visitors who could consume the
configured API quota.

The current Project page also repeats the project identity in two consecutive
black panels. Development labels such as `CURATED DEMO` and `LIVE AVAILABLE`
make the deployed application read like a prototype rather than a formal
research workbench.

## Goals

- Keep the existing black, white, cyan, magenta, and orange visual language.
- Present one project identity panel instead of two repeated panels.
- Identify the 2023 evidence as a college-student study and distinguish it from
  the 2026 adolescent reconstruction.
- Keep reference items as the default, no-generation experience without
  exposing `CURATED DEMO` as a user-facing status.
- Require a session-scoped access code before any live model generation.
- Store the access code only in local or deployment secrets.

## Non-Goals

- Do not add user accounts, persistent login, role management, or a database.
- Do not change the psychometric taxonomy, item schema, prompt pipeline, or
  review workflow.
- Do not claim that either the archived study or the reconstructed items are
  validated for adolescent assessment.
- Do not make the entire public workbench password protected.

## Project Header

The global black header remains the visual anchor on every page. Its project
status badges are removed. On the Project page only, the header adds one compact
metadata row:

- `AGE 12-15`
- `LOCALE zh-CN`
- `Mainland Chinese junior-secondary students`

The separate `ACTIVE RESEARCH PROJECT` panel is removed, including its repeated
title, `CURATED DEMO` badge, and `Candidate item development - empirical
validation required` sentence. Other pages retain the compact global header
without the Project metadata row.

## Project Evidence Layout

The metric row remains, with `CURATED CANDIDATES` renamed to `REFERENCE ITEMS`.
The existing `VALIDATED ITEMS 0` metric continues to communicate the current
validation boundary without another warning banner.

The research lineage reads:

`2023 COLLEGE STUDENT STUDY -> 2026 ADOLESCENT RECONSTRUCTION -> FUTURE VALIDATION`

The archived evidence heading reads:

`2023 STUDY / COLLEGE STUDENT SAMPLE`

The alpha and omega table remains. The separate `Openness item-total r` line is
removed. The large orange-accent evidence note becomes a quiet footnote:

`Historical summary from the 2023 college-student study; raw response data are no longer available.`

The phrase `not evidence for V2` is removed because the revised lineage and
sample label already distinguish the two research phases.

## Formal User-Facing Language

The header no longer displays `CURATED DEMO`, `LIVE AVAILABLE`, or
`LIVE UNAVAILABLE`. Internal enum values and provenance fields may retain their
existing values where required for data compatibility.

Generation Studio no longer exposes a generation-mode selector. Reference
content loads by default, and `LOAD CURATED EXAMPLE` is renamed to
`LOAD REFERENCE ITEM`. Live generation is an explicitly unlocked action rather
than a persistent display mode.

## Live Access Control

The deployment defines a root-level secret named `LIVE_ACCESS_CODE`. The same
name may be used as a local environment variable. It is never committed.

Generation Studio starts with `v2_live_unlocked` false. A restrained
`UNLOCK LIVE GENERATION` control opens a password input. Submission follows
these rules:

1. If `LIVE_ACCESS_CODE` is absent or blank, Live generation remains disabled.
2. The submitted value is compared with `hmac.compare_digest`.
3. A match sets `v2_live_unlocked` for the current Streamlit session only.
4. A mismatch displays `Access code not recognized.` without revealing any
   configuration detail.
5. Ending the browser session starts a new locked Streamlit session.

The `GENERATE` action is disabled until both model configuration and session
access are present. The server-side generation branch checks access again before
constructing the model client, so UI state alone cannot authorize an API call.

Unlocking does not trigger generation. It only makes the existing live pipeline
available. Loading a reference item never requires the access code and never
calls the model.

## Configuration

`.env.example` documents `LIVE_ACCESS_CODE` without a real value. Streamlit
Community Cloud stores the production value alongside `OPENAI_API_KEY`,
`LLM_MODEL`, and `OPENAI_BASE_URL` in encrypted Secrets.

The deployment operator chooses and rotates the actual access code. A missing
access code fails closed.

## Error Handling

- Missing model configuration: generation stays disabled with a concise setup
  message visible only inside Generation Studio.
- Missing access-code configuration: the unlock control stays unavailable and
  reports that Live access is not configured.
- Incorrect access code: show the generic rejection message and keep the
  session locked.
- Model or persistence failure: preserve the existing sanitized failure paths;
  never display secrets or raw provider responses.

## Testing

Automated tests will cover:

- constant-time access-code verification for matching, mismatching, and missing
  configuration;
- locked-by-default session behavior;
- failed and successful unlock submissions;
- defense-in-depth rejection before any model client is created;
- reference loading while locked and without model calls;
- absence of `CURATED DEMO`, `LIVE AVAILABLE`, and `LIVE UNAVAILABLE` from the
  rendered header and Project page;
- the single Project identity panel, integrated metadata, revised lineage,
  college-student evidence label, renamed metric, and shortened footnote;
- absence of the old Project warning and `Openness item-total r` line.

The full existing test suite must pass before deployment. After merge, the
deployed app will be checked at desktop and mobile widths for Project and
Generation Studio, followed by a locked-access test that confirms no model call
can be initiated without the code.

## Release Flow

Implementation will be committed on `codex/formal-release-live-access`, pushed
for review, merged into `master`, and deployed automatically by Streamlit
Community Cloud. The production `LIVE_ACCESS_CODE` will be added to Streamlit
Secrets before testing the unlocked state.
