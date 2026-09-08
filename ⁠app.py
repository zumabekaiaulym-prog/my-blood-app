import streamlit as st
from PIL import Image
import pandas as pd
import requests
import io
import numpy as np
import cv2

st.set_page_config(page_title="BloodScan AI", layout="wide")
st.title("BloodScan AI — Анализ снимка крови")

# ==========================================
# ДАННЫЕ ROBOFLOW
# ==========================================
ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
MODEL_ID = "complete-blood-cell-analysis-1-yolo26n-seg-t1/1"

st.subheader("1. Источник снимка с микроскопа")

source_mode = st.radio("Выберите способ получения снимка:", ["Загрузить файл снимка", "Сделать снимок с камеры / USB-микроскопа"])

uploaded_file = None

if source_mode == "Загрузить файл снимка":
    uploaded_file = st.file_uploader("Выберите фото крови (JPG/PNG)", type=["jpg", "jpeg", "png"])
else:
    uploaded_file = st.camera_input("Снимок с камеры / USB-микроскопа")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Исходный снимок", use_container_width=True)
    
    with col2:
        st.subheader("2. Результат работы ИИ")
        if st.button("🔬 Проанализировать через ИИ", use_container_width=True):
            with st.spinner("ИИ считает клетки крови..."):
                try:
                    # Преобразуем фото в байты
                    img_byte_arr = io.BytesIO()
                    image.convert("RGB").save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Отправляем запрос в API с порогом 20% для лучшего обнаружения
                    url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=20"
                    response = requests.post(
                        url,
                        files={"file": ("image.jpg", img_bytes, "image/jpeg")}
                    )
                    
                    res_json = response.json()
                    
                    if "error" in res_json:
                        st.error(f"Ошибка Roboflow: {res_json['error']}")
                    else:
                        predictions = res_json.get("predictions", [])
                        
                        # Рисуем рамки с помощью OpenCV
                        cv_img = np.array(image.convert("RGB"))
                        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
                        
                        counts = {}
                        for p in predictions:
                            cell_class = p.get("class", "Клетка")
                            confidence = p.get("confidence", 0)
                            counts[cell_class] = counts.get(cell_class, 0) + 1
                            
                            x = int(p["x"])
                            y = int(p["y"])
                            w = int(p["width"])
                            h = int(p["height"])
                            
                            x1 = int(x - w / 2)
                            y1 = int(y - h / 2)
                            x2 = int(x + w / 2)
                            y2 = int(y + h / 2)
                            
                            color = (0, 255, 0) if cell_class == "RBC" else (255, 0, 0)
                            cv2.rectangle(cv_img, (x1, y1), (x2, y2), color, 2)
                            label = f"{cell_class} {int(confidence * 100)}%"
                            cv2.putText(cv_img, label, (x1, max(y1 - 10, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        result_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                        st.image(result_img, caption="Размеченный ИИ снимок", use_container_width=True)
                        
                        st.success(f"Найдено всего объектов: {len(predictions)}")
                        
                        if counts:
                            df_result = pd.DataFrame(list(counts.items()), columns=["Тип клетки / объекта", "Количество"])
                            st.dataframe(df_result, use_container_width=True)
                        else:
                            st.warning("Клетки не обнаружены. Попробуйте другой снимок.")
                            
                except Exception as e:
                    st.error(f"Ошибка анализа: {e}")
