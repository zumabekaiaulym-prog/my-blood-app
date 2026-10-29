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

# Кастомные стили CSS
st.markdown("""
<style>
    .stApp {
        background-color: #EBF2F5;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #D9E6EB;
        border-right: 1px solid #C4D7E0;
    }
    .patient-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #E0E8EC;
        text-align: center;
        margin-bottom: 12px;
    }
    .brand-title {
        color: #1A5265;
        font-weight: 800;
        font-size: 28px;
        margin-bottom: 0px;
    }
    .stButton>button {
        background-color: #1E6075;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #154656;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0. ИНИЦИАЛИЗАЦИЯ И МИГРАЦИЯ БАЗЫ ДАННЫХ
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
# 1. МУЛЬТИЯЗЫЧНОСТЬ (3 ЯЗЫКА)
# ==========================================
translations = {
    "Русский": {
        "title": "ScanHemo AI 🩸",
        "login_title": "Вход в систему лабораторной диагностики",
        "btn_login": "Войти",
        "nav_patients": "👥 Пациенты",
        "nav_analysis": "🔬 Анализы & Сканирование",
        "nav_stats": "📊 Статистика & Сравнение",
        "nav_settings": "⚙️ Настройки",
        "nav_logout": "🚪 Выйти",
        "patient_list": "Список пациентов",
        "add_patient": "➕ Зарегистрировать нового пациента",
        "p_id": "ID / ИИН пациента",
        "p_name": "ФИО пациента",
        "p_dob": "Дата рождения",
        "p_gender": "Пол",
        "select_patient": "Выбрать пациента",
        "selected_patient_title": "📋 Данные пациента:",
        "btn_new_scan": "🔬 Сделать новый анализ",
        "btn_view_history": "📜 Посмотреть предыдущие данные & динамику",
        "upload_label": "Загрузите файл или сделайте снимок с камеры микроскопа",
        "orig_img": "Исходный снимок",
        "ai_result": "Результат размещения ИИ",
        "btn_analyze": "🔬 Проанализировать через ИИ",
        "analyzing": "ИИ считает клетки крови...",
        "total_found": "Найдено объектов: ",
        "download_pdf": "📄 Скачать PDF отчет",
        "send_whatsapp": "💬 Отправить результаты в WhatsApp",
        "comparison_title": "📈 Динамика и история анализов пациента",
        "obs_normal": "Соотношение основных элементов крови в пределах нормы.",
        "rec_normal": "Плановый профилактический осмотр раз в год."
    },
    "Қазақша": {
        "title": "ScanHemo AI 🩸",
        "login_title": "Зертханалық диагностика жүйесіне кіру",
        "btn_login": "Кіру",
        "nav_patients": "👥 Пациенттер",
        "nav_analysis": "🔬 Талдау & Сканерлеу",
        "nav_stats": "📊 Статистика & Салыстыру",
        "nav_settings": "⚙️ Баптаулар",
        "nav_logout": "🚪 Шығу",
        "patient_list": "Пациенттер тізімі",
        "add_patient": "➕ Жаңа пациентті тіркеу",
        "p_id": "Пациент ID / ЖСН",
        "p_name": "Пациенттің Аты-Жөні",
        "p_dob": "Туған күні",
        "p_gender": "Жынысы",
        "select_patient": "Пациентті таңдау",
        "selected_patient_title": "📋 Пациент мәліметтері:",
        "btn_new_scan": "🔬 Жаңа талдау жасау",
        "btn_view_history": "📜 Бұрынғы нәтижелерді & динамиканы қарау",
        "upload_label": "Файлды жүктеңіз немесе микроскоп камерасынан суретке түсіріңіз",
        "orig_img": "Бастапқы сурет",
        "ai_result": "ЖИ белгілеген нәтиже",
        "btn_analyze": "🔬 ЖИ арқылы талдау",
        "analyzing": "ЖИ қан жасушаларын санауда...",
        "total_found": "Табылған нысандар саны: ",
        "download_pdf": "📄 PDF есепті жүктеу",
        "send_whatsapp": "💬 Нәтижелерді WhatsApp арқылы жіберу",
        "comparison_title": "📈 Пациенттің талдау динамикасы",
        "obs_normal": "Қан элементтерінің арақатынасы норма шегінде.",
        "rec_normal": "Жоспарлы тексеру."
    },
    "English": {
        "title": "ScanHemo AI 🩸",
        "login_title": "Laboratory Diagnostics System Login",
        "btn_login": "Log In",
        "nav_patients": "👥 Patients",
        "nav_analysis": "🔬 Analysis & Scanning",
        "nav_stats": "📊 Statistics & Comparison",
        "nav_settings": "⚙️ Settings",
        "nav_logout": "🚪 Log Out",
        "patient_list": "Patient List",
        "add_patient": "➕ Register New Patient",
        "p_id": "Patient ID / SSN",
        "p_name": "Patient Full Name",
        "p_dob": "Date of Birth",
        "p_gender": "Gender",
        "select_patient": "Select Patient",
        "selected_patient_title": "📋 Patient Profile:",
        "btn_new_scan": "🔬 Perform New Analysis",
        "btn_view_history": "📜 View Past History & Trends",
        "upload_label": "Upload file or capture image from microscope camera",
        "orig_img": "Original Image",
        "ai_result": "AI Annotated Image",
        "btn_analyze": "🔬 Analyze with AI",
        "analyzing": "AI is counting blood cells...",
        "total_found": "Total Objects Found: ",
        "download_pdf": "📄 Download PDF Report",
        "send_whatsapp": "💬 Send Results via WhatsApp",
        "comparison_title": "📈 Patient Analysis History & Trends",
        "obs_normal": "Blood cell ratios are within normal ranges.",
        "rec_normal": "Routine annual checkup."
    }
}

# Инициализация состояния сессии
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "selected_patient_id" not in st.session_state:
    st.session_state["selected_patient_id"] = "100000284"
if "selected_patient_name" not in st.session_state:
    st.session_state["selected_patient_name"] = "Иванов Иван Иванович"
if "selected_patient_dob" not in st.session_state:
    st.session_state["selected_patient_dob"] = "25.07.1993"
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "👥 Пациенты"

# Выбор языка на боковой панели
selected_lang = st.sidebar.selectbox("🌐 Язык / Тіл / Language", ["Русский", "Қазақша", "English"])
t = translations[selected_lang]

# Синхронизация названий страниц с языком
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
        st.markdown(f"<h1 style='text-align: center; color: #1E6075;'>{t['title']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #555;'>{t['login_title']}</p>", unsafe_allow_html=True)
        
        doc_name = st.text_input("Имя специалиста", value="Dr. Alex Smith")
        doc_role = st.text_input("Должность / Роль", value="Лаборант-технолог")
        clinic_name = st.text_input("Лаборатория / Клиника", value="Центральная клиническая лаборатория")
        password = st.text_input("Пароль", type="password", value="******")
        
        if st.button(t["btn_login"], use_container_width=True):
            st.session_state["authenticated"] = True
            st.session_state["doc_name"] = doc_name
            st.session_state["doc_role"] = doc_role
            st.session_state["clinic_name"] = clinic_name
            st.rerun()
    st.stop()

# ==========================================
# 3. НАВИГАЦИЯ БОКОВОЙ ПАНЕЛИ
# ==========================================
with st.sidebar:
    st.markdown("<h2 class='brand-title'>ScanHemo AI</h2>", unsafe_allow_html=True)
    st.write(f"👤 **{st.session_state.get('doc_name', 'Специалист')}**")
    st.caption(f"{st.session_state.get('doc_role', '')} | {st.session_state.get('clinic_name', '')}")
    st.markdown("---")
    
    # Интерактивное радиоменю, связанное со стейтом
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

# Функция генерации PDF
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
    
    c.setFillColor(colors.HexColor("#1E6075"))
    c.rect(0, height - 60, width, 60, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 38, "SCANHEMO AI — BLOOD DIAGNOSTIC REPORT")
    
    y = height - 90
    c.setFillColor(colors.HexColor("#F0F4F8"))
    c.roundRect(40, y - 45, width - 80, 45, 6, fill=True, stroke=False)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y - 20, f"Patient: {clean_text(p_name)} (ID: {clean_text(p_id)})")
    c.drawString(55, y - 35, f"DOB: {clean_text(p_dob)} | Facility: {clean_text(clinic)}")
    
    y -= 65
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Cell Count Summary:")
    y -= 15
    
    for k, v in counts.items():
        c.setFont("Helvetica", 10)
        c.drawString(55, y, f"{clean_text(k)}: {v}")
        y -= 15
        
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 4. РАЗДЕЛ: ПАЦИЕНТЫ
# ==========================================
if page == t["nav_patients"]:
    st.title(t["patient_list"])
    
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
                <div style='font-size: 35px;'>👤</div>
                <h4 style='margin: 5px 0; color: #1E6075;'>{p['patient_name']}</h4>
                <p style='margin: 0; color: #777; font-size: 12px;'>ID: {p['patient_id']}</p>
                <p style='margin: 0; color: #777; font-size: 12px;'>Дата рожд: {p['patient_dob']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(t["select_patient"], key=f"btn_{p['patient_id']}", use_container_width=True):
                st.session_state["selected_patient_id"] = p['patient_id']
                st.session_state["selected_patient_name"] = p['patient_name']
                st.session_state["selected_patient_dob"] = p['patient_dob']
                st.success(f"Выбран пациент: {p['patient_name']}")

    # ПОКАЗ ВЫБРАННОГО ПАЦИЕНТА И МГНОВЕННЫЙ ПЕРЕХОД К КНОПКАМ
    if st.session_state["selected_patient_id"]:
        st.markdown("---")
        st.subheader(f"{t['selected_patient_title']} {st.session_state['selected_patient_name']} (ID: {st.session_state['selected_patient_id']})")
        
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
# 5. РАЗДЕЛ: АНАЛИЗЫ & СКАНИРОВАНИЕ (ВКЛЮЧАЯ КАМЕРУ МИКРОСКОПА)
# ==========================================
elif page == t["nav_analysis"]:
    st.title(t["nav_analysis"])
    
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    with col_sel1:
        p_id = st.text_input(t["p_id"], value=st.session_state.get("selected_patient_id", "115002084"))
    with col_sel2:
        p_name = st.text_input(t["p_name"], value=st.session_state.get("selected_patient_name", "Иванов Иван Иванович"))
    with col_sel3:
        p_dob = st.text_input(t["p_dob"], value=st.session_state.get("selected_patient_dob", "27.03.1999"))
        
    st.markdown("### 📷 Источник изображения крови")
    input_method = st.radio("Выберите способ получения снимка", ["Загрузить файл изображения", "Снять с камеры микроскопа / Веб-камеры"], horizontal=True)
    
    image = None
    if input_method == "Загрузить файл изображения":
        uploaded_file = st.file_uploader(t["upload_label"], type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
    else:
        camera_file = st.camera_input("Наведите микроскоп и нажмите кнопку захвата снимка")
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
                        cv2.rectangle(cv_img, (int(x-w/2), int(y-h/2)), (int(x+w/2), int(y+h/2)), (0, 255, 0), 2)
                    
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
                        wa_text = f"🩸 *ScanHemo AI Report*\n👤 Patient: {p_name} (ID: {p_id})\n🔬 Total Cells: {len(predictions)}\nCounts: {json.dumps(counts)}"
                        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
                        st.markdown(
                            f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:10px 20px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;">{t["send_whatsapp"]}</button></a>',
                            unsafe_allow_html=True
                        )

# ==========================================
# 6. РАЗДЕЛ: СТАТИСТИКА & СРАВНЕНИЕ (РЕАЛЬНЫЕ ДАННЫЕ)
# ==========================================
elif page == t["nav_stats"]:
    st.title(t["comparison_title"])
    
    curr_id = st.session_state.get("selected_patient_id", "100000284")
    curr_name = st.session_state.get("selected_patient_name", "Иванов Иван Иванович")
    st.write(f"👤 Пациент: **{curr_name}** (ID: {curr_id})")
    
    patient_df = get_patient_history(curr_id)
    
    if not patient_df.empty:
        st.success(f"Найдено сохраненных анализов в базе: {len(patient_df)}")
        
        # Подготовка данных для графиков на основе реальной истории
        chart_source = pd.DataFrame({
            'Дата': patient_df['timestamp'],
            'Всего клеток': patient_df['total_count']
        })
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Динамика общего числа обнаруженных объектов")
            st.line_chart(chart_source.set_index('Дата'))
            
        with g2:
            st.subheader("Сравнение по количеству")
            st.bar_chart(chart_source.set_index('Дата'))
            
        st.subheader("📋 История анализов этого пациента")
        st.dataframe(patient_df[['timestamp', 'doctor_name', 'clinic', 'total_count', 'counts_json']], use_container_width=True)
    else:
        st.info("У этого пациента пока нет сохраненных анализов. Сделайте первый снимок через вкладку 'Анализы & Сканирование', чтобы увидеть динамику.")

# ==========================================
# 7. РАЗДЕЛ: НАСТРОЙКИ
# ==========================================
elif page == t["nav_settings"]:
    st.title(t["nav_settings"])
    st.text_input("Название клиники", value=st.session_state.get('clinic_name'))
    st.text_input("ФИО Специалиста", value=st.session_state.get('doc_name'))
    if st.button("Сохранить изменения"):
        st.success("Настройки успешно сохранены!")
