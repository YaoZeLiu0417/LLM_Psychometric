# Adolescent Big Five Research Workbench V2 Design

Date: 2026-07-22  
Target demo: 2026-07-24  
Status: Approved in conversation; awaiting written-spec review

## 1. Purpose

Rebuild the master's-project prototype as a stable, presentation-ready research workbench for developing situational Big Five items for mainland Chinese adolescents aged 12-15.

The product is not an AI personality quiz and is not a validated clinical or educational assessment. It is a researcher-facing authoring, review, and provenance tool that produces candidate items for later expert review and empirical validation.

The core product claim is:

> The workbench turns established personality constructs into age-appropriate situational item candidates while keeping the theoretical anchors, generation constraints, scoring logic, quality checks, and human edits inspectable.

## 2. Research Positioning

The presentation tells a three-part research story:

1. **Prior work:** the 2023 master's project implemented an early LLM-assisted personality SJT pipeline and completed an empirical study with real participants.
2. **Current reconstruction:** V2 uses a cleaner construct model, structured generation, explicit provenance, human review, and a stable research interface.
3. **Future program:** the same research workflow can later host construct-specific modules for adolescent emotion regulation, impulsivity, attention/control, psychopathology-related phenotypes, and links to longitudinal or neuroimaging research.

Archived results are historical evidence, not evidence that V2 is superior. Figures and sample sizes appear in the product only when verified against the archived thesis or slides. No new psychometric claim is inferred from the missing raw data.

## 3. Users and Context

### Primary user for V2

The researcher operating a controlled 6-8 minute live demonstration.

### Near-term user

Psychology and cognitive-neuroscience researchers who author, inspect, revise, and export candidate items.

### Participant context

Mainland Chinese junior-secondary students aged 12-15. Their scenarios use age-appropriate Chinese, familiar roles, and bounded settings such as classroom learning, group work, assignments and exams, clubs, peer interaction, family communication, and online interaction.

## 4. Scope

### Required for the first-stage demo

- A clean V2 entry point that does not depend on the broken state flow of the legacy pages.
- An English research workspace with Chinese assessment content.
- A complete map of five Big Five domains, 15 facets, and the available 60 source anchors.
- One end-to-end workflow from facet selection through human review.
- Full item provenance and explicit evidence status.
- Editable scenario and response options with saved review status.
- Five curated Chinese demo items, at least one per Big Five domain.
- A five-item participant preview without a personality result.
- JSON export of the full structured item and CSV export of tabular item/option fields.
- Live model generation when configured and a fully functional curated-demo path when it is not.
- Preservation of the legacy application and research artifacts.

### Explicitly excluded from the first stage

- Live generation and review of all 60 items.
- New participant data collection or empirical validation.
- CFA, IRT, reliability, validity, or measurement-invariance analysis.
- Simulated LLM respondents.
- Clinical interpretation, diagnostic advice, or adolescent personality reports.
- Authentication, cloud storage, multi-user collaboration, or formal public deployment.
- PDF reporting.
- Implemented executive-function or psychopathology modules.

## 5. Technical Strategy

V2 remains a Python and Streamlit application for the Friday deadline. It is an isolated vertical slice inside the existing project rather than another set of pages coupled to legacy session state.

The architecture has four layers:

```text
Streamlit views
    -> application workflow/state services
        -> construct, generation, review, and export domain services
            -> model adapter and local JSON repository
```

Business rules do not live in Streamlit page files. The Python domain and service layers remain reusable when the project later adds FastAPI and a React client.

The first-stage repository uses typed Python models with explicit validation and versioned JSON persistence. It does not introduce a database. Writes are local and atomic. A future FastAPI layer can expose the same service interfaces without changing the construct or generation logic.

### 5.1 Legacy Asset Reuse

V2 is a reconstruction of the master's project, not an unrelated greenfield application. It preserves the project's research lineage by auditing and migrating useful legacy assets into the new domain model.

Assets eligible for direct reuse are:

