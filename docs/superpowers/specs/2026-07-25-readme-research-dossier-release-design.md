# Research Dossier README and v0.1.0 Release Design

## 1. Objective

Upgrade the repository presentation into a concise research dossier for doctoral conversations and job-talk review without redesigning the existing README or implying that the workbench is a validated assessment.

The enhancement must make three capabilities legible within the first minute:

1. the project begins with established construct anchors rather than unconstrained prompting;
2. model-assisted authoring remains inspectable and governed by human review;
3. the researcher has implemented a working, tested, publicly viewable system with explicit scientific and operational boundaries.

## 2. Primary Audience and Positioning

The primary audience is a prospective doctoral supervisor evaluating research fit, methodological judgment, and engineering execution. General GitHub visitors and technical reviewers are secondary audiences.

The repository remains a research workbench, not a product landing page. The current Alto-inspired visual language, README structure, badges, metrics, restrained palette, and research-first prose remain in place. The enhancement adds a small number of high-value visual and documentary elements rather than rewriting the page.

The release is positioned as:

> `v0.1.0 Research Preview`

This label refers to software presentation readiness. It does not indicate that the candidate items, scores, or assessment interpretation have been psychometrically validated.

## 3. Current Baseline

The current repository already provides:

- a polished English-first README with Chinese operating guidance;
- four real interface captures for Construct Map, Generation Studio, Review, and Participant View;
- one simple Mermaid workflow from source anchors to Participant View;
- a public, read-only Streamlit deployment;
- explicit warnings against diagnostic, high-stakes, and individual-level use;
- a tested public-demo boundary that does not construct a model client for anonymous visitors.

The current repository does not provide:

- a composite interface overview;
- an animated walkthrough;
- a dedicated technical architecture figure;
- a responsibility-aware construct-to-candidate figure;
- a formal GitHub Release or version tag;
- a root license file;
- a standalone English project case study.

## 4. Scope and Non-Goals

### 4.1 In Scope

- one composite overview PNG;
- one 35-45 second read-only GIF walkthrough;
- one local SVG construct-to-candidate diagram;
- one local SVG system architecture diagram;
- minimal README insertions and link updates;
- one root `CASE_STUDY.md`;
- one root `LICENSE` with an all-rights-reserved boundary;
- focused documentation and asset tests;
- one `v0.1.0` tag and GitHub Release after merge and verification.

### 4.2 Out of Scope

- visual redesign of the application or README;
- GitHub Pages or a separate marketing site;
- changes to Streamlit application behavior, deployment mode, credentials, or generation access;
- empirical claims, generated-item performance claims, or historical sample-size claims;
- new psychometric analyses or simulated results;
- a permissive or open-source license;
- release of workspace records, API credentials, access codes, or model-generated research data.

## 5. README Information Architecture

The existing README order remains substantially unchanged. Only the following targeted changes are made:

1. Add `English Case Study` and `v0.1.0 Research Preview` to the existing top link row.
2. Replace the current top Construct Map image with the composite interface overview.
3. Move the existing direct Construct Map capture into the `Workbench tour / Construct Map` subsection so all four detailed page captures remain available exactly once.
4. Insert a short `35-45 second walkthrough` section after the project lineage and before the research workflow.
5. Replace the current simple Mermaid workflow with the responsibility-zoned SVG.
6. Insert the system architecture SVG inside `Technical foundation` before the implementation table.
7. Link the existing `License and research use` section to the root `LICENSE` file.

All existing prose, headings, metrics, badges, detailed page captures, deployment boundaries, roadmap content, and Chinese instructions remain unless a small link-level edit or the specified Construct Map image move is required by these additions.

The reading sequence becomes:

```text
Title and research proposition
-> Links, metrics, and research-use warning
-> Interface overview
-> Research proposition and project lineage
-> 35-45 second walkthrough
-> Construct-to-candidate responsibility flow
-> Existing detailed workbench tour
-> System architecture and technical foundation
-> Deployment and validation boundaries
-> Roadmap, license, and Chinese operating guide
```

## 6. Visual Asset System

All new assets use the existing workbench palette and real interface material:

- black: `#0B0B0D`;
- magenta: `#D81B78`;
- violet: `#40358C`;
- cyan: `#24A8D8`;
- orange: `#EF5A24`;
- light neutral: `#F5F5F6`.

