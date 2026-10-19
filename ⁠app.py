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

# Настройка страницы и кастомные CSS стили для дизайна ScanHemo AI
st.set_page_config(page_title="ScanHemo AI", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Главный фон и шрифты */
    .stApp {
        background-color: #EBF2F5;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Стилизация боковой панели */
    [data-testid="stSidebar"] {
        background-color: #D9E6EB;
        border-right: 1px solid #C4D7E0;
    }
    
    /* Карточки пациентов */
    .patient-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #E0E8EC;
        text-align: center;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    
    .patient-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Заголовки и логотипы */
    .brand-title {
        color: #1A5265;
        font-weight: 800;
        font-size: 32px;
        margin-bottom: 0px;
    }
    
    /* Кастомные кнопки */
    .stButton>button {
        background-color: #1E6075;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 8px 16px;
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

# Session State для авторизации и навигации
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Пациенты"
if "selected_patient_id" not in st.session_state:
    st.session_state["selected_patient_id"] = None

# ==========================================
# 1. ЭКРАН АВТОРИЗАЦИИ (LOGIN)
# ==========================================
if not st.session_state["authenticated"]:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<h1 style='text-align: center; color: #1E6075;'>ScanHemo 🩸</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #555;'>Вход в систему лабораторной диагностики</p>", unsafe_allow_html=True)
            
            doc_name = st.text_input("Имя специалиста", value="Dr. Alex Smith")
            doc_role = st.text_input("Должность / Роль", value="Лаборант-технолог")
            clinic_name = st.text_input("Лаборатория / Клиника", value="Центральная клиническая лаборатория")
            password = st.text_input("Пароль", type="password", value="******")
            
            if st.button("Войти", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["doc_name"] = doc_name
                st.session_state["doc_role"] = doc_role
                st.session_state["clinic_name"] = clinic_name
                st.rerun()
    st.stop()

# ==========================================
# 2. МЕНЮ НАВИГАЦИИ (БОКОВАЯ ПАНЕЛЬ)
# ==========================================
with st.sidebar:
    st.markdown("<h2 class='brand-title'>ScanHemo AI</h2>", unsafe_allow_html=True)
    st.write(f"👤 **{st.session_state.get('doc_name', 'Специалист')}**")
    st.caption(f"{st.session_state.get('doc_role', '')} | {st.session_state.get('clinic_name', '')}")
    st.markdown("---")
    
    page = st.radio(
        "Навигация",
        ["👥 Пациенты", "🔬 Анализы & Сканирование", "📊 Статистика & Сравнение", "⚙️ Настройки"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Выйти", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ==========================================
# 3. СТРАНИЦА: ПАЦИЕНТЫ (СПИСОК И КАРТОЧКИ)
# ==========================================
if page == "👥 Пациенты":
    st.title("Пациент list")
    
    # Кнопка добавления нового пациента
    with st.expander("➕ Зарегистрировать нового пациента"):
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            new_id = st.text_input("ID / ИИН", value="110002084")
        with col_n2:
            new_name = st.text_input("ФИО Пациента", value="Иванов Иван Иванович")
        with col_n3:
            new_dob = st.text_input("Дата рождения", value="27.03.1999")
            
    history_df = get_history()
    
    # Фильтрация уникальных пациентов
    if not history_df.empty and 'patient_id' in history_df.columns:
        patients = history_df[['patient_id', 'patient_name', 'patient_dob']].drop_duplicates()
    else:
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
                <div style='font-size: 40px;'>👤</div>
                <h4 style='margin: 5px 0; color: #1E6075;'>{p['patient_name']}</h4>
                <p style='margin: 0; color: #777; font-size: 13px;'>ID: {p['patient_id']}</p>
                <p style='margin: 0; color: #777; font-size: 13px;'>Дождн: {p['patient_dob']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Выбрать пациента", key=f"btn_{p['patient_id']}", use_container_width=True):
                st.session_state["selected_patient_id"] = p['patient_id']
                st.session_state["selected_patient_name"] = p['patient_name']
                st.session_state["selected_patient_dob"] = p['patient_dob']
                st.toast(f"Выбран пациент: {p['patient_name']}")

# ==========================================
# 4. СТРАНИЦА: АНАЛИЗЫ & СКАНИРОВАНИЕ
# ==========================================
elif page == "🔬 Анализы & Сканирование":
    st.title("Сканирование и обработка снимка крови")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        p_id = st.text_input("ID / ИИН пациента", value=st.session_state.get("selected_patient_id", "115002084"))
    with col_sel2:
        p_name = st.text_input("ФИО пациента", value=st.session_state.get("selected_patient_name", "Иванов Иван Иванович"))
        
    uploaded_file = st.file_uploader("Загрузите микроскопический снимок", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        c1, c2 = st.columns(2)
        with c1:
            st.image(image, caption="Исходный снимок", use_container_width=True)
        with c2:
            if st.button("🔬 Проанализировать через ИИ", use_container_width=True):
                with st.spinner("ИИ анализирует снимок..."):
                    ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
                    MODEL_ID = "complete-blood-cell-analysis/1"
                    img_byte_arr = io.BytesIO()
                    image.convert("RGB").save(img_byte_arr, format='JPEG', quality=95)
                    img_bytes = img_byte_arr.getvalue()
                    
                    url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=10"
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
                    st.image(result_img, caption="Результат размеченный ИИ", use_container_width=True)
                    st.dataframe(pd.DataFrame(list(counts.items()), columns=["Тип клетки", "Количество"]), use_container_width=True)
                    
                    save_analysis(
                        st.session_state.get('doc_name'), st.session_state.get('doc_role'), 
                        st.session_state.get('clinic_name'), p_id, p_name, "27.03.1999", "Мужской",
                        len(predictions), counts, ["Анализ завершен"], ["Рекомендуется плановый просмотр"]
                    )
                    st.success("Анализ сохранен в базу ScanHemo AI!")

# ==========================================
# 5. СТРАНИЦА: СТАТИСТИКА & СРАВНЕНИЕ (ДИЗAЙН С МАКЕТА)
# ==========================================
elif page == "📊 Статистика & Сравнение":
    st.title("Сравнение с предыдущими анализами")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        p1 = st.selectbox("Выбрать первый анализ / пациента", ["Иванов Иван Иванович", "Геранта Иван Иванович"])
    with col_c2:
        p2 = st.selectbox("Выбрать второй анализ для сравнения", ["Геранта Иван Иванович", "Иванов Иван Иванович"])
        
    st.button("Сравнение", use_container_width=False)
    
    # Визуальные графики сравнения показателей (как на вашем макете)
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("RBC / WBC Динамика (↑↑)")
        chart_data1 = pd.DataFrame(
            np.random.randn(10, 2) + [100, 80],
            columns=['Текущий', "Прошлый"]
        )
        st.line_chart(chart_data1)
        
    with g2:
        st.subheader("RA / RC Плотность (↓↓)")
        chart_data2 = pd.DataFrame(
            np.random.randn(10, 2) + [50, 40],
            columns=['Текущий', "Прошлый"]
        )
        st.area_chart(chart_data2)

    # Таблица сравнения компонентов
    st.subheader("Сводная таблица показателей")
    table_data = pd.DataFrame({
        'Компонент': ['RBC', 'WBC', 'Platelets'],
        'Прошлый анализ': [17.53, 9.63, 0.55],
        'Текущий анализ': [11.0, 0.37, 0.82],
        'Норма': [18.6, 11.6, 10.3],
        'Динамика': ['📈 Рост', '📉 Снижение', '📈 Рост']
    })
    st.dataframe(table_data, use_container_width=True)

# ==========================================
# 6. СТРАНИЦА: НАСТРОЙКИ
# ==========================================
elif page == "⚙️ Настройки":
    st.title("Настройки профиля и системы")
    st.text_input("Название клиники", value=st.session_state.get('clinic_name'))
    st.text_input("ФИО Специалиста", value=st.session_state.get('doc_name'))
    st.text_input("Язык интерфейса", value="Русский")
    st.checkbox("Включить автоматическую генерацию PDF", value=True)
    st.button("Сохранить настройки")
