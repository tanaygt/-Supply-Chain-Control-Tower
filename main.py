import json
import os
import random
import shutil
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import init_db, reset_database
from inventory import render_inventory
from orders import render_orders
from shipments import render_shipments
from utils import (
    inject_css,
    is_dark,
    kpi_cards_css,
    load_data,
    moving_average,
    page_header,
    save_data,
    section_header,
    theme,
)
from vendors import render_vendors

REGION_PROFILES = {
    "India": {
        "demand_multiplier": 1.0,
        "delay_probability": 0.24,
        "label": "Balanced demand with moderate logistics volatility.",
    },
    "UAE": {
        "demand_multiplier": 1.15,
        "delay_probability": 0.38,
        "label": "High import dependency with elevated delay exposure.",
    },
    "USA": {
        "demand_multiplier": 1.08,
        "delay_probability": 0.18,
        "label": "Stable demand with stronger delivery consistency.",
    },
}


st.set_page_config(
    page_title="Supply Chain Control Tower",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "region" not in st.session_state:
    st.session_state.region = "India"
if "inventory_trend" not in st.session_state:
    st.session_state.inventory_trend = []
if "delay_trend" not in st.session_state:
    st.session_state.delay_trend = []

inject_css()
kpi_cards_css()

t = theme()
dark = is_dark()


def ensure_bootstrap_data():
    if not os.path.exists("data.json"):
        save_data(
            {
                "inventory": [],
                "orders": [],
                "shipments": [],
                "vendors": [],
                "demand_history": {},
            }
        )


def compute_delay_days(shipment: dict) -> int:
    explicit_days = shipment.get("delay_days")
    if explicit_days is not None:
        return max(0, int(explicit_days))
    if shipment.get("delayed"):
        expected = shipment.get("expected_date")
        actual = shipment.get("actual_date")
        try:
            if expected and actual:
                exp = datetime.strptime(expected, "%Y-%m-%d")
                act = datetime.strptime(actual, "%Y-%m-%d")
                return max(0, (act - exp).days)
        except ValueError:
            pass
        return 4
    return 0


ensure_bootstrap_data()


def normalize_data(data: dict) -> dict:
    for shipment in data.get("shipments", []):
        shipment["delay_days"] = compute_delay_days(shipment)
    return data


def get_product_vendor_map(data: dict) -> dict:
    mapping = {}
    for order in data.get("orders", []):
        mapping.setdefault(order.get("product"), order.get("vendor"))
    return mapping


def get_vendor_lookup(data: dict) -> dict:
    return {vendor["name"]: vendor for vendor in data.get("vendors", [])}


def build_alerts_and_decisions(data: dict, region: str):
    inventory = data["inventory"]
    shipments = data["shipments"]
    vendor_lookup = get_vendor_lookup(data)
    product_vendor_map = get_product_vendor_map(data)

    alerts = []
    critical_list = []
    warning_list = []
    safe_list = []

    for item in inventory:
        vendor_name = product_vendor_map.get(item["name"])
        vendor = vendor_lookup.get(vendor_name, {})
        ratio = item["quantity"] / item["reorder_point"] if item["reorder_point"] else 2
        if item["quantity"] < item["reorder_point"]:
            alerts.append(
                {
                    "level": "critical",
                    "title": f"Low stock: {item['name']}",
                    "text": f"Only {item['quantity']} units available vs reorder point {item['reorder_point']}.",
                }
            )
            critical_list.append(
                {
                    "title": f"Restock {item['name']}",
                    "text": f"{item['name']} is below safety stock in {item['warehouse']}. Suggested replenishment should start now.",
                }
            )
        elif ratio <= 1.4:
            alerts.append(
                {
                    "level": "warning",
                    "title": f"Inventory tightening: {item['name']}",
                    "text": f"Coverage is approaching reorder point. Monitor next cycle closely in {region}.",
                }
            )
            warning_list.append(
                {
                    "title": f"Monitor {item['name']}",
                    "text": f"{item['name']} is nearing threshold and may need action if demand rises further.",
                }
            )
        else:
            safe_list.append(
                {
                    "title": f"{item['name']} stock healthy",
                    "text": f"{item['quantity']} units available and comfortably above the reorder point.",
                }
            )

        if vendor and vendor.get("score", 100) < 50:
            alerts.append(
                {
                    "level": "warning",
                    "title": f"Vendor risk: {vendor['name']}",
                    "text": f"Reliability score is {vendor['score']}. Source alternatives for {item['name']}.",
                }
            )
            warning_list.append(
                {
                    "title": f"Review vendor {vendor['name']}",
                    "text": f"{vendor['name']} is underperforming and could impact {item['name']} supply continuity.",
                }
            )
        elif vendor and vendor.get("score", 100) >= 80:
            safe_list.append(
                {
                    "title": f"{vendor['name']} performing well",
                    "text": f"Vendor reliability remains strong for {item['name']} supply continuity.",
                }
            )

    for shipment in shipments:
        delay_days = compute_delay_days(shipment)
        if delay_days > 2:
            alerts.append(
                {
                    "level": "critical",
                    "title": f"Severe shipment delay: {shipment['id']}",
                    "text": f"Delay of {delay_days} days on order {shipment['order_id']} needs escalation.",
                }
            )
            critical_list.append(
                {
                    "title": f"Shipment delay high: {shipment['id']}",
                    "text": f"Shipment {shipment['id']} is delayed by {delay_days} days. Expedite carrier follow-up immediately.",
                }
            )
        elif delay_days > 0:
            alerts.append(
                {
                    "level": "warning",
                    "title": f"Delay building: {shipment['id']}",
                    "text": f"Shipment has a {delay_days}-day delay trend and should stay on the watchlist.",
                }
            )
            warning_list.append(
                {
                    "title": f"Slight delay detected: {shipment['id']}",
                    "text": f"Shipment {shipment['id']} is slipping and may become critical if no recovery occurs.",
                }
            )
        else:
            safe_list.append(
                {
                    "title": f"Shipment on track: {shipment['id']}",
                    "text": f"Shipment {shipment['id']} is currently moving without delay risk.",
                }
            )

    if not critical_list and not warning_list:
        alerts.append(
            {
                "level": "safe",
                "title": "Network stable",
                "text": f"No critical exceptions detected across inventory, shipments, or vendors in {region}.",
            }
        )
        safe_list.append(
            {
                "title": "No major issues",
                "text": "Inventory, shipment reliability, and vendor performance are currently within safe limits.",
            }
        )

    decisions = {
        "Critical": critical_list,
        "Warning": warning_list,
        "Safe": safe_list,
        "critical_list": critical_list,
        "warning_list": warning_list,
        "safe_list": safe_list,
    }

    return alerts[:6], decisions



def calculate_risk_score(data: dict) -> tuple[int, str, str]:
    risk = 0

    for item in data["inventory"]:
        if item["quantity"] < item["reorder_point"]:
            risk += 18
        elif item["quantity"] < item["reorder_point"] * 1.3:
            risk += 8

    for shipment in data["shipments"]:
        delay_days = compute_delay_days(shipment)
        risk += min(delay_days * 6, 24)

    for vendor in data["vendors"]:
        score = vendor.get("score", 100)
        if score < 50:
            risk += 18
        elif score < 70:
            risk += 8

    risk = max(0, min(100, risk))
    if risk <= 40:
        return risk, "Safe", theme()["safe"]
    if risk <= 70:
        return risk, "Warning", theme()["warning"]
    return risk, "Critical", theme()["danger"]



def snapshot_metrics(data: dict):
    stamp = datetime.now().strftime("%H:%M:%S")
    total_inventory = sum(item["quantity"] for item in data["inventory"])
    delayed_orders = sum(1 for shipment in data["shipments"] if compute_delay_days(shipment) > 0)

    inventory_history = st.session_state.inventory_trend
    delay_history = st.session_state.delay_trend

    if not inventory_history or inventory_history[-1]["time"] != stamp:
        inventory_history.append({"time": stamp, "value": total_inventory})
    if not delay_history or delay_history[-1]["time"] != stamp:
        delay_history.append({"time": stamp, "value": delayed_orders})

    st.session_state.inventory_trend = inventory_history[-12:]
    st.session_state.delay_trend = delay_history[-12:]



def build_forecast_rows(data: dict, region: str):
    profile = REGION_PROFILES[region]
    rows = []
    for item in data["inventory"]:
        history = data.get("demand_history", {}).get(item["name"], [])
        current_value = history[-1] if history else max(10, item["quantity"] // 8)
        growth = random.uniform(1.05, 1.15) * profile["demand_multiplier"]
        predicted = int(current_value * growth)
        if predicted >= current_value * 1.08:
            trend = "Demand increasing 📈"
        elif predicted <= current_value * 0.99:
            trend = "Demand decreasing 📉"
        else:
            trend = "Demand stable ⚖️"
        rows.append(
            {
                "Product": item["name"],
                "Current Demand": int(current_value),
                "Predicted Demand": predicted,
                "Trend": trend,
            }
        )
    return rows



def build_insights(data: dict, region: str, risk_score: int):
    total_inventory = sum(item["quantity"] for item in data["inventory"])
    low_stock_count = sum(1 for item in data["inventory"] if item["quantity"] < item["reorder_point"])
    delayed_count = sum(1 for shipment in data["shipments"] if compute_delay_days(shipment) > 0)
    avg_vendor = round(
        sum(vendor.get("score", 0) for vendor in data["vendors"]) / max(len(data["vendors"]), 1),
        1,
    )

    insights = []
    if low_stock_count >= 2:
        insights.append("⚠️ Inventory is decreasing fast across multiple SKUs.")
    else:
        insights.append(f"✅ Inventory cover is manageable for most products in {region}.")

    if delayed_count >= 2:
        insights.append("🚨 Delay trend increasing and needs carrier escalation.")
    else:
        insights.append("✅ Delivery flow is largely stable with isolated exceptions.")

    if avg_vendor >= 80:
        insights.append("✅ Vendors performing well with reliable fulfillment quality.")
    else:
        insights.append("⚠️ Vendor portfolio needs review to reduce supply risk.")

    if risk_score > 70:
        insights.append("🚨 Network risk is elevated and near-term intervention is recommended.")
    else:
        insights.append("📈 Decision signals remain actionable without major disruption.")

    return insights, total_inventory, delayed_count, avg_vendor



def build_business_impact(data: dict):
    delay_days_total = sum(compute_delay_days(shipment) for shipment in data["shipments"])
    delayed_orders = [shipment for shipment in data["shipments"] if compute_delay_days(shipment) > 0]
    low_stock_items = [item for item in data["inventory"] if item["quantity"] < item["reorder_point"]]

    estimated_loss = delay_days_total * 1200
    revenue_impact = sum(
        next((order.get("total", 0) for order in data["orders"] if order["id"] == shipment["order_id"]), 0)
        * 0.18
        for shipment in delayed_orders
    )
    stockout_cost = sum((item["reorder_point"] - item["quantity"]) * item.get("unit_cost", 0) * 2.5 for item in low_stock_items)

    return int(estimated_loss), round(revenue_impact, 2), round(stockout_cost, 2)



def answer_query(question: str, data: dict) -> str:
    q = question.lower().strip()
    if not q:
        return "Ask about risky products, weak vendors, delays, or stockouts."

    risky_products = [item for item in data["inventory"] if item["quantity"] < item["reorder_point"]]
    weak_vendors = sorted(data["vendors"], key=lambda vendor: vendor.get("score", 100))
    delayed_shipments = sorted(data["shipments"], key=compute_delay_days, reverse=True)

    if "product" in q or "risky" in q or "stock" in q:
        if risky_products:
            item = min(risky_products, key=lambda product: product["quantity"] - product["reorder_point"])
            return f"{item['name']} is the riskiest product right now because stock is {item['quantity']} against a reorder point of {item['reorder_point']}."
        return "No product is currently below its reorder point."

    if "vendor" in q or "bad" in q or "reliability" in q:
        if weak_vendors:
            vendor = weak_vendors[0]
            return f"{vendor['name']} needs the most attention with a score of {vendor['score']} and on-time rate of {vendor.get('on_time_rate', 0)}%."
        return "There are no vendors available to evaluate."

    if "delay" in q or "shipment" in q:
        delayed = [shipment for shipment in delayed_shipments if compute_delay_days(shipment) > 0]
        if delayed:
            shipment = delayed[0]
            return f"Shipment {shipment['id']} is the top delay risk with {compute_delay_days(shipment)} delay days linked to order {shipment['order_id']}."
        return "No active shipment delays were detected."

    return "Current watchlist: focus on low-stock products, delayed shipments, and vendors with weaker scores."



def simulate_live_environment(data: dict, region: str) -> dict:
    profile = REGION_PROFILES[region]
    updated = json.loads(json.dumps(data))

    for item in updated["inventory"]:
        swing = random.randint(-90, 60)
        adjusted = max(0, item["quantity"] + int(swing * profile["demand_multiplier"]))
        item["quantity"] = adjusted
        demand_history = updated.setdefault("demand_history", {}).setdefault(item["name"], [])
        observed = max(5, int((demand_history[-1] if demand_history else item["reorder_point"]) * random.uniform(0.96, 1.18)))
        demand_history.append(observed)
        updated["demand_history"][item["name"]] = demand_history[-10:]

    for shipment in updated["shipments"]:
        delayed = random.random() < profile["delay_probability"]
        shipment["delayed"] = delayed
        shipment["delay_days"] = random.randint(1, 6) if delayed else 0
        if delayed and shipment["status"] == "Delivered":
            shipment["status"] = "In Transit"
        elif not delayed and shipment["status"] == "Pending":
            shipment["status"] = random.choice(["Dispatched", "In Transit"])

    for vendor in updated["vendors"]:
        vendor["score"] = max(35, min(98, vendor.get("score", 75) + random.randint(-6, 4)))
        vendor["on_time_rate"] = max(45, min(99, vendor.get("on_time_rate", 80) + random.randint(-5, 3)))

    return updated



def render_alerts(alerts: list[dict]):
    for alert in alerts:
        st.markdown(
            f"""
            <div class="alert-strip {alert['level']}">
                <div class="alert-strip-title">{alert['title']}</div>
                <div class="alert-strip-text">{alert['text']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )



def render_decision_panel(decisions: dict):
    section_header("🤖 AI Decision Panel")
    critical_list = decisions.get("critical_list", decisions.get("Critical", []))
    warning_list = decisions.get("warning_list", decisions.get("Warning", []))
    safe_list = decisions.get("safe_list", decisions.get("Safe", []))

    summary_cards = [
        ("critical", "🚨", "Critical Issues", critical_list),
        ("warning", "⚠️", "Warnings", warning_list),
        ("safe", "✅", "Safe", safe_list),
    ]
    border_map = {
        "critical": theme()["danger"],
        "warning": theme()["warning"],
        "safe": theme()["safe"],
    }

    columns = st.columns(3, gap="large")
    for column, (tone, icon, label, items) in zip(columns, summary_cards):
        count = len(items)
        if tone == "safe" and count == 0:
            headline = "✅ All Good"
        else:
            headline = f"{icon} {count} {label}" if count != 1 else f"{icon} 1 {label[:-1] if label.endswith('s') else label}"
        preview_items = items[:2]
        preview_html = "".join(
            f"<div class='decision-meta' style='margin-top:8px;'>- {entry['title']}</div>"
            for entry in preview_items
        ) or "<div class='decision-meta' style='margin-top:8px;'>No issues detected</div>"

        with column:
            st.markdown(
                f"""
                <div class="decision-panel" style="border-top: 4px solid {border_map[tone]};">
                    <div class="decision-chip {tone}">{label}</div>
                    <div class="decision-title" style="font-size:18px; margin-bottom:10px;">{headline}</div>
                    {preview_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    detail_columns = st.columns(3, gap="large")
    detail_map = [
        ("Critical", "critical", critical_list),
        ("Warning", "warning", warning_list),
        ("Safe", "safe", safe_list),
    ]
    for column, (label, tone, items) in zip(detail_columns, detail_map):
        with column:
            st.markdown(
                f'<div class="decision-chip {tone}" style="margin-top:14px;">{label} Details</div>',
                unsafe_allow_html=True,
            )
            detail_items = items if items else [{"title": "No issues detected", "text": "Nothing needs attention in this category right now."}]
            for item in detail_items[:4]:
                st.markdown(
                    f"""
                    <div class="decision-item">
                        <div class="decision-title">{item['title']}</div>
                        <div class="decision-meta">{item['text']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )



def render_dashboard():
    data = normalize_data(load_data())
    region = st.session_state.region
    profile = REGION_PROFILES[region]

    alerts, decisions = build_alerts_and_decisions(data, region)
    risk_score, risk_label, risk_color = calculate_risk_score(data)
    insights, total_inventory, delayed_count, avg_vendor = build_insights(data, region, risk_score)
    forecast_rows = build_forecast_rows(data, region)
    estimated_loss, revenue_impact, stockout_cost = build_business_impact(data)

    snapshot_metrics(data)

    page_header(
        "📊 AI-Powered Supply Chain Decision System",
        f"Live region: {region} · {profile['label']} · Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}",
    )

    render_alerts(alerts)

    kpi_html = f"""
    <div class="kpi-grid">
      <div class="kpi-card blue">
        <div class="kpi-icon">📦</div>
        <div class="kpi-label">Total Inventory</div>
        <div class="kpi-value">{total_inventory:,}</div>
        <div class="kpi-sub">{'⚠️ Inventory is decreasing fast' if delayed_count >= 2 else 'Healthy stock visibility across network'}</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-icon">🚚</div>
        <div class="kpi-label">Delayed Orders</div>
        <div class="kpi-value">{delayed_count}</div>
        <div class="kpi-sub">{'🚨 Delay trend increasing' if delayed_count >= 2 else 'Delay exposure remains controlled'}</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🤝</div>
        <div class="kpi-label">Active Vendors</div>
        <div class="kpi-value">{len(data['vendors'])}</div>
        <div class="kpi-sub">{'✅ Vendors performing well' if avg_vendor >= 80 else 'Review weaker supplier partners'}</div>
      </div>
      <div class="kpi-card gold">
        <div class="kpi-icon">🛡️</div>
        <div class="kpi-label">Risk Score</div>
        <div class="kpi-value">{risk_score}</div>
        <div class="kpi-sub">{risk_label} network risk</div>
      </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    section_header("📌 KPI Insights")
    insight_columns = st.columns(2, gap="large")
    for idx, insight in enumerate(insights):
        with insight_columns[idx % 2]:
            st.markdown(f'<div class="signal-card">{insight}</div>', unsafe_allow_html=True)

    section_header("📉 Supply Chain Risk Score")
    risk_col1, risk_col2 = st.columns([2, 1], gap="large")
    with risk_col1:
        st.progress(risk_score / 100)
        st.markdown(
            f"<div class='signal-card'><strong style='color:{risk_color}'>{risk_label}</strong><br>Risk score is {risk_score}/100 based on stock exposure, shipment delays, and vendor quality.</div>",
            unsafe_allow_html=True,
        )
    with risk_col2:
        st.metric("Region Delay Probability", f"{int(profile['delay_probability'] * 100)}%")
        st.metric("Avg Vendor Score", f"{avg_vendor}/100")
        st.metric("Products Below Threshold", sum(1 for item in data['inventory'] if item['quantity'] < item['reorder_point']))

    render_decision_panel(decisions)

    section_header("📊 Demand Forecast")
    forecast_df = pd.DataFrame(forecast_rows)
    forecast_col1, forecast_col2 = st.columns([1.2, 1.8], gap="large")
    with forecast_col1:
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)
    with forecast_col2:
        fig_forecast = px.bar(
            forecast_df,
            x="Product",
            y="Predicted Demand",
            color="Trend",
            color_discrete_map={
                "Demand increasing 📈": t["danger"],
                "Demand stable ⚖️": t["accent"],
                "Demand decreasing 📉": t["secondary"],
            },
            title="Predicted Demand by Product",
        )
        fig_forecast.update_layout(
            plot_bgcolor=t["plot_bg"],
            paper_bgcolor=t["paper_bg"],
            font_color=t["font_color"],
            margin=dict(t=40, b=20, l=10, r=10),
            xaxis=dict(gridcolor=t["border_soft"]),
            yaxis=dict(gridcolor=t["border_soft"]),
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

    section_header("🔄 Real-Time Simulation")
    sim_col1, sim_col2, sim_col3 = st.columns([1.2, 1.2, 2.6], gap="large")
    with sim_col1:
        if st.button("Simulate Live Data", use_container_width=True):
            new_data = simulate_live_environment(data, region)
            save_data(new_data)
            st.success("Live data simulation completed.")
            st.rerun()
    with sim_col2:
        st.metric("Demand Multiplier", f"{profile['demand_multiplier']:.2f}x")
    with sim_col3:
        st.markdown(
            f'<div class="signal-card">Region simulation is set to <strong>{region}</strong>. {profile["label"]}</div>',
            unsafe_allow_html=True,
        )

    section_header("📈 Visualization Upgrade")
    chart_col1, chart_col2 = st.columns(2, gap="large")

    inventory_trend_df = pd.DataFrame(st.session_state.inventory_trend)
    delay_trend_df = pd.DataFrame(st.session_state.delay_trend)

    with chart_col1:
        if not inventory_trend_df.empty:
            fig_inventory = px.line(
                inventory_trend_df,
                x="time",
                y="value",
                markers=True,
                title="Inventory Trend",
            )
            fig_inventory.update_traces(line_color=t["primary"], marker_color=t["primary"])
            fig_inventory.update_layout(
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["paper_bg"],
                font_color=t["font_color"],
                margin=dict(t=40, b=20, l=10, r=10),
                xaxis=dict(gridcolor=t["border_soft"]),
                yaxis=dict(gridcolor=t["border_soft"]),
            )
            st.plotly_chart(fig_inventory, use_container_width=True)

    with chart_col2:
        if not delay_trend_df.empty:
            fig_delay = px.bar(
                delay_trend_df,
                x="time",
                y="value",
                title="Delay Trend",
                color_discrete_sequence=[t["danger"]],
            )
            fig_delay.update_layout(
                plot_bgcolor=t["plot_bg"],
                paper_bgcolor=t["paper_bg"],
                font_color=t["font_color"],
                margin=dict(t=40, b=20, l=10, r=10),
                xaxis=dict(gridcolor=t["border_soft"]),
                yaxis=dict(gridcolor=t["border_soft"]),
                showlegend=False,
            )
            st.plotly_chart(fig_delay, use_container_width=True)

    section_header("🧠 Mini AI Query Box")
    question = st.text_input("Ask the decision engine", placeholder="Which product is risky? Which vendor is bad?")
    st.markdown(f'<div class="query-answer">{answer_query(question, data)}</div>', unsafe_allow_html=True)

    section_header("🏢 Business Impact")
    impact_columns = st.columns(3, gap="large")
    impact_values = [
        ("Estimated Loss Due To Delays", f"${estimated_loss:,.0f}", "Delay days multiplied by operational penalty."),
        ("Revenue Impact", f"${revenue_impact:,.2f}", "Revenue at risk from delayed orders."),
        ("Stockout Cost", f"${stockout_cost:,.2f}", "Cost of demand not served because of low stock."),
    ]
    for column, (label, value, note) in zip(impact_columns, impact_values):
        with column:
            st.markdown(
                f"""
                <div class="impact-card">
                    <div class="impact-label">{label}</div>
                    <div class="impact-value">{value}</div>
                    <div class="impact-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    section_header("📈 Historical Demand Trends")
    demand_hist = data.get("demand_history", {})
    if demand_hist:
        fig3 = go.Figure()
        line_colors = [t["primary"], t["secondary"], t["accent"], "#A78BFA", "#F472B6"]
        for i, (product, values) in enumerate(demand_hist.items()):
            fig3.add_trace(
                go.Scatter(
                    y=values,
                    name=product,
                    mode="lines+markers",
                    line=dict(color=line_colors[i % len(line_colors)], width=2.5),
                    marker=dict(size=6, symbol="circle"),
                )
            )
        fig3.update_layout(
            plot_bgcolor=t["plot_bg"],
            paper_bgcolor=t["paper_bg"],
            font_color=t["font_color"],
            margin=dict(t=36, b=16, l=8, r=8),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
            xaxis=dict(gridcolor=t["border_soft"], linecolor=t["border_soft"], title="Period"),
            yaxis=dict(gridcolor=t["border_soft"], linecolor=t["border_soft"], title="Units"),
            height=320,
        )
        st.plotly_chart(fig3, use_container_width=True)



def render_data_management():
    page_header("⚙️ Data Management", "Export, import, reset, and run operational scenario workflows")
    data = load_data()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        section_header("📥 Export / Import")
        st.download_button(
            "⬇️ Download data.json",
            json.dumps(data, indent=2),
            "supply_chain_data.json",
            "application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("Upload a data.json file to import", type=["json"])
        if uploaded:
            try:
                new_data = json.load(uploaded)
                save_data(new_data)
                st.success("Data imported successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Invalid file: {exc}")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Reset to Current Sample Data", use_container_width=True):
            if os.path.exists("data.json"):
                reset_database()
                st.success("Database reset completed.")
                st.rerun()

    with col2:
        section_header("🎛️ Demand Surge Simulator")
        pct = st.slider("Demand increase (%)", 5, 100, 20)
        if st.button("Run Scenario Simulation", use_container_width=True):
            rows = []
            for product, values in data.get("demand_history", {}).items():
                simulated_values = [int(value * (1 + pct / 100)) for value in values]
                average = moving_average(simulated_values)
                current = next((item["quantity"] for item in data["inventory"] if item["name"] == product), 0)
                shortfall = max(0, int(average * 7 - current))
                rows.append(
                    {
                        "Product": product,
                        "Simulated Avg Demand": average,
                        "Current Stock": current,
                        "Potential Shortfall": shortfall,
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 24px 16px 18px; border-bottom: 1px solid {t['border_soft']}; margin-bottom: 4px;">
            <div style="font-size: 20px; font-weight: 800; color: {t['primary']}; letter-spacing: -0.03em;">
                🏭 Control Tower
            </div>
            <div style="font-size: 11px; color: {t['text_muted']}; margin-top: 4px; font-weight: 400;">
                AI Supply Chain Suite · v3.0
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    toggle_label = "☀️ Light Mode" if dark else "🌙 Dark Mode"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.dark_mode = not dark
        st.rerun()

    st.markdown(
        f"<div style='height:4px; border-bottom: 1px solid {t['border_soft']}; margin-bottom: 8px'></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='font-size:10px; text-transform:uppercase; letter-spacing:0.12em; color:{t['text_sub']}; padding: 12px 0 6px; font-weight:700;'>Scenario Control</div>",
        unsafe_allow_html=True,
    )
    st.session_state.region = st.selectbox(
        "Operational Region",
        list(REGION_PROFILES.keys()),
        index=list(REGION_PROFILES.keys()).index(st.session_state.region),
    )
    st.caption(REGION_PROFILES[st.session_state.region]["label"])

    st.markdown(
        f"<div style='font-size:10px; text-transform:uppercase; letter-spacing:0.12em; color:{t['text_sub']}; padding: 16px 0 6px; font-weight:700;'>Navigation</div>",
        unsafe_allow_html=True,
    )
    page = st.radio(
        "nav",
        ["📊 Dashboard", "📦 Inventory", "🛒 Orders", "🚚 Shipments", "🤝 Vendors", "⚙️ Data Management"],
        label_visibility="collapsed",
    )

    sidebar_data = normalize_data(load_data())
    stats = [
        ("📦 Products", len(sidebar_data["inventory"])),
        ("🛒 Orders", len(sidebar_data["orders"])),
        ("🚚 Shipments", len(sidebar_data["shipments"])),
        ("🤝 Vendors", len(sidebar_data["vendors"])),
    ]
    st.markdown(
        f"<div style='font-size:10px; text-transform:uppercase; letter-spacing:0.12em; color:{t['text_sub']}; padding: 20px 0 8px; font-weight:700;'>Data Status</div>",
        unsafe_allow_html=True,
    )
    for label, value in stats:
        st.markdown(
            f"""
            <div class="sidebar-stat">
                <span>{label}</span>
                <span class="stat-val">{value}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    delayed_shipments = sum(1 for shipment in sidebar_data["shipments"] if compute_delay_days(shipment) > 0)
    st.markdown(
        f"""
        <div style="margin-top:14px; background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
                    border-left: 3px solid {t['danger']}; border-radius: 8px; padding: 10px 12px;
                    font-size: 12px; color: {t['danger']}; font-weight: 600;">
            ⚡ {delayed_shipments} delayed shipment{'s' if delayed_shipments != 1 else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


if page == "📊 Dashboard":
    render_dashboard()
elif page == "📦 Inventory":
    render_inventory()
elif page == "🛒 Orders":
    render_orders()
elif page == "🚚 Shipments":
    render_shipments()
elif page == "🤝 Vendors":
    render_vendors()
elif page == "⚙️ Data Management":
    render_data_management()

st.markdown(
    '<div class="footer">Built for decision intelligence · Supply Chain Control Tower · v3.0</div>',
    unsafe_allow_html=True,
)
