import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, time as dt_time

# --- CONFIG & THEME ---
st.set_page_config(page_title="Bodyshop", layout="wide", page_icon="🚗")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .customer-card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.1); border-left: 10px solid #1E88E5;
        margin-top: 20px;
    }
    .status-time {
        font-size: 13px; color: #1565C0; font-weight: bold; margin-bottom: 5px;
    }
    .delivery-ready-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f8e9 100%);
        padding: 30px; border-radius: 25px; border: 3px solid #28a745; 
        text-align: center; box-shadow: 0px 10px 30px rgba(40, 167, 69, 0.2);
    }
    .main-header {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;
    }
    .section-header {
        background-color: #ffffff; color: #333; padding: 12px;
        border-radius: 10px; margin: 25px 0 10px 0;
        font-weight: bold; font-size: 18px; border-left: 5px solid #1E88E5;
    }
    .note-box {
        background-color: #fff9c4; color: #5d4037; padding: 15px;
        border-radius: 10px; border-left: 5px solid #fbc02d; margin-top: 15px;
    }
    .update-ts-label {
        font-size: 12px; color: #d32f2f; font-weight: bold;
    }
    .next-step-box {
        background-color: #f1f8e9; border: 1px dashed #28a745;
        padding: 8px 15px; border-radius: 8px; margin-top: 10px; font-size: 14px;
    }
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; }
    
    div.stFormSubmitButton > button {
        background-color: #28a745 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"
NOW = datetime.now()
TODAY_STR = NOW.strftime("%Y-%m-%d")
TIME_STR = NOW.strftime("%I:%M %p")

MAIN_SEQUENCE = [
    "Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", 
    "Dismantle", "Denting", "Painting", "Fitting", 
    "Delivery Order Waiting from Insurance Company", "Final Delivery"
]

STATUS_LIST = [
    "Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", 
    "WCA - Waiting for Customer Approval", "Claim Rejected", "PNA - Part Not Available",
    "WIP - Work Started", "Dismantle", "Denting", "Painting", "Fitting", 
    "Delivery Order Waiting from Insurance Company", "Final Delivery"
]

STATUS_DETAILS = {
    "Car Received": "We have received your vehicle. / आपकी गाड़ी हमें प्राप्त हो गई है।",
    "Claim Intimation": "Your claim has been registered. / आपका क्लेम पंजीकृत कर दिया गया है।",
    "Insurance Survey": "Vehicle survey has been completed. / आपकी गाड़ी का सर्वे पूरा हो गया है।",
    "Insurance Approval": "Work approval has been received from the surveyor. / आपकी गाड़ी का वर्क अप्रूवल सर्वेयर से प्राप्त हो गया है।",
    "WCA - Waiting for Customer Approval": "Waiting for customer approval to start work. / हम कार्य शुरू करने के लिए आपकी अनुमति का इंतज़ार कर रहे हैं।",
    "Claim Rejected": "Claim has been rejected by the insurance company. / बीमा कंपनी द्वारा क्लेम निरस्त कर दिया गया है।",
    "PNA - Part Not Available": "Some parts have been ordered. Work will resume once they arrive. / आपकी गाड़ी का कुछ पार्ट ऑर्डर किया गया है, उनके आते ही काम दोबारा शुरू हो जाएगा।",
    "WIP - Work Started": "Repair work has started on your vehicle. / आपकी गाड़ी में मरम्मत का काम शुरू हो चुका है।",
    "Dismantle": "Your vehicle is being dismantled. / आपकी गाड़ी खोली जा रही है।",
    "Denting": "Denting work is in progress. / आपकी गाड़ी का डेंटिंग कार्य चल रहा है।",
    "Painting": "Painting work is in progress. / आपकी गाड़ी का पेंटिंग कार्य चल रहा है।",
    "Fitting": "Final fitting is being performed. / आपकी गाड़ी में फाइनल फिटिंग की जा रही है।",
    "Delivery Order Waiting from Insurance Company": "Waiting for delivery order. Vehicle cannot be released without it. / डिलीवरी ऑर्डर का इंतज़ार किया जा रहा है। इसके बिना गाड़ी रिलीज नहीं हो पाएगी।",
    "Final Delivery": "Your vehicle is ready for delivery! / आपकी गाड़ी डिलीवरी के लिए तैयार है!"
}

def get_next_status(current):
    if current == "Claim Rejected": return "N/A (Claim Terminated)"
    if current == "Final Delivery": return "Completed / पूर्ण"
    if current == "WCA - Waiting for Customer Approval": return "Resuming Work (Post Approval)"
    if current == "PNA - Part Not Available": return "Resuming Work (Post Parts Arrival)"
    if current == "WIP - Work Started": return "Dismantle"
    
    if current in MAIN_SEQUENCE:
        idx = MAIN_SEQUENCE.index(current)
        if idx < len(MAIN_SEQUENCE) - 1:
            return MAIN_SEQUENCE[idx+1]
    return "Next process update soon"

def load_data():
    base_cols = ["Car Number", "Customer Name", "Service Advisor", "Status", "Delivery Date", "Message", "Last Update", "Delivery Time", "Remark Update TS"]
    tracking_cols = [f"Date_{s.split(' - ')[0]}" for s in STATUS_LIST]
    all_cols = base_cols + tracking_cols
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE).astype(str)
        for col in all_cols:
            if col not in df.columns: df[col] = ""
        return df
    return pd.DataFrame(columns=all_cols)

