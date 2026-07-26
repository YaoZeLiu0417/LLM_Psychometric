from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets" / "readme"
FONT_PATH = ROOT / "psychometric_v2" / "assets" / "fonts" / "SourceSans3-Variable.ttf"

BLACK = "#0B0B0D"
MAGENTA = "#D81B78"
VIOLET = "#40358C"
CYAN = "#24A8D8"
ORANGE = "#EF5A24"
NEUTRAL = "#F5F5F6"
WHITE = "#FFFFFF"

GIF_SIZE = (960, 540)
FRAMES_PER_SCENE = 64
TRANSITION_FRAMES = 8
FRAME_COUNT = 320
PROGRESS_HEIGHT = 4
PALETTE_COLORS = 64


def _font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_PATH), size)
    font.set_variation_by_name("SemiBold")
    return font


def _screenshot(name: str) -> Image.Image:
    with Image.open(ASSET_DIR / name) as image:
        image.load()
        return image.convert("RGB")


def _paste_capture(
    canvas: Image.Image, capture: Image.Image, box: tuple[int, int, int, int]
) -> None:
    fitted = ImageOps.fit(
        capture,
        (box[2] - box[0], box[3] - box[1]),
        method=Image.Resampling.LANCZOS,
    )
    canvas.paste(fitted, box[:2])
    ImageDraw.Draw(canvas).rectangle(
        (box[0], box[1], box[2] - 1, box[3] - 1), outline=BLACK, width=2
    )


def build_overview() -> None:
    canvas = Image.new("RGB", (1600, 900), NEUTRAL)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1599, 117), fill=BLACK)
    draw.text(
        (48, 53),
        "ADOLESCENT BIG FIVE WORKBENCH",
        font=_font(28),
        fill=WHITE,
        anchor="lm",
    )
    draw.rectangle((48, 86, 398, 90), fill=MAGENTA)
    draw.text(
        (1552, 57),
        "FROM CONSTRUCT TO CANDIDATE",
        font=_font(24),
        fill=WHITE,
        anchor="rm",
    )

    draw.rectangle((48, 154, 1041, 845), fill=WHITE, outline=BLACK, width=2)
    draw.rectangle((48, 154, 1041, 197), fill=BLACK)
    draw.text((66, 175), "01  CONSTRUCT MAP", font=_font(20), fill=WHITE, anchor="lm")
    _paste_capture(
        canvas, _screenshot("construct-map.png"), (48, 242, 1042, 801)
    )

    rail = (
        (154, 370, MAGENTA, "02  GENERATION STUDIO", "generation-studio.png"),
        (392, 608, CYAN, "03  HUMAN REVIEW", "review-workbench.png"),
        (630, 846, ORANGE, "04  PARTICIPANT VIEW", "participant-view.png"),
    )
    for top, bottom, color, label, source in rail:
        draw.rectangle((1070, top, 1551, top + 39), fill=color)
        label_color = WHITE if color == MAGENTA else BLACK
        draw.text((1088, top + 20), label, font=_font(18), fill=label_color, anchor="lm")
        _paste_capture(canvas, _screenshot(source), (1070, top + 40, 1552, bottom))

    canvas.save(ASSET_DIR / "workbench-overview.png", format="PNG", compress_level=9)


