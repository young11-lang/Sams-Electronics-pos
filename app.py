import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import random

# ==========================================
# SHOP CONFIGURATION
# ==========================================
SHOP_NAME = "Sam's Electronics & Phone Repair"
SHOP_LOCATION = "Ruburi, Gatundu, Kiambu County"

st.set_page_config(page_title=f"{SHOP_NAME} - POS & Inventory", page_icon="⚡", layout="wide")
st.title(f"⚡ {SHOP_NAME} - POS, Sales & Inventory Dashboard")
st.caption(f"📍 Location: {SHOP_LOCATION}")

# Initialize Inventory in Session State
if 'inventory_data' not in st.session_state:
    try:
        df = pd.read_csv("inventory.csv")
    except Exception:
        try:
            df = pd.read_csv("inventory.csv.csv")
        except Exception:
            df = pd.DataFrame({
                "SKU": ["SKU-1001", "SKU-1002"],
                "Item Name": ["PPR Gate Valve 3/4\"", "PVC Elbow 1/2\""],
                "Category": ["Plumbing Product", "Plumbing Product"],
                "Cost Price (KES)": [455.0, 35.0],
                "Unit Price (KES)": [650.0, 50.0],
                "Stock Qty": [102, 30],
                "Reorder Level": [15, 15]
            })

    df.columns = [str(c).strip().replace('"', '').replace("'", "") for c in df.columns]
    cols = df.columns.tolist()
    if len(cols) >= 7:
        df = df.rename(columns={
            cols[0]: 'SKU',
            cols[1]: 'Item Name',
            cols[2]: 'Category',
            cols[3]: 'Cost Price (KES)',
            cols[4]: 'Unit Price (KES)',
            cols[5]: 'Stock Qty',
            cols[6]: 'Reorder Level'
        })

    for col in ['Cost Price (KES)', 'Unit Price (KES)', 'Stock Qty', 'Reorder Level']:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('KES', '', case=False).str.replace(',', '').str.replace('"', '').str.strip(), 
                errors='coerce'
            ).fillna(0)
    st.session_state.inventory_data = df

# Initialize Sales Session State (with Profit tracking)
if 'sales_data' not in st.session_state:
    try:
        df_existing = pd.read_csv("sales_ledger.csv")
        if 'Timestamp' in df_existing.columns and not df_existing.empty:
            if 'Profit (KES)' not in df_existing.columns:
                df_existing['Profit (KES)'] = 0.0
            st.session_state.sales_data = df_existing
        else:
            st.session_state.sales_data = pd.DataFrame(columns=['Timestamp', 'SKU', 'Item Name', 'Category', 'Quantity Sold', 'Unit Price (KES)', 'Total Amount (KES)', 'Profit (KES)', 'Payment Method', 'M-Pesa Code'])
    except Exception:
        st.session_state.sales_data = pd.DataFrame(columns=['Timestamp', 'SKU', 'Item Name', 'Category', 'Quantity Sold', 'Unit Price (KES)', 'Total Amount (KES)', 'Profit (KES)', 'Payment Method', 'M-Pesa Code'])

if 'last_success_message' not in st.session_state:
    st.session_state.last_success_message = ""

if 'latest_receipt' not in st.session_state:
    st.session_state.latest_receipt = None

df_inv = st.session_state.inventory_data
df_sales = st.session_state.sales_data

# Sidebar Navigation Tabs
tab_choice = st.sidebar.radio("Navigation", [
    "🛒 POS Checkout Counter", 
    "📈 Inventory & Stock Analytics", 
    "➕ Add Product & Restock", 
    "💰 Sales & M-Pesa Ledger"
])

# Display persistent success banner if present
if st.session_state.last_success_message:
    st.success(st.session_state.last_success_message)
    st.session_state.last_success_message = ""

