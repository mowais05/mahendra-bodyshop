import streamlit as st
import pandas as pd
import os

# --- APP CONFIG & BRANDING ---
st.set_page_config(page_title="Mahendra Bodyshop | Faizabad", layout="wide", page_icon="🚗")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main-title { font-size: 42px; font-weight: bold; color: #1E88E5; text-align: center; margin-bottom: -10px; }
    .subtitle { font-size: 20px; color: #444; text-align: center; margin-bottom: 30px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #1E88E5; text-align: center; padding: 8px; font-weight: bold; border-top: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).astype(str)
    return pd.DataFrame(columns=["Car Number", "Customer Name", "Status", "Delivery Date", "Message"])

STATUS_LIST = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "Dismental", "Denting", "Painting", "Fitting", "Delivery Order Waiting from Insurance Company", "Final Delivery"]

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1E88E5;'>Mahendra Bodyshop</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation Menu", ["Customer Portal", "Employee Login"])

# --- HEADER ---
st.markdown("<div class='main-title'>MAHENDRA BODYSHOP FAIZABAD</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Premium Car Claim Tracking Portal</div>", unsafe_allow_html=True)

# --- CUSTOMER PORTAL ---
if menu == "Customer Portal":
    st.subheader("🔍 Check Your Car Process Status")
    car_input = st.text_input("Enter your Car Number (e.g., UP42XXXX):").upper().strip()
    if st.button("Track Progress"):
        df = load_data()
        result = df[df["Car Number"] == car_input]
        if not result.empty:
            status, delivery, msg = result.iloc[0]["Status"], result.iloc[0]["Delivery Date"], result.iloc[0]["Message"]
            st.success(f"**Current Status:** {status}"); st.info(f"**Estimated Delivery:** {delivery}")
            if msg and msg != "nan": st.warning(f"**Note:** {msg}")
            if status in STATUS_LIST: st.progress((STATUS_LIST.index(status) + 1) / len(STATUS_LIST))
        else:
            st.error("No record found. Please contact Mahendra Bodyshop.")

# --- EMPLOYEE SIDE ---
else:
    st.subheader("👨‍🔧 Workshop Management")
    password = st.text_input("Enter Password", type="password")
    
    if password == "admin123":
        df = load_data()

        # --- SEARCH SECTION ---
        st.write("### 🔎 Quick Search (Last 4 Digits)")
        search_query = st.text_input("Enter Last 4 Digits or Full Car Number to Filter").upper().strip()

        # Filtering logic: matches full number OR just the last 4 digits
        if search_query:
            display_df = df[df["Car Number"].str.contains(search_query, na=False)]
        else:
            display_df = df

        # --- TABLE ---
        st.write("### 📋 Active Claim Records")
        if not display_df.empty:
            cols = st.columns([2, 2, 2, 2, 2, 1, 1])
            fields = ["Car Number", "Customer", "Status", "Delivery", "Message", "Edit", "Delete"]
            for col, field in zip(cols, fields): col.write(f"**{field}**")

            for index, row in display_df.iterrows():
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 2, 2, 2, 2, 1, 1])
                c1.write(row["Car Number"])
                c2.write(row["Customer Name"])
                c3.write(row["Status"])
                c4.write(row["Delivery Date"])
                c5.write(row["Message"] if row["Message"] != "nan" else "-")
                if c6.button("📝", key=f"edit_{index}"): st.session_state['edit_car'] = row["Car Number"]
                if c7.button("🗑️", key=f"del_{index}"):
                    df = df.drop(df[df["Car Number"] == row["Car Number"]].index)
                    df.to_csv(DB_FILE, index=False); st.rerun()
        else:
            st.info("No matching records found.")

        st.markdown("---")

        # --- EDIT FORM ---
        edit_car_no = st.session_state.get('edit_car', "")
        st.write(f"### 🛠️ {'Update' if edit_car_no else 'Add New'} Claim Entry")
        
        d_name, d_status, d_msg = "", "Car Received", ""
        if edit_car_no:
            rec = df[df["Car Number"] == edit_car_no]
            if not rec.empty: d_name, d_status, d_msg = rec.iloc[0]["Customer Name"], rec.iloc[0]["Status"], rec.iloc[0]["Message"]

        with st.form("main_form", clear_on_submit=True):
            f_car = st.text_input("Car Number", value=edit_car_no).upper().strip()
            f_name = st.text_input("Customer Name", value=d_name)
            idx = STATUS_LIST.index(d_status) if d_status in STATUS_LIST else 0
            f_status = st.selectbox("Process Stage", STATUS_LIST, index=idx)
            f_date = st.date_input("Target Delivery Date")
            f_msg = st.text_area("Comments", value="" if d_msg == "nan" else d_msg)
            
            if st.form_submit_button("Update Records"):
                if f_car:
                    df = load_data() # reload to ensure fresh data
                    df = df[df["Car Number"] != f_car]
                    new_data = pd.DataFrame([[f_car, f_name, f_status, str(f_date), f_msg]], columns=df.columns)
                    df = pd.concat([df, new_data], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.session_state['edit_car'] = ""
                    st.success("Updated!"); st.rerun()
                else: st.error("Car Number required!")

    elif password != "": st.error("Wrong Password")

st.markdown("<div class='footer'>Mahendra Bodyshop Faizabad © 2026 | Powered by Owais Production</div>", unsafe_allow_html=True)