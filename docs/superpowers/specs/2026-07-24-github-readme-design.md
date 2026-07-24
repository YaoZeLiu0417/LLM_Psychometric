# GitHub README Design

Date: 2026-07-24
Status: Approved for specification review

## 1. Purpose

Create a polished root-level GitHub README for the Adolescent Big Five Workbench. The README must explain the research contribution, show that the workbench is already usable, and provide accurate instructions for the deployed and local systems.

The README is a research dossier, not a marketing landing page. Its first impression must be scientifically credible to a prospective doctoral supervisor or job-talk audience while remaining practical for a researcher who wants to open and use the system.

## 2. Audience and Core Message

The primary audience is psychology, psychometrics, developmental science, and cognitive-neuroscience researchers. A secondary audience is software-oriented collaborators who need to understand how the workbench runs and where its current boundaries are.

The core message is:

> The workbench transforms established Big Five construct anchors into age-appropriate situational judgement item candidates for mainland Chinese adolescents aged 12-15 while preserving theoretical provenance, generation constraints, quality evidence, and human review history.

The README must not imply that the system is a validated test, a diagnostic product, or evidence that generated items are psychometrically superior.

## 3. Selected Direction

The selected visual and editorial direction is **A: Research dossier**, with screenshot composition **A1: Research panorama plus details**.

This direction leads with:

1. the research problem and target population;
2. traceability and human review;
3. the evidence boundary;
4. immediate proof that the software is usable;
5. detailed workflow and operating instructions.

The visual language adapts the existing Alto-inspired application identity: black and white foundations, restrained magenta emphasis, and sparse cyan, orange, and deep-purple scientific accents. The README uses GitHub-native typography and layout instead of attempting to reproduce a web landing page.

## 4. Language Strategy

The README uses **English primary narrative plus Chinese operating instructions**.

English is used for:

- the title, research proposition, and audience-facing summary;
- research lineage and workflow descriptions;
- feature tour captions;
- architecture, limitations, and research roadmap.

Chinese is used for:

- the step-by-step online workflow;
- live-generation access and model-configuration instructions;
- the review-to-participant workflow;
- local installation and launch instructions;
- concise troubleshooting notes where operational precision matters.

Chinese question stems and response options remain visible in screenshots because they are the participant-facing research content.

## 5. README Information Architecture

### 5.1 Research Dossier Hero

The first screen contains:

- `Adolescent Big Five Workbench` as the literal project name;
- one concise research proposition;
- links to the deployed workbench and repository workflow sections;
- restrained badges for Python, Streamlit, BFI-2 construct mapping, and human-in-the-loop review;
- the factual counts `5 domains`, `15 facets`, and `60 traceable anchors`;
- a prominent evidence-boundary statement;
- one full-width real screenshot of Construct Map.

The hero must not use `curated demo`, `live available`, or other provisional release language. It must not use decorative illustrations, generated brain imagery, or a marketing-style banner.

### 5.2 Research Lineage

`From 2023 to the Current Workbench` explains:

- the 2023 master's project focused on college students;
- the current reconstruction targets mainland Chinese adolescents aged 12-15;
- V2 improves the authoring, provenance, review, and interface workflow;
- the earlier study is research lineage, not evidence that V2 is validated or superior;
- unverified historical sample sizes or results are not restated.

### 5.3 Research Workflow

A Mermaid flow diagram presents:

```text
Big Five source anchors
-> Construct Map
-> Adolescent scenario constraints
-> Structured generation
-> Quality checks
-> Human review and version history
-> Pilot candidate
-> Participant View and research export
```

The accompanying text explains that the facet is the generation unit and that source direction, behavioral indicators, scenario constraints, option scoring, checks, and human edits remain inspectable.

### 5.4 Workbench Tour

The feature tour uses three focused screenshots after the Construct Map panorama:

1. `Generation Studio`: construct specification, scenario blueprint, response-option design, and checks.
2. `Review Workbench`: editable Chinese content, evidence status, provenance, reviewer notes, and version history.
3. `Participant View`: participant-facing Chinese items without construct labels, scoring keys, or personality feedback.

Captions describe research functions, not generic product benefits.

### 5.5 Chinese Usage Guide

The guide contains five short paths:

1. **Online reference path**: open the deployed URL and inspect the existing project, construct map, reference items, review metadata, and participant preview without making a model call.
2. **Live generation path**: unlock the current Streamlit session with the configured access code, select live generation, choose a domain/facet/context, and generate one candidate.
3. **Human review path**: select the generated candidate, enter reviewer and note, revise as needed, use `APPROVE CONTENT`, then use `PROMOTE TO PILOT`.
4. **Participant path**: open Participant View; pilot candidates replace the default five reference items for that project state.
5. **Local path**: clone, install `requirements-v2.txt`, configure root environment variables, run `run_v2.ps1`, and open `http://localhost:8501`.

