# Construct Map Visual Fix Design

## Goal

Make the Construct Map readable and presentation-ready without changing the Big Five taxonomy, construct identifiers, source anchors, or measurement content.

## Confirmed Scope

The fix covers two defects on the existing Construct Map page:

1. The sunburst hides long labels or lets them crowd the chart boundary at the width available in the two-column layout.
2. Indented multiline source-anchor markup is partially parsed as a Markdown code block, exposing raw HTML after the first anchor row.

No taxonomy definitions, item text, anchor direction, generation behavior, page navigation, or stored research data will change.

## Sunburst Design

The sunburst retains the existing five-domain inner ring and 15-facet outer ring. Formal English and Chinese construct names remain in `DOMAINS` and `FACETS`; the chart receives presentation-only aliases through a local mapping in the Construct Map page.

The inner ring uses the conventional Big Five letters:

| Formal domain | Wheel label |
| --- | --- |
| Extraversion | E |
| Agreeableness | A |
| Conscientiousness | C |
| Negative Emotionality | N |
| Open-Mindedness | O |

The outer ring uses readable short words:

| Formal facet | Wheel label |
| --- | --- |
| Sociability | Social |
| Assertiveness | Assert |
| Energy Level | Energy |
| Compassion | Compassion |
| Respectfulness | Respect |
| Trust | Trust |
| Organization | Organized |
| Productiveness | Productive |
| Responsibility | Responsible |
| Anxiety | Anxiety |
| Depression | Depression |
| Emotional Volatility | Volatility |
| Intellectual Curiosity | Curiosity |
| Aesthetic Sensitivity | Aesthetic |
| Creative Imagination | Creative |

Every segment keeps the complete formal English and Chinese names in Plotly `customdata`. Hover text displays both formal names, so the aliases never become measurement labels or exported values. The current colors, radial orientation, segment order, two-column layout, and restrained Alto-inspired visual language remain unchanged.

`textinfo="label"` will make the visible-label contract explicit. Font sizing and uniform-text behavior may be tuned only enough to keep the short labels legible; the implementation must not solve overflow by shrinking text below a readable size.

## Source-Anchor Rendering

The page will build the complete source list as continuous, unindented HTML. Each row retains the current anchor ID, Chinese item text, and forward/reverse badge.

All dynamic values continue to pass through HTML escaping. Rendering remains local to Streamlit with `unsafe_allow_html=True`; no script, external component, or new dependency is introduced.

The markup builder will be a small pure helper so tests can verify:

- four rows are emitted for the selected facet;
- no line begins with Markdown code-block indentation;
- anchor IDs and item text remain escaped;
- forward/reverse labels remain accurate.

## Verification

Automated tests will first fail against the current implementation, then cover both contracts:

- the sunburst uses the approved display aliases while hover data preserves complete English and Chinese names;
- Construct Map source-list markup contains all four rows and cannot be parsed as an indented code block.

After focused and full Python tests pass, browser verification will reload the running Streamlit app and check desktop and narrow viewports. Acceptance requires:

- all five domain labels and all 15 facet labels are visible and contained by the chart;
- the wheel remains legible without overlapping the adjacent detail panel;
- no raw `<div class="source-row">` text or copy-code control appears;
- all four source anchors render as styled rows;
- hover exposes the complete bilingual construct name.