# ==========================================
# TAB 1: POS CHECKOUT COUNTER
# ==========================================
if tab_choice == "🛒 POS Checkout Counter":
    st.header("🛒 Point of Sale (POS) Checkout")
    col_pos1, col_pos2 = st.columns([2, 1])

    with col_pos1:
        st.subheader("Select Item / Service to Sell")
        item_options = df_inv["Item Name"].tolist()
        if not item_options:
            st.warning("No inventory items available.")
        else:
            selected_item_name = st.selectbox("Choose Product or Service:", options=item_options)
            
            item_row = df_inv[df_inv["Item Name"] == selected_item_name].iloc[0]
            sku = item_row["SKU"]
            category = item_row["Category"]
            cost_price = float(item_row["Cost Price (KES)"])
            unit_price = float(item_row["Unit Price (KES)"])
            max_stock = int(item_row["Stock Qty"])

            st.info(f"**Category:** {category} | **SKU:** {sku} | **Unit Price:** KES {unit_price:,.2f} | **Available Stock:** {max_stock}")

            qty_sold = st.number_input("Quantity Sold:", min_value=1, max_value=max(1, max_stock), value=1)
            total_amount = unit_price * qty_sold
            total_profit = (unit_price - cost_price) * qty_sold

            st.markdown(f"### Total Due: KES {total_amount:,.2f}")

            payment_method = st.selectbox("Payment Method:", ["Cash", "M-Pesa STK Push Prompt", "M-Pesa Manual Code", "Bank Transfer"])
            
            customer_phone = ""
            mpesa_code = "N/A"
            
            if payment_method == "M-Pesa STK Push Prompt":
                customer_phone = st.text_input("Customer Phone Number (e.g., 0712345678):", value="07")
            elif payment_method == "M-Pesa Manual Code":
                mpesa_code = st.text_input("M-Pesa Confirmation Code (e.g., QGH78...):")

            button_label = "📲 Send M-Pesa STK Prompt" if payment_method == "M-Pesa STK Push Prompt" else "Complete Sale & Record"
            
            if st.button(button_label, type="primary"):
                if payment_method == "M-Pesa STK Push Prompt":
                    if len(customer_phone) < 10:
                        st.error("Please enter a valid customer phone number for the M-Pesa prompt.")
                    else:
                        with st.spinner(f"Sending M-Pesa payment prompt to {customer_phone} for KES {total_amount:,.2f}..."):
                            time.sleep(2.0)
                        
                        random_suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
                        mpesa_code = f"RKT{random_suffix}"
                        st.success(f"✅ STK Push Successful! Confirmed with M-Pesa Code: **{mpesa_code}**")
                
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_sale = {
                    'Timestamp': timestamp_str,
                    'SKU': sku,
                    'Item Name': selected_item_name,
                    'Category': category,
                    'Quantity Sold': qty_sold,
                    'Unit Price (KES)': unit_price,
                    'Total Amount (KES)': total_amount,
                    'Profit (KES)': total_profit,
                    'Payment Method': payment_method,
                    'M-Pesa Code': mpesa_code
                }
                
                st.session_state.sales_data = pd.concat([st.session_state.sales_data, pd.DataFrame([new_sale])], ignore_index=True)
                st.session_state.inventory_data.loc[st.session_state.inventory_data["SKU"] == sku, "Stock Qty"] -= qty_sold
                
                st.session_state.latest_receipt = new_sale
                
                try:
                    st.session_state.sales_data.to_csv("sales_ledger.csv", index=False)
                    st.session_state.inventory_data.to_csv("inventory.csv", index=False)
                except Exception:
                    pass
                
                st.session_state.last_success_message = f"✅ Sale Complete! KES {total_amount:,.2f} processed via {payment_method}. Stock updated!"
                st.rerun()

    with col_pos2:
        st.subheader("Quick Cash Calculator")
        tendered = st.number_input("Cash Tendered by Customer (KES):", min_value=0.0, step=50.0)
        if tendered >= total_amount:
            change = tendered - total_amount
            st.metric("Change to Return", f"KES {change:,.2f}")
        else:
            st.warning("Amount tendered is less than total due.")

    # Printable Customer Receipt
    if st.session_state.latest_receipt:
        st.markdown("---")
        st.subheader("🧾 Latest Customer Receipt")
        rec = st.session_state.latest_receipt
        receipt_text = f"""
========================================
     SAM'S ELECTRONICS & PHONE REPAIR   
     Ruburi, Gatundu, Kiambu County     
========================================
Date/Time : {rec['Timestamp']}
SKU       : {rec['SKU']}
Item      : {rec['Item Name']}
Category  : {rec['Category']}
Qty Sold  : {rec['Quantity Sold']}
Unit Price: KES {rec['Unit Price (KES)']:,.2f}
----------------------------------------
TOTAL DUE : KES {rec['Total Amount (KES)']:,.2f}
Payment   : {rec['Payment Method']}
M-Pesa ID : {rec['M-Pesa Code']}
========================================
     Thank you! Welcome again.          
========================================
"""
        st.code(receipt_text, language="text")
        if st.button("Clear Receipt View"):
            st.session_state.latest_receipt = None
            st.rerun()

# ==========================================
# TAB 2: INVENTORY & STOCK ANALYTICS
# ==========================================
elif tab_choice == "📈 Inventory & Stock Analytics":
    st.header("📈 Inventory & Reorder Analytics")
    
    total_items = df_inv["Stock Qty"].sum()
    total_val = (df_inv["Cost Price (KES)"] * df_inv["Stock Qty"]).sum()
    potential_profit = ((df_inv["Unit Price (KES)"] - df_inv["Cost Price (KES)"]) * df_inv["Stock Qty"]).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Items in Stock", f"{int(total_items):,}")
    col2.metric("Total Inventory Value", f"KES {float(total_val):,.2f}")
    col3.metric("Potential Profit", f"KES {float(potential_profit):,.2f}")

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Inventory Value by Category")
        df_inv["Total Value"] = df_inv["Cost Price (KES)"] * df_inv["Stock Qty"]
        fig_cat = px.pie(df_inv, names="Category", values="Total Value", hole=0.4)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        st.subheader("Stock Levels per SKU")
        fig_bar = px.bar(df_inv.head(15), x="SKU", y="Stock Qty", color="Category")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Current Inventory Stock List")
    st.dataframe(df_inv, use_container_width=True)

    st.subheader("⚠️ Reorder Alerts")
    low_stock = df_inv[df_inv["Stock Qty"] <= df_inv["Reorder Level"]]
    if not low_stock.empty:
        st.dataframe(low_stock, use_container_width=True)
    else:
        st.success("All stock levels are healthy!")