- the available 60 Big Five source anchors;
- five-domain and 15-facet mappings;
- source direction and reverse-key metadata;
- archived research slides and verified historical findings;
- existing generated-item examples that remain theoretically and linguistically suitable.

Assets eligible for reuse after review and adaptation are:

- the Trait Analysis Expert, Scenario Construction Expert, and Behavior Adaptation Expert concepts;
- prompt templates, retrieval materials, construct descriptions, situation templates, and review rules;
- useful editing, preview, and export interactions;
- strong legacy questions that can be normalized into the V2 schema, checked for adolescent appropriateness, and human-reviewed as curated examples.

The three legacy expert roles map to inspectable V2 stages:

```text
Trait Analysis Expert       -> Construct Specification
Scenario Construction Expert -> Scenario Blueprint
Behavior Adaptation Expert  -> Response Option Design
```

The following are not carried forward as implementation foundations:

- fragmented Streamlit session state and disconnected page hand-offs;
- conflicting `score`, `behavior_score`, and `self_awareness` schemas;
- paths that drop domain, source direction, or scoring metadata;
- the default ten-item generation limit;
- unsupported psychometric interpretations, simulated-answer workflows, and non-core PDF paths;
- legacy credentials, sensitive logs, or unsafe configuration practices;
- raw chain-of-thought as a provenance mechanism.

Legacy examples do not automatically become curated demo items. Each migrated example must pass the V2 schema, adolescent-context review, quality checks, and a recorded human-review decision. Migration scripts or adapters remain isolated from the V2 domain model so legacy irregularities do not become new contracts.

## 6. Information Architecture

The workbench has five primary views:

1. **PROJECT**
   - Research purpose, population, context domains, generation mode, and project status.
   - A compact research-lineage section for verified 2023 evidence.
   - Entry points to the prepared demo and live generation.

2. **CONSTRUCT MAP**
   - Five domains, 15 facets, and source anchors.
   - Facet definition, observable indicators, exclusions, confounds, and source direction.
   - A domain-specific interactive construct fingerprint rather than decorative imagery.

3. **GENERATION STUDIO**
   - Construct specification, scenario blueprint, response options, and quality checks as inspectable stages.
   - Main content in the center and persistent provenance/constraint context on the right.

4. **REVIEW**
   - A compact queue with domain, facet, context, quality flags, and review status.
   - Single-item editing, version comparison, reviewer notes, approve, and return-for-revision actions.

5. **PARTICIPANT VIEW**
   - A low-distraction Chinese preview of five items.
   - No construct labels, scoring keys, quality metadata, or personality interpretation.

Global navigation appears in a full-width dark header. A compact process rail supports the generation flow without duplicating global navigation.

## 7. Domain Model and Provenance

Each candidate item preserves the following chain:

```text
source anchor
-> Big Five domain and facet
-> observable behavioral indicators
-> adolescent scenario constraints and blueprint
-> four response options and scoring key
-> automated quality checks
-> human review versions
-> current evidence status
```

Core records are:

- `ProjectConfig`: population, age band, locale, context domains, reading constraints, safety constraints, model/prompt version, and generation mode.
- `ConstructAnchor`: source item, domain, facet, source direction, definition, behavioral indicators, exclusions, and potential confounds.
- `ScenarioBlueprint`: setting, actors/relationship, goal, trigger event, decision point, context domain, and constraint snapshot.
- `CandidateItem`: Chinese stem, instruction, four options, display order, provenance IDs, generation metadata, and evidence status.
- `ResponseOption`: visible behavior, target-facet expression level, score, concise behavioral rationale, and social-desirability note.
- `QualityCheck`: check name, severity, result, concise evidence, and recommended action.
- `ReviewVersion`: timestamp, before/after content, reviewer note, action, and resulting status.

The source-anchor direction and any reverse-key metadata remain explicit. Options represent four increasing levels of the target facet and carry scores 1-4 internally, but their visible order is not correlated with score. Demo ordering is seeded for repeatability.

Evidence status uses only:

