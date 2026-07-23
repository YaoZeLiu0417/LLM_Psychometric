# Construct Map Wheel Scale Design

## Goal

Give the Construct Map wheel slightly more visual presence and breathing room for its longest facet labels while keeping the approved two-column workbench layout intact.

## Approved Change

The Plotly figure height increases from `520px` to `560px`, and all four layout margins decrease from `8px` to `4px`. This produces an approximately 8% larger wheel in the current desktop chart column without reducing the width of the adjacent facet detail panel.

The sunburst text orientation changes from forced `radial` to Plotly `auto`. The five single-letter domain labels (`O`, `C`, `E`, `A`, `N`) must remain upright relative to the page rather than rotating around the wheel. Plotly may continue to orient longer outer-ring labels to fit their facets.

## Preserved Behavior

The change does not alter:

- domain or facet IDs, order, values, colors, or hierarchy;
- approved wheel aliases or formal bilingual hover data;
- source-anchor content, markup, badges, or responsive source-row layout;
- the `1.22:1` chart/detail column ratio;
- font family, font size, uniform-text threshold, or page typography.

No dependency, custom annotation layer, JavaScript override, or exported data change is introduced.

## Verification

Automated coverage will assert the `560px` height, `4px` margins, and `auto` orientation while retaining the existing alias and hover contracts.

Browser acceptance at `1280x720` and `760x900` requires:

- all 20 wheel labels have non-zero rendered bounds;
- no label extends outside the Plotly chart container;
- OCEAN letters are upright rather than radially rotated;
- `Compassion`, `Responsible`, and `Depression` have visibly more breathing room;
- the wheel does not overlap or compress the facet detail panel;
- all four source anchors remain readable, with no raw HTML or code-copy control.