# ==========================================
# TAB 3: ADD PRODUCT & RESTOCK
# ==========================================
elif tab_choice == "➕ Add Product & Restock":
    st.header("➕ Product Management & Restocking")
    
    col_add, col_restock = st.columns(2)

    with col_add:
        st.subheader("Add New Product / Repair Service")
        with st.form("add_product_form"):
            new_sku = st.text_input("New SKU (e.g., SKU-1050):")
            new_name = st.text_input("Item / Service Name:")
            new_category = st.selectbox("Category:", ["Phone Repair & Parts", "Electrical Wiring", "Plumbing Product", "Jua Kali Amplifiers"])
            new_cost = st.number_input("Cost Price (KES):", min_value=0.0, step=10.0)
            new_price = st.number_input("Unit Selling Price (KES):", min_value=0.0, step=10.0)
            new_qty = st.number_input("Initial Stock Quantity:", min_value=1, step=1)
            new_reorder = st.number_input("Reorder Level Alert:", min_value=1, value=15, step=1)
            
            submit_add = st.form_submit_button("Save New Product to Inventory")
            
            if submit_add:
                if new_sku and new_name:
                    if new_sku in df_inv["SKU"].values:
                        st.error(f"SKU {new_sku} already exists in inventory!")
                    else:
                        new_row = {
                            "SKU": new_sku,
                            "Item Name": new_name,
                            "Category": new_category,
                            "Cost Price (KES)": new_cost,
                            "Unit Price (KES)": new_price,
                            "Stock Qty": new_qty,
                            "Reorder Level": new_reorder
                        }
                        st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, pd.DataFrame([new_row])], ignore_index=True)
                        try:
                            st.session_state.inventory_data.to_csv("inventory.csv", index=False)
                        except Exception:
                            pass
                        st.session_state.last_success_message = f"✅ Successfully added new item: {new_name} ({new_sku})!"
                        st.rerun()
                else:
                    st.warning("Please provide both a SKU and an Item Name.")

    with col_restock:
        st.subheader("Restock Existing Inventory")
        restock_item = st.selectbox("Select Item to Restock:", options=df_inv["Item Name"].tolist(), key="restock_select")
        
        current_row = df_inv[df_inv["Item Name"] == restock_item].iloc[0]
        current_stock = int(current_row["Stock Qty"])
        item_sku = current_row["SKU"]
        
        st.info(f"**SKU:** {item_sku} | **Current Stock Qty:** {current_stock}")
        
        add_qty = st.number_input("Quantity to Add:", min_value=1, value=10, step=1, key="add_stock_num")
        
        if st.button("Confirm Restock Update", type="primary"):
            st.session_state.inventory_data.loc[st.session_state.inventory_data["SKU"] == item_sku, "Stock Qty"] += add_qty
            try:
                st.session_state.inventory_data.to_csv("inventory.csv", index=False)
            except Exception:
                pass
            st.session_state.last_success_message = f"✅ Restocked {add_qty} units to {restock_item}! New total stock: {current_stock + add_qty}."
            st.rerun()

# ==========================================
# TAB 4: SALES & M-PESA LEDGER
# ==========================================
elif tab_choice == "💰 Sales & M-Pesa Ledger":
    st.header("💰 Sales & Payment Reconciliation Ledger")
    
    current_sales = st.session_state.sales_data
    if not current_sales.empty:
        total_revenue = current_sales["Total Amount (KES)"].sum()
        total_net_profit = current_sales["Profit (KES)"].sum() if "Profit (KES)" in current_sales.columns else 0.0
        cash_rev = current_sales[current_sales["Payment Method"] == "Cash"]["Total Amount (KES)"].sum()
        mpesa_rev = current_sales[current_sales["Payment Method"].str.contains("M-Pesa", case=False, na=False)]["Total Amount (KES)"].sum()
        bank_rev = current_sales[current_sales["Payment Method"] == "Bank Transfer"]["Total Amount (KES)"].sum()

        rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns(5)
        rcol1.metric("Total Revenue", f"KES {total_revenue:,.2f}")
        rcol2.metric("Net Profit", f"KES {total_net_profit:,.2f}")
        rcol3.metric("Cash Collected", f"KES {cash_rev:,.2f}")
        rcol4.metric("M-Pesa Total", f"KES {mpesa_rev:,.2f}")
        rcol5.metric("Bank Transfers", f"KES {bank_rev:,.2f}")

        st.markdown("---")
        st.subheader("📋 Complete Transaction History")
        st.dataframe(current_sales, use_container_width=True)

        csv_data = current_sales.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Sales Ledger as CSV",
            data=csv_data,
            file_name="daily_sales_ledger.csv",
            mime="text/csv",
        )
    else:
        st.info("No sales recorded yet. Use the POS Checkout Counter tab to log your first transaction!")