No gradients, decorative illustrations, fabricated controls, or marketing-style hero composition are introduced. English labels remain brief. Chinese item content remains unaltered.

### 6.1 Composite Interface Overview

Path:

```text
docs/assets/readme/workbench-overview.png
```

Specification:

- `1600 x 900` PNG;
- Construct Map occupies the dominant left region;
- Generation Studio, Human Review, and Participant View form a narrower right rail;
- real repository screenshots are used as the only interface content;
- minimal labels identify the project and the `FROM CONSTRUCT TO CANDIDATE` narrative;
- the image replaces the current top Construct Map placement; the original detailed Construct Map capture moves to its existing tour subsection and remains referenced once.

### 6.2 Animated Walkthrough

Path:

```text
docs/assets/readme/workbench-walkthrough.gif
```

Specification:

- `960 x 540` pixels;
- duration between 35 and 45 seconds;
- target 8 frames per second, with an accepted range of 6-10 frames per second after optimization;
- maximum file size of 10 MiB;
- stable cursor movement and readable pauses;
- no credentials, access codes, personal information, or model calls.

Sequence:

```text
Project lineage and scope
-> Construct Map and source anchors
-> Generation stages and a reference item
-> Review provenance and quality checks
-> Participant View
```

The public read-only deployment is the recording source. The walkthrough does not press Generate or imply that the displayed reference item was produced during recording.

### 6.3 Construct-to-Candidate Diagram

Path:

```text
docs/assets/readme/construct-to-candidate.svg
```

The diagram uses three responsibility zones:

1. **Theoretical Inputs**
   - source anchors and scoring direction;
   - facet definition, observable behaviors, exclusions, and confounds.
2. **Model-Assisted Authoring**
   - adolescent scenario blueprint;
   - four observable response options and rationales;
   - automated structural checks.
3. **Human Governance**
   - editing, documented rationale, and content approval;
   - promotion to `PILOT_CANDIDATE` with `EMPIRICAL VALIDATION REQUIRED`.

The footer states:

> `MODEL PROPOSES · RESEARCHER DECIDES · DATA VALIDATE`

This SVG replaces the current simple Mermaid workflow. It must not represent workflow completion as evidence of reliability, validity, or measurement invariance.

### 6.4 System Architecture Diagram

Path:

```text
docs/assets/readme/system-architecture.svg
```

The diagram uses four vertical layers:

1. **Streamlit Research Views**
   - Project, Construct Map, Generation, Review, Participant View.
2. **Application Services**
   - workflow state, authorization, generation coordination, review transitions.
3. **Typed Research Domain**
   - anchors, specifications, candidates, quality checks, review history, evidence state.
4. **Adapters and Storage**
   - OpenAI-compatible client, session-isolated and durable JSON repositories, reference exports.

The figure explains that the domain and service layers can later support another interface without making React or FastAPI an implemented capability.

Both SVG files use `viewBox="0 0 1600 900"`, embedded accessible titles and descriptions, stable system fonts, and text large enough to remain readable at normal GitHub width.

## 7. English Case Study

Path:

```text
CASE_STUDY.md
```

The case study is a 900-1,400 word English portfolio narrative designed for a three-to-five-minute read. It is linked from the README top row and reuses the overview and diagram assets rather than creating a second visual system.

Required sections, in order:

1. `Executive Summary`
2. `Research Problem`
3. `From the 2023 Master's Project to the Adolescent Workbench`
4. `My Role: Researcher · System Designer · Developer`
5. `Construct and Item-Development Method`
6. `Human-AI Responsibility Boundary`
7. `System Architecture`
8. `What the Current Workbench Demonstrates`
9. `What Has Not Yet Been Validated`
10. `Future Research Program`

The case study may describe implemented capabilities, design decisions, provenance, safeguards, tests, and future research directions. It must not claim that the new system outperforms the 2023 system, that the generated items are valid, or that the workbench supports diagnosis, clinical inference, or completed neuroimaging integration.

## 8. License and Research-Use Boundary

Path:

```text
LICENSE
```

The license file begins with:

```text
Copyright (c) 2026 Yaoze Liu. All rights reserved.
```

It states that the public source is provided only for viewing, academic evaluation, and reference. Except for the limited platform rights required by GitHub's Terms of Service to host, view, and fork a public repository within GitHub, no license is granted to copy, modify, redistribute, sublicense, host a derivative deployment, or use the repository in an empirical study without prior written permission.

