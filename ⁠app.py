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

st.set_page_config(page_title="BloodScan AI", layout="wide")

# ==========================================
# 0. ИНИЦИАЛИЗА БАЗЫ ДАННЫХ (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("bloodscan_history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            doctor_name TEXT,
            doctor_role TEXT,
            clinic TEXT,
            patient_id TEXT,
            total_count INTEGER,
            counts_json TEXT,
            observations_json TEXT,
            recommendations_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(doc_name, doc_role, clinic, p_id, total, counts, obs, recs):
    conn = sqlite3.connect("bloodscan_history.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (
            timestamp, doctor_name, doctor_role, clinic, 
            patient_id, total_count, 
            counts_json, observations_json, recommendations_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        doc_name, doc_role, clinic, p_id, total,
        json.dumps(counts, ensure_ascii=False),
        json.dumps(obs, ensure_ascii=False),
        json.dumps(recs, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("bloodscan_history.db")
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 1. МУЛЬТИЯЗЫЧНОСТЬ (TRANSLATIONS)
# ==========================================
translations = {
    "Русский": {
        "title": "🩸 BloodScan AI — Анализ снимка крови",
        "account_title": "👤 Учетная запись",
        "user_name": "Имя специалиста",
        "user_role": "Должность / Роль",
        "clinic_name": "Лаборатория / Клиника",
        "history_title": "📜 История анализов",
        "history_select": "Выберите анализ из базы",
        "patient_info": "📋 Данные пациента",
        "p_id": "ID / ИИН пациента",
        "source_title": "📸 Источник снимка с микроскопа",
        "source_option_1": "Загрузить файл снимка",
        "source_option_2": "Сделать снимок с камеры / USB-микроскопа",
        "source_label": "Выберите фото крови (JPG/PNG)",
        "orig_img": "Исходный снимок",
        "ai_title": "🔬 Результат работы ИИ",
        "btn_analyze": "🔬 Проанализировать через ИИ",
        "analyzing": "ИИ считает клетки крови и делает анализ...",
        "annotated_img": "Размеченный ИИ снимок",
        "total_found": "Найдено всего объектов: ",
        "cell_type": "Тип клетки / объекта",
        "count": "Количество",
        "not_found": "Клетки не обнаружены.",
        "download_pdf": "📄 Скачать профессиональный PDF отчет",
        "diag_title": "🩺 Предварительная диагностика и рекомендации ИИ",
        "disclaimer": "⚠️ Внимание: Результаты ИИ носят информационный характер и требуют подтверждения квалифицированным врачом.",
        "obs_wbc_high": "Повышенный уровень лейкоцитов (Лейкоцитоз). Подозрение на воспалительный процесс.",
        "rec_wbc_high": "Рекомендуется сдать развернутый анализ крови с лейкоцитарной формулой.",
        "obs_wbc_low": "Низкий уровень лейкоцитов (Лейкопения). Снижен иммунный ответ.",
        "rec_wbc_low": "Консультация гематолога / терапевта.",
        "obs_plt_low": "Пониженное количество тромбоцитов (Тромбоцитопения).",
        "rec_plt_low": "Пройти коагулограмму (анализ на свертываемость).",
        "obs_rbc_low": "Относительно низкая плотность эритроцитов. Признак анемии.",
        "rec_rbc_low": "Сдать анализ на ферритин и сывороточное железо.",
        "obs_normal": "Соотношение основных элементов крови в пределах нормы.",
        "rec_normal": "Плановый профилактический осмотр раз в год."
    },
    "Қазақша": {
        "title": "🩸 BloodScan AI — Қан үлгісін талдау",
        "account_title": "👤 Пайдаланушы есептік жазбасы",
        "user_name": "Маманның аты-жөні",
        "user_role": "Қызметі / Рөлі",
        "clinic_name": "Зертхана / Клиника",
        "history_title": "📜 Талдаулар тарихы",
        "history_select": "Дерекқордан талдауды таңдаңыз",
        "patient_info": "📋 Пациент мәліметтері",
        "p_id": "Пациенттің ID / ЖСН",
        "source_title": "📸 Микроскоптан сурет алу көзі",
        "source_option_1": "Сурет файлын жүктеу",
        "source_option_2": "Камерадан / USB-микроскоптан түсіру",
        "source_label": "Қан суретін таңдаңыз (JPG/PNG)",
        "orig_img": "Бастапқы сурет",
        "ai_title": "🔬 ЖИ талдау нәтижесі",
        "btn_analyze": "🔬 ЖИ арқылы талдау",
        "analyzing": "ЖИ қан жасушаларын санауда...",
        "annotated_img": "ЖИ белгілеген сурет",
        "total_found": "Табылған нысандар саны: ",
        "cell_type": "Жасуша / нысан түрі",
        "count": "Саны",
        "not_found": "Жасушалар табылмады.",
        "download_pdf": "📄 Кәсіби PDF есепті жүктеу",
        "diag_title": "🩺 Алдын ала диагностика және ЖИ ұсыныстары",
        "disclaimer": "⚠️ Назар аударыңыз: ЖИ нәтижелері ақпараттық сипатта және білікті дәрігердің растауын талап етеді.",
        "obs_wbc_high": "Лейкоциттер деңгейінің жоғарылауы (Лейкоцитоз).",
        "rec_wbc_high": "Кеңейтілген қан талдауын тапсыру ұсынылады.",
        "obs_wbc_low": "Лейкоциттердің төмен деңгейі (Лейкопения).",
        "rec_wbc_low": "Гематолог / терапевт кеңесі.",
        "obs_plt_low": "Тромбоциттер санының төмендеуі (Тромбоцитопения).",
        "rec_plt_low": "Коагулограммадан өту.",
        "obs_rbc_low": "Эритроциттердің төмен тығыздығы. Анемия белгісі.",
        "rec_rbc_low": "Ферритин мен темірге талдау тапсыру.",
        "obs_normal": "Қан элементтерінің арақатынасы норма шегінде.",
        "rec_normal": "Жоспарлы тексеру."
    },
    "English": {
        "title": "🩸 BloodScan AI — Blood Sample Analysis",
        "account_title": "👤 User Account",
        "user_name": "Specialist Name",
        "user_role": "Position / Role",
        "clinic_name": "Laboratory / Clinic",
        "history_title": "📜 Analysis History",
        "history_select": "Select analysis from database",
        "patient_info": "📋 Patient Information",
        "p_id": "Patient ID",
        "source_title": "📸 Microscope Image Source",
        "source_option_1": "Upload image file",
        "source_option_2": "Take a photo with Camera / USB Microscope",
        "source_label": "Select blood image (JPG/PNG)",
        "orig_img": "Original Image",
        "ai_title": "🔬 AI Analysis Result",
        "btn_analyze": "🔬 Analyze with AI",
        "analyzing": "AI is counting blood cells and analyzing...",
        "annotated_img": "AI Annotated Image",
        "total_found": "Total objects found: ",
        "cell_type": "Cell / Object Type",
        "count": "Count",
        "not_found": "No cells detected.",
        "download_pdf": "📄 Download Professional PDF Report",
        "diag_title": "🩺 AI Preliminary Diagnostics & Recommendations",
        "disclaimer": "⚠️ Disclaimer: AI results are informational and require confirmation by a qualified medical specialist.",
        "obs_wbc_high": "Elevated leukocyte level (Leukocytosis).",
        "rec_wbc_high": "A detailed blood count test is recommended.",
        "obs_wbc_low": "Low leukocyte level (Leukopenia).",
        "rec_wbc_low": "Consultation with a hematologist.",
        "obs_plt_low": "Decreased platelet count (Thrombocytopenia).",
        "rec_plt_low": "Perform a coagulation profile.",
        "obs_rbc_low": "Low erythrocyte density. Possible sign of anemia.",
        "rec_rbc_low": "Test for ferritin and serum iron.",
        "obs_normal": "Ratio of main blood cells is within normal limits.",
        "rec_normal": "Routine preventive checkup."
    }
}

selected_lang = st.sidebar.selectbox("Language / Язык / Тіл", ["Русский", "Қазақша", "English"])
t = translations[selected_lang]

st.sidebar.markdown("---")
st.sidebar.subheader(t["account_title"])
account_name = st.sidebar.text_input(t["user_name"], value="Dr. Alex Smith")
account_role = st.sidebar.text_input(t["user_role"], value="Lab Technologist")
account_clinic = st.sidebar.text_input(t["clinic_name"], value="Central Clinical Lab")

st.sidebar.markdown("---")
st.sidebar.subheader(t["history_title"])
history_df = get_history()

selected_history_id = None
if not history_df.empty:
    history_options = ["—"] + [f"[{row['timestamp']}] ID: {row['patient_id']}" for _, row in history_df.iterrows()]
    selected_option = st.sidebar.selectbox(t["history_select"], history_options)
    
    if selected_option != "—":
        selected_idx = history_options.index(selected_option) - 1
        selected_history_row = history_df.iloc[selected_idx]
        selected_history_id = selected_history_row["id"]

st.title(t["title"])

# ==========================================
# 2. ГЕНЕРАЦИЯ СТАБИЛЬНОГО PDF (БЕЗ ВОЗРАСТА)
# ==========================================
def clean_text(text):
    """Очистка текста для защиты от сбоев шрифта Helvetica"""
    return str(text).encode('latin-1', 'asciixml').decode('latin-1')

def generate_pdf(p_id, counts, total, obs, recs, doc_name, doc_role, clinic):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(colors.HexColor("#003366"))
    c.rect(0, height - 70, width, 70, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 42, "BLOODSCAN AI — DIAGNOSTIC REPORT")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 35, f"Facility: {clean_text(clinic)}")
    c.drawRightString(width - 40, height - 50, f"Operator: {clean_text(doc_name)} ({clean_text(doc_role)})")
    
    y = height - 100
    
    # Patient Info Block (Без возраста)
    c.setFillColor(colors.HexColor("#F0F4F8"))
    c.roundRect(40, y - 45, width - 80, 45, 6, fill=True, stroke=False)
    
    c.setFillColor(colors.HexColor("#1A252C"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y - 25, f"Patient ID: {clean_text(p_id)}")
    c.drawString(320, y - 25, f"Total Objects Counted: {total}")
    
    y -= 70
    
    # 1. Statistics
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#003366"))
    c.drawString(40, y, "1. Cell Analysis Statistics")
    y -= 15
    
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.5)
    c.line(40, y, width - 40, y)
    y -= 18
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(60, y, "Cell / Object Type")
    c.drawString(300, y, "Quantity")
    y -= 10
    c.line(40, y, width - 40, y)
    y -= 18
    
    c.setFont("Helvetica", 10)
    for cell_class, count in counts.items():
        c.drawString(60, y, clean_text(cell_class))
        c.drawString(300, y, str(count))
        y -= 16
        
    y -= 15
    
    # 2. Observations
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#003366"))
    c.drawString(40, y, "2. Clinical Observations & Detection")
    y -= 15
    c.line(40, y, width - 40, y)
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    for o in obs:
        c.drawString(55, y, f"- {clean_text(o[:80])}")
        y -= 15
        
    y -= 15
    
    # 3. Recommendations
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#003366"))
    c.drawString(40, y, "3. Recommended Next Steps")
    y -= 15
    c.line(40, y, width - 40, y)
    y -= 18
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    for r in recs:
        c.drawString(55, y, f"-> {clean_text(r[:80])}")
        y -= 15
        
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawString(40, 30, "Disclaimer: Generated by BloodScan AI. Results require medical confirmation.")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 3. ЕСЛИ ВЫБРАН АНАЛИЗ ИЗ ИСТОРИИ
# ==========================================
if selected_history_id is not None:
    h_row = history_df[history_df["id"] == selected_history_id].iloc[0]
    st.info(f"📜 Просмотр сохраненного анализа от {h_row['timestamp']}")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.write(f"**ID Пациента:** {h_row['patient_id']}")
        st.write(f"**Лаборатория:** {h_row['clinic']}")
    with col_h2:
        st.write(f"**Специалист:** {h_row['doctor_name']} ({h_row['doctor_role']})")
        st.write(f"**Всего клеток:** {h_row['total_count']}")
        
    h_counts = json.loads(h_row["counts_json"])
    h_obs = json.loads(h_row["observations_json"])
    h_recs = json.loads(h_row["recommendations_json"])
    
    st.dataframe(pd.DataFrame(list(h_counts.items()), columns=[t["cell_type"], t["count"]]), use_container_width=True)
    
    st.subheader(t["diag_title"])
    for o in h_obs:
        st.warning(f"• {o}")
    for r in h_recs:
        st.info(f"👉 {r}")
        
    h_pdf = generate_pdf(
        h_row['patient_id'], h_counts, 
        h_row['total_count'], h_obs, h_recs,
        h_row['doctor_name'], h_row['doctor_role'], h_row['clinic']
    )
    
    st.download_button(
        label=t["download_pdf"],
        data=h_pdf,
        file_name=f"BloodScan_Report_{h_row['patient_id']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

else:
    # ==========================================
    # 4. НОВЫЙ АНАЛИЗ
    # ==========================================
    st.subheader(t["patient_info"])
    patient_id = st.text_input(t["p_id"], value="ID-100293")

    ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
    MODEL_ID = "complete-blood-cell-analysis/1"

    st.subheader(t["source_title"])
    source_mode = st.radio("", [t["source_option_1"], t["source_option_2"]])

    uploaded_file = None
    if source_mode == t["source_option_1"]:
        uploaded_file = st.file_uploader(t["source_label"], type=["jpg", "jpeg", "png"])
    else:
        uploaded_file = st.camera_input(t["source_title"])

    def analyze_health(counts, total, lang_dict):
        observations = []
        recommendations = []
        
        if total == 0:
            return [lang_dict["not_found"]], ["—"]
            
        rbc_count = counts.get("RBC", counts.get("Erythrocyte", 0))
        wbc_count = counts.get("WBC", counts.get("Leukocyte", 0))
        platelet_count = counts.get("Platelet", counts.get("Platelets", 0))
        
        wbc_ratio = (wbc_count / total) if total > 0 else 0
        platelet_ratio = (platelet_count / total) if total > 0 else 0
        
        if wbc_ratio > 0.15:
            observations.append(lang_dict["obs_wbc_high"])
            recommendations.append(lang_dict["rec_wbc_high"])
        elif wbc_count == 0 and total > 30:
            observations.append(lang_dict["obs_wbc_low"])
            recommendations.append(lang_dict["rec_wbc_low"])
            
        if platelet_ratio < 0.02 and total > 20:
            observations.append(lang_dict["obs_plt_low"])
            recommendations.append(lang_dict["rec_plt_low"])
            
        if rbc_count / total < 0.70 if total > 0 else False:
            observations.append(lang_dict["obs_rbc_low"])
            recommendations.append(lang_dict["rec_rbc_low"])
            
        if not observations:
            observations.append(lang_dict["obs_normal"])
            recommendations.append(lang_dict["rec_normal"])
            
        return observations, recommendations

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption=t["orig_img"], use_container_width=True)
        
        with col2:
            st.subheader(t["ai_title"])
            if st.button(t["btn_analyze"], use_container_width=True):
                with st.spinner(t["analyzing"]):
                    try:
                        img_byte_arr = io.BytesIO()
                        image.convert("RGB").save(img_byte_arr, format='JPEG', quality=95)
                        img_bytes = img_byte_arr.getvalue()
                        
                        url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=10"
                        response = requests.post(
                            url,
                            files={"file": ("image.jpg", img_bytes, "image/jpeg")}
                        )
                        
                        res_json = response.json()
                        
                        if "error" in res_json:
                            st.error(f"Error: {res_json['error']}")
                        else:
                            predictions = res_json.get("predictions", [])
                            
                            cv_img = np.array(image.convert("RGB"))
                            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
                            
                            counts = {}
                            for p in predictions:
                                cell_class = p.get("class", "Cell")
                                confidence = p.get("confidence", 0)
                                counts[cell_class] = counts.get(cell_class, 0) + 1
                                
                                x, y, w, h = int(p["x"]), int(p["y"]), int(p["width"]), int(p["height"])
                                x1, y1 = int(x - w / 2), int(y - h / 2)
                                x2, y2 = int(x + w / 2), int(y + h / 2)
                                
                                color = (0, 255, 0) if cell_class == "RBC" else (255, 0, 0)
                                cv2.rectangle(cv_img, (x1, y1), (x2, y2), color, 2)
                                cv2.putText(cv_img, f"{cell_class} {int(confidence * 100)}%", 
                                            (x1, max(y1 - 10, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                            
                            result_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                            st.image(result_img, caption=t["annotated_img"], use_container_width=True)
                            
                            st.success(f"{t['total_found']}{len(predictions)}")
                            
                            if counts:
                                df_result = pd.DataFrame(list(counts.items()), columns=[t["cell_type"], t["count"]])
                                st.dataframe(df_result, use_container_width=True)
                                
                                st.markdown("---")
                                st.subheader(t["diag_title"])
                                
                                obs, recs = analyze_health(counts, len(predictions), t)
                                
                                for o in obs:
                                    st.warning(f"• {o}")
                                for r in recs:
                                    st.info(f"👉 {r}")
                                    
                                st.caption(t["disclaimer"])
                                
                                save_analysis(
                                    account_name, account_role, account_clinic,
                                    patient_id, len(predictions),
                                    counts, obs, recs
                                )
                                st.toast("✅ Анализ сохранен в историю!")
                                
                                pdf_bytes = generate_pdf(
                                    patient_id, 
                                    counts, 
                                    len(predictions), 
                                    obs, 
                                    recs,
                                    account_name,
                                    account_role,
                                    account_clinic
                                )
                                
                                st.download_button(
                                    label=t["download_pdf"],
                                    data=pdf_bytes,
                                    file_name=f"BloodScan_Report_{patient_id}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            else:
                                st.warning(t["not_found"])
                                
                    except Exception as e:
                        st.error(f"Error: {e}")
