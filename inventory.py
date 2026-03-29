# inventory.py — Inventory Management

import streamlit as st
import pandas as pd
from utils import load_data, save_data, gen_id, moving_average, suggest_reorder
from utils import section_header, page_header, alert_box, theme

def _init_stacks():
    if "inv_undo" not in st.session_state: st.session_state.inv_undo = []
    if "inv_redo" not in st.session_state: st.session_state.inv_redo = []

def _push_undo(snapshot):
    st.session_state.inv_undo.append(snapshot)
    st.session_state.inv_redo.clear()

def render_inventory():
    t = theme()
    _init_stacks()
    data      = load_data()
    inventory = data["inventory"]

    page_header("📦 Inventory Management", "Add, edit and monitor your product stock levels")

    # ── Low stock alerts ──────────────────────────────────────────────────────
    low = [i for i in inventory if i["quantity"] <= i["reorder_point"]]
    if low:
        for item in low:
            alert_box(f"<b>{item['name']}</b> is critically low — "
                      f"<b>{item['quantity']}</b> units left "
                      f"(reorder at {item['reorder_point']})")

    # ── Undo / Redo ───────────────────────────────────────────────────────────
    c1, c2, _ = st.columns([1, 1, 5])
    if c1.button("↩ Undo", disabled=not st.session_state.inv_undo, use_container_width=True):
        st.session_state.inv_redo.append([i.copy() for i in inventory])
        data["inventory"] = st.session_state.inv_undo.pop()
        save_data(data); st.rerun()
    if c2.button("↪ Redo", disabled=not st.session_state.inv_redo, use_container_width=True):
        st.session_state.inv_undo.append([i.copy() for i in inventory])
        data["inventory"] = st.session_state.inv_redo.pop()
        save_data(data); st.rerun()

    # ── Add product ───────────────────────────────────────────────────────────
    with st.expander("➕  Add New Product", expanded=False):
        with st.form("add_inv", clear_on_submit=True):
            r1 = st.columns([3, 1, 1, 1, 1])
            name = r1[0].text_input("Product Name")
            sku  = r1[1].text_input("SKU")
            qty  = r1[2].number_input("Quantity", min_value=0, value=0)
            wh   = r1[3].selectbox("Warehouse", ["WH-A","WH-B","WH-C","WH-D"])
            rop  = r1[4].number_input("Reorder Point", min_value=0, value=100)
            cost = st.number_input("Unit Cost ($)", min_value=0.0, value=1.0, step=0.01)

            if st.form_submit_button("✅  Add Product", use_container_width=True):
                if name and sku:
                    _push_undo([i.copy() for i in inventory])
                    inventory.append({
                        "id": gen_id("INV"), "name": name, "sku": sku,
                        "quantity": qty, "warehouse": wh,
                        "reorder_point": rop, "unit_cost": cost
                    })
                    save_data(data)
                    st.success(f"✅ Added **{name}** to inventory.")
                    st.rerun()
                else:
                    st.warning("Product name and SKU are required.")

    # ── Search + Table ────────────────────────────────────────────────────────
    section_header("📋 Inventory Table")

    search = st.text_input("🔍 Search by name or SKU", placeholder="e.g. Steel Bolts or SKU-001")
    if not inventory:
        st.info("No inventory items yet. Add a product above.")
        return

    df = pd.DataFrame(inventory)
    if search:
        mask = (df["name"].str.contains(search, case=False) |
                df["sku"].str.contains(search, case=False))
        df = df[mask]

    df["Total Value ($)"] = (df["quantity"] * df["unit_cost"]).round(2)
    df["Stock Status"] = df.apply(
        lambda r: "🔴 Critical" if r.quantity <= r.reorder_point else
                  ("🟡 Low"      if r.quantity <= r.reorder_point * 1.5 else "🟢 OK"), axis=1
    )

    st.dataframe(
        df[["id","name","sku","quantity","warehouse","reorder_point","unit_cost","Total Value ($)","Stock Status"]],
        use_container_width=True, hide_index=True
    )
    st.download_button("⬇️  Export as CSV", df.to_csv(index=False),
                       "inventory.csv", "text/csv", use_container_width=False)

    # ── Edit / Delete ─────────────────────────────────────────────────────────
    section_header("✏️ Edit / Delete Item")
    ids    = [i["id"] for i in data["inventory"]]
    sel_id = st.selectbox("Select item to edit", ids)
    item   = next(i for i in data["inventory"] if i["id"] == sel_id)

    with st.form("edit_inv"):
        r = st.columns([3, 1, 1, 1, 1, 1])
        new_name = r[0].text_input("Name",  value=item["name"])
        new_sku  = r[1].text_input("SKU",   value=item["sku"])
        new_qty  = r[2].number_input("Qty", value=item["quantity"],      min_value=0)
        wh_opts  = ["WH-A","WH-B","WH-C","WH-D"]
        new_wh   = r[3].selectbox("Warehouse", wh_opts,
                                   index=wh_opts.index(item["warehouse"]) if item["warehouse"] in wh_opts else 0)
        new_rop  = r[4].number_input("Reorder Pt", value=item["reorder_point"], min_value=0)
        new_cost = r[5].number_input("Cost ($)",   value=item["unit_cost"],     min_value=0.0, step=0.01)

        sa, sb = st.columns(2)
        if sa.form_submit_button("💾  Save Changes", use_container_width=True):
            _push_undo([i.copy() for i in data["inventory"]])
            item.update({"name": new_name, "sku": new_sku, "quantity": new_qty,
                         "warehouse": new_wh, "reorder_point": new_rop, "unit_cost": new_cost})
            save_data(data); st.success("✅ Changes saved."); st.rerun()
        if sb.form_submit_button("🗑️  Delete Item", use_container_width=True):
            _push_undo([i.copy() for i in data["inventory"]])
            data["inventory"] = [i for i in data["inventory"] if i["id"] != sel_id]
            save_data(data); st.warning("Item deleted."); st.rerun()

    # ── AI Forecast ───────────────────────────────────────────────────────────
    section_header("🤖 AI Demand Forecast & Reorder Suggestions")
    st.caption("Based on moving average of historical demand data (no API required).")
    demand_hist = data.get("demand_history", {})
    rows = []
    for inv_item in data["inventory"]:
        hist  = demand_hist.get(inv_item["name"], [])
        avg   = moving_average(hist)
        sugg  = suggest_reorder(inv_item["quantity"], avg)
        trend = "📈 Rising" if len(hist) >= 2 and hist[-1] > hist[-2] else "📉 Flat/Down"
        rows.append({
            "Product":           inv_item["name"],
            "Avg Demand/Period": avg,
            "Current Stock":     inv_item["quantity"],
            "Suggested Reorder": sugg,
            "Trend":             trend,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
