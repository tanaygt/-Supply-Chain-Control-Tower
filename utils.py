import uuid
from datetime import datetime

import streamlit as st

from database import init_db, load_all_data, save_all_data


def load_data() -> dict:
    init_db()
    return load_all_data()


def save_data(data: dict):
    init_db()
    save_all_data(data)


def gen_id(prefix: str) -> str:
    return f"{prefix}-{str(uuid.uuid4())[:6].upper()}"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def moving_average(values: list, window: int = 3) -> float:
    if not values:
        return 0
    tail = values[-window:] if len(values) >= window else values
    return round(sum(tail) / len(tail), 1)


def suggest_reorder(current_qty: int, avg_demand: float, lead_days: int = 7) -> int:
    safety_stock = avg_demand * 1.5
    return max(0, int((avg_demand * lead_days) + safety_stock - current_qty))


def is_dark() -> bool:
    return st.session_state.get("dark_mode", True)


def theme() -> dict:
    if is_dark():
        return {
            "bg": "#0F172A",
            "sidebar_bg": "#0B1120",
            "card": "#1E293B",
            "card2": "#162032",
            "border": "rgba(59,130,246,0.18)",
            "border_soft": "rgba(255,255,255,0.06)",
            "primary": "#3B82F6",
            "secondary": "#22C55E",
            "accent": "#FBBF24",
            "danger": "#EF4444",
            "warning": "#F59E0B",
            "safe": "#22C55E",
            "text": "#E5E7EB",
            "text_muted": "#64748B",
            "text_sub": "#94A3B8",
            "plotly_tmpl": "plotly_dark",
            "plot_bg": "#1E293B",
            "paper_bg": "#1E293B",
            "font_color": "#E5E7EB",
            "legend_bg": "rgba(0,0,0,0)",
            "shadow": "0 4px 24px rgba(0,0,0,0.5)",
            "glow_blue": "0 0 0 1px rgba(59,130,246,0.3), 0 4px 20px rgba(59,130,246,0.15)",
            "glow_green": "0 0 0 1px rgba(34,197,94,0.3), 0 4px 20px rgba(34,197,94,0.12)",
            "glow_red": "0 0 0 1px rgba(239,68,68,0.3), 0 4px 20px rgba(239,68,68,0.12)",
            "glow_gold": "0 0 0 1px rgba(251,191,36,0.3), 0 4px 20px rgba(251,191,36,0.12)",
            "input_bg": "#0F172A",
            "hover_nav": "rgba(59,130,246,0.12)",
        }
    return {
        "bg": "#F8FAFC",
        "sidebar_bg": "#F1F5F9",
        "card": "#FFFFFF",
        "card2": "#F8FAFC",
        "border": "rgba(37,99,235,0.15)",
        "border_soft": "rgba(0,0,0,0.07)",
        "primary": "#2563EB",
        "secondary": "#10B981",
        "accent": "#F59E0B",
        "danger": "#DC2626",
        "warning": "#F59E0B",
        "safe": "#10B981",
        "text": "#111827",
        "text_muted": "#6B7280",
        "text_sub": "#9CA3AF",
        "plotly_tmpl": "plotly_white",
        "plot_bg": "#FFFFFF",
        "paper_bg": "#FFFFFF",
        "font_color": "#111827",
        "legend_bg": "rgba(255,255,255,0.8)",
        "shadow": "0 2px 16px rgba(0,0,0,0.07)",
        "glow_blue": "0 2px 16px rgba(37,99,235,0.12)",
        "glow_green": "0 2px 16px rgba(16,185,129,0.12)",
        "glow_red": "0 2px 16px rgba(220,38,38,0.1)",
        "glow_gold": "0 2px 16px rgba(245,158,11,0.12)",
        "input_bg": "#FFFFFF",
        "hover_nav": "rgba(37,99,235,0.08)",
    }


def inject_css():
    t = theme()
    dark = is_dark()

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: {t["bg"]} !important;
    color: {t["text"]} !important;
    transition: background-color 0.3s ease, color 0.3s ease;
}}

#MainMenu, footer {{ visibility: hidden; }}
header {{ visibility: visible !important; }}
[data-testid="stHeader"] {{
    visibility: visible !important;
    background: transparent !important;
}}
[data-testid="stToolbar"] {{
    visibility: visible !important;
}}
[data-testid="stDecoration"] {{ display: none; }}

