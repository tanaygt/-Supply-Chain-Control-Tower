# shipments.py — Shipment Tracking

import streamlit as st
import pandas as pd
from utils import load_data, save_data, gen_id, today, section_header, page_header, alert_box, theme

SHIP_STATUSES = ["Pending", "Dispatched", "In Transit", "Delivered"]
STAGE_COLORS  = {"Pending": "#64748B", "Dispatched": "#3B82F6",
                 "In Transit": "#F59E0B", "Delivered": "#22C55E"}

def render_shipments():
    t = theme()
    data      = load_data()
    shipments = data["shipments"]
    orders    = data["orders"]
    order_ids = [o["id"] for o in orders]

    page_header("🚚 Shipment Tracking", "Monitor the full shipment lifecycle from dispatch to delivery")

    # ── Delayed alert ─────────────────────────────────────────────────────────
    delayed = [s for s in shipments if s.get("delayed")]
    if delayed:
        alert_box(f"<b>{len(delayed)} delayed shipment{'s' if len(delayed)>1 else ''}</b> require attention — review below.")

    # ── Create shipment ───────────────────────────────────────────────────────
    with st.expander("➕  Create New Shipment", expanded=False):
        with st.form("new_shp", clear_on_submit=True):
            cols = st.columns([2, 2, 2, 2])
            oid      = cols[0].selectbox("Linked Order", order_ids or ["No Orders"])
            carrier  = cols[1].text_input("Carrier", value="FedEx")
            exp_date = cols[2].text_input("Expected Date (YYYY-MM-DD)", value=today())
            status   = cols[3].selectbox("Status", SHIP_STATUSES)
            if st.form_submit_button("✅  Create Shipment", use_container_width=True):
                if order_ids:
                    shipments.append({
                        "id": gen_id("SHP"), "order_id": oid, "carrier": carrier,
                        "status": status, "dispatch_date": today(),
                        "expected_date": exp_date, "actual_date": None, "delayed": False
                    })
                    save_data(data); st.success("Shipment created!"); st.rerun()
                else:
                    st.warning("Create an order first.")

    if not shipments:
        st.info("No shipments yet.")
        return

    # ── Table ─────────────────────────────────────────────────────────────────
    section_header("📋 Shipment Table")
    rows = []
    for s in shipments:
        rows.append({
            "ID":        s["id"],
            "Order":     s["order_id"],
            "Carrier":   s["carrier"],
            "Status":    s["status"],
            "Dispatched":s["dispatch_date"],
            "Expected":  s["expected_date"],
            "Delivered": s.get("actual_date") or "—",
            "Delayed":   "🔴 Yes" if s.get("delayed") else "🟢 No",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("⬇️  Export CSV", df.to_csv(index=False),
                       "shipments.csv", "text/csv")

    # ── Update ────────────────────────────────────────────────────────────────
    section_header("✏️ Update Shipment")
    sel_id = st.selectbox("Select Shipment", [s["id"] for s in shipments])
    shp    = next(s for s in shipments if s["id"] == sel_id)

    with st.form("upd_shp"):
        cols = st.columns([2, 2, 1])
        new_status   = cols[0].selectbox("Status", SHIP_STATUSES,
                                         index=SHIP_STATUSES.index(shp["status"]))
        act_date     = cols[1].text_input("Actual Delivery Date", value=shp.get("actual_date") or "")
        mark_delayed = cols[2].checkbox("Mark as Delayed", value=shp.get("delayed", False))
        if st.form_submit_button("💾  Update Shipment", use_container_width=True):
            shp["status"]      = new_status
            shp["actual_date"] = act_date or None
            shp["delayed"]     = mark_delayed
            save_data(data); st.success("Shipment updated!"); st.rerun()

    # ── Pipeline board ────────────────────────────────────────────────────────
    section_header("🗂️ Shipment Pipeline")
    cols = st.columns(4, gap="small")
    for i, stage in enumerate(SHIP_STATUSES):
        items = [s for s in shipments if s["status"] == stage]
        color = STAGE_COLORS[stage]
        with cols[i]:
            st.markdown(f"""
            <div class="pipeline-col">
                <div class="pipeline-col-title">
                    <span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block;"></span>
                    {stage} <span style="margin-left:4px;background:{t['card2']};border:1px solid {t['border_soft']};
                    border-radius:99px;padding:1px 8px;font-family:'JetBrains Mono',monospace;font-size:11px;
                    color:{t['text']}">{len(items)}</span>
                </div>
                {"".join(
                    f'<div class="pipeline-item{" delayed" if s.get("delayed") else ""}">'
                    f'{s["id"]}<br><span style="font-size:10px;color:{t["text_muted"]}">{s["carrier"]}</span></div>'
                    for s in items
                ) or f'<div style="font-size:12px;color:{t["text_sub"]};padding:8px 0;">No shipments</div>'}
            </div>
            """, unsafe_allow_html=True)