- `MODEL_DRAFT`
- `NEEDS_REVISION`
- `HUMAN_REVIEWED`
- `PILOT_CANDIDATE`

The interface must never label an item `VALIDATED` without empirical evidence.

## 8. Generation and Review Pipeline

### Stage 1: Project constraints

Apply the 12-15 age band, mainland Chinese context, language/readability target, allowed scenario domains, response format, and sensitive-content restrictions.

### Stage 2: Construct specification

Use source items as traceable anchors and the facet as the actual generation unit. Produce a concise construct definition, observable behaviors, exclusions, and likely confounds. Mechanical sentence-to-story paraphrasing is rejected.

The construct map follows the BFI-2 five-domain, 15-facet organization. The interface can show legacy/common labels alongside BFI-2 terminology where necessary, particularly for Openness/Open-Mindedness and Neuroticism/Negative Emotionality.

### Stage 3: Scenario blueprint

Generate the setting, actors, relationship, goal, trigger, and decision point before writing response options. The blueprint must be plausible for a 12-15-year-old and must not directly name the measured trait.

### Stage 4: Behavioral options

Generate four plausible answers to the instruction: "如果是你，你最可能怎么做？"

Options vary in target-facet expression while remaining reasonably balanced in length, readability, and social desirability. High-trait behavior must not automatically be the morally correct answer. Each option receives a hidden score and concise observable-behavior rationale.

### Stage 5: Quality checks

Deterministic checks cover schema completeness, option count, duplicate content, length balance, missing provenance, and forbidden status transitions.

Model-assisted checks cover:

- age and cultural appropriateness;
- ecological plausibility;
- construct alignment;
- contamination by other traits;
- option distinguishability;
- social-desirability leakage;
- answer obviousness;
- language complexity and safety.

Automated checks are advisory. A human reviewer remains responsible for approval.

### Stage 6: Human review

The reviewer can edit the stem and options, add a note, approve, or return the item. Every edit creates a review version rather than overwriting provenance.

### Stage 7: Preview and export

The participant view renders approved demo candidates. JSON retains the complete record; CSV flattens item and option fields for inspection. Preview responses are session-only and do not create a report.

## 9. Model Integration

The model layer is provider-adaptable. V2 ships with one OpenAI-compatible adapter and obtains provider, model name, and API key from environment configuration. The model name is never hard-coded into the research records by the UI.

Each generation stage requests schema-constrained JSON. Invalid output receives one repair/retry attempt. A second failure preserves all completed work and offers the curated demo path.

The system records model identifier, prompt-template version, generation timestamp, input constraint snapshot, and structured output. It does not request, expose, or store private chain-of-thought. Provenance consists of inspectable inputs, outputs, concise rationales, checks, and human edits.

## 10. Runtime Modes and Error Handling

### LIVE GENERATION

- Calls the configured model.
- Shows the active model identifier and live status.
- Generates one item at a time for the demonstration.

### CURATED DEMO

- Loads locally stored, human-inspected examples.
- Is clearly labeled as curated content.
- Supports the complete navigation, provenance, review, preview, and export workflow without a network or API key.

Startup validates configuration without blocking access to the app. Missing credentials disable live generation only. Model timeouts, malformed output, and service errors produce concise user-facing messages; raw stack traces remain out of the interface. Streamlit session state preserves completed stages across reruns.

## 11. Visual System

