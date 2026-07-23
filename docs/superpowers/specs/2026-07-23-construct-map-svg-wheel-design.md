# Construct Map Responsive SVG Wheel Design

## Goal

Replace the Plotly Sunburst used only on Construct Map with a responsive SVG wheel that gives facet labels more radial space and enforces one consistent reading direction.

## Why the Renderer Changes

Plotly Sunburst 5.24.1 supports only trace-wide text orientations (`horizontal`, `radial`, `tangential`, and `auto`). It does not expose different inner/outer ring widths or per-segment text angles. The approved design therefore requires a small purpose-built SVG renderer rather than further Plotly parameter changes.

## Geometry

The SVG uses a square `0 0 600 600` view box centered at `(300, 300)`.

- Outer radius: `292` units.
- Domain radius: `123` units, approximately 42% of the outer radius.
- Facet band: `169` units, approximately 58% of the radius.
- Maximum rendered width: `600px`; width remains `100%` within the existing chart column.
- Domain sectors: five equal 72-degree wedges.
- Facet sectors: fifteen equal 24-degree annular wedges.

The domain and facet order remains the insertion order of `DOMAINS` and `FACETS`. The first boundary stays at the rightmost horizontal radius and sectors proceed counterclockwise, preserving the current visual sequence and color grouping.

## Labels

The five domain aliases (`E`, `A`, `C`, `N`, `O` in taxonomy order) remain upright relative to the page. They use centered text positioned within each domain wedge and have no rotation transform.

Each facet label begins near the outer edge and extends toward the center. Its rotation is fixed rather than delegated to a chart library:

| Facet label | Rotation |
| --- | ---: |
| Social | 168 degrees |
| Assert | 144 degrees |
| Energy | 120 degrees |
| Compassion | 96 degrees |
| Respect | 72 degrees |
| Trust | 48 degrees |
| Organized | 24 degrees |
| Productive | 0 degrees |
| Responsible | -24 degrees |
| Anxiety | -48 degrees |
| Depression | -72 degrees |
| Volatility | -96 degrees |
| Curiosity | -120 degrees |
| Aesthetic | -144 degrees |
| Creative | -168 degrees |

This makes every word read from the outer circumference toward the center. `Productive` remains left-to-right and `Energy` reverses from its previous center-to-edge direction, matching the approved reference.

Facet text uses 19 SVG units and domain letters use 22 SVG units. At the narrow acceptance width, the responsive scale keeps facet text at approximately 11.4 CSS pixels while the thicker band keeps the longest labels inside their sectors.

## Component Boundary

A new pure Python module, `psychometric_v2/ui/construct_wheel.py`, owns SVG geometry and markup. Its public function accepts the existing domain and facet mappings and returns one continuous, escaped SVG HTML string.

`construct_map.py` remains responsible for Streamlit layout and renders the returned markup with `unsafe_allow_html=True`. The right-side facet selector, construct details, source anchors, session state, and service boundary do not change.

The SVG uses existing Source Sans styling and taxonomy colors. Segment paths keep the current off-white two-unit separators. No JavaScript, remote asset, runtime dependency, custom Streamlit component, or data/export change is introduced.

## Hover And Accessibility

Every domain and facet path contains a native SVG `<title>` with the complete formal English and Chinese names. Dynamic labels, colors, IDs, and tooltip text are HTML/XML-escaped. The root SVG has an accessible bilingual description, and each segment exposes a matching `aria-label`.

The wheel remains informational: it does not add click navigation or mutation. This preserves the page's current interaction model, where the adjacent selectbox controls the active facet.

## Testing

Pure unit tests parse the generated SVG with `xml.etree.ElementTree` and verify:

- exactly five domain paths, fifteen facet paths, and twenty titles;
- domain/facet order, colors, formal bilingual tooltip content, and escaped markup;
- the `292` outer radius and `123` domain radius geometry contract;
- all domain label transforms contain translation only;
- all fifteen facet transforms contain the approved rotation sequence;
- `Productive` is `0` degrees and `Energy` is `120` degrees;
- the SVG payload has no Markdown code-block indentation.

The existing Construct Map AppTest continues to verify all four source anchors and absence of indented HTML.

## Browser Acceptance

At `1280x720` and `760x900`:

- the SVG remains square, centered, and contained within the chart column;
- the domain boundary is approximately 42% of the outer radius;
- all twenty labels are visible and remain inside the SVG bounds;
- every facet reads from the outer edge toward the center;
- `Compassion`, `Responsible`, and `Depression` render completely;
- OCEAN letters remain upright;
- the wheel does not overlap or compress the detail panel;
- four source rows remain readable, with no raw HTML or copy-code control.

