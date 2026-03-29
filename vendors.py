# vendors.py — Vendor Management

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, save_data, gen_id, section_header, page_header, theme

CATEGORIES = ["Metals","Electronics","Plastics","Raw Materials","Chemicals","Logistics","Other"]

def render_vendors():
    t = theme()
    data    = load_data()
    vendors = data["vendors"]

    page_header("🤝 Vendor Management", "Track vendor details, performance scores and reliability")

    # ── Add vendor ────────────────────────────────────────────────────────────
    with st.expander("➕  Add New Vendor", expanded=False):
        with st.form("new_vendor", clear_on_submit=True):
            cols = st.columns([2, 2, 1, 1])
            name     = cols[0].text_input("Vendor Name")
            contact  = cols[1].text_input("Contact Email")
            phone    = cols[2].text_input("Phone")
            category = cols[3].selectbox("Category", CATEGORIES)
            if st.form_submit_button("✅  Add Vendor", use_container_width=True):
                if name:
                    vendors.append({
                        "id": gen_id("VEN"), "name": name, "contact": contact,
                        "phone": phone, "category": category,
                        "score": 75, "orders_fulfilled": 0, "on_time_rate": 80
                    })
                    save_data(data); st.success(f"Vendor **{name}** added."); st.rerun()
                else:
                    st.warning("Vendor name is required.")

    if not vendors:
        st.info("No vendors yet. Add one above.")
        return

    # ── Score summary cards ───────────────────────────────────────────────────
    top    = max(vendors, key=lambda v: v["score"])
    avg_sc = round(sum(v["score"] for v in vendors) / len(vendors), 1)
    worst  = min(vendors, key=lambda v: v["score"])

    kc = st.columns(3)
    kc[0].metric("🏆 Top Vendor",    f"{top['name']}",    f"Score: {top['score']}")
    kc[1].metric("📊 Avg Score",     f"{avg_sc}/100",     f"{len(vendors)} vendors")
    kc[2].metric("⚠️  Needs Review",  f"{worst['name']}", f"Score: {worst['score']}")

    # ── Table ─────────────────────────────────────────────────────────────────
    section_header("📋 Vendor List")
    df = pd.DataFrame(vendors)
    df["Grade"] = df["score"].apply(
        lambda s: "⭐ Excellent" if s >= 90 else ("✅ Good" if s >= 75 else "⚠️ Review")
    )
    st.dataframe(
        df[["id","name","contact","phone","category","score","orders_fulfilled","on_time_rate","Grade"]],
        use_container_width=True, hide_index=True
    )
    st.download_button("⬇️  Export CSV", df.to_csv(index=False), "vendors.csv", "text/csv")

    # ── Edit ──────────────────────────────────────────────────────────────────
    section_header("✏️ Update Vendor Performance")
    sel_id = st.selectbox("Select Vendor", [v["id"] for v in vendors])
    vendor = next(v for v in vendors if v["id"] == sel_id)

    with st.form("upd_vendor"):
        cols = st.columns(3)
        new_score = cols[0].slider("Performance Score",  0, 100, vendor["score"])
        new_ord   = cols[1].number_input("Orders Fulfilled", value=vendor["orders_fulfilled"], min_value=0)
        new_otr   = cols[2].slider("On-Time Rate (%)",   0, 100, vendor["on_time_rate"])
        a, b = st.columns(2)
        if a.form_submit_button("💾  Save", use_container_width=True):
            vendor.update({"score": new_score, "orders_fulfilled": new_ord, "on_time_rate": new_otr})
            save_data(data); st.success("Updated!"); st.rerun()
        if b.form_submit_button("🗑️  Delete Vendor", use_container_width=True):
            data["vendors"] = [v for v in vendors if v["id"] != sel_id]
            save_data(data); st.warning("Deleted."); st.rerun()

    # ── Charts ────────────────────────────────────────────────────────────────
    section_header("📊 Performance Analytics")

    chart_base = dict(
        plot_bgcolor=t["plot_bg"], paper_bgcolor=t["paper_bg"],
        font_color=t["font_color"], margin=dict(t=36,b=16,l=8,r=8),
        font=dict(family="Plus Jakarta Sans"),
        xaxis=dict(gridcolor=t["border_soft"]),
        yaxis=dict(gridcolor=t["border_soft"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        df_s = df.sort_values("score", ascending=True)
        colors = [t["danger"] if s < 75 else (t["accent"] if s < 90 else t["secondary"])
                  for s in df_s["score"]]
        fig = go.Figure(go.Bar(
            x=df_s["score"], y=df_s["name"], orientation="h",
            marker_color=colors, marker_line_width=0
        ))
        fig.update_layout(**chart_base, title="Vendor Scores", height=260)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(
            df, x="orders_fulfilled", y="on_time_rate", size="score",
            color="category", hover_name="name",
            color_discrete_sequence=[t["primary"], t["secondary"], t["accent"],
                                      t["danger"], "#A78BFA", "#F472B6", "#67E8F9"],
            labels={"orders_fulfilled": "Orders Fulfilled", "on_time_rate": "On-Time Rate (%)"},
            title="Reliability Matrix"
        )
        fig2.update_layout(**chart_base, height=260)
        st.plotly_chart(fig2, use_container_width=True)
