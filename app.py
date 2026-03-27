import streamlit as st
import pandas as pd
import os
import time
import urllib.parse
from datetime import datetime

# --- LIBRARIES & AUTO-INSTALL ---
try:
    import pytz
    from filelock import FileLock
except ImportError:
    os.system('pip install pytz filelock')
    import pytz
    from filelock import FileLock

# --- CONFIG & THEME ---
# initial_sidebar_state="collapsed" taaki direct portal dikhe
st.set_page_config(page_title="Bodyshop", layout="wide", page_icon="🚗", initial_sidebar_state="collapsed")

# Accurate India Time Function
def get_india_time():
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'guard_logged_in' not in st.session_state:
    st.session_state['guard_logged_in'] = False

# --- FULL CSS RESTORED + STEPPER CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .customer-card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.1); border-left: 10px solid #1E88E5;
        margin-top: 20px;
    }
    
    /* --- 10-STEP SLIM STEPPER CSS --- */
    .stepper-wrapper {
        display: flex; justify-content: space-between; margin-top: 30px; margin-bottom: 30px; position: relative;
    }
    .stepper-item {
        position: relative; display: flex; flex-direction: column; align-items: center; flex: 1; z-index: 2;
    }
    .stepper-item::before {
        position: absolute; content: ""; border-bottom: 2px solid #e0e0e0; width: 100%; top: 11px; left: -50%; z-index: 1;
    }
    .stepper-item::after {
        position: absolute; content: ""; border-bottom: 2px solid #e0e0e0; width: 100%; top: 11px; left: 50%; z-index: 1;
    }
    .stepper-item .step-counter {
        position: relative; z-index: 5; display: flex; justify-content: center; align-items: center;
        width: 22px; height: 22px; border-radius: 50%; background: #fff; border: 2px solid #e0e0e0;
        margin-bottom: 6px; color: #ccc; font-weight: bold; font-size: 10px; transition: all 0.4s ease;
    }
    .stepper-item.completed .step-counter { 
        background-color: #28a745; border-color: #28a745; color: white;
        box-shadow: 0 0 8px rgba(40,167,69,0.3); 
    }
    .stepper-item.completed::after, .stepper-item.completed::before { border-bottom: 2px solid #28a745; }
    .stepper-item:first-child::before, .stepper-item:last-child::after { content: none; }
    .step-name { font-size: 8px; color: #888; text-align: center; font-weight: 600; text-transform: uppercase; line-height: 1.2; }
    .stepper-item.completed .step-name { color: #28a745; }

    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
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
    .update-ts-label { font-size: 12px; color: #d32f2f; font-weight: bold; }
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
    .footer-text {
        color: #777; font-size: 14px; margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "claim_database.csv"
GUARD_FILE = "guard_entry.csv"
DB_LOCK = "claim_database.csv.lock"
GUARD_LOCK = "guard_entry.csv.lock"

NOW_IN = get_india_time()
TODAY_STR = NOW_IN.strftime("%Y-%m-%d")

WEB_URL = "https://mahendra-bodyshop-pnzpwm5nbeok4x5usgtntb.streamlit.app/"

MAIN_SEQUENCE = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "Dismantle", "Denting", "Painting", "Fitting", "Delivery Order Waiting from Insurance Company", "Final Delivery"]
STATUS_LIST = ["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "WCA - Waiting for Customer Approval", "Claim Rejected", "PNA - Part Not Available", "WIP - Work Started", "Dismantle", "Denting", "Painting", "Fitting", "Delivery Order Waiting from Insurance Company", "Final Delivery"]
TIME_OPTIONS = [f"{h:02d}:00 {( 'AM' if h < 12 else 'PM')}" for h in range(24)]

APPROVAL_INDEX = STATUS_LIST.index("Insurance Survey")

STATUS_DETAILS = {
    "Car Received": "We have received your vehicle. The next step will be the registration of your motor insurance claim / आपकी गाड़ी हमें प्राप्त हो गई है। अगले चरण में आपकी गाड़ी का बीमा क्लेम दर्ज किया जाएगा।",
    "Claim Intimation": "Your insurance claim has been successfully registered. A surveyor will visit our workshop within 24 hours to inspect your vehicle. / आपका बीमा क्लेम सफलतापूर्वक दर्ज कर लिया गया है। अगले 24 घंटों के अंदर इंश्योरेंस सर्वेयर हमारी वर्कशॉप पर आपकी गाड़ी चेक करने आएंगे।",
    "Insurance Survey": "The vehicle inspection by the insurance surveyor has been completed. We are now awaiting the official work approval to start the repairs. / बीमा सर्वेयर द्वारा गाड़ी का निरीक्षण पूरा कर लिया गया है। अब हम मरम्मत कार्य शुरू करने के लिए आधिकारिक मंजूरी (Approval) का इंतज़ार कर रहे हैं।",
    "Insurance Approval": "Work approval has been received from the surveyor. / आपकी गाड़ी का वर्क अप्रूवल सर्वेयर से प्राप्त हो गया है।",
    "WCA - Waiting for Customer Approval": "To proceed with your vehicle's repair, your confirmation is required. We request you to kindly get in touch with our service advisor or visit the garage to authorize the process. / आपकी गाड़ी की मरम्मत शुरू करने के लिए आपकी पुष्टि (Confirmation) ज़रूरी है। आपसे अनुरोध है कि कृपया हमारे सर्विस एडवाइजर से बात करें या गैराज पर संपर्क करें ताकि हम काम आगे बढ़ा सकें।",
    "Claim Rejected": "Claim has been rejected by the insurance company. Please pick up your vehicle from the garage or go with the cash work to repair your vehicle. / बीमा कंपनी द्वारा क्लेम निरस्त कर दिया गया है। कृपया गैरेज से अपनी गाड़ी ले जाएं या अपनी गाड़ी की मरम्मत के लिए नकद कार्य (Cash Work) के साथ आगे बढ़ें।",
    "PNA - Part Not Available": "Certain parts required for your vehicle are currently on order. Work will resume immediately upon their arrival. We apologize for the delay. / आपकी गाड़ी के लिए कुछ ज़रूरी पार्ट्स ऑर्डर किए गए हैं। उनके आते ही मरम्मत का काम तुरंत दोबारा शुरू कर दिया जाएगा। देरी के लिए हमें खेद है।",
    "WIP - Work Started": "Repair work has started on your vehicle. / आपकी गाड़ी में मरम्मत का काम शुरू कर दिया गया हैं।",
    "Dismantle": "Your vehicle is currently undergoing dismantling for a detailed damage assessment and repair preparation. / आपकी गाड़ी की मरम्मत की तैयारी और नुकसान की बारीकी से जांच करने के लिए उसे डिस्मेंटल किया (खोला) जा रहा है।",
    "Denting": "Denting work is in progress. / आपकी गाड़ी का डेंटिंग कार्य चल रहा है।",
    "Painting": "Painting work is in progress. / आपकी गाड़ी का पेंटिंग कार्य चल रहा. है।",
    "Fitting": "The major repairs are complete. Your vehicle is now undergoing final assembly and quality testing to ensure your safety on the road. / मुख्य मरम्मत का काम पूरा हो चुका है। सड़क पर आपकी सुरक्षा सुनिश्चित करने के लिए अब गाड़ी की फाइनल फिटिंग और क्वालिटी टेस्टिंग की जा रही है।",
    "Delivery Order Waiting from Insurance Company": "The repair work is complete, and we are currently awaiting the official Delivery Order (DO) from the insurance surveyor. Please note that the vehicle cannot be released without this mandatory document. For any updates regarding the DO, we kindly request you to contact your insurance surveyor directly, as the repairer has no authority in this matter. We appreciate your cooperation. / आपकी गाड़ी की मरम्मत का कार्य पूरा हो चुका है, और अब हमें बीमा सर्वेयर से आधिकारिक डिलीवरी ऑर्डर (DO) मिलने का इंतज़ार है। कृपया ध्यान दें कि इस अनिवार्य दस्तावेज़ के बिना गाड़ी हैंडओवर नहीं की जा सकती। डिलीवरी ऑर्डर (DO) के संबंध में किसी भी जानकारी के लिए कृपया सीधे अपने बीमा सर्वेयर से संपर्क करें, क्योंकि इसमें रिपेयरर (वर्कशॉप) का कोई अधिकार नहीं होता है। आपके सहयोग के लिए धन्यवाद।",
    "Final Delivery": "Your vehicle is ready for delivery! / आपकी गाड़ी डिलीवरी के लिए तैयार हैं!"
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
    lock = FileLock(DB_LOCK)
    with lock:
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE).astype(str)
            for col in all_cols:
                if col not in df.columns: df[col] = ""
            return df
    return pd.DataFrame(columns=all_cols)

def load_guard_data():
    lock = FileLock(GUARD_LOCK)
    with lock:
        if os.path.exists(GUARD_FILE):
            return pd.read_csv(GUARD_FILE).astype(str)
    return pd.DataFrame(columns=["Car Number", "Kilometer", "Entry Date", "Entry Time"])

st.sidebar.markdown("### 🛠️ Bodyshop")
# index=0 ensures Customer Portal is default
menu = st.sidebar.radio("Navigation", ["Customer Portal / ग्राहक पोर्टल", "Guard Portal / गार्ड पोर्टल", "Staff Dashboard / स्टाफ"], index=0)

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
    if st.button("Check Status") and car_input:
        df = load_data()
        res = df[df["Car Number"].str.replace(" ", "").str.upper() == car_input]
        if not res.empty:
            for _, row in res.iterrows():
                # --- 10-STEP PROGRESS BAR LOGIC ---
                steps = ["Received", "Intimation", "Survey", "Approval", "Repairing", "Denting", "Painting", "Fitting", "DO Wait", "Ready"]
                mapping = {
                    "Car Received": 1, "Claim Intimation": 2, "Insurance Survey": 3,
                    "Insurance Approval": 4, "WCA - Waiting for Customer Approval": 4,
                    "WIP - Work Started": 5, "Dismantle": 5, "Denting": 6, 
                    "Painting": 7, "Fitting": 8, "PNA - Part Not Available": 8,
                    "Delivery Order Waiting from Insurance Company": 9, "Final Delivery": 10
                }
                current_step_idx = mapping.get(row['Status'], 1)
                
                stepper_html = '<div class="stepper-wrapper">'
                for idx, step_name in enumerate(steps, 1):
                    is_completed = "completed" if idx <= current_step_idx else ""
                    icon = "✓" if idx <= current_step_idx else ""
                    stepper_html += f'<div class="stepper-item {is_completed}"><div class="step-counter">{icon}</div><div class="step-name">{step_name}</div></div>'
                stepper_html += '</div>'

                nxt = get_next_status(row['Status'])
                current_status_idx = STATUS_LIST.index(row['Status']) if row['Status'] in STATUS_LIST else 0
                
                if row['Status'] == "Claim Rejected": is_approved = False
                else: is_approved = current_status_idx > APPROVAL_INDEX
                
                if is_approved:
                    d_date_display = row['Delivery Date']
                    d_time_display = row['Delivery Time'] if row['Delivery Time'] not in ["nan", ""] else "Not Scheduled"
                else:
                    d_date_display = "Pending Approval"
                    d_time_display = "TBD"

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
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    if row['Status'] == "Claim Rejected": delivery_info_html = ""
                    elif not is_approved:
                        delivery_info_html = f"<p style='margin-top:10px; font-size:14px; color:#d32f2f; background:#fff3e0; padding:10px; border-radius:8px; border-left:4px solid #f57c00;'><b>Note:</b> The estimated delivery date can only be confirmed once approval is received from the insurance company.</p>"
                    else:
                        delivery_info_html = f"<p>Expected Delivery: <b>{d_date_display}</b><br>Scheduled Time: <b>{d_time_display}</b></p>"

                    st.markdown(f"""
                        <div class='customer-card'>
                            <h2 style='margin:0;'>🚗 {row['Car Number']}</h2>
                            <p>Owner: <b>{row['Customer Name']}</b> | Advisor: <b>{row['Service Advisor']}</b></p>
                            <p class='status-time'>🕒 Last Update: {row['Remark Update TS']}</p>
                            {stepper_html}
                            <hr style='opacity:0.3;'>
                            <h3 style='color:#1E88E5;'>Current Status: {row['Status']}</h3>
                            <div class='next-step-box'><b>Next Step:</b> {row['Status']} ➔ <span style='color:#1565C0;'>{nxt}</span></div>
                            <p style='margin-top:15px; font-size:16px; color:#333; background:#e3f2fd; padding:15px; border-radius:10px;'>{STATUS_DETAILS.get(row['Status'], 'Updating...')}</p>
                            {delivery_info_html}
                        </div>
                    """, unsafe_allow_html=True)
                
                msg = str(row['Message'])
                if msg != "" and msg != "nan" and msg.strip() != "":
                    st.markdown(f"<div class='note-box'><b>Workshop Remarks:</b><br>\"{msg}\"</div>", unsafe_allow_html=True)
        else: st.error("❌ No record found.")

# --- GUARD & STAFF PORTAL (RESTORED EXACTLY AS YOUR BASE CODE) ---
elif menu == "Guard Portal / गार्ड पोर्टल":
    if not st.session_state['guard_logged_in']:
        st.markdown("<div class='main-header'><h1>GUARD LOGIN</h1></div>", unsafe_allow_html=True)
        g_pw = st.text_input("Guard Password", type="password")
        if st.button("🔓 Open Gate Portal"):
            if g_pw == "krishna":
                st.session_state['guard_logged_in'] = True
                st.rerun()
            else: st.error("Incorrect Password!")
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
                    now_ts = get_india_time()
                    new_e = pd.DataFrame([{"Car Number": g_car, "Kilometer": g_km, "Entry Date": now_ts.strftime("%Y-%m-%d"), "Entry Time": now_ts.strftime("%I:%M %p")}])
                    lock = FileLock(GUARD_LOCK)
                    with lock: pd.concat([gdf, new_e]).to_csv(GUARD_FILE, index=False)
                    st.success(f"Entry Saved for {g_car}!"); time.sleep(1); st.rerun()
        
        gdf = load_guard_data()
        if not gdf.empty:
            gdf_rev = gdf.iloc[::-1]
            for i, row in gdf_rev.iterrows():
                with st.expander(f"🚗 {row['Car Number']} | {row['Kilometer']} KM | {row['Entry Date']}"):
                    if st.button(f"🗑️ Delete {row['Car Number']}", key=f"del_{i}"):
                        lock = FileLock(GUARD_LOCK)
                        with lock: gdf.drop(i).to_csv(GUARD_FILE, index=False)
                        st.warning("Deleted!"); time.sleep(1); st.rerun()

else:
    if not st.session_state['logged_in']:
        pw = st.text_input("Password", type="password")
        if st.button("🔓 Login"):
            if pw == "admin123": st.session_state['logged_in'] = True; st.rerun()
    else:
        if st.sidebar.button("🔒 Logout"): st.session_state['logged_in'] = False; st.rerun()
        
        col_title, col_share = st.columns([3, 1])
        with col_title: st.markdown("## 📋 Staff Dashboard")
        with col_share:
            wa_msg = f"Dear sir! Aap apni gaadi ka status yahan check kar sakte hain: {WEB_URL}"
            wa_link = f"https://wa.me/?text={urllib.parse.quote(wa_msg)}"
            st.markdown(f"<a href='{wa_link}' target='_blank' style='background-color: #25D366; color: white; padding: 10px 15px; border-radius: 10px; text-decoration: none; font-weight: bold; display: inline-block; float: right; margin-top: 20px;'>📲 Share Portal Link</a>", unsafe_allow_html=True)
        
        df = load_data()
        t1, t2, t3 = st.tabs([" View Records", " Add New Car", "🛡️ Guard Records"])
        
        with t1:
            search_input = st.text_input("Search Car").upper().strip()
            f_df = df if not search_input else df[(df["Car Number"].str.upper().str.contains(search_input, na=False)) | (df["Car Number"].str.strip().str[-4:].str.contains(search_input, na=False))]
            
            def render_staff_expander(i, r, lock_sensitive=False):
                tick = " ✅" if str(r['Last Update']) == TODAY_STR else ""
                with st.expander(f"🚗 {r['Car Number']} - {r['Status']}{tick}"):
                    with st.form(f"f_{i}"):
                        c_stat, c_date, c_time = st.columns([2, 1, 1])
                        ns = c_stat.selectbox("Status", STATUS_LIST, index=STATUS_LIST.index(r['Status']) if r['Status'] in STATUS_LIST else 0)
                        is_approved_staff = STATUS_LIST.index(ns) > APPROVAL_INDEX
                        try: default_date = datetime.strptime(r['Delivery Date'], '%Y-%m-%d').date()
                        except: default_date = get_india_time().date()
                        nd = c_date.date_input("Delivery Date", value=default_date, key=f"date_{i}", disabled=(not is_approved_staff))
                        curr_time = r['Delivery Time'] if r['Delivery Time'] in TIME_OPTIONS else TIME_OPTIONS[10]
                        nt = c_time.selectbox("Delivery Time", TIME_OPTIONS, index=TIME_OPTIONS.index(curr_time), key=f"time_{i}", disabled=(not is_approved_staff))
                        nm = st.text_area("Remark", value=r['Message'] if r['Message'] != 'nan' else "")
                        if st.form_submit_button("Update ✅"):
                            now_ts = get_india_time()
                            new_ts_str = f"{now_ts.strftime('%Y-%m-%d')} at {now_ts.strftime('%I:%M %p')}"
                            df.at[i,'Status'], df.at[i,'Delivery Date'], df.at[i,'Delivery Time'], df.at[i,'Message'], df.at[i,'Remark Update TS'], df.at[i,'Last Update'] = ns, (str(nd) if is_approved_staff else ""), (nt if is_approved_staff else ""), nm, new_ts_str, now_ts.strftime('%Y-%m-%d')
                            with FileLock(DB_LOCK): df.to_csv(DB_FILE, index=False)
                            st.rerun()
                        if not lock_sensitive and st.form_submit_button("Delete 🗑️"):
                            with FileLock(DB_LOCK): df.drop(i).to_csv(DB_FILE, index=False)
                            st.rerun()

            front_df = f_df[f_df['Status'].isin(["Car Received", "Claim Intimation", "Insurance Survey", "Insurance Approval", "WCA - Waiting for Customer Approval", "Claim Rejected"])]
            st.markdown("<div class='section-header'>🏢 FRONT OFFICE</div>", unsafe_allow_html=True)
            if not front_df.empty:
                for advisor in front_df['Service Advisor'].unique():
                    st.markdown(f"<div class='advisor-header'>👤 Advisor: {advisor}</div>", unsafe_allow_html=True)
                    adv_data = front_df[front_df['Service Advisor'] == advisor]
                    for i, r in adv_data.iterrows(): render_staff_expander(i, r)

            workshop_df = f_df[f_df['Status'].isin(["WIP - Work Started", "Dismantle", "Denting", "Painting", "Fitting", "PNA - Part Not Available"])]
            st.markdown("<div class='section-header'>🔧 WORKSHOP FLOOR</div>", unsafe_allow_html=True)
            for i, r in workshop_df.iterrows(): render_staff_expander(i, r, lock_sensitive=True)
            
            ready_df = f_df[f_df['Status'].isin(["Delivery Order Waiting from Insurance Company", "Final Delivery"])]
            st.markdown("<div class='section-header'>🏁 Ready</div>", unsafe_allow_html=True)
            for i, r in ready_df.iterrows(): render_staff_expander(i, r)

        with t2:
            with st.form("new_car"):
                nc = st.text_input("Car Number").upper().strip()
                nn = st.text_input("Customer Name"); sa = st.text_input("Advisor")
                if st.form_submit_button("🚀 Save Car"):
                    if nc and nn:
                        now_ts = get_india_time()
                        new_data = {col: "" for col in df.columns}
                        new_data.update({"Car Number": nc, "Customer Name": nn, "Service Advisor": sa, "Status": "Car Received", "Last Update": now_ts.strftime('%Y-%m-%d'), "Remark Update TS": f"{now_ts.strftime('%Y-%m-%d')} at {now_ts.strftime('%I:%M %p')}"})
                        with FileLock(DB_LOCK): pd.concat([df, pd.DataFrame([new_data])]).to_csv(DB_FILE, index=False)
                        st.success(f"{nc} Saved!"); time.sleep(1); st.rerun()

st.markdown("<br><center class='footer-text'><b>Engineered by Owais</b><br>Bodyshop Portal © 2026</center>", unsafe_allow_html=True)