It also states:

- the repository is not open-source software;
- public repository visibility does not grant reuse rights;
- third-party questionnaire wording, construct materials, fonts, and other assets remain subject to their respective owners and terms;
- candidate items and software presentation do not constitute a validated assessment;
- no diagnostic, clinical, educational placement, employment, or other high-stakes use is authorized.

The README summarizes this boundary and links to `LICENSE`. The wording is a project-use notice and is not presented as legal advice.

## 9. GitHub Release

Tag:

```text
v0.1.0
```

Release title:

```text
Adolescent Big Five Workbench v0.1.0 Research Preview
```

The release is created only after the documentation branch is merged, the final `master` test suite and public-release audit pass, and the deployed read-only URL is rechecked.

Release notes include:

- the research question and target population;
- the five implemented workbench views;
- construct traceability, staged authoring, quality checks, human review, and participant preview;
- the public read-only URL;
- local installation and launch commands;
- test and audit status;
- known deployment, export, evidence, and validation boundaries;
- the all-rights-reserved license boundary.

No separate release binary is attached. GitHub's generated source archives are sufficient for this research preview. The tag points to the verified merge commit and is not moved after publication.

## 10. Verification Strategy

Focused tests extend `tests/test_readme.py` and verify:

- exact README and case-study headings and links;
- the new local asset paths appear in the intended sections exactly once;
- existing detailed screenshots remain present exactly once;
- the overview PNG fully decodes and is exactly `1600 x 900`;
- the GIF fully decodes, is exactly `960 x 540`, lasts 35-45 seconds, contains at least 120 decoded frames, and is no larger than 10 MiB;
- both SVG files parse as XML, use the required viewBox, include accessible titles/descriptions, and contain the required conceptual labels;
- `CASE_STUDY.md` contains all required sections and evidence-boundary language;
- `LICENSE` contains the copyright holder, all-rights-reserved statement, prohibited reuse categories, third-party rights boundary, and high-stakes-use exclusion;
- unsupported research or validation claims remain absent.

The full repository test suite, `scripts/audit_public_release.py`, and `git diff --check` run before commit, before PR completion, and after merge.

Manual verification covers:

- GitHub README rendering at desktop and narrow widths;
- SVG legibility without opening the raw asset;
- GIF pacing, looping, text readability, and absence of sensitive content;
- case-study reading order and three-to-five-minute length;
- the public workbench URL and anonymous read-only boundary;
- the final release page, tag, links, and notes.

## 11. Failure Handling

- If the deployed app is asleep, warm it before capture and restart the recording from the first scene.
- If any capture reveals a credential, access code, personal path, or private record, discard the entire capture and record again.
- If the GIF exceeds 10 MiB, reduce frame rate, palette size, and transition frames before reducing image dimensions or removing research-critical scenes.
- If SVG text is unreadable at GitHub width, simplify labels and increase type size rather than enlarging the README section.
- If GitHub sanitizes or misrenders an SVG, rasterize a PNG fallback from the same composition and update the documented asset contract.
- If release verification fails, do not create or move the tag; fix the branch, merge, and rerun verification first.

## 12. Implementation Sequence

```text
Write failing documentation and asset contracts
-> Produce overview PNG and both SVG diagrams
-> Capture and optimize the read-only GIF
-> Apply minimal README enhancements
-> Write CASE_STUDY.md and LICENSE
-> Run focused tests, full tests, release audit, and visual QA
-> Review and merge the documentation PR
-> Verify final master and public deployment
-> Create the immutable v0.1.0 tag and Research Preview release
-> Verify GitHub README, release page, and public links
```

## 13. Success Criteria

The work is complete when:

- the existing README aesthetic is visibly preserved;
- the first screen communicates the actual workbench and its research purpose;
- a reviewer can understand the theory-to-candidate responsibility chain in under one minute;
- the architecture diagram demonstrates real engineering boundaries without overstating future technology;
- the GIF demonstrates the actual read-only workflow without consuming model tokens;
- the case study accurately presents the research problem, implemented contribution, scientific limits, and future program;
- reuse rights and research-use prohibitions are explicit;
- `v0.1.0 Research Preview` is reproducible, tested, linked, and publicly viewable.