::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {t["border"]}; border-radius: 99px; }}

[data-testid="stSidebar"] {{
    background: {t["sidebar_bg"]} !important;
    border-right: 1px solid {t["border_soft"]} !important;
    padding-top: 0 !important;
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; }}

[data-testid="stSidebar"] .stRadio > div {{
    gap: 2px !important;
    flex-direction: column !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    background: transparent !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    cursor: pointer !important;
    transition: background 0.18s, color 0.18s !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: {t["text_muted"]} !important;
    width: 100% !important;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: {t["hover_nav"]} !important;
    color: {t["primary"]} !important;
}}

.main .block-container {{
    padding: 28px 36px 40px !important;
    max-width: 1400px !important;
}}

.stButton > button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1.5px solid {t["border"]} !important;
    background: {t["card"]} !important;
    color: {"#FFFFFF" if dark else t["primary"]} !important;
    box-shadow: {t["shadow"]} !important;
    letter-spacing: 0.01em !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: {t["glow_blue"]} !important;
    background: {t["primary"]} !important;
    color: #FFFFFF !important;
    border-color: {t["primary"]} !important;
}}
.stButton > button:active {{ transform: translateY(0px) !important; }}

[data-testid="stForm"] {{
    background: {t["card2"]} !important;
    border: 1px solid {t["border_soft"]} !important;
    border-radius: 14px !important;
    padding: 20px !important;
}}