The visual reference is [Alto Neuroscience Platform](https://altoneuroscience.com/platform/#overview), adapted from a marketing site into a compact research workspace.

### Design principles

- High-contrast black and white foundation.
- Magenta for active navigation and primary actions.
- Cyan for provenance and model-generated information.
- Orange for warnings and revision states.
- Deep purple for construct/theory information.
- Saturated color is semantic and sparse, not decorative.
- Full-width light/dark bands create hierarchy; nested cards are avoided.
- Controls and tables remain dense, predictable, and work-focused.

### Color tokens

```text
Ink          #0B0B0D
Paper        #F7F7F5
Text         #202124
Magenta      #D81B78
Cyan         #24A8D8
Orange       #F28C28
Deep Purple  #40358C
```

The five domains receive distinct secondary markers, but primary controls retain a consistent action color.

### Typography and language

The workspace shell, global navigation, workflow labels, and compact scientific metadata are English-first. Big Five facet names may include a smaller Chinese alias where it prevents ambiguity. Chinese is mandatory for assessment instructions, stems, options, and adolescent-facing content.

Latin text uses a bundled Source Sans 3 webfont with a light heading weight. Chinese uses Microsoft YaHei on the target Windows demo machine, followed by Noto Sans SC and generic sans-serif fallbacks. The stack must remain functional offline. Headings inside the workbench stay in the 28-36px range; body text stays in the 15-17px range. Letter spacing is zero.

### Layout

- Full-width black global header.
- Compact left process navigation where needed.
- White main work surface.
- Persistent right provenance inspector in authoring views.
- Stable responsive grid at common presentation widths.
- Cards use at most an 8px radius and only frame individual records or tools.

The signature visualization is a functional Big Five construct fingerprint showing five domains, 15 facets, and selected-anchor relationships. It draws inspiration from Alto's layered scientific graphics without copying its brain illustration or brand identity.

## 12. Security and Privacy

- API keys are read only from environment variables.
- Keys never appear in UI state, generated records, exports, or logs.
- Legacy credential-bearing files and logs are not imported into V2.
- V2 collects no real adolescent or participant data.
- Participant-preview responses remain in memory for the current session.
- Exports contain candidate-item research metadata, not personal data.

## 13. Demo Script

The stable 6-8 minute path is:

1. Open the prepared project and establish the 2023 research lineage.
2. Select one domain/facet and inspect source anchors and behavioral indicators.
3. Confirm the 12-15-year-old context constraints.
4. Show or live-generate a scenario blueprint.
5. Generate four behavioral options.
6. Inspect provenance and quality flags.
7. Make one visible human edit and mark the item reviewed.
8. Open the five-item participant preview.
9. Close with the future construct-module roadmap.

The backup path performs the same steps entirely with curated local content.

## 14. Verification

### Automated checks

- Domain-model serialization and validation.
- Required provenance and exactly four options.
- Score/display-order independence.
- Review-status transitions and immutable version creation.
- JSON and CSV export shape.
- Missing API key, successful model response, malformed response, repair failure, and timeout behavior using mocked calls.
- App import/startup smoke test.

### Manual and visual checks

- Complete the live and curated demo scripts from a clean launch.
- Verify no state loss during Streamlit reruns.
- Check 1440x900 and 1280x720 research-workbench viewports, plus a 390x844 participant-preview viewport.
- Confirm no clipped navigation, overlapping text, truncated Chinese options, or inaccessible right-panel content.
- Confirm the participant view hides construct and score metadata.
- Confirm model/evidence status labels are truthful in every mode.

## 15. Acceptance Criteria

The first stage is complete when:

1. V2 launches through one documented command.
2. All five primary views are usable from the prepared project.
3. One item can traverse every pipeline stage and retain provenance.
4. Five curated Chinese items support a complete participant preview.
5. The app remains fully demonstrable without network access or credentials.
6. No participant profile or empirical-validation claim is produced.
7. Automated checks pass and browser screenshots confirm the main layouts are coherent.
8. The legacy system and research artifacts remain untouched.

## 16. Evolution After the Demo

After the stable Streamlit release, preserve the Python domain layer and evolve in this order:

1. Expand expert review and full-item-bank authoring.
2. Add pilot-data collection and psychometric analysis as a separate evidence module.
3. Define construct-specific task adapters for emotion regulation, impulsivity, attention/control, and psychopathology-related phenotypes.
4. Expose the domain services through FastAPI.
5. Add a React client, authentication, database persistence, and multi-user collaboration.

Personality, executive-function, and psychopathology modules may share project, provenance, review, and evidence infrastructure, but they must not share measurement or scoring logic merely by changing prompts.
