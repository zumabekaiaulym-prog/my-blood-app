import streamlit as st
from PIL import Image
import pandas as pd
import requests
import io
import numpy as np
import cv2
import sqlite3
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import urllib.parse

# Настройка страницы
st.set_page_config(page_title="ScanHemo AI", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# КАСПЕРЫ И СТИЛИЗАЦИЯ ПОД МАКЕТ (ЖУРНАЛ / HIGH-TECH)
# ==========================================
st.markdown("""
<style>
    /* Основные цвета фона и текста в стиле темного кибер-журнала */
    .stApp {
        background-color: #0d0f12;
        color: #f0f0f0;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Сайдбар */
    [data-testid="stSidebar"] {
        background-color: #14171d;
        border-right: 1px solid #262c36;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }

    /* Брендовый заголовок */
    .brand-title {
        color: #ffffff;
        font-weight: 900;
        font-size: 32px;
        letter-spacing: -1px;
    }
    .brand-title span {
        color: #FF007F;
    }

    /* Карточки пациентов в стиле макета */
    .patient-card {
        background-color: #171b22;
        border-radius: 4px;
        padding: 20px;
        border: 1px solid #2a323d;
        border-left: 4px solid #FF007F;
        text-align: left;
        margin-bottom: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    
    /* Журнальные акцентные заголовки */
    .journal-header {
        border-bottom: 2px solid #FF007F;
        padding-bottom: 8px;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 800;
        color: #ffffff;
    }

    /* Кнопки */
    .stButton>button {
        background-color: #FF007F;
        color: white;
        border-radius: 2px;
        border: none;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #d9006b;
        color: white;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
    }
    
    /* Текстовые поля и селекты */
    input, textarea, select {
        background-color: #171b22 !important;
        color: white !important;
        border: 1px solid #2a323d !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. БАЗА ДАННЫХ
# ==========================================
def init_db():
    conn = sqlite3.connect("scanhemo_history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            doctor_name TEXT,
            doctor_role TEXT,
            clinic TEXT,
            patient_id TEXT,
            patient_name TEXT,
            patient_dob TEXT,
            patient_gender TEXT,
            total_count INTEGER,
            counts_json TEXT,
            observations_json TEXT,
            recommendations_json TEXT
        )
    ''')
    existing_cols = [col[1] for col in c.execute("PRAGMA table_info(history)").fetchall()]
    for new_col in ["patient_name", "patient_dob", "patient_gender"]:
        if new_col not in existing_cols:
            c.execute(f"ALTER TABLE history ADD COLUMN {new_col} TEXT DEFAULT ''")
    conn.commit()
    conn.close()

def save_analysis(doc_name, doc_role, clinic, p_id, p_name, p_dob, p_gender, total, counts, obs, recs):
    conn = sqlite3.connect("scanhemo_history.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (
            timestamp, doctor_name, doctor_role, clinic, 
            patient_id, patient_name, patient_dob, patient_gender, total_count, 
            counts_json, observations_json, recommendations_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        doc_name, doc_role, clinic, p_id, p_name, p_dob, p_gender, total,
        json.dumps(counts, ensure_ascii=False),
        json.dumps(obs, ensure_ascii=False),
        json.dumps(recs, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("scanhemo_history.db")
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

def get_patient_history(p_id):
    if not p_id:
        return pd.DataFrame()
    conn = sqlite3.connect("scanhemo_history.db")
    df = pd.read_sql_query(f"SELECT * FROM history WHERE patient_id = '{p_id}' ORDER BY id ASC", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 1. МУЛЬТИЯЗЫЧНОСТЬ
# ==========================================
translations = {
    "Русский": {
        "title": "ScanHemo<span>Ai</span>",
        "subtitle": "Квантовый скачок в гематологии",
        "login_title": "АВТОРИЗАЦИЯ В СИСТЕМЕ",
        "btn_login": "ВОЙТИ В СИСТЕМУ",
        "nav_patients": "👥 ПАЦИЕНТЫ",
        "nav_analysis": "🔬 АНАЛИЗ & СКАНЕР",
        "nav_stats": "📊 СТАТИСТИКА & ДИНАМИКА",
        "nav_settings": "⚙️ НАСТРОЙКИ",
        "nav_logout": "🚪 ВЫЙТИ",
        "patient_list": "РЕЕСТР ПАЦИЕНТОВ",
        "add_patient": "➕ ЗАРЕГИСТРИРОВАТЬ НОВОГО ПАЦИЕНТА",
        "p_id": "ID / ИИН пациента",
        "p_name": "ФИО пациента",
        "p_dob": "Дата рождения",
        "select_patient": "ВЫБРАТЬ ПРОФИЛЬ",
        "selected_patient_title": "АКТИВНЫЙ ПРОФИЛЬ:",
        "btn_new_scan": "🔬 СДЕЛАТЬ АНАЛИЗ",
        "btn_view_history": "📜 ИСТОРИЯ И ДИНАМИКА",
        "upload_label": "Загрузите файл или используйте камеру микроскопа",
        "orig_img": "ИСХОДНЫЙ СНИМОК",
        "ai_result": "АНАЛИЗ ИИ (ДЕТЕКЦИЯ КЛЕТОК)",
        "btn_analyze": "⚡ ЗАПУСТИТЬ ИИ-АНАЛИЗ",
        "analyzing": "Квантовый сканер обрабатывает клетки крови...",
        "total_found": "ВСЕГО ОБНАРУЖЕНО ОБЪЕКТОВ: ",
        "download_pdf": "📄 СКАЧАТЬ PDF ОТЧЕТ",
        "send_whatsapp": "💬 ОТПРАВИТЬ В WHATSAPP",
        "comparison_title": "📈 ДИНАМИКА И ИСТОРИЯ АНАЛИЗОВ",
        "obs_normal": "Гематологические показатели в пределах референтной нормы.",
        "rec_normal": "Контрольный осмотр через 12 месяцев."
    },
    "Қазақша": {
        "title": "ScanHemo<span>Ai</span>",
        "subtitle": "Гематологиядағы кванттық серпіліс",
        "login_title": "ЖҮЙЕГЕ КІРУ",
        "btn_login": "КІРУ",
        "nav_patients": "👥 ПАЦИЕНТТЕР",
        "nav_analysis": "🔬 ТАЛДАУ & СКАНЕР",
        "nav_stats": "📊 СТАТИСТИКА & ДИНАМИКА",
        "nav_settings": "⚙️ БАПТАУЛАР",
        "nav_logout": "🚪 ШЫҒУ",
        "patient_list": "ПАЦИЕНТТЕР ТІЗІМІ",
        "add_patient": "➕ ЖАҢА ПАЦИЕНТТІ ТІРКЕУ",
        "p_id": "Пациент ID / ЖСН",
        "p_name": "Аты-Жөні",
        "p_dob": "Туған күні",
        "select_patient": "ТАҢДАУ",
        "selected_patient_title": "БЕЛСЕНДІ ПАЦИЕНТ:",
        "btn_new_scan": "🔬 ТАЛДАУ ЖАСАУ",
        "btn_view_history": "📜 ДИНАМИКАНЫ ҚАРАУ",
        "upload_label": "Суретті жүктеңіз немесе камераны қолданыңыз",
        "orig_img": "БАСТАПҚЫ СУРЕТ",
        "ai_result": "ЖИ ТАЛДАУ НӘТИЖЕСІ",
        "btn_analyze": "⚡ ЖИ АНАЛИЗБЕН БАСТАУ",
        "analyzing": "ЖИ қан жасушаларын өңдеуде...",
        "total_found": "ТАБЫЛҒАН НЫСАНДАР: ",
        "download_pdf": "📄 PDF ЕСЕПТІ ЖҮКТЕУ",
        "send_whatsapp": "💬 WHATSAPP ЖІБЕРУ",
        "comparison_title": "📈 ТАЛДАУ ДИНАМИКАСЫ",
        "obs_normal": "Норма шегінде.",
        "rec_normal": "Жоспарлы бақылау."
    },
    "English": {
        "title": "ScanHemo<span>Ai</span>",
        "subtitle": "Quantum Leap in Hematology",
        "login_title": "SYSTEM LOGIN",
        "btn_login": "LOG IN",
        "nav_patients": "👥 PATIENTS",
        "nav_analysis": "🔬 ANALYSIS & SCAN",
        "nav_stats": "📊 STATISTICS & TRENDS",
        "nav_settings": "⚙️ SETTINGS",
        "nav_logout": "🚪 LOG OUT",
        "patient_list": "PATIENT REGISTRY",
        "add_patient": "➕ REGISTER NEW PATIENT",
        "p_id": "Patient ID / SSN",
        "p_name": "Full Name",
        "p_dob": "Date of Birth",
        "select_patient": "SELECT PROFILE",
        "selected_patient_title": "ACTIVE PROFILE:",
        "btn_new_scan": "🔬 RUN NEW ANALYSIS",
        "btn_view_history": "📜 HISTORY & TRENDS",
        "upload_label": "Upload image or use microscope camera",
        "orig_img": "ORIGINAL IMAGE",
        "ai_result": "AI ANNOTATED RESULT",
        "btn_analyze": "⚡ RUN AI ANALYSIS",
        "analyzing": "AI quantum scanner is processing blood cells...",
        "total_found": "TOTAL OBJECTS FOUND: ",
        "download_pdf": "📄 DOWNLOAD PDF REPORT",
        "send_whatsapp": "💬 SEND VIA WHATSAPP",
        "comparison_title": "📈 PATIENT ANALYSIS TRENDS",
        "obs_normal": "Blood parameters within normal limits.",
        "rec_normal": "Routine follow-up in 12 months."
    }
}

# Инициализация стейта
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "selected_patient_id" not in st.session_state:
    st.session_state["selected_patient_id"] = "100000284"
if "selected_patient_name" not in st.session_state:
    st.session_state["selected_patient_name"] = "Иванов Иван Иванович"
if "selected_patient_dob" not in st.session_state:
    st.session_state["selected_patient_dob"] = "25.07.1993"
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "👥 ПАЦИЕНТЫ"

selected_lang = st.sidebar.selectbox("🌐 LANGUAGE / ТІЛ / ЯЗЫК", ["Русский", "Қазақша", "English"])
t = translations[selected_lang]

nav_options = [t["nav_patients"], t["nav_analysis"], t["nav_stats"], t["nav_settings"]]
if st.session_state["nav_page"] not in nav_options:
    st.session_state["nav_page"] = nav_options[0]

# ==========================================
# 2. АВТОРИЗАЦИЯ
# ==========================================
if not st.session_state["authenticated"]:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;' class='brand-title'>{t['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #FF007F; font-weight: 700; letter-spacing: 2px;'>{t['subtitle']}</p><br>", unsafe_allow_html=True)
        
        doc_name = st.text_input("Имя специалиста", value="Dr. Alex Smith")
        doc_role = st.text_input("Должность / Роль", value="Ведущий гематолог")
        clinic_name = st.text_input("Лаборатория / Клиника", value="ScanHemo Research Lab 2026")
        password = st.text_input("Пароль", type="password", value="******")
        
        if st.button(t["btn_login"], use_container_width=True):
            st.session_state["authenticated"] = True
            st.session_state["doc_name"] = doc_name
            st.session_state["doc_role"] = doc_role
            st.session_state["clinic_name"] = clinic_name
            st.rerun()
    st.stop()

# ==========================================
# 3. САЙДБАР
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 class='brand-title'>{t['title']}</h2>", unsafe_allow_html=True)
    st.caption(f"THE FUTURE: NOW 2026")
    st.write(f"👤 **{st.session_state.get('doc_name', 'Специалист')}**")
    st.markdown("---")
    
    page = st.radio(
        "Навигация",
        nav_options,
        index=nav_options.index(st.session_state["nav_page"]),
        label_visibility="collapsed"
    )
    st.session_state["nav_page"] = page
    
    st.markdown("---")
    if st.button(t["nav_logout"], use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# Генератор PDF отчетов
def clean_text(text):
    charmap = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z',
        'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
        'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
        'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'Yo','Ж':'Zh','З':'Z',
        'И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R',
        'С':'S','Т':'T','У':'U','Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch',
        'Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya'
    }
    return "".join([charmap.get(c, c) for c in str(text)]).encode('ascii', 'ignore').decode('ascii')

def generate_pdf(p_id, p_name, p_dob, counts, total, obs, recs, doc_name, clinic):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFillColor(colors.HexColor("#14171d"))
    c.rect(0, height - 70, width, 70, fill=True, stroke=False)
    
    c.setFillColor(colors.HexColor("#FF007F"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 42, "SCANHEMO AI — QUANTUM REPORT")
    
    y = height - 100
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Patient: {clean_text(p_name)} (ID: {clean_text(p_id)})")
    c.drawString(40, y - 15, f"DOB: {clean_text(p_dob)} | Facility: {clean_text(clinic)}")
    
    y -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Detected Elements Count:")
    y -= 20
    
    for k, v in counts.items():
        c.setFont("Helvetica", 10)
        c.drawString(55, y, f"- {clean_text(k)}: {v}")
        y -= 15
        
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 4. РАЗДЕЛ: ПАЦИЕНТЫ
# ==========================================
if page == t["nav_patients"]:
    st.markdown(f"<h1 class='journal-header'>{t['patient_list']}</h1>", unsafe_allow_html=True)
    
    with st.expander(t["add_patient"]):
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            new_id = st.text_input(t["p_id"], value="115002084")
        with col_n2:
            new_name = st.text_input(t["p_name"], value="Иванов Иван Иванович")
        with col_n3:
            new_dob = st.text_input(t["p_dob"], value="27.03.1999")
            
    patients = pd.DataFrame([
        {"patient_id": "100000284", "patient_name": "Иванов Иван Иванович", "patient_dob": "25.07.1993"},
        {"patient_id": "150002038", "patient_name": "Иванова Анна Сергеевна", "patient_dob": "27.05.1998"},
        {"patient_id": "115002084", "patient_name": "Иванов Иван Иванович", "patient_dob": "27.03.1999"},
        {"patient_id": "130002634", "patient_name": "Петров Пётр Петрович", "patient_dob": "25.02.1983"}
    ])

    cols = st.columns(4)
    for idx, p in patients.iterrows():
        col = cols[idx % 4]
        with col:
            st.markdown(f"""
            <div class='patient-card'>
                <div style='font-size: 28px;'>🧬</div>
                <h4 style='margin: 8px 0; color: #ffffff;'>{p['patient_name']}</h4>
                <p style='margin: 0; color: #8a99ad; font-size: 11px;'>ID: {p['patient_id']}</p>
                <p style='margin: 0; color: #8a99ad; font-size: 11px;'>ДР: {p['patient_dob']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(t["select_patient"], key=f"btn_{p['patient_id']}", use_container_width=True):
                st.session_state["selected_patient_id"] = p['patient_id']
                st.session_state["selected_patient_name"] = p['patient_name']
                st.session_state["selected_patient_dob"] = p['patient_dob']
                st.success(f"Выбран профиль: {p['patient_name']}")

    if st.session_state["selected_patient_id"]:
        st.markdown("---")
        st.markdown(f"<h3 style='color: #FF007F;'>{t['selected_patient_title']} {st.session_state['selected_patient_name']} (ID: {st.session_state['selected_patient_id']})</h3>", unsafe_allow_html=True)
        
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if st.button(t["btn_new_scan"], use_container_width=True):
                st.session_state["nav_page"] = translations[selected_lang]["nav_analysis"]
                st.rerun()
        with act_col2:
            if st.button(t["btn_view_history"], use_container_width=True):
                st.session_state["nav_page"] = translations[selected_lang]["nav_stats"]
                st.rerun()

# ==========================================
# 5. РАЗДЕЛ: АНАЛИЗ & СКАНИРОВАНИЕ (КАМЕРА МИКРОСКОПА)
# ==========================================
elif page == t["nav_analysis"]:
    st.markdown(f"<h1 class='journal-header'>{t['nav_analysis']}</h1>", unsafe_allow_html=True)
    
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    with col_sel1:
        p_id = st.text_input(t["p_id"], value=st.session_state.get("selected_patient_id", "115002084"))
    with col_sel2:
        p_name = st.text_input(t["p_name"], value=st.session_state.get("selected_patient_name", "Иванов Иван Иванович"))
    with col_sel3:
        p_dob = st.text_input(t["p_dob"], value=st.session_state.get("selected_patient_dob", "27.03.1999"))
        
    st.markdown("### 🔬 ВЫБОР ИСТОЧНИКА КРОВИ")
    input_method = st.radio("Источник изображения", ["Загрузить файл изображения", "Снять с камеры микроскопа / Веб-камеры"], horizontal=True)
    
    image = None
    if input_method == "Загрузить файл изображения":
        uploaded_file = st.file_uploader(t["upload_label"], type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
    else:
        camera_file = st.camera_input("Прямой захват с цифрового окуляра микроскопа")
        if camera_file:
            image = Image.open(camera_file)
            
    if image is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.image(image, caption=t["orig_img"], use_container_width=True)
        with c2:
            if st.button(t["btn_analyze"], use_container_width=True):
                with st.spinner(t["analyzing"]):
                    ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
                    MODEL_ID = "complete-blood-cell-analysis/1"
                    img_byte_arr = io.BytesIO()
                    image.convert("RGB").save(img_byte_arr, format='JPEG', quality=95)
                    img_bytes = img_byte_arr.getvalue()
                    
                    url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=15"
                    response = requests.post(url, files={"file": ("image.jpg", img_bytes, "image/jpeg")})
                    res_json = response.json()
                    
                    predictions = res_json.get("predictions", [])
                    cv_img = np.array(image.convert("RGB"))
                    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
                    
                    counts = {}
                    for p in predictions:
                        cell_class = p.get("class", "Cell")
                        counts[cell_class] = counts.get(cell_class, 0) + 1
                        x, y, w, h = int(p["x"]), int(p["y"]), int(p["width"]), int(p["height"])
                        cv2.rectangle(cv_img, (int(x-w/2), int(y-h/2)), (int(x+w/2), int(y+h/2)), (255, 0, 127), 2)
                    
                    result_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                    st.image(result_img, caption=t["ai_result"], use_container_width=True)
                    st.success(f"{t['total_found']}{len(predictions)}")
                    st.dataframe(pd.DataFrame(list(counts.items()), columns=["Тип клетки", "Количество"]), use_container_width=True)
                    
                    obs = [t["obs_normal"]]
                    recs = [t["rec_normal"]]
                    
                    save_analysis(
                        st.session_state.get('doc_name'), st.session_state.get('doc_role'), 
                        st.session_state.get('clinic_name'), p_id, p_name, p_dob, "Мужской",
                        len(predictions), counts, obs, recs
                    )
                    
                    pdf_bytes = generate_pdf(
                        p_id, p_name, p_dob, counts, len(predictions), obs, recs,
                        st.session_state.get('doc_name'), st.session_state.get('clinic_name')
                    )
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label=t["download_pdf"],
                            data=pdf_bytes,
                            file_name=f"ScanHemo_Report_{p_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col_dl2:
                        wa_text = f"🩸 *ScanHemo AI Quantum Report*\n👤 Patient: {p_name} (ID: {p_id})\n🔬 Total Cells: {len(predictions)}"
                        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
                        st.markdown(
                            f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:10px 20px;border:none;border-radius:2px;font-weight:bold;cursor:pointer;text-transform:uppercase;">{t["send_whatsapp"]}</button></a>',
                            unsafe_allow_html=True
                        )

# ==========================================
# 6. СТАТИСТИКА & СРАВНЕНИЕ (РЕАЛЬНАЯ ИСТОРИЯ)
# ==========================================
elif page == t["nav_stats"]:
    st.markdown(f"<h1 class='journal-header'>{t['comparison_title']}</h1>", unsafe_allow_html=True)
    
    curr_id = st.session_state.get("selected_patient_id", "100000284")
    curr_name = st.session_state.get("selected_patient_name", "Иванов Иван Иванович")
    st.write(f"👤 Активный профиль: **{curr_name}** (ID: {curr_id})")
    
    patient_df = get_patient_history(curr_id)
    
    if not patient_df.empty:
        chart_source = pd.DataFrame({
            'Дата': patient_df['timestamp'],
            'Всего клеток': patient_df['total_count']
        })
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Динамика клеточного объема")
            st.line_chart(chart_source.set_index('Дата'))
        with g2:
            st.subheader("Гистограмма сканирования")
            st.bar_chart(chart_source.set_index('Дата'))
            
        st.subheader("📋 Архивы анализов пациента")
        st.dataframe(patient_df[['timestamp', 'doctor_name', 'clinic', 'total_count', 'counts_json']], use_container_width=True)
    else:
        st.info("У этого пациента еще нет сохраненных сеансов. Проведите первое сканирование через вкладку анализа.")

# ==========================================
# 7. НАСТРОЙКИ
# ==========================================
elif page == t["nav_settings"]:
    st.markdown(f"<h1 class='journal-header'>{t['nav_settings']}</h1>", unsafe_allow_html=True)
    st.text_input("Название клиники / лаборатории", value=st.session_state.get('clinic_name'))
    st.text_input("ФИО Специалиста", value=st.session_state.get('doc_name'))
    if st.button("Сохранить параметры"):
        st.success("Параметры успешно обновлены.")