st.sidebar.markdown("### 🛠️ Bodyshop")
menu = st.sidebar.radio("Navigation", ["Customer Portal / ग्राहक पोर्टल", "Staff Dashboard / स्टाफ"])

if menu == "Customer Portal / ग्राहक पोर्टल":
    st.markdown("<div class='main-header'><h1>BODYSHOP</h1><p>Check Status / गाड़ी का स्टेटस देखें</p></div>", unsafe_allow_html=True)
    car_input = st.text_input("Enter Full Vehicle Number").upper().replace(" ", "").strip()
    
    if st.button("📊 Check Status") and car_input:
        df = load_data()
        res = df[df["Car Number"].str.replace(" ", "").str.upper() == car_input]
        if not res.empty:
            for _, row in res.iterrows():
                nxt = get_next_status(row['Status'])
                if row['Status'] == "Final Delivery":
                    st.markdown(f"""
                    <div class='delivery-ready-card'>
                        <div style='font-size:26px; font-weight:bold; color:#1b5e20;'>🎉 Congratulations! / बधाई हो!</div>
                        <h2 style='margin:10px 0;'>🚗 {row['Car Number']}</h2>
                        <p style='font-size:18px;'>{STATUS_DETAILS.get(row['Status'], '')}</p>
                        <p>Service Advisor: <b>{row['Service Advisor']}</b></p>
                        <p class='status-time'>Final Update: {row['Remark Update TS']}</p>
                        <hr style='border: 0.5px solid #ccc;'>
                        <p style='font-size:20px; color:#28a745; font-weight:bold;'>✨ Delivery Date: {row['Delivery Date']}</p>
                        <div class='time-large'>🕒 Time: {row['Delivery Time']}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='customer-card'>
                        <h2 style='margin:0;'>🚗 {row['Car Number']}</h2>
                        <p>Owner: <b>{row['Customer Name']}</b> | Advisor: <b>{row['Service Advisor']}</b></p>
                        <p class='status-time'>🕒 Last Update: {row['Remark Update TS']}</p>
                        <hr style='opacity:0.3;'>
                        <h3 style='color:#1E88E5;'>Current Status: {row['Status']}</h3>
                        <div class='next-step-box'><b>Next Step:</b> {row['Status']} ➔ <span style='color:#1565C0;'>{nxt}</span></div>
                        <p style='margin-top:15px; font-size:16px; color:#333; background:#e3f2fd; padding:15px; border-radius:10px;'>
                            {STATUS_DETAILS.get(row['Status'], "Information update in progress...")}
                        </p>
                        <p>Expected Delivery / डिलीवरी तिथि: <b>{row['Delivery Date']}</b></p>
                    </div>""", unsafe_allow_html=True)
                
                msg = str(row['Message'])
                if msg != "" and msg != "nan" and msg.strip() != "":
                    st.markdown(f"<div class='note-box'><b>Workshop Remarks:</b><br>\"{msg}\"</div>", unsafe_allow_html=True)
        else: st.error("❌ No record found / कोई रिकॉर्ड नहीं मिला।")

