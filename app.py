import streamlit as st
import pandas as pd
import os

# --- CONFIG & THEME ---
st.set_page_config(page_title="Mahendra Bodyshop Management", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff; padding: 20px; border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #1E88E5;
        text-align: center; margin-bottom: 20px;
    }
    .main-title { font-size: 30px; font-weight: bold; color: #1E88E5; text-align: center; }
    .stExpander { border: 1px solid #1E88E5; border-radius: 10px; margin-bottom: 10px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #1E88E5; text-align: center; padding: 5px; font-size: 12px; border-top: 1px solid #ddd; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).astype(str)
    return pd.DataFrame(columns=["Car Number", "Customer Name", "Status", "Delivery Date", "Message"])

STATUS_LIST = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "Dismental", "Denting", "Painting", "Fitting", "Delivery Order Waiting from Insurance Company", "Final Delivery"]

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- SIDEBAR ---
st.sidebar.title("Mahendra Bodyshop")
menu = st.sidebar.radio("Navigation", ["Customer Portal", "Employee Dashboard"])

if st.session_state['logged_in'] and menu == "Employee Dashboard":
    if st.sidebar.button("🔒 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

st.markdown(f"<div class='main-title'>MAHENDRA BODYSHOP FAIZABAD</div>", unsafe_allow_html=True)
st.markdown("---")

# --- CUSTOMER PORTAL ---
if menu == "Customer Portal":
    st.subheader("🔍 Track Your Repair")
    car_input = st.text_input("Enter Car Number:").upper().strip()
    if st.button("Check Status"):
        df = load_data()
        res = df[df["Car Number"] == car_input]
        if not res.empty:
            row = res.iloc[0]
            st.success(f"**Current Status:** {row['Status']}")
            st.info(f"**Expected Delivery:** {row['Delivery Date']}")
            if row['Status'] in STATUS_LIST:
                st.progress((STATUS_LIST.index(row['Status']) + 1) / len(STATUS_LIST))
        else: st.error("No record found.")

# --- EMPLOYEE DASHBOARD ---
else:
    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("👨‍💻 Staff Login")
            pw = st.text_input("Password", type="password")
            if st.button("Login"):
                if pw == "admin123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Incorrect Password")
    else:
        df = load_data()
        
        # --- TOP METRICS ---
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'><h3>Total Cars</h3><h1>{len(df)}</h1></div>", unsafe_allow_html=True)
        with c2: 
            work_in_progress = len(df[df["Status"] != "Final Delivery"])
            st.markdown(f"<div class='metric-card'><h3>In Progress</h3><h1>{work_in_progress}</h1></div>", unsafe_allow_html=True)
        with c3:
            ready_cars = len(df[df["Status"] == "Final Delivery"])
            st.markdown(f"<div class='metric-card'><h3>Ready</h3><h1>{ready_cars}</h1></div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📋 Manage Records (Quick Edit)", "➕ Add New Entry"])

        with tab1:
            search = st.text_input("🔎 Search (Last 4 Digits / Name)").upper()
            filtered_df = df[df.apply(lambda row: search in row.astype(str).str.upper().values, axis=1)] if search else df
            
            for i, row in filtered_df.iterrows():
                icon = "✅" if row['Status'] == "Final Delivery" else "🛠️"
                display_title = f"{icon} {row['Car Number']} | {row['Customer Name']} | 📍 {row['Status']}"
                
                with st.expander(display_title):
                    # IN-LINE EDITING FORM
                    with st.form(key=f"quick_form_{i}"):
                        st.write("### Quick Status Update")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            new_status = st.selectbox("Change Status", STATUS_LIST, 
                                                     index=STATUS_LIST.index(row['Status']) if row['Status'] in STATUS_LIST else 0)
                        with col_b:
                            new_date = st.date_input("Update Delivery Date", value=pd.to_datetime(row['Delivery Date']).date() if row['Delivery Date'] != 'nan' else None)
                        
                        new_msg = st.text_area("Update Note", value="" if row['Message'] == "nan" else row['Message'])
                        
                        btn_col1, btn_col2 = st.columns([1, 4])
                        if btn_col1.form_submit_button("Update ✅"):
                            df.at[i, 'Status'] = new_status
                            df.at[i, 'Delivery Date'] = str(new_date)
                            df.at[i, 'Message'] = new_msg
                            df.to_csv(DB_FILE, index=False)
                            st.success("Updated!")
                            st.rerun()
                        
                        if btn_col2.form_submit_button("Delete 🗑️"):
                            df = df.drop(i)
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()

        with tab2:
            st.write("### Register New Vehicle")
            with st.form("new_entry_form"):
                f_car = st.text_input("Car Number").upper().strip()
                f_name = st.text_input("Customer Name")
                f_status = st.selectbox("Current Status", STATUS_LIST)
                f_date = st.date_input("Target Delivery")
                f_msg = st.text_area("Initial Notes")
                
                if st.form_submit_button("Save New Claim"):
                    if f_car:
                        df = load_data()
                        new_row = pd.DataFrame([[f_car, f_name, f_status, str(f_date), f_msg]], columns=df.columns)
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(DB_FILE, index=False)
                        st.success("New Entry Saved!")
                        st.rerun()
                    else: st.error("Car Number Required!")

st.markdown("<div class='footer'>Mahendra Bodyshop Faizabad © 2026 | Developed by Owais Production</div>", unsafe_allow_html=True)