def build_construct_flow() -> None:
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="construct-title construct-description">
  <title id="construct-title">Research responsibility map from construct anchors to pilot candidates</title>
  <desc id="construct-description">Three responsibility zones separate theoretical inputs, model-assisted authoring, and researcher-owned governance while reserving empirical validation for future research.</desc>
  <style>
    text { font-family: "Source Sans 3", Arial, sans-serif; letter-spacing: 0; fill: #0B0B0D; }
    .kicker { font-size: 20px; font-weight: 700; }
    .header-title { font-size: 32px; font-weight: 650; }
    .zone-label { font-size: 18px; font-weight: 700; }
    .zone-title { font-size: 29px; font-weight: 700; }
    .zone-subtitle { font-size: 20px; font-weight: 500; }
    .item-label { font-size: 17px; font-weight: 700; }
    .item { font-size: 20px; font-weight: 500; }
    .boundary { font-size: 17px; font-weight: 700; }
    .footer-main { font-size: 23px; font-weight: 700; }
    .footer-note { font-size: 17px; font-weight: 400; }
    .on-dark { fill: #FFFFFF; }
  </style>
  <rect width="1600" height="900" fill="#F5F5F6"/>
  <rect width="1600" height="118" fill="#0B0B0D"/>
  <text class="kicker on-dark" x="48" y="40">RESEARCH RESPONSIBILITY MAP</text>
  <text class="header-title on-dark" x="48" y="82">From construct anchors to pilot candidates</text>
  <rect x="1242" y="94" width="310" height="4" fill="#D81B78"/>

  <rect x="48" y="154" width="459" height="610" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="48" y="154" width="459" height="48" fill="#40358C"/>
  <text class="zone-label on-dark" x="68" y="185">01 / THEORETICAL INPUTS</text>
  <text class="zone-title" x="68" y="250">Theoretical Inputs</text>
  <text class="zone-subtitle" x="68" y="282" fill="#6B6B70">Source anchors and scoring direction</text>
  <line x1="68" y1="306" x2="487" y2="306" stroke="#D7D7DA" stroke-width="2"/>
  <text class="item-label" x="68" y="340" fill="#40358C">TRACEABLE IDENTIFIERS</text>
  <text class="item" x="68" y="372">Anchor ID / source / direction</text>
  <text class="item-label" x="68" y="430" fill="#40358C">Construct specification</text>
  <text class="item" x="68" y="463">Facet definition</text>
  <text class="item" x="68" y="495">Observable behaviors</text>
  <text class="item-label" x="68" y="553" fill="#40358C">Exclusions and confounds</text>
  <text class="item" x="68" y="586">Defined before generation</text>
  <rect x="68" y="690" width="419" height="50" fill="#F5F5F6" stroke="#40358C" stroke-width="2"/>
  <text class="boundary" x="277.5" y="721" text-anchor="middle">RESEARCHER-DEFINED BOUNDARY</text>

  <line x1="522" y1="459" x2="550" y2="459" stroke="#0B0B0D" stroke-width="3"/>
  <path d="M550 451 L565 459 L550 467 Z" fill="#0B0B0D"/>

  <rect x="570" y="154" width="459" height="610" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="570" y="154" width="459" height="48" fill="#D81B78"/>
  <text class="zone-label on-dark" x="590" y="185">02 / STRUCTURED PROPOSAL</text>
  <text class="zone-title" x="590" y="250">Model-Assisted Authoring</text>
  <text class="zone-subtitle" x="590" y="282" fill="#6B6B70">Adolescent scenario blueprint</text>
  <line x1="590" y1="306" x2="1009" y2="306" stroke="#D7D7DA" stroke-width="2"/>
  <text class="item-label" x="590" y="340" fill="#D81B78">CONTEXT CONSTRAINTS</text>
  <text class="item" x="590" y="372">Mainland Chinese, ages 12-15</text>
  <text class="item-label" x="590" y="430" fill="#D81B78">Observable response options</text>
  <text class="item" x="590" y="463">Four actions / hidden scores / rationales</text>
  <text class="item-label" x="590" y="521" fill="#D81B78">Automated structural checks</text>
  <text class="item" x="590" y="554">Schema / count / rationale presence</text>
  <rect x="590" y="690" width="419" height="50" fill="#F5F5F6" stroke="#D81B78" stroke-width="2"/>
  <text class="boundary" x="799.5" y="721" text-anchor="middle">MODEL-GENERATED PROPOSAL</text>

  <line x1="1044" y1="459" x2="1072" y2="459" stroke="#0B0B0D" stroke-width="3"/>
  <path d="M1072 451 L1087 459 L1072 467 Z" fill="#0B0B0D"/>

  <rect x="1092" y="154" width="460" height="610" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="1092" y="154" width="460" height="48" fill="#EF5A24"/>
  <text class="zone-label" x="1112" y="185">03 / ACCOUNTABLE DECISION</text>
  <text class="zone-title" x="1112" y="250">Human Governance</text>
  <text class="zone-subtitle" x="1112" y="282" fill="#6B6B70">Edit and inspect</text>
  <line x1="1112" y1="306" x2="1532" y2="306" stroke="#D7D7DA" stroke-width="2"/>
  <text class="item-label" x="1112" y="340" fill="#EF5A24">ACCOUNTABLE REVIEW</text>
  <text class="item" x="1112" y="372">Rationale / reviewer / content approval</text>
  <text class="item" x="1112" y="406">Review history</text>
  <rect x="1112" y="450" width="218" height="44" fill="#0B0B0D"/>
  <text class="item-label on-dark" x="1221" y="478" text-anchor="middle">PILOT_CANDIDATE</text>
  <rect x="1112" y="512" width="400" height="44" fill="#EF5A24"/>
  <text class="item-label" x="1312" y="540" text-anchor="middle">EMPIRICAL VALIDATION REQUIRED</text>
  <rect x="1112" y="690" width="420" height="50" fill="#F5F5F6" stroke="#EF5A24" stroke-width="2"/>
  <text class="boundary" x="1322" y="721" text-anchor="middle">RESEARCHER-OWNED DECISION</text>

  <rect x="0" y="806" width="1600" height="94" fill="#0B0B0D"/>
  <text class="footer-main on-dark" x="800" y="846" text-anchor="middle">MODEL PROPOSES &#183; RESEARCHER DECIDES &#183; DATA VALIDATE</text>
  <text class="footer-note on-dark" x="800" y="877" text-anchor="middle">Workflow state is not evidence of reliability, validity, or measurement invariance.</text>
</svg>
"""
    (ASSET_DIR / "construct-to-candidate.svg").write_text(
        svg, encoding="utf-8", newline="\n"
    )


def build_architecture() -> None:
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="architecture-title architecture-description">
  <title id="architecture-title">Implemented research workbench architecture</title>
  <desc id="architecture-description">Four connected layers show the implemented Streamlit views, application services, typed research domain, and adapters and storage, without claiming React or FastAPI components.</desc>
  <style>
    text { font-family: "Source Sans 3", Arial, sans-serif; letter-spacing: 0; fill: #0B0B0D; }
    .kicker { font-size: 20px; font-weight: 700; }
    .header-title { font-size: 32px; font-weight: 650; }
    .layer-index { font-size: 17px; font-weight: 700; }
    .layer-title { font-size: 26px; font-weight: 700; }
    .component { font-size: 20px; font-weight: 600; }
    .footer { font-size: 20px; font-weight: 500; }
    .footer-claim { font-size: 20px; font-weight: 700; }
    .on-dark { fill: #FFFFFF; }
  </style>
  <rect width="1600" height="900" fill="#F5F5F6"/>
  <rect width="1600" height="118" fill="#0B0B0D"/>
  <text class="kicker on-dark" x="48" y="40">IMPLEMENTED SYSTEM BOUNDARIES</text>
  <text class="header-title on-dark" x="48" y="82">Research workbench architecture</text>
  <rect x="1242" y="94" width="310" height="4" fill="#24A8D8"/>

  <rect x="48" y="144" width="1504" height="126" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="48" y="144" width="414" height="126" fill="#24A8D8"/>
  <text class="layer-index" x="72" y="179">01 / INTERFACE</text>
  <text class="layer-title" x="72" y="222">Streamlit Research Views</text>
  <text class="component" x="510" y="215">Project</text>
  <text class="component" x="675" y="215">Construct Map</text>
  <text class="component" x="921" y="215">Generation</text>
  <text class="component" x="1120" y="215">Review</text>
  <text class="component" x="1280" y="215">Participant View</text>

  <line x1="800" y1="270" x2="800" y2="286" stroke="#0B0B0D" stroke-width="3"/>
  <path d="M792 286 L800 298 L808 286 Z" fill="#0B0B0D"/>

  <rect x="48" y="298" width="1504" height="126" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="48" y="298" width="414" height="126" fill="#D81B78"/>
  <text class="layer-index on-dark" x="72" y="333">02 / ORCHESTRATION</text>
  <text class="layer-title on-dark" x="72" y="376">Application Services</text>
  <text class="component" x="510" y="369">Workflow state</text>
  <text class="component" x="745" y="369">Authorization</text>
  <text class="component" x="955" y="369">Generation coordination</text>
  <text class="component" x="1290" y="369">Review transitions</text>

  <line x1="800" y1="424" x2="800" y2="440" stroke="#0B0B0D" stroke-width="3"/>
  <path d="M792 440 L800 452 L808 440 Z" fill="#0B0B0D"/>

  <rect x="48" y="452" width="1504" height="126" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="48" y="452" width="414" height="126" fill="#40358C"/>
  <text class="layer-index on-dark" x="72" y="487">03 / RESEARCH OBJECTS</text>
  <text class="layer-title on-dark" x="72" y="530">Typed Research Domain</text>
  <text class="component" x="510" y="502">Anchors</text>
  <text class="component" x="800" y="502">Specifications</text>
  <text class="component" x="1130" y="502">Candidates</text>
  <text class="component" x="510" y="548">Quality checks</text>
  <text class="component" x="800" y="548">Review history</text>
  <text class="component" x="1130" y="548">Evidence state</text>

  <line x1="800" y1="578" x2="800" y2="594" stroke="#0B0B0D" stroke-width="3"/>
  <path d="M792 594 L800 606 L808 594 Z" fill="#0B0B0D"/>

  <rect x="48" y="606" width="1504" height="126" fill="#FFFFFF" stroke="#0B0B0D" stroke-width="2"/>
  <rect x="48" y="606" width="414" height="126" fill="#EF5A24"/>
  <text class="layer-index" x="72" y="641">04 / INFRASTRUCTURE</text>
  <text class="layer-title" x="72" y="684">Adapters and Storage</text>
  <text class="component" x="510" y="677">OpenAI-compatible client</text>
  <text class="component" x="850" y="660">
    <tspan x="850" dy="0">Session-isolated and durable JSON</tspan>
    <tspan x="850" dy="29">repositories</tspan>
  </text>
  <text class="component" x="1300" y="677">Reference exports</text>

  <rect x="0" y="772" width="1600" height="128" fill="#0B0B0D"/>
  <text class="footer on-dark" x="48" y="824">Domain and service boundaries support future interfaces.</text>
  <text class="footer-claim on-dark" x="48" y="862">No React or FastAPI implementation is claimed in this release.</text>
</svg>
"""
    (ASSET_DIR / "system-architecture.svg").write_text(
        svg, encoding="utf-8", newline="\n"
    )


def _walkthrough_scene(
    source: Image.Image, eyebrow: str, heading: str, accent: str
) -> Image.Image:
    scene = ImageOps.fit(
        source,
        GIF_SIZE,
        method=Image.Resampling.LANCZOS,
    ).convert("RGBA")
    overlay = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, 959, 102), fill=(0, 0, 0, 216))
    draw.rectangle((0, 0, 10, 102), fill=accent)
    draw.text((30, 18), eyebrow, font=_font(18), fill=accent)
    draw.text((30, 46), heading, font=_font(31), fill=WHITE)
    return Image.alpha_composite(scene, overlay).convert("RGB")