The guide explicitly states that unlocking a session does not itself call the model and that ordinary page browsing consumes no model tokens.

### 5.6 Technical Foundation

The technical section stays compact and describes:

- Streamlit views;
- workflow and review services;
- Pydantic typed research records;
- versioned local JSON persistence;
- an OpenAI-compatible model adapter;
- structured JSON generation and one repair attempt;
- JSON and CSV research exports.

It links to the existing implementation notes instead of duplicating every runtime detail.

### 5.7 Deployment and Evidence Boundaries

The README must state:

- live generation requires `OPENAI_API_KEY`, `LLM_MODEL`, and a valid session access code;
- `OPENAI_BASE_URL` is optional for compatible endpoints;
- credentials and access codes must never be committed;
- Streamlit Community Cloud storage is ephemeral, so generated and reviewed items may disappear after an app restart or redeployment;
- exported JSON/CSV should be downloaded when work needs to be retained;
- model output, automated checks, and human review do not substitute for pilot testing and psychometric validation;
- the system must not be used for diagnosis, high-stakes decisions, or individual personality inference.

### 5.8 Research Roadmap

The closing section positions the current Big Five module as a starting point for future adolescent research modules involving individual differences, executive function, psychopathology-related phenotypes, longitudinal designs, and potential neuroimaging integration.

All roadmap language is prospective. No unimplemented module is presented as an existing capability.

## 6. Screenshot and Asset Design

Create the following committed assets under `docs/assets/readme/`:

- `construct-map.png`
- `generation-studio.png`
- `review-workbench.png`
- `participant-view.png`

Screenshot requirements:

- capture the real local V2 application with stable seeded content;
- use a consistent desktop viewport and crop away browser chrome;
- preserve readable Chinese item content and English research labels;
- avoid API keys, access codes, environment values, local user paths, and browser identity;
- avoid transient spinners, error messages, or provisional labels;
- use PNG for sharp interface text;
- keep each image large enough to inspect but compressed enough for a responsive GitHub page;
- verify that markdown alt text explains the research function shown.

The Construct Map image appears near the top as the research panorama. The remaining images appear only in the Workbench Tour so the README does not become a screenshot gallery.

## 7. Files and Ownership

Implementation changes are limited to documentation assets:

- `README.md`: new GitHub-facing research dossier and usage guide.
- `docs/assets/readme/*.png`: four real application captures.
- `.gitignore`: ignore `.superpowers/` visual-brainstorming artifacts.
- `README_V2.md`: retained as the existing implementation note; the new root README may link to it but does not delete or rewrite its historical content in this task.

No application behavior, model prompts, research records, or deployment secrets are changed.

## 8. Failure Handling in the Documentation

The README gives readers a stable fallback for each operational boundary:

- no model configuration: browse reference content and the complete workbench structure;
- invalid or missing access code: remain in the public reference path;
- generation failure: retain completed work, retry later, or inspect reference content;
- ephemeral cloud restart: restore from a previously downloaded export where available;
- broken local launch: verify Python dependencies, root environment variables, and the single Streamlit process requirement.

The wording remains concise and does not expose stack traces or encourage users to paste credentials into issues.

## 9. Verification

Before publication:

1. verify every screenshot against the current application and inspect it for sensitive data;
2. verify image paths and alt text using the repository-relative GitHub renderer contract;
3. verify the deployed URL and repository-internal links;
4. verify all commands and environment-variable names against the current files;
5. verify the documented review transition against the current status rules;
6. verify Participant View behavior: all `PILOT_CANDIDATE` items when present, otherwise the first five reference items;
7. run the complete Python test suite to ensure documentation work did not disturb the repository;
8. inspect the rendered README at desktop and narrow widths for clipping, excessive image size, and unreadable labels;
9. scan the final diff for credentials, access codes, local paths, provisional release language, and unsupported psychometric claims.

The README does not display a fixed passing-test count because it would become stale without an automated badge source.

## 10. Acceptance Criteria

The work is complete when:

- GitHub renders a root README with the approved Research Dossier structure;
- the deployed workbench is reachable from the first screen;
- the first screen communicates target population, traceability, core scope, and evidence boundary;
- all four real screenshots render and contain no sensitive information;
- a Chinese-speaking researcher can follow the online and local workflows without prior project context;
- the 2023 college-student lineage and current adolescent focus are clearly distinguished;
- the live-generation, review, pilot-promotion, and participant-preview instructions match the application;
- persistence and psychometric limitations are explicit;
- future research directions are clearly prospective;
- repository verification passes and the final changes are published through the agreed Git workflow.

## 11. Out of Scope

This task does not:

- redesign application pages;
- change generation, review, or Participant View behavior;
- add cloud persistence, authentication, or CI infrastructure;
- publish model credentials or the live access code;
- claim new psychometric evidence;
- create a paper, slide deck, or full research protocol.
