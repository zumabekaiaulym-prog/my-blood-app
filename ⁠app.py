import streamlit as st
from PIL import Image
import pandas as pd
import requests
import io
import numpy as np
import cv2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="BloodScan AI", layout="wide")

# ==========================================
# 1. МУЛЬТИЯЗЫЧНОСТЬ
# ==========================================
translations = {
    "Русский": {
        "title": "🩸 BloodScan AI — Анализ снимка крови",
        "patient_info": "📋 Данные пациента",
        "p_name": "ФИО пациента",
        "p_age": "Возраст",
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
        "download_pdf": "📄 Скачать PDF отчет",
        "diag_title": "🩺 Предварительная диагностика и рекомендации ИИ",
        "disclaimer": "⚠️ Внимание: Результаты ИИ носят информационный характер и требуют подтверждения квалифицированным врачом."
    },
    "Қазақша": {
        "title": "🩸 BloodScan AI — Қан үлгісін талдау",
        "patient_info": "📋 Пациент мәліметтері",
        "p_name": "Пациенттің Т.А.Ә.",
        "p_age": "Жасы",
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
        "download_pdf": "📄 PDF есепті жүктеу",
        "diag_title": "🩺 Алдын ала диагностика және ЖИ ұсыныстары",
        "disclaimer": "⚠️ Назар аударыңыз: ЖИ нәтижелері ақпараттық сипатта және білікті дәрігердің растауын талап етеді."
    },
    "English": {
        "title": "🩸 BloodScan AI — Blood Sample Analysis",
        "patient_info": "📋 Patient Information",
        "p_name": "Patient Full Name",
        "p_age": "Age",
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
        "download_pdf": "📄 Download PDF Report",
        "diag_title": "🩺 AI Preliminary Diagnostics & Recommendations",
        "disclaimer": "⚠️ Disclaimer: AI results are informational and require confirmation by a qualified medical specialist."
    }
}

selected_lang = st.sidebar.selectbox("Language / Язык / Тіл", ["Русский", "Қазақша", "English"])
t = translations[selected_lang]

st.title(t["title"])

# ==========================================
# 2. ДАННЫЕ ПАЦИЕНТА
# ==========================================
st.subheader(t["patient_info"])
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    patient_name = st.text_input(t["p_name"], value="Ivanov I.I.")
with col_p2:
    patient_age = st.text_input(t["p_age"], value="35")
with col_p3:
    patient_id = st.text_input(t["p_id"], value="ID-100293")

# ==========================================
# 3. НАСТРОЙКИ МОДЕЛИ ROBOFLOW
# ==========================================
ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
MODEL_ID = "complete-blood-cell-analysis/1"

st.subheader(t["source_title"])
source_mode = st.radio("", [t["source_option_1"], t["source_option_2"]])

uploaded_file = None
if source_mode == t["source_option_1"]:
    uploaded_file = st.file_uploader(t["source_label"], type=["jpg", "jpeg", "png"])
else:
    uploaded_file = st.camera_input(t["source_title"])

# ==========================================
# 4. ЛОГИКА ДИАГНОСТИКИ И РЕКОМЕНДАЦИЙ
# ==========================================
def analyze_health(counts, total):
    observations = []
    recommendations = []
    
    if total == 0:
        return ["Клетки не обнаружены"], ["Попробуйте загрузить другой снимок с четким фокусом."]
        
    rbc_count = counts.get("RBC", counts.get("Erythrocyte", 0))
    wbc_count = counts.get("WBC", counts.get("Leukocyte", 0))
    platelet_count = counts.get("Platelet", counts.get("Platelets", 0))
    
    # Расчет соотношений
    wbc_ratio = (wbc_count / total) if total > 0 else 0
    platelet_ratio = (platelet_count / total) if total > 0 else 0
    
    if wbc_ratio > 0.15:
        observations.append("Повышенный уровень лейкоцитов (Лейкоцитоз). Подозрение на воспалительный или инфекционный процесс.")
        recommendations.append("Рекомендуется сдать развернутый анализ крови с лейкоцитарной формулой и C-реактивный белок (СРБ).")
    elif wbc_count == 0 and total > 30:
        observations.append("Низкий уровень лейкоцитов (Лейкопения). Снижен иммунный ответ.")
        recommendations.append("Консультация гематолога / терапевта.")
        
    if platelet_ratio < 0.02 and total > 20:
        observations.append("Пониженное количество тромбоцитов (Тромбоцитопения). Риск замедленной свертываемости крови.")
        recommendations.append("Пройти коагулограмму (анализ на свертываемость).")
        
    if rbc_count / total < 0.70 if total > 0 else False:
        observations.append("Относительно низкая плотность эритроцитов. Возможный признак анемии.")
        recommendations.append("Сдать анализ на ферритин, сывороточное железо и витамин B12.")
        
    if not observations:
        observations.append("Соотношение основных форменных элементов крови в пределах визуальной нормы снимка.")
        recommendations.append("Плановый профилактический осмотр раз в год.")
        
    return observations, recommendations

# Генерация PDF
def generate_pdf(p_name, p_age, p_id, counts, total, obs, recs):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "BloodScan AI — Diagnostic Report")
    
    c.setFont("Helvetica", 11)
    c.drawString(50, 720, f"Patient Name: {p_name}")
    c.drawString(50, 705, f"Age: {p_age}")
    c.drawString(50, 690, f"Patient ID: {p_id}")
    
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 655, f"Total Objects Found: {total}")
    
    c.setFont("Helvetica", 11)
    y = 635
    for cell_class, count in counts.items():
        c.drawString(70, y, f"- {cell_class}: {count}")
        y -= 15
        
    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Observations:")
    y -= 15
    c.setFont("Helvetica", 10)
    for o in obs:
        c.drawString(60, y, f"* {o[:80]}")
        y -= 15
        
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Recommendations:")
    y -= 15
    c.setFont("Helvetica", 10)
    for r in recs:
        c.drawString(60, y, f"* {r[:80]}")
        y -= 15
        
    y -= 25
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y, "Disclaimer: AI-generated report. Consult a physician for accurate medical diagnosis.")
        
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

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
                            
                            # Диагностический блок
                            st.markdown("---")
                            st.subheader(t["diag_title"])
                            
                            obs, recs = analyze_health(counts, len(predictions))
                            
                            for o in obs:
                                st.warning(f"• {o}")
                            for r in recs:
                                st.info(f"👉 {r}")
                                
                            st.caption(t["disclaimer"])
                            
                            # Генерация и скачивание PDF
                            pdf_bytes = generate_pdf(patient_name, patient_age, patient_id, counts, len(predictions), obs, recs)
                            
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
