import streamlit as st
import pandas as pd
import os
from datetime import datetime, time

# --- CONFIG & THEME ---
st.set_page_config(page_title="Mahendra Bodyshop Management", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
    .customer-card {
        background-color: #ffffff; padding: 25px; border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1); border-top: 5px solid #28A745;
        margin-top: 20px;
    }
    .status-badge {
        padding: 8px 15px; border-radius: 20px; color: white;
        font-weight: bold; font-size: 15px; display: inline-block;
        margin-bottom: 10px;
    }
    .time-badge {
        background-color: #f1f8e9; color: #1b5e20; padding: 15px;
        border-radius: 10px; border: 2px solid #2e7d32;
        font-weight: bold; font-size: 22px; text-align: center; margin-top: 15px;
    }
    .section-header {
        background-color: #1E88E5; color: white; padding: 10px;
        border-radius: 5px; margin-top: 20px; margin-bottom: 10px;
        font-weight: bold; font-size: 18px; text-align: center;
    }
    .stButton>button {
        height: 3em;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

STATUS_LIST = [
    "Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", 
    "WIP - Work Started", "Dismental", "Denting", "Painting", "Fitting", 
    "Delivery Order Waiting from Insurance Company", "Final Delivery"
]

STATUS_MAP_HINDI = {
    "Car Received": "गाड़ी प्राप्त हुई (Car Received)",
    "Claim Intimation": "क्लेम की सूचना दी गई (Claim Intimation)",
    "Insurance Survey": "बीमा सर्वे जारी है (Insurance Survey)",
    "Insurance Approval": "बीमा कंपनी से मंजूरी मिली (Insurance Approval)",
    "WIP - Work Started": "काम शुरू हो चुका है (Work Started)",
    "Dismental": "गाड़ी खोली जा रही है (Dismental)",
    "Denting": "डेंटिंग का काम जारी है (Denting)",
    "Painting": "पेंटिंग का काम जारी है (Painting)",
    "Fitting": "फिटिंग का काम चल रहा है (Fitting)",
    "Delivery Order Waiting from Insurance Company": "बीमा कंपनी से D.O. का इंतज़ार (D.O. Waiting)",
    "Final Delivery": "गाड़ी डिलीवरी के लिए तैयार है (Ready for Delivery)"
}

FRONT_OFFICE = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval"]
WORKSHOP_FLOOR = ["WIP - Work Started", "Dismental", "Denting", "Painting", "Fitting"]
READY_SECTION = ["Delivery Order Waiting from Insurance Company", "Final Delivery"]

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE).astype(str)
        if "Delivery Time" not in df.columns: df["Delivery Time"] = ""
        return df
    return pd.DataFrame(columns=["Car Number", "Customer Name", "Status", "Delivery Date", "Message", "Last Update", "Delivery Time"])

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

st.sidebar.title("Mahendra Bodyshop")
menu = st.sidebar.radio("Navigation", ["Customer Portal", "Staff Dashboard"])

# --- CUSTOMER PORTAL ---
if menu == "Customer Portal":
    st.markdown("<h2 style='text-align: center; color: #1E88E5;'>MAHENDRA BODYSHOP FAIZABAD</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        car_input = st.text_input("गाड़ी नंबर डालें (UP42...)").upper().strip()
        check_now = st.button("📊 स्टेटस देखें (Check Status)", use_container_width=True)
    
    if check_now and car_input:
        df = load_data()
        res = df[df["Car Number"] == car_input]
        if not res.empty:
            row = res.iloc[0]
            curr = row['Status']
            st.markdown(f"""
            <div class='customer-card'>
                <h3 style='margin-bottom:0;'>🚗 {row['Car Number']}</h3>
                <p style='color:gray;'>Customer: {row['Customer Name']}</p>
                <hr>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <p style='margin:0; font-size:14px;'>Status / स्थिति:</p>
                        <span class='status-badge' style='background-color: {"#28A745" if curr == "Final Delivery" else "#FFA500" if curr in WORKSHOP_FLOOR else "#1E88E5"}'>
                            {STATUS_MAP_HINDI.get(curr, curr)}
                        </span>
                    </div>
                    <div style='text-align:right;'>
                        <p style='margin:0; font-size:14px;'>Expected Date:</p>
                        <b style='font-size:18px; color:#1E88E5;'>{row['Delivery Date']}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if curr == "Final Delivery" and row['Delivery Time'] not in ["", "nan"]:
                st.markdown(f"<div class='time-badge'>🕒 डिलीवरी समय: {row['Delivery Time']}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            idx = STATUS_LIST.index(curr) if curr in STATUS_LIST else 0
            st.progress((idx + 1) / len(STATUS_LIST))
        else:
            st.error("No record found.")

# --- STAFF DASHBOARD ---
else:
    if not st.session_state['logged_in']:
        pw = st.text_input("Staff Password", type="password")
        if st.button("Login", use_container_width=True):
            if pw == "admin123": st.session_state['logged_in'] = True; st.rerun()
    else:
        df = load_data()
        t1, t2 = st.tabs(["📋 View Records", "➕ Add Car"])

        with t1:
            search_q = st.text_input("🔍 Search Car No/Name").upper().strip()
            search_btn = st.button("Search / खोजें", use_container_width=True)
            f_df = df[df.apply(lambda r: search_q in r.astype(str).str.upper().values, axis=1)] if (search_btn and search_q) else df
            
            def render_list(data, title, clr):
                if not data.empty:
                    st.markdown(f"<div class='section-header' style='background-color:{clr}'>{title}</div>", unsafe_allow_html=True)
                    for i, r in data.iterrows():
                        with st.expander(f"⚙️ {r['Car Number']} | {r['Customer Name']}"):
                            with st.form(f"f_edit_{i}"):
                                ns = st.selectbox("Status", STATUS_LIST, index=STATUS_LIST.index(r['Status']) if r['Status'] in STATUS_LIST else 0)
                                nd = st.text_input("Date", value=r['Delivery Date'])
                                f_time = r['Delivery Time']
                                if ns == "Final Delivery":
                                    t_pick = st.time_input("Select Time", value=time(10, 0), key=f"t_p_{i}")
                                    f_time = t_pick.strftime("%I:%M %p")
                                nm = st.text_area("Notes", value=r['Message'] if r['Message'] != 'nan' else "")
                                b_up, b_del = st.columns(2)
                                if b_up.form_submit_button("Update ✅", use_container_width=True):
                                    df.at[i, 'Status'] = ns
                                    df.at[i, 'Delivery Date'] = nd
                                    df.at[i, 'Delivery Time'] = f_time
                                    df.at[i, 'Message'] = nm
                                    df.at[i, 'Last Update'] = TODAY
                                    df.to_csv(DB_FILE, index=False); st.rerun()
                                if b_del.form_submit_button("Delete 🗑️", use_container_width=True):
                                    df.drop(i).to_csv(DB_FILE, index=False); st.rerun()
            
            render_list(f_df[f_df['Status'].isin(FRONT_OFFICE)], "🏢 FRONT OFFICE", "#1E88E5")
            render_list(f_df[f_df['Status'].isin(WORKSHOP_FLOOR)], "🔧 WORKSHOP FLOOR", "#FFA500")
            render_list(f_df[f_df['Status'].isin(READY_SECTION)], "🏁 READY SECTION", "#28A745")

        with t2:
            with st.form("new_entry", clear_on_submit=True):
                nc = st.text_input("Car Number").upper().strip()
                nn = st.text_input("Customer Name")
                ns = st.selectbox("Initial Status", STATUS_LIST)
                nd = st.date_input("Target Date")
                
                if st.form_submit_button("🚀 Register Vehicle", use_container_width=True):
                    if not nc or not nn:
                        st.warning("Please fill details.")
                    elif nc in df["Car Number"].values:
                        st.error(f"Error: {nc} already exists!")
                    else:
                        new_r = pd.DataFrame([[nc, nn, ns, str(nd), "", TODAY, ""]], columns=df.columns)
                        pd.concat([df, new_r], ignore_index=True).to_csv(DB_FILE, index=False)
                        st.success(f"Vehicle {nc} Registered Successfully! ✅") # Pure professional message

st.markdown("<center>Mahendra Bodyshop © 2026</center>", unsafe_allow_html=True)