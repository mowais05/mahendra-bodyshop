import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, time as dt_time

# --- CONFIG & THEME ---
st.set_page_config(page_title="Bodyshop", layout="wide", page_icon="🚗")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'guard_logged_in' not in st.session_state:
    st.session_state['guard_logged_in'] = False

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
    .disclaimer-box {
        background-color: #fdf2f2; border: 1px solid #f8d7da; color: #721c24;
        padding: 15px; border-radius: 10px; font-size: 13px; margin-bottom: 20px;
        text-align: center; line-height: 1.6;
    }
    .section-header {
        background-color: #ffffff; color: #333; padding: 12px;
        border-radius: 10px; margin: 25px 0 10px 0;
        font-weight: bold; font-size: 18px; border-left: 5px solid #1E88E5;
    }
    .advisor-header {
        background-color: #e3f2fd; color: #0d47a1; padding: 8px;
        border-radius: 5px; margin: 10px 0; font-weight: bold; font-size: 16px;
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
    .time-large {
        font-size: 20px; color: #1565C0; font-weight: bold; margin-top: 10px;
    }
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; }
    
    div.stFormSubmitButton > button {
        background-color: #28a745 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"
GUARD_FILE = "guard_entry.csv"
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

# Time options for delivery
TIME_OPTIONS = [f"{h:02d}:00 {( 'AM' if h < 12 else 'PM')}" for h in range(24)]

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
        if idx < len(MAIN_SEQUENCE) - 1: return MAIN_SEQUENCE[idx+1]
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

def load_guard_data():
    if os.path.exists(GUARD_FILE):
        return pd.read_csv(GUARD_FILE).astype(str)
    return pd.DataFrame(columns=["Car Number", "Kilometer", "Entry Date", "Entry Time"])

st.sidebar.markdown("### 🛠️ Bodyshop")
menu = st.sidebar.radio("Navigation", ["Customer Portal / ग्राहक पोर्टल", "Guard Portal / गार्ड पोर्टल", "Staff Dashboard / स्टाफ"])

# --- CUSTOMER PORTAL ---
if menu == "Customer Portal / ग्राहक पोर्टल":
    st.markdown("<div class='main-header'><h1>BODYSHOP</h1><p>Check Status / गाड़ी का स्टेटस देखें</p></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='disclaimer-box'>
            <b>DISCLAIMER / अस्वीकरण:</b><br>
            This website is managed by a third party to provide information regarding your vehicle's claim status. 
            This portal has no direct affiliation with Mahindra Company or Amit Motors.<br>
            <i>यह वेबसाइट आपकी गाड़ी के क्लेम स्टेटस की जानकारी देने के लिए एक थर्ड पार्टी द्वारा मैनेज की जा रही है। 
            इस पोर्टल का महिंद्रा कंपनी या अमित मोटर्स से कोई सीधा संबंध नहीं है।</i>
        </div>
    """, unsafe_allow_html=True)

    car_input = st.text_input("Enter Full Vehicle Number").upper().replace(" ", "").strip()
    if st.button("📊 Check Status") and car_input:
        df = load_data()
        res = df[df["Car Number"].str.replace(" ", "").str.upper() == car_input]
        if not res.empty:
            for _, row in res.iterrows():
                nxt = get_next_status(row['Status'])
                # Delivery details display
                d_time = row['Delivery Time'] if row['Delivery Time'] != "nan" and row['Delivery Time'] != "" else "Not Scheduled"
                
                if row['Status'] == "Final Delivery":
                    st.markdown(f"<div class='delivery-ready-card'><div style='font-size:26px; font-weight:bold; color:#1b5e20;'>🎉 Congratulations! / बधाई हो!</div><h2 style='margin:10px 0;'>🚗 {row['Car Number']}</h2><p style='font-size:18px;'>{STATUS_DETAILS.get(row['Status'], '')}</p><p>Service Advisor: <b>{row['Service Advisor']}</b></p><p class='status-time'>Final Update: {row['Remark Update TS']}</p><hr style='border: 0.5px solid #ccc;'><p style='font-size:20px; color:#28a745; font-weight:bold;'>✨ Delivery Date: {row['Delivery Date']}</p><div class='time-large'>🕒 Time: {d_time}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='customer-card'><h2 style='margin:0;'>🚗 {row['Car Number']}</h2><p>Owner: <b>{row['Customer Name']}</b> | Advisor: <b>{row['Service Advisor']}</b></p><p class='status-time'>🕒 Last Update: {row['Remark Update TS']}</p><hr style='opacity:0.3;'><h3 style='color:#1E88E5;'>Current Status: {row['Status']}</h3><div class='next-step-box'><b>Next Step:</b> {row['Status']} ➔ <span style='color:#1565C0;'>{nxt}</span></div><p style='margin-top:15px; font-size:16px; color:#333; background:#e3f2fd; padding:15px; border-radius:10px;'>{STATUS_DETAILS.get(row['Status'], 'Information update in progress...')}</p><p>Expected Delivery / डिलीवरी तिथि: <b>{row['Delivery Date']}</b><br>Scheduled Time / समय: <b>{d_time}</b></p></div>", unsafe_allow_html=True)
                msg = str(row['Message'])
                if msg != "" and msg != "nan" and msg.strip() != "":
                    st.markdown(f"<div class='note-box'><b>Workshop Remarks:</b><br>\"{msg}\"</div>", unsafe_allow_html=True)
        else: st.error("❌ No record found / कोई रिकॉर्ड नहीं मिला।")

# --- GUARD PORTAL ---
elif menu == "Guard Portal / गार्ड पोर्टल":
    if not st.session_state['guard_logged_in']:
        st.markdown("<div class='main-header'><h1>GUARD LOGIN</h1></div>", unsafe_allow_html=True)
        g_pw = st.text_input("Guard Password", type="password")
        if st.button("🔓 Open Gate Portal"):
            if g_pw == "krishna":
                st.session_state['guard_logged_in'] = True
                st.rerun()
            else:
                st.error("Incorrect Password!")
    else:
        if st.sidebar.button("🔒 Guard Logout"):
            st.session_state['guard_logged_in'] = False
            st.rerun()

        st.markdown("<div class='main-header'><h1>GUARD ENTRY</h1></div>", unsafe_allow_html=True)
        with st.form("guard_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            g_car = c1.text_input("Vehicle Number").upper().strip()
            g_km = c2.text_input("Kilometer Reading")
            if st.form_submit_button("🚀 Save Gate Entry"):
                if g_car and g_km:
                    gdf = load_guard_data()
                    new_e = pd.DataFrame([{"Car Number": g_car, "Kilometer": g_km, "Entry Date": TODAY_STR, "Entry Time": TIME_STR}])
                    pd.concat([gdf, new_e]).to_csv(GUARD_FILE, index=False)
                    st.success(f"Entry Saved for {g_car}!"); time.sleep(1); st.rerun()

        st.markdown("### 📋 Recent Entries & Management")
        gdf = load_guard_data()
        if not gdf.empty:
            gdf_rev = gdf.iloc[::-1]
            for i, row in gdf_rev.iterrows():
                with st.expander(f"🚗 {row['Car Number']} | {row['Kilometer']} KM | {row['Entry Date']} | {row['Entry Time']}"):
                    if st.button(f"🗑️ Delete Entry {row['Car Number']}", key=f"del_{i}"):
                        gdf.drop(i).to_csv(GUARD_FILE, index=False)
                        st.warning("Entry Deleted!"); time.sleep(1); st.rerun()
        else:
            st.info("No entries yet today.")

# --- STAFF DASHBOARD ---
else:
    if not st.session_state['logged_in']:
        pw = st.text_input("Password", type="password")
        if st.button("🔓 Login"):
            if pw == "admin123": st.session_state['logged_in'] = True; st.rerun()
    else:
        if st.sidebar.button("🔒 Logout"): st.session_state['logged_in'] = False; st.rerun()
        df = load_data()
        t1, t2, t3 = st.tabs(["📋 View Records", "➕ Add New Car", "🛡️ Guard Records"])

        with t1:
            st.download_button("📥 Download Report", df.to_csv(index=False).encode('utf-8-sig'), f"Report_{TODAY_STR}.csv")
            search = st.text_input("Search Car").upper().strip()
            f_df = df[df["Car Number"].str.upper().str.contains(search, na=False)] if search else df

            def render_staff_expander(i, r):
                tick = " ✅" if str(r['Last Update']) == TODAY_STR else ""
                last_update_date = f" ({r['Last Update']})" if r['Last Update'] != "nan" and r['Last Update'] != "" else ""
                with st.expander(f"🚗 {r['Car Number']} - {r['Status']}{tick}{last_update_date}"):
                    st.markdown(f"**Customer:** {r['Customer Name']} | **Advisor:** {r['Service Advisor']}")
                    st.markdown(f"<div class='update-ts-label'>🕒 Last Activity: {r['Remark Update TS']}</div>", unsafe_allow_html=True)
                    with st.form(f"f_{i}"):
                        c_stat, c_date, c_time = st.columns([2, 1, 1])
                        ns = c_stat.selectbox("Status", STATUS_LIST, index=STATUS_LIST.index(r['Status']) if r['Status'] in STATUS_LIST else 0)
                        
                        try: default_date = datetime.strptime(r['Delivery Date'], '%Y-%m-%d').date()
                        except: default_date = NOW.date()
                        nd = c_date.date_input("Delivery Date", value=default_date, key=f"date_{i}")
                        
                        # Added Delivery Time selection
                        curr_time = r['Delivery Time'] if r['Delivery Time'] in TIME_OPTIONS else TIME_OPTIONS[10] # Default 10 AM
                        nt = c_time.selectbox("Delivery Time", TIME_OPTIONS, index=TIME_OPTIONS.index(curr_time), key=f"time_{i}")
                        
                        nm = st.text_area("Remark", value=r['Message'] if r['Message'] != 'nan' else "")
                        
                        if st.form_submit_button("Update ✅"):
                            new_ts = f"{TODAY_STR} at {TIME_STR}"
                            df.at[i,'Status'], df.at[i,'Delivery Date'], df.at[i,'Delivery Time'], df.at[i,'Message'], df.at[i,'Remark Update TS'], df.at[i,'Last Update'] = ns, str(nd), nt, nm, new_ts, TODAY_STR
                            df.to_csv(DB_FILE, index=False); st.rerun()
                        if st.form_submit_button("Delete 🗑️"):
                            df.drop(i).to_csv(DB_FILE, index=False); st.rerun()

            front_df = f_df[f_df['Status'].isin(["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "WCA - Waiting for Customer Approval", "Claim Rejected"])]
            st.markdown(f"<div class='section-header' style='border-left-color:#1E88E5'>🏢 FRONT OFFICE ({len(front_df)})</div>", unsafe_allow_html=True)
            if not front_df.empty:
                advisors = front_df['Service Advisor'].unique()
                for advisor in advisors:
                    st.markdown(f"<div class='advisor-header'>👤 Advisor: {advisor}</div>", unsafe_allow_html=True)
                    adv_data = front_df[front_df['Service Advisor'] == advisor]
                    for i, r in adv_data.iterrows(): render_staff_expander(i, r)

            workshop_df = f_df[f_df['Status'].isin(["WIP - Work Started", "Dismantle", "Denting", "Painting", "Fitting", "PNA - Part Not Available"])]
            st.markdown(f"<div class='section-header' style='border-left-color:#FFA500'>🔧 WORKSHOP FLOOR ({len(workshop_df)})</div>", unsafe_allow_html=True)
            for i, r in workshop_df.iterrows(): render_staff_expander(i, r)

            ready_df = f_df[f_df['Status'].isin(["Delivery Order Waiting from Insurance Company", "Final Delivery"])]
            st.markdown(f"<div class='section-header' style='border-left-color:#28A745'>🏁 Ready ({len(ready_df)})</div>", unsafe_allow_html=True)
            for i, r in ready_df.iterrows(): render_staff_expander(i, r)

        with t2:
            with st.form("new_car"):
                nc = st.text_input("Car Number").upper().strip()
                nn = st.text_input("Customer Name"); sa = st.text_input("Advisor")
                c1, c2 = st.columns(2)
                nd = c1.date_input("Expected Date")
                nt = c2.selectbox("Expected Time", TIME_OPTIONS, index=10) # Default 10 AM
                if st.form_submit_button("🚀 Save Car"):
                    if nc and nn:
                        new_data = {col: "" for col in df.columns}
                        new_data.update({"Car Number": nc, "Customer Name": nn, "Service Advisor": sa, "Status": "Car Received", "Delivery Date": str(nd), "Delivery Time": nt, "Last Update": TODAY_STR, "Remark Update TS": f"{TODAY_STR} at {TIME_STR}"})
                        pd.concat([df, pd.DataFrame([new_data])]).to_csv(DB_FILE, index=False)
                        st.success(f"{nc} Saved!"); time.sleep(1); st.rerun()

        with t3:
            st.markdown("### 🛡️ Guard Gate Entries (Staff View)")
            gdf_staff = load_guard_data()
            if not gdf_staff.empty:
                st.dataframe(gdf_staff.iloc[::-1], use_container_width=True, hide_index=True)

st.markdown("<br><center>Bodyshop © 2026</center>", unsafe_allow_html=True)