def _walkthrough_frame(
    scenes: list[Image.Image], scene_index: int, scene_frame_index: int
) -> Image.Image:
    if scene_index and scene_frame_index < TRANSITION_FRAMES:
        frame = Image.blend(
            scenes[scene_index - 1],
            scenes[scene_index],
            (scene_frame_index + 1) / TRANSITION_FRAMES,
        )
    else:
        frame = scenes[scene_index].copy()

    global_frame_index = scene_index * FRAMES_PER_SCENE + scene_frame_index
    progress_width = (global_frame_index + 1) * GIF_SIZE[0] // FRAME_COUNT
    draw = ImageDraw.Draw(frame)
    track_top = GIF_SIZE[1] - PROGRESS_HEIGHT
    draw.rectangle((0, track_top, GIF_SIZE[0] - 1, GIF_SIZE[1] - 1), fill=BLACK)
    draw.rectangle((0, track_top, progress_width - 1, GIF_SIZE[1] - 1), fill=MAGENTA)
    return frame


def build_walkthrough() -> None:
    scene_specs = (
        (
            "workbench-overview.png",
            "RESEARCH PREVIEW / READ-ONLY",
            "From the 2023 college-student project to an adolescent workbench",
            CYAN,
        ),
        (
            "construct-map.png",
            "01 / THEORETICAL INPUTS",
            "Inspect domains, facets, source anchors, and scoring direction",
            VIOLET,
        ),
        (
            "generation-studio.png",
            "02 / MODEL-ASSISTED AUTHORING",
            "Review construct, blueprint, options, rationales, and checks",
            MAGENTA,
        ),
        (
            "review-workbench.png",
            "03 / HUMAN GOVERNANCE",
            "Inspect provenance, edit content, and record review decisions",
            CYAN,
        ),
        (
            "participant-view.png",
            "04 / PARTICIPANT PREVIEW",
            "Preview pilot candidates without scores or personality feedback",
            ORANGE,
        ),
    )
    scenes = [
        _walkthrough_scene(_screenshot(source), eyebrow, heading, accent)
        for source, eyebrow, heading, accent in scene_specs
    ]

    first_frame = _walkthrough_frame(scenes, 0, 0)
    palette = first_frame.quantize(
        colors=PALETTE_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    gif_frames = [first_frame.quantize(palette=palette, dither=Image.Dither.NONE)]
    for global_frame_index in range(1, FRAME_COUNT):
        scene_index, scene_frame_index = divmod(global_frame_index, FRAMES_PER_SCENE)
        frame = _walkthrough_frame(scenes, scene_index, scene_frame_index)
        gif_frames.append(frame.quantize(palette=palette, dither=Image.Dither.NONE))

    # GIF delays use 10 ms units, so alternate around 125 ms to preserve 8 fps.
    # Disposal 1 keeps unchanged pixels available for compact delta frames.
    frame_durations = [120 + 10 * (index % 2) for index in range(FRAME_COUNT)]
    gif_frames[0].save(
        ASSET_DIR / "workbench-walkthrough.gif",
        format="GIF",
        save_all=True,
        append_images=gif_frames[1:],
        duration=frame_durations,
        loop=0,
        disposal=1,
        optimize=True,
    )


def main() -> None:
    build_overview()
    build_construct_flow()
    build_architecture()
    build_walkthrough()


if __name__ == "__main__":
    main()
