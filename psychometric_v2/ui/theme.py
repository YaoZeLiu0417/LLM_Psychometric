from __future__ import annotations

from base64 import b64encode
from functools import lru_cache

import streamlit as st

from psychometric_v2.config import FONT_ASSET


@lru_cache(maxsize=1)
def _font_data_uri() -> str:
    encoded = b64encode(FONT_ASSET.read_bytes()).decode("ascii")
    return f"data:font/ttf;base64,{encoded}"


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'Source Sans 3';
            src: url('{_font_data_uri()}') format('truetype');
            font-style: normal;
            font-weight: 200 900;
            font-display: swap;
        }}

        :root {{
            --ink: #0B0B0D;
            --paper: #F7F7F5;
            --text: #202124;
            --muted: #68696D;
            --line: #D9D9D5;
            --magenta: #D81B78;
            --cyan: #24A8D8;
            --orange: #F28C28;
            --purple: #40358C;
            --negative: #E44B5F;
        }}

        html, body, [class*="st-"] {{
            font-family: 'Source Sans 3', Arial, sans-serif;
            letter-spacing: 0 !important;
        }}
        html, body, p, li, label, input, button {{
            font-size: 16px;
            color: var(--text);
        }}
        .stApp {{ background: var(--paper); }}
        .main .block-container {{
            max-width: 1480px;
            padding: 1rem 2rem 3rem;
        }}
        h1, h2, h3, h4 {{
            color: var(--ink);
            letter-spacing: 0 !important;
        }}
        h1 {{ font-size: 34px !important; line-height: 1.08 !important; }}
        h2 {{ font-size: 28px !important; line-height: 1.14 !important; }}
        h3 {{ font-size: 20px !important; line-height: 1.2 !important; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{ display: none; }}

        .zh-content {{
            font-family: 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
            letter-spacing: 0 !important;
        }}
        .top-shell {{
            background: var(--ink);
            color: white;
            border: 1px solid var(--ink);
            padding: 18px 22px;
            margin: 0 0 10px;
        }}
        .top-row {{
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 20px;
        }}
        .top-eyebrow {{
            color: #BFC0C3;
            font-size: 12px;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 5px;
        }}
        .top-title {{
            color: white;
            font-size: 32px;
            font-weight: 760;
            line-height: 1.05;
        }}
        .top-subtitle {{
            color: #D8D8DA;
            font-size: 15px;
            margin-top: 5px;
        }}
        .top-badges {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 6px;
        }}
        .mode-badge, .availability-badge, .status-badge {{
            display: inline-block;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 750;
            line-height: 1.2;
            padding: 5px 8px;
        }}
        .mode-badge {{ background: var(--magenta); color: white; }}
        .availability-badge {{
            background: transparent;
            border: 1px solid #6E6E72;
            color: #E7E7E8;
        }}
        .status-model-draft {{ background: var(--magenta); color: white; }}
        .status-needs-revision {{ background: var(--orange); color: var(--ink); }}
        .status-human-reviewed {{ background: var(--cyan); color: var(--ink); }}
        .status-pilot-candidate {{ background: var(--purple); color: white; }}
        .status-pass {{ background: #DFF2E8; color: #155E3D; }}
        .status-flag {{ background: #FCE5E9; color: #9D1D35; }}
        .status-review {{ background: #E3F3F8; color: #11617C; }}

        [data-testid="stSegmentedControl"] {{
            background: white;
            border-bottom: 1px solid var(--ink);
            padding: 4px 0 8px;
            margin-bottom: 22px;
        }}
        [data-testid="stSegmentedControl"] button {{
            min-height: 36px;
            border-radius: 3px !important;
            font-size: 13px !important;
            font-weight: 700;
            white-space: normal;
        }}
        [data-testid="stMetric"] {{
            background: white;
            border-top: 3px solid var(--ink);
            border-radius: 0;
            padding: 12px 14px;
            min-height: 100px;
        }}
        [data-testid="stMetricLabel"] {{ min-height: 36px; }}
        [data-testid="stMetricValue"] {{ font-size: 27px; }}
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--line);
            border-radius: 4px;
            overflow: hidden;
        }}
        [data-testid="stPlotlyChart"] {{
            min-height: 500px;
            width: 100%;
        }}

        .page-kicker, .section-label, .field-label {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 760;
            line-height: 1.25;
        }}
        .workspace-heading {{
            color: var(--ink);
            font-size: 32px;
            font-weight: 760;
            line-height: 1.08;
            margin: 4px 0 18px;
        }}
        .project-band {{
            background: var(--ink);
            color: white;
            border-left: 6px solid var(--magenta);
            padding: 18px 20px;
            margin-bottom: 18px;
        }}
        .project-band h2 {{
            color: white;
            font-size: 30px !important;
            margin: 0 0 6px;
        }}
        .project-meta {{
            color: #D5D5D7;
            display: flex;
            flex-wrap: wrap;
            gap: 8px 18px;
            margin-bottom: 10px;
        }}
        .project-boundary {{
            color: white;
            font-size: 16px;
            font-weight: 650;
        }}
        .lineage-band {{
            border-top: 1px solid var(--ink);
            border-bottom: 1px solid var(--ink);
            color: var(--ink);
            font-size: 14px;
            font-weight: 760;
            margin: 20px 0 26px;
            padding: 11px 0;
            overflow-wrap: anywhere;
        }}
        .section-heading {{
            border-bottom: 2px solid var(--ink);
            color: var(--ink);
            font-size: 21px;
            font-weight: 760;
            margin: 28px 0 12px;
            padding-bottom: 7px;
        }}
        .evidence-note {{
            border-left: 4px solid var(--orange);
            color: var(--text);
            margin-top: 12px;
            padding: 8px 12px;
        }}
        .unit-statement {{
            background: var(--ink);
            color: white;
            font-size: 17px;
            font-weight: 680;
            margin: 0 0 18px;
            padding: 12px 15px;
        }}
        .detail-grid, .trace-grid, .stage-grid {{
            display: grid;
            gap: 10px;
        }}
        .detail-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
        .trace-grid {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
        .stage-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
        .detail-cell {{
            border-top: 2px solid var(--ink);
            min-width: 0;
            padding: 9px 0 4px;
        }}
        .detail-value {{
            color: var(--ink);
            font-size: 16px;
            font-weight: 650;
            overflow-wrap: anywhere;
        }}
        .stage-step {{
            background: white;
            border: 1px solid var(--line);
            border-radius: 4px;
            min-height: 78px;
            padding: 10px;
        }}
        .stage-step.is-active {{ border-top: 4px solid var(--magenta); }}
        .stage-number {{ color: var(--magenta); font-size: 12px; font-weight: 800; }}
        .stage-name {{
            color: var(--ink);
            font-size: 14px;
            font-weight: 720;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}
        .trace-record {{
            background: white;
            border: 1px solid var(--line);
            border-radius: 5px;
            padding: 13px;
        }}
        .trace-cell {{ min-width: 0; overflow-wrap: anywhere; }}
        .trace-value {{ color: var(--ink); font-size: 14px; font-weight: 650; }}
        .source-list {{ border-top: 1px solid var(--line); }}
        .source-row {{
            display: grid;
            grid-template-columns: 150px minmax(0, 1fr) 120px;
            gap: 12px;
            align-items: start;
            border-bottom: 1px solid var(--line);
            padding: 11px 0;
        }}
        .source-id {{ color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }}
        .source-text {{ color: var(--ink); font-size: 16px; }}
        .tool-band {{
            border-top: 3px solid var(--ink);
            margin: 18px 0;
            padding-top: 10px;
        }}
        .option-row {{
            background: white;
            border-left: 4px solid var(--cyan);
            margin: 7px 0;
            padding: 10px 12px;
        }}
        .assessment-shell {{
            border-top: 5px solid var(--ink);
            max-width: 860px;
            padding-top: 20px;
        }}
        .assessment-index {{ color: var(--muted); font-size: 13px; font-weight: 700; }}
        .assessment-instruction {{
            color: var(--ink);
            font-size: 18px;
            font-weight: 760;
            margin: 12px 0;
        }}
        .assessment-stem {{
            color: var(--ink);
            font-size: 20px;
            font-weight: 620;
            line-height: 1.55;
            margin-bottom: 16px;
        }}

        @media (max-width: 1280px) {{
            .main .block-container {{ padding-right: 1.25rem; padding-left: 1.25rem; }}
            .trace-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
        }}

        @media (max-width: 600px) {{
            .main .block-container {{ padding: .7rem .9rem 2rem; }}
            .top-shell {{ padding: 14px; }}
            .top-row {{ align-items: flex-start; flex-direction: column; }}
            .top-title {{ font-size: 28px; }}
            .top-badges {{ justify-content: flex-start; }}
            .workspace-heading {{ font-size: 28px; }}
            .detail-grid {{ grid-template-columns: 1fr; }}
            .trace-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .stage-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .source-row {{ grid-template-columns: 1fr; gap: 4px; }}
            [data-testid="stPlotlyChart"] {{ min-height: 420px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
