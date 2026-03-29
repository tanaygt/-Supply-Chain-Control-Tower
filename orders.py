# orders.py — Order Management

import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, save_data, gen_id, today, section_header, page_header, theme

STATUSES      = ["Pending", "Processing", "Completed", "Cancelled"]
STATUS_EMOJI  = {"Pending": "🟡", "Processing": "🔵", "Completed": "🟢", "Cancelled": "🔴"}

def _init_stacks():
    if "ord_undo" not in st.session_state: st.session_state.ord_undo = []
    if "ord_redo" not in st.session_state: st.session_state.ord_redo = []

def _push_undo(snapshot):
    st.session_state.ord_undo.append(snapshot)
    st.session_state.ord_redo.clear()

def render_orders():
    t = theme()
    _init_stacks()
    data    = load_data()
    orders  = data["orders"]
    vendors = [v["name"] for v in data["vendors"]] or ["No Vendors"]
    products= [i["name"] for i in data["inventory"]] or ["No Products"]

    page_header("🛒 Order Management", "Create, track and manage purchase orders")

    # ── Undo / Redo ───────────────────────────────────────────────────────────
    c1, c2, _ = st.columns([1, 1, 5])
    if c1.button("↩ Undo", key="ord_un", disabled=not st.session_state.ord_undo, use_container_width=True):
        st.session_state.ord_redo.append([o.copy() for o in orders])
        data["orders"] = st.session_state.ord_undo.pop()
        save_data(data); st.rerun()
    if c2.button("↪ Redo", key="ord_re", disabled=not st.session_state.ord_redo, use_container_width=True):
        st.session_state.ord_undo.append([o.copy() for o in orders])
        data["orders"] = st.session_state.ord_redo.pop()
        save_data(data); st.rerun()

    # ── Create order ──────────────────────────────────────────────────────────
    with st.expander("➕  Create New Order", expanded=False):
        with st.form("new_order", clear_on_submit=True):
            cols = st.columns([2, 1, 2, 1])
            prod   = cols[0].selectbox("Product",  products)
            qty    = cols[1].number_input("Qty",   min_value=1, value=10)
            vendor = cols[2].selectbox("Vendor",   vendors)
            status = cols[3].selectbox("Status",   STATUSES)
            unit_cost = next((i.get("unit_cost", 0.0) for i in data["inventory"] if i["name"] == prod), 0.0)
            total     = round(qty * unit_cost, 2)
            st.markdown(f"<div style='font-size:13px; color:{t['text_muted']}; padding:4px 0;'>Estimated Total: <b style='color:{t['text']}'>${total:,.2f}</b></div>",
                        unsafe_allow_html=True)
            if st.form_submit_button("✅  Create Order", use_container_width=True):
                _push_undo([o.copy() for o in orders])
                orders.append({
                    "id": gen_id("ORD"), "product": prod, "quantity": qty,
                    "status": status, "vendor": vendor,
                    "date": today(), "total": total
                })
                save_data(data); st.success("Order created!"); st.rerun()

    # ── Quick stats ───────────────────────────────────────────────────────────
    if orders:
        df_all = pd.DataFrame(orders)
        kc = st.columns(4)
        for i, s in enumerate(STATUSES):
            cnt = len(df_all[df_all["status"] == s])
            kc[i].metric(f"{STATUS_EMOJI[s]} {s}", cnt)

    # ── Filter + Table ────────────────────────────────────────────────────────
    section_header("📋 Order List")
    filt = st.pills("Filter by Status", ["All"] + STATUSES, default="All") \
           if hasattr(st, "pills") else st.selectbox("Filter by Status", ["All"] + STATUSES)
    disp = orders if filt == "All" else [o for o in orders if o["status"] == filt]

    if not disp:
        st.info("No orders match this filter.")
    else:
        df = pd.DataFrame(disp)
        df["status"] = df["status"].apply(lambda s: f"{STATUS_EMOJI.get(s,'')} {s}")
        st.dataframe(df[["id","product","quantity","status","vendor","date","total"]],
                     use_container_width=True, hide_index=True)
        st.download_button("⬇️  Export CSV", df.to_csv(index=False),
                           "orders.csv", "text/csv")

    # ── Edit / Delete ─────────────────────────────────────────────────────────
    if orders:
        section_header("✏️ Update / Delete Order")
        sel_id = st.selectbox("Select Order", [o["id"] for o in orders], key="ord_sel")
        order  = next(o for o in orders if o["id"] == sel_id)

        with st.form("upd_order"):
            cols = st.columns([2, 1, 2])
            new_status = cols[0].selectbox("Status", STATUSES,
                                           index=STATUSES.index(order["status"]))
            new_qty    = cols[1].number_input("Qty", value=order["quantity"], min_value=1)
            new_vendor = cols[2].selectbox("Vendor", vendors,
                                           index=vendors.index(order["vendor"])
                                                  if order["vendor"] in vendors else 0)
            a, b = st.columns(2)
            if a.form_submit_button("💾  Update Order", use_container_width=True):
                _push_undo([o.copy() for o in orders])
                order.update({"status": new_status, "quantity": new_qty, "vendor": new_vendor})
                save_data(data); st.success("Updated!"); st.rerun()
            if b.form_submit_button("🗑️  Delete Order", use_container_width=True):
                _push_undo([o.copy() for o in orders])
                data["orders"] = [o for o in orders if o["id"] != sel_id]
                save_data(data); st.warning("Order deleted."); st.rerun()

    # ── Value chart ───────────────────────────────────────────────────────────
    if orders:
        section_header("📊 Order Value by Vendor")
        t = theme()
        df_v = pd.DataFrame(orders).groupby("vendor")["total"].sum().reset_index()
        fig  = px.bar(df_v, x="vendor", y="total", color="vendor",
                      labels={"vendor":"Vendor","total":"Total Value ($)"},
                      color_discrete_sequence=[t["primary"], t["secondary"], t["accent"],
                                               t["danger"], "#A78BFA"])
        fig.update_layout(
            plot_bgcolor=t["plot_bg"], paper_bgcolor=t["paper_bg"],
            font_color=t["font_color"], showlegend=False,
            margin=dict(t=20, b=16, l=8, r=8),
            font=dict(family="Plus Jakarta Sans"),
            xaxis=dict(gridcolor=t["border_soft"]),
            yaxis=dict(gridcolor=t["border_soft"]),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