[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
    background: {t["input_bg"]} !important;
    border-color: {t["border_soft"]} !important;
    border-radius: 8px !important;
    color: {t["text"]} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
[data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder {{
    color: {t["text_muted"]} !important;
    opacity: 1 !important;
}}
[data-baseweb="input"]:focus-within {{
    border-color: {t["primary"]} !important;
    box-shadow: 0 0 0 3px {"rgba(59,130,246,0.15)" if dark else "rgba(37,99,235,0.12)"} !important;
}}
[data-baseweb="textarea"]:focus-within {{
    border-color: {t["primary"]} !important;
    box-shadow: 0 0 0 3px {"rgba(59,130,246,0.15)" if dark else "rgba(37,99,235,0.12)"} !important;
}}
[data-baseweb="select"] > div {{
    background: {t["input_bg"]} !important;
    border-color: {t["border_soft"]} !important;
    border-radius: 8px !important;
    color: {t["text"]} !important;
}}
[data-baseweb="select"] span {{
    color: {t["text"]} !important;
}}
[data-baseweb="popover"] {{
    background: {t["card"]} !important;
    border: 1px solid {t["border_soft"]} !important;
    border-radius: 10px !important;
}}
[data-baseweb="menu"] {{
    background: {t["card"]} !important;
    color: {t["text"]} !important;
}}
[data-baseweb="menu"] ul, [data-baseweb="menu"] li {{
    background: {t["card"]} !important;
    color: {t["text"]} !important;
}}
[role="listbox"] {{
    background: {t["card"]} !important;
    color: {t["text"]} !important;
}}
[role="option"] {{
    background: {t["card"]} !important;
    color: {t["text"]} !important;
}}
[role="option"]:hover, [role="option"][aria-selected="true"] {{
    background: {t["hover_nav"]} !important;
    color: {t["text"]} !important;
}}

details {{
    background: {t["card"]} !important;
    border: 1px solid {t["border_soft"]} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 12px !important;
    box-shadow: {t["shadow"]} !important;
}}
details summary {{
    font-weight: 600 !important;
    font-size: 14px !important;
    color: {t["text"]} !important;
    padding: 14px 18px !important;
    background: {t["card"]} !important;
}}
details[open] summary {{ border-bottom: 1px solid {t["border_soft"]}; }}

[data-testid="stDataFrame"] {{
    border: 1px solid {t["border_soft"]} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: {t["shadow"]} !important;
}}

[data-testid="stMetric"] {{
    background: {t["card"]} !important;
    border: 1px solid {t["border_soft"]} !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    box-shadow: {t["shadow"]} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {t["text_muted"]} !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}}
[data-testid="stMetricValue"] {{
    color: {t["text"]} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 28px !important;
}}

.stDownloadButton > button {{
    background: {t["card"]} !important;
    border: 1.5px solid {t["secondary"]} !important;
    color: {t["secondary"]} !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}}
.stDownloadButton > button:hover {{
    background: {t["secondary"]} !important;
    color: white !important;
    transform: translateY(-1px) !important;
}}

.stCaption, .caption {{ color: {t["text_muted"]} !important; font-size: 12px !important; }}
label, p, h1, h2, h3, h4 {{ color: {t["text"]} !important; }}

.stTabs [data-baseweb="tab-list"] {{
    background: {t["card2"]} !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid {t["border_soft"]} !important;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px !important;
    color: {t["text_muted"]} !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}}
.stTabs [aria-selected="true"] {{
    background: {t["card"]} !important;
    color: {t["primary"]} !important;
    box-shadow: {t["shadow"]} !important;
}}

[data-testid="stSuccess"] {{ background: rgba(34,197,94,0.08) !important; border-radius: 10px !important; border: 1px solid rgba(34,197,94,0.25) !important; }}
[data-testid="stWarning"] {{ background: rgba(251,191,36,0.08) !important; border-radius: 10px !important; border: 1px solid rgba(251,191,36,0.25) !important; }}
[data-testid="stError"] {{ background: rgba(239,68,68,0.08) !important; border-radius: 10px !important; border: 1px solid rgba(239,68,68,0.25) !important; }}
[data-testid="stInfo"] {{ background: rgba(59,130,246,0.06) !important; border-radius: 10px !important; border: 1px solid rgba(59,130,246,0.2) !important; }}

@keyframes fadeSlideIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.main .block-container {{ animation: fadeSlideIn 0.28s ease; }}

.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 32px;
}}
.kpi-card {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 16px;
    padding: 22px 24px 18px;
    position: relative;
    overflow: hidden;
    transition: transform 0.22s cubic-bezier(0.4,0,0.2,1), box-shadow 0.22s;
}}
.kpi-card:hover {{ transform: translateY(-3px); }}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}}
.kpi-card.blue::before {{ background: linear-gradient(90deg, {t["primary"]}, #60A5FA); }}
.kpi-card.green::before {{ background: linear-gradient(90deg, {t["secondary"]}, #4ADE80); }}
.kpi-card.red::before {{ background: linear-gradient(90deg, {t["danger"]}, #F87171); }}
.kpi-card.gold::before {{ background: linear-gradient(90deg, {t["accent"]}, #FCD34D); }}
.kpi-card.blue {{ box-shadow: {t["glow_blue"]}; }}
.kpi-card.green {{ box-shadow: {t["glow_green"]}; }}
.kpi-card.red {{ box-shadow: {t["glow_red"]}; }}
.kpi-card.gold {{ box-shadow: {t["glow_gold"]}; }}

.kpi-icon {{
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    margin-bottom: 16px;
}}
.kpi-card.blue .kpi-icon {{ background: rgba(59,130,246,0.12); }}
.kpi-card.green .kpi-icon {{ background: rgba(34,197,94,0.12); }}
.kpi-card.red .kpi-icon {{ background: rgba(239,68,68,0.12); }}
.kpi-card.gold .kpi-icon {{ background: rgba(251,191,36,0.12); }}

.kpi-label {{
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {t["text_muted"]};
    font-weight: 700;
    margin-bottom: 6px;
}}
.kpi-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 36px;
    font-weight: 700;
    color: {t["text"]};
    line-height: 1;
}}
.kpi-sub {{ font-size: 12px; color: {t["text_sub"]}; margin-top: 8px; }}

.section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 700;
    color: {t["text"]};
    margin: 32px 0 18px;
    padding-bottom: 12px;
    border-bottom: 2px solid {t["border_soft"]};
}}
.section-header .sh-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {t["primary"]};
    flex-shrink: 0;
    box-shadow: 0 0 8px {t["primary"]};
}}

.alert-box {{
    background: {"rgba(251,191,36,0.07)" if dark else "rgba(245,158,11,0.06)"};
    border: 1px solid rgba(251,191,36,0.3);
    border-left: 4px solid {t["accent"]};
    border-radius: 10px;
    padding: 13px 16px;
    margin: 6px 0;
    font-size: 13px;
    color: {t["text"]};
    font-weight: 500;
}}

.page-header {{
    margin-bottom: 28px;
    padding-bottom: 20px;
    border-bottom: 1px solid {t["border_soft"]};
}}
.page-title {{
    font-size: 24px;
    font-weight: 800;
    color: {t["text"]};
    letter-spacing: -0.02em;
    margin-bottom: 4px;
}}
.page-subtitle {{ font-size: 13px; color: {t["text_muted"]}; font-weight: 400; }}

.pipeline-col {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 14px;
    padding: 16px;
    box-shadow: {t["shadow"]};
    min-height: 120px;
}}
.pipeline-col-title {{
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {t["text_muted"]};
    font-weight: 700;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.pipeline-item {{
    background: {t["card2"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 8px;
    padding: 8px 12px;
    margin: 6px 0;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    color: {t["text"]};
    font-weight: 500;
    transition: border-color 0.15s;
}}
.pipeline-item:hover {{ border-color: {t["primary"]}; }}
.pipeline-item.delayed {{ border-left: 3px solid {t["danger"]}; color: {t["danger"]}; }}

.footer {{
    text-align: center;
    padding: 28px 0 12px;
    font-size: 11.5px;
    color: {t["text_muted"]};
    border-top: 1px solid {t["border_soft"]};
    margin-top: 48px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}}

.sidebar-stat {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 12px;
    color: {t["text_muted"]};
    font-weight: 500;
}}
.sidebar-stat .stat-val {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 6px;
    padding: 2px 9px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: {t["text"]};
    font-weight: 600;
}}

.signal-card {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: {t["shadow"]};
    margin-bottom: 12px;
}}
.signal-card strong {{ color: {t["text"]}; }}
.alert-strip {{
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border: 1px solid {t["border_soft"]};
    background: {t["card"]};
    box-shadow: {t["shadow"]};
}}
.alert-strip.critical {{
    border-left: 4px solid {t["danger"]};
    background: {"rgba(239,68,68,0.12)" if dark else "rgba(254,226,226,0.95)"};
}}
.alert-strip.warning {{
    border-left: 4px solid {t["warning"]};
    background: {"rgba(245,158,11,0.12)" if dark else "rgba(255,247,237,0.95)"};
}}
.alert-strip.safe {{
    border-left: 4px solid {t["safe"]};
    background: {"rgba(34,197,94,0.12)" if dark else "rgba(236,253,245,0.95)"};
}}
.alert-strip-title {{
    font-size: 13px;
    font-weight: 700;
    color: {t["text"]};
    margin-bottom: 4px;
}}
.alert-strip-text {{
    font-size: 12px;
    color: {t["text_muted"]};
}}
.decision-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-bottom: 8px;
}}
.decision-chip.critical {{
    color: #FFFFFF;
    background: {t["danger"]};
}}
.decision-chip.warning {{
    color: {"#111827" if dark else "#7C2D12"};
    background: {t["accent"]};
}}
.decision-chip.safe {{
    color: #FFFFFF;
    background: {t["secondary"]};
}}
.decision-panel {{
    background: linear-gradient(180deg, {t["card"]} 0%, {t["card2"]} 100%);
    border: 1px solid {t["border_soft"]};
    border-radius: 16px;
    padding: 18px;
    box-shadow: {t["shadow"]};
    min-height: 180px;
}}
.decision-item {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 12px;
    padding: 14px;
    margin-top: 10px;
}}
.decision-title {{
    color: {t["text"]};
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 6px;
}}
.decision-meta {{
    color: {t["text_muted"]};
    font-size: 12px;
}}
.impact-card {{
    background: {t["card"]};
    border: 1px solid {t["border_soft"]};
    border-radius: 14px;
    padding: 18px;
    box-shadow: {t["shadow"]};
    height: 100%;
}}
.impact-label {{
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {t["text_sub"]};
    margin-bottom: 6px;
}}
.impact-value {{
    color: {t["text"]};
    font-size: 28px;
    font-weight: 800;
}}
.impact-note {{
    color: {t["text_muted"]};
    font-size: 12px;
    margin-top: 6px;
}}
.query-answer {{
    background: {t["card"]};
    border: 1px dashed {t["border"]};
    border-radius: 12px;
    padding: 14px 16px;
    color: {t["text"]};
    font-size: 13px;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def section_header(label: str):
    st.markdown(
        f'<div class="section-header"><span class="sh-dot"></span>{label}</div>',
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
    <div class="page-header">
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
    </div>""",
        unsafe_allow_html=True,
    )


def alert_box(msg: str):
    st.markdown(f'<div class="alert-box">⚠️ {msg}</div>', unsafe_allow_html=True)


def kpi_cards_css():
    return ""
