import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
    .recent-update { border: 2px solid #FF4B4B !important; border-radius: 10px; margin-bottom: 10px; background-color: #FFF5F5; }
    .normal-update { border: 1px solid #1E88E5; border-radius: 10px; margin-bottom: 10px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; color: #1E88E5; text-align: center; padding: 5px; font-size: 12px; border-top: 1px solid #ddd; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"
# Aj ki date automatically pick hogi
TODAY = datetime.now().strftime("%Y-%m-%d")

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE).astype(str)
        if "Last Update" not in df.columns:
            df["Last Update"] = TODAY
        # Recent updates ko hamesha top par rakhega
        df = df.sort_values(by="Last Update", ascending=False)
        return df
    return pd.DataFrame(columns=["Car Number", "Customer Name", "Status", "Delivery Date", "Message", "Last Update"])

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
            st.warning(f"🕒 **Data Updated On:** {row['Last Update']}")
            if row['Status'] in STATUS_LIST:
                st.progress((STATUS_LIST.index(row['Status']) + 1) / len(STATUS_LIST))
        else: st.error("No record found for this car number.")

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
        
        # --- DASHBOARD METRICS ---
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'><h3>Total Cars</h3><h1>{len(df)}</h1></div>", unsafe_allow_html=True)
        with c2: 
            updated_today = len(df[df["Last Update"] == TODAY])
            st.markdown(f"<div class='metric-card'><h3>Updated Today</h3><h1>{updated_today}</h1></div>", unsafe_allow_html=True)
        with c3:
            ready_cars = len(df[df["Status"] == "Final Delivery"])
            st.markdown(f"<div class='metric-card'><h3>Ready to Go</h3><h1>{ready_cars}</h1></div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📋 Records (Newest First)", "➕ Register New Car"])

        with tab1:
            search = st.text_input("🔎 Search (Last 4 digits/Name)").upper()
            filtered_df = df[df.apply(lambda row: search in row.astype(str).str.upper().values, axis=1)] if search else df
            
            for i, row in filtered_df.iterrows():
                is_recent = row['Last Update'] == TODAY
                box_class = "recent-update" if is_recent else "normal-update"
                icon = "🔴" if is_recent else "⚪"
                
                st.markdown(f"<div class='{box_class}'>", unsafe_allow_html=True)
                # Display title with Status and Last Update Date
                display_title = f"{icon} {row['Car Number']} | {row['Customer Name']} | {row['Status']} (Last: {row['Last Update']})"
                
                with st.expander(display_title):
                    with st.form(key=f"quick_edit_{i}"):
                        st.write("### Quick Management")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            new_status = st.selectbox("Status", STATUS_LIST, index=STATUS_LIST.index(row['Status']) if row['Status'] in STATUS_LIST else 0)
                        with col_b:
                            # Handling date conversion safely
                            try:
                                default_date = pd.to_datetime(row['Delivery Date']).date()
                            except:
                                default_date = datetime.now().date()
                            new_date = st.date_input("Target Delivery", value=default_date)
                        
                        new_msg = st.text_area("Update Note", value="" if row['Message'] == "nan" else row['Message'])
                        
                        # ACTION BUTTONS
                        btn_col1, btn_col2 = st.columns([1, 1])
                        
                        if btn_col1.form_submit_button("Save Update ✅"):
                            df.at[i, 'Status'] = new_status
                            df.at[i, 'Delivery Date'] = str(new_date)
                            df.at[i, 'Message'] = new_msg
                            df.at[i, 'Last Update'] = TODAY
                            df.to_csv(DB_FILE, index=False)
                            st.success("Data Updated!")
                            st.rerun()

                        if btn_col2.form_submit_button("Delete Car 🗑️"):
                            # Delete by checking Car Number in original dataframe
                            df = df.drop(i)
                            df.to_csv(DB_FILE, index=False)
                            st.warning("Car Record Deleted!")
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.write("### New Vehicle Entry")
            with st.form("new_car_form"):
                f_car = st.text_input("Car Number (Full)").upper().strip()
                f_name = st.text_input("Customer Name")
                f_status = st.selectbox("Initial Status", STATUS_LIST)
                f_date = st.date_input("Target Delivery Date")
                f_msg = st.text_area("Workshop Comments")
                
                if st.form_submit_button("Add to Database"):
                    if f_car:
                        df = load_data()
                        new_row = pd.DataFrame([[f_car, f_name, f_status, str(f_date), f_msg, TODAY]], columns=df.columns)
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(DB_FILE, index=False)
                        st.success("Vehicle Added Successfully!")
                        st.rerun()
                    else: st.error("Car Number cannot be empty.")

st.markdown("<div class='footer'>Mahendra Bodyshop Faizabad © 2026 | Powered by Owais Production</div>", unsafe_allow_html=True)