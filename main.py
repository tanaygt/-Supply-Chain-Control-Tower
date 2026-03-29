# main.py — Supply Chain Control Tower
# Run: streamlit run main.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os, shutil
from datetime import datetime

from utils import (load_data, save_data, moving_average, inject_css,
                   section_header, page_header, alert_box, theme, is_dark, kpi_cards_css)
from inventory import render_inventory
from orders    import render_orders
from shipments import render_shipments
from vendors   import render_vendors

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supply Chain Control Tower",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state defaults ────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# ── Bootstrap data file ───────────────────────────────────────────────────────
if not os.path.exists("data.json"):
    sample = os.path.join(os.path.dirname(__file__), "data.json")
    if os.path.exists(sample):
        shutil.copy(sample, "data.json")
    else:
        save_data({"inventory": [], "orders": [], "shipments": [], "vendors": [], "demand_history": {}})

# ── Inject theme CSS ──────────────────────────────────────────────────────────
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
t = theme()
dark = is_dark()

with st.sidebar:
    # Brand
    st.markdown(f"""
    <div style="padding: 24px 16px 18px; border-bottom: 1px solid {t['border_soft']}; margin-bottom: 4px;">
        <div style="font-size: 20px; font-weight: 800; color: {t['primary']}; letter-spacing: -0.03em;">
            🏭 Control Tower
        </div>
        <div style="font-size: 11px; color: {t['text_muted']}; margin-top: 4px; font-weight: 400;">
            Supply Chain Suite &nbsp;·&nbsp; v2.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    toggle_label = "☀️  Light Mode" if dark else "🌙  Dark Mode"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.dark_mode = not dark
        st.rerun()

    st.markdown(f"<div style='height:4px; border-bottom: 1px solid {t['border_soft']}; margin-bottom: 8px'></div>",
                unsafe_allow_html=True)

    # Navigation
    st.markdown(f"<div style='font-size:10px; text-transform:uppercase; letter-spacing:0.12em; color:{t['text_sub']}; padding: 12px 0 6px; font-weight:700;'>Navigation</div>",
                unsafe_allow_html=True)

    page = st.radio(
        "nav", ["📊 Dashboard", "📦 Inventory", "🛒 Orders",
                "🚚 Shipments", "🤝 Vendors", "⚙️ Data Management"],
        label_visibility="collapsed"
    )

    # Data stats
    st.markdown(f"<div style='font-size:10px; text-transform:uppercase; letter-spacing:0.12em; color:{t['text_sub']}; padding: 20px 0 8px; font-weight:700;'>Data Status</div>",
                unsafe_allow_html=True)

    data = load_data()
    stats = [
        ("📦 Products",  len(data["inventory"])),
        ("🛒 Orders",    len(data["orders"])),
        ("🚚 Shipments", len(data["shipments"])),
        ("🤝 Vendors",   len(data["vendors"])),
    ]
    for label, val in stats:
        st.markdown(f"""
        <div class="sidebar-stat">
            <span>{label}</span>
            <span class="stat-val">{val}</span>
        </div>""", unsafe_allow_html=True)

    # Delayed shipment warning
    delayed = [s for s in data["shipments"] if s.get("delayed")]
    if delayed:
        st.markdown(f"""
        <div style="margin-top:14px; background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
                    border-left: 3px solid {t['danger']}; border-radius: 8px; padding: 10px 12px;
                    font-size: 12px; color: {t['danger']}; font-weight: 600;">
            ⚡ {len(delayed)} delayed shipment{"s" if len(delayed) > 1 else ""}
        </div>""", unsafe_allow_html=True)

# ── Dashboard ─────────────────────────────────────────────────────────────────
def render_dashboard():
    t = theme()
    dark = is_dark()
    data      = load_data()
    inventory = data["inventory"]
    orders    = data["orders"]
    shipments = data["shipments"]
    vendors   = data["vendors"]

    page_header(
        "📊 Dashboard",
        f"Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M')} &nbsp;·&nbsp; Supply Chain overview"
    )

    total_inv      = sum(i["quantity"] for i in inventory)
    active_orders  = len([o for o in orders if o["status"] in ["Pending","Processing"]])
    delayed_ships  = len([s for s in shipments if s.get("delayed")])
    avg_score      = round(sum(v["score"] for v in vendors) / len(vendors), 1) if vendors else 0

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card blue">
        <div class="kpi-icon">📦</div>
        <div class="kpi-label">Total Inventory</div>
        <div class="kpi-value">{total_inv:,}</div>
        <div class="kpi-sub">units · all warehouses</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🛒</div>
        <div class="kpi-label">Active Orders</div>
        <div class="kpi-value">{active_orders}</div>
        <div class="kpi-sub">pending + processing</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-icon">🚚</div>
        <div class="kpi-label">Delayed Shipments</div>
        <div class="kpi-value">{delayed_ships}</div>
        <div class="kpi-sub">require immediate action</div>
      </div>
      <div class="kpi-card gold">
        <div class="kpi-icon">🤝</div>
        <div class="kpi-label">Avg Vendor Score</div>
        <div class="kpi-value">{avg_score}</div>
        <div class="kpi-sub">out of 100</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts row 1 ──────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2], gap="large")

    chart_layout = dict(
        plot_bgcolor=t["plot_bg"], paper_bgcolor=t["paper_bg"],
        font_color=t["font_color"], margin=dict(t=36, b=16, l=8, r=8),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        font=dict(family="Plus Jakarta Sans"),
        title_font=dict(size=14, family="Plus Jakarta Sans", color=t["font_color"]),
        xaxis=dict(gridcolor=t["border_soft"], linecolor=t["border_soft"]),
        yaxis=dict(gridcolor=t["border_soft"], linecolor=t["border_soft"]),
    )

    with col1:
        if inventory:
            df_inv = pd.DataFrame(inventory)
            colors = [t["primary"], t["secondary"], t["accent"], "#A78BFA", "#F472B6"]
            wh_list = df_inv["warehouse"].unique().tolist()
            color_map = {w: colors[i % len(colors)] for i, w in enumerate(wh_list)}
            fig = px.bar(df_inv, x="name", y="quantity", color="warehouse",
                         title="Inventory by Product",
                         color_discrete_map=color_map,
                         labels={"name": "", "quantity": "Units"})
            fig.update_layout(**chart_layout, barmode="group")
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if orders:
            df_ord = pd.DataFrame(orders)
            sc = df_ord["status"].value_counts().reset_index()
            sc.columns = ["Status","Count"]
            colors_pie = [t["primary"], t["secondary"], t["accent"], t["danger"]]
            fig2 = px.pie(sc, names="Status", values="Count",
                          title="Order Status",
                          color_discrete_sequence=colors_pie,
                          hole=0.55)
            fig2.update_traces(textfont_size=12, textfont_color=t["font_color"])
            fig2.update_layout(**{k:v for k,v in chart_layout.items()
                                   if k not in ("xaxis","yaxis")})
            st.plotly_chart(fig2, use_container_width=True)

    # ── Demand trend ──────────────────────────────────────────────────────────
    section_header("📈 Historical Demand Trends")
    demand_hist = data.get("demand_history", {})
    if demand_hist:
        fig3 = go.Figure()
        line_colors = [t["primary"], t["secondary"], t["accent"], "#A78BFA", "#F472B6"]
        for i, (prod, vals) in enumerate(demand_hist.items()):
            fig3.add_trace(go.Scatter(
                y=vals, name=prod, mode="lines+markers",
                line=dict(color=line_colors[i % len(line_colors)], width=2.5),
                marker=dict(size=6, symbol="circle"),
                fill="tozeroy",
                fillcolor=f"rgba({','.join(str(int(line_colors[i%len(line_colors)].lstrip('#')[j:j+2],16)) for j in (0,2,4))},0.04)"
            ))
        fig3.update_layout(
            **chart_layout,
            xaxis_title="Period", yaxis_title="Units",
            height=280
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Low stock ─────────────────────────────────────────────────────────────
    low = [i for i in inventory if i["quantity"] <= i["reorder_point"]]
    if low:
        section_header("⚠️ Low Stock Alerts")
        for item in low:
            alert_box(f"<b>{item['name']}</b> ({item['sku']}) — "
                      f"<b>{item['quantity']}</b> units in {item['warehouse']} "
                      f"(reorder threshold: {item['reorder_point']})")


# ── Data Management ───────────────────────────────────────────────────────────
def render_data_mgmt():
    t = theme()
    page_header("⚙️ Data Management", "Export, import and simulate supply chain scenarios")
    data = load_data()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        section_header("📥 Export / Import")
        st.download_button(
            "⬇️  Download data.json", json.dumps(data, indent=2),
            "supply_chain_data.json", "application/json", use_container_width=True
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload a data.json file to import", type=["json"])
        if uploaded:
            try:
                new_data = json.load(uploaded)
                save_data(new_data)
                st.success("✅ Data imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Invalid file: {e}")

    with col2:
        section_header("🎛️ Demand Surge Simulator")
        st.caption("Simulate a future demand spike to expose potential inventory shortfalls.")
        pct = st.slider("Demand increase (%)", 5, 100, 20)
        if st.button("▶ Run Simulation", use_container_width=True):
            dh = data.get("demand_history", {})
            rows = []
            for prod, vals in dh.items():
                sim_vals = [int(v * (1 + pct / 100)) for v in vals]
                avg = moving_average(sim_vals)
                cur = next((i["quantity"] for i in data["inventory"] if i["name"] == prod), 0)
                shortfall = max(0, int(avg * 7 - cur))
                rows.append({"Product": prod, "Sim. Avg Demand": avg,
                             "Current Stock": cur, "Potential Shortfall": shortfall})
            st.success(f"Simulation complete — +{pct}% demand surge")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section_header("🔄 Reset")
        if st.button("Reset to Sample Data", use_container_width=True):
            sample = os.path.join(os.path.dirname(__file__), "data.json")
            if os.path.exists(sample):
                with open(sample) as f:
                    save_data(json.load(f))
                st.success("Reset complete.")
                st.rerun()
            else:
                st.warning("No sample data.json found in directory.")


# ── Router ────────────────────────────────────────────────────────────────────
if   page == "📊 Dashboard":       render_dashboard()
elif page == "📦 Inventory":       render_inventory()
elif page == "🛒 Orders":          render_orders()
elif page == "🚚 Shipments":       render_shipments()
elif page == "🤝 Vendors":         render_vendors()
elif page == "⚙️ Data Management":  render_data_mgmt()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Built by Tanay Shrivastava &nbsp;·&nbsp; Supply Chain Control Tower &nbsp;·&nbsp; v2.0</div>',
    unsafe_allow_html=True
)