else:
    if not st.session_state['logged_in']:
        pw = st.text_input("Password", type="password")
        if st.button("🔓 Login"):
            if pw == "admin123": st.session_state['logged_in'] = True; st.rerun()
    else:
        if st.sidebar.button("🔒 Logout"): st.session_state['logged_in'] = False; st.rerun()
        df = load_data()
        t1, t2 = st.tabs(["📋 View Records", "➕ Add New Car"])

        with t1:
            st.download_button("📥 Download Excel Report", df.to_csv(index=False).encode('utf-8-sig'), f"Report_{TODAY_STR}.csv")
            search = st.text_input("Search Car").upper().strip()
            f_df = df[df["Car Number"].str.upper().str.contains(search, na=False)] if search else df

            def render_list(data, title, clr):
                if not data.empty:
                    st.markdown(f"<div class='section-header' style='border-left-color:{clr}'>{title} ({len(data)})</div>", unsafe_allow_html=True)
                    for i, r in data.iterrows():
                        last_upd = r['Remark Update TS']
                        with st.expander(f"🚗 {r['Car Number']} - {r['Customer Name']} (Upd: {last_upd})"):
                            st.markdown(f"<div class='update-ts-label'>🕒 Last Activity Record: {last_upd}</div>", unsafe_allow_html=True)
                            with st.form(f"f_{i}"):
                                ns = st.selectbox("Update Status", STATUS_LIST, index=STATUS_LIST.index(r['Status']) if r['Status'] in STATUS_LIST else 0)
                                d_label = "Final Delivery Date" if ns == "Final Delivery" else "Expected Delivery Date"
                                try:
                                    default_date = datetime.strptime(r['Delivery Date'], '%Y-%m-%d').date()
                                except:
                                    default_date = NOW.date()
                                nd = st.date_input(d_label, value=default_date, key=f"date_{i}")
                                cur_time = r['Delivery Time']
                                if ns == "Final Delivery":
                                    t_p = st.time_input("Set Time", value=dt_time(10, 0), step=900, key=f"t_{i}")
                                    cur_time = t_p.strftime("%I:%M %p")
                                nm = st.text_area("Remark", value=r['Message'] if r['Message'] != 'nan' else "")
                                
                                if st.form_submit_button("Update ✅"):
                                    new_ts = f"{TODAY_STR} at {TIME_STR}"
                                    df.at[i,'Status'], df.at[i,'Delivery Date'], df.at[i,'Message'], df.at[i,'Delivery Time'], df.at[i,'Remark Update TS'], df.at[i,'Last Update'] = ns, str(nd), nm, cur_time, new_ts, TODAY_STR
                                    status_col = f"Date_{ns.split(' - ')[0]}"
                                    df.at[i, status_col] = TODAY_STR
                                    df.to_csv(DB_FILE, index=False); st.rerun()
                                if st.form_submit_button("Delete 🗑️"):
                                    df.drop(i).to_csv(DB_FILE, index=False); st.rerun()

            # Updated Group Names
            FRONT_GRP = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "WCA - Waiting for Customer Approval", "Claim Rejected"]
            render_list(f_df[f_df['Status'].isin(FRONT_GRP)], "🏢 FRONT OFFICE", "#1E88E5")
            render_list(f_df[f_df['Status'].isin(["WIP - Work Started", "Dismantle", "Denting", "Painting", "Fitting", "PNA - Part Not Available"])], "🔧 WORKSHOP FLOOR", "#FFA500")
            render_list(f_df[f_df['Status'].isin(["Delivery Order Waiting from Insurance Company", "Final Delivery"])], "🏁 Ready", "#28A745")

        with t2:
            st.markdown("### ➕ Register New Vehicle")
            with st.form("new_car_form", clear_on_submit=True):
                nc_raw = st.text_input("Car Number").strip()
                nn = st.text_input("Customer Name")
                sa = st.text_input("Service Advisor Name")
                ns = st.selectbox("Initial Status", STATUS_LIST)
                nd = st.date_input("Expected Delivery Date")
                if st.form_submit_button("🚀 Save Car"):
                    if nc_raw and nn:
                        nc = nc_raw.upper()
                        new_data = {col: "" for col in df.columns}
                        new_data.update({
                            "Car Number": nc, "Customer Name": nn, "Service Advisor": sa, 
                            "Status": ns, "Delivery Date": str(nd), "Last Update": TODAY_STR, 
                            "Remark Update TS": f"{TODAY_STR} at {TIME_STR}",
                            f"Date_{ns.split(' - ')[0]}": TODAY_STR
                        })
                        new_r = pd.DataFrame([new_data])
                        pd.concat([df, new_r]).to_csv(DB_FILE, index=False)
                        st.success(f"✅ {nc} Saved successfully!")
                        time.sleep(1.5); st.rerun()

st.markdown("<br><center>Bodyshop © 2026</center>", unsafe_allow_html=True)