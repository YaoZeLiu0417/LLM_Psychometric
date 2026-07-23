# Participant Pilot Preview Design

## Goal

Make Participant View display generated items only after they have been explicitly promoted to `PILOT_CANDIDATE`, while retaining curated reference items as the default preview when no pilot candidates exist.

## Eligibility And Precedence

Participant View selects its item pool in this order:

1. Collect every project item whose `evidence_status` is `PILOT_CANDIDATE`.
2. If at least one pilot candidate exists, display only that pilot-candidate pool.
3. Otherwise, display the first five `CURATED` items as the reference fallback.

Generation mode does not independently exclude a pilot candidate. A generated `LIVE` item therefore becomes participant-visible after promotion. `MODEL_DRAFT`, `NEEDS_REVISION`, and `HUMAN_REVIEWED` items remain hidden from participants.

## Scope

The change is limited to the item-pool selector in `psychometric_v2/ui/pages/participant.py` and focused Streamlit smoke tests. It does not change generation, review transitions, persistence, scoring, response storage, navigation, or visual styling.

## Verification

Tests must prove that:

- A pilot candidate replaces the curated fallback pool and is immediately visible as item `1 / 1`.
- A `HUMAN_REVIEWED` live item is not participant-visible.
- With no pilot candidates, the existing five-item curated preview remains unchanged.
- A project with neither pilot candidates nor curated items still reports `Preview unavailable`.

