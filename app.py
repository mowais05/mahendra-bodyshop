import streamlit as st
import pandas as pd
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Mahendra Bodyshop | Faizabad", layout="wide", page_icon="🚗")

# Custom CSS for Mobile & Branding
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E88E5; text-align: center; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #1E88E5; text-align: center; padding: 5px; font-size: 12px; border-top: 1px solid #ddd; }
    /* Making buttons look better on mobile */
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E88E5; color: white; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).astype(str)
    return pd.DataFrame(columns=["Car Number", "Customer Name", "Status", "Delivery Date", "Message"])

STATUS_LIST = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "Dismental", "Denting", "Painting", "Fitting", "Delivery Order Waiting from Insurance Company", "Final Delivery"]

# Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR ---
st.sidebar.title("Mahendra Bodyshop")
menu = st.sidebar.radio("Menu", ["Customer Portal", "Employee Login"])

if st.session_state['logged_in'] and menu == "Employee Login":
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

st.markdown("<div class='main-title'>MAHENDRA BODYSHOP FAIZABAD</div>", unsafe_allow_html=True)

# --- CUSTOMER PORTAL ---
if menu == "Customer Portal":
    st.subheader("🔍 Check Your Car Status")
    car_input = st.text_input("Enter Car Number (UP42-XXXX):").upper().strip()
    if st.button("Track Progress"):
        df = load_data()
        result = df[df["Car Number"] == car_input]
        if not result.empty:
            row = result.iloc[0]
            st.success(f"Status: {row['Status']}")
            st.info(f"Delivery: {row['Delivery Date']}")
            if row['Message'] != "nan": st.warning(f"Note: {row['Message']}")
            if row['Status'] in STATUS_LIST:
                st.progress((STATUS_LIST.index(row['Status']) + 1) / len(STATUS_LIST))
        else:
            st.error("No record found.")

# --- EMPLOYEE SIDE ---
else:
    if not st.session_state['logged_in']:
        st.subheader("👨‍🔧 Employee Login")
        with st.container():
            user_pass = st.text_input("Enter Password", type="password")
            if st.button("Login"):
                if user_pass == "admin123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Wrong Password!")
    else:
        df = load_data()
        
        # SEARCH
        st.write("### 🔎 Quick Search")
        search_query = st.text_input("Enter Last 4 Digits or Car Number").upper().strip()
        display_df = df[df["Car Number"].str.contains(search_query, na=False)] if search_query else df

        # TABLE
        st.write("### 📋 Active Claims")
        if not display_df.empty:
            for index, row in display_df.iterrows():
                with st.expander(f"🚗 {row['Car Number']} - {row['Customer Name']}"):
                    st.write(f"**Status:** {row['Status']}")
                    st.write(f"**Delivery:** {row['Delivery Date']}")
                    col_edit, col_del = st.columns(2)
                    if col_edit.button("Edit 📝", key=f"ed_{index}"):
                        st.session_state['edit_car'] = row['Car Number']
                    if col_del.button("Delete 🗑️", key=f"dl_{index}"):
                        df = df.drop(df[df["Car Number"] == row["Car Number"]].index)
                        df.to_csv(DB_FILE, index=False); st.rerun()
        
        st.markdown("---")
        
        # FORM
        edit_car_no = st.session_state.get('edit_car', "")
        st.subheader("🛠️ Update/Add Record")
        
        d_name, d_status, d_msg = "", "Car Received", ""
        if edit_car_no:
            rec = df[df["Car Number"] == edit_car_no]
            if not rec.empty: d_name, d_status, d_msg = rec.iloc[0]["Customer Name"], rec.iloc[0]["Status"], rec.iloc[0]["Message"]

        with st.form("main_form"):
            f_car = st.text_input("Car Number", value=edit_car_no).upper().strip()
            f_name = st.text_input("Customer Name", value=d_name)
            idx = STATUS_LIST.index(d_status) if d_status in STATUS_LIST else 0
            f_status = st.selectbox("Status", STATUS_LIST, index=idx)
            f_date = st.date_input("Delivery Date")
            f_msg = st.text_area("Message", value="" if d_msg == "nan" else d_msg)
            
            if st.form_submit_button("Save Changes"):
                if f_car:
                    df = load_data()
                    df = df[df["Car Number"] != f_car]
                    new_row = pd.DataFrame([[f_car, f_name, f_status, str(f_date), f_msg]], columns=df.columns)
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.session_state['edit_car'] = ""
                    st.success("Saved!"); st.rerun()

st.markdown("<div class='footer'>Mahendra Bodyshop Faizabad © 2026 | Powered by Owais Production</div>", unsafe_allow_html=True)