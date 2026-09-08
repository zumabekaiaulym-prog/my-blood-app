import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import cv2
import tempfile
import os
from roboflow import Roboflow

st.set_page_config(page_title="BloodScan AI", layout="wide")
st.title("🩸 BloodScan AI — Тестирование модели ИИ")

# ==========================================
# ИНИЦИАЛИЗА ROBOFLOW SDK
# ==========================================
ROBOFLOW_API_KEY = "NJw10P0PWJp9Ee4A3uF1"
WORKSPACE_NAME = "aia-zum"
PROJECT_NAME = "complete-blood-cell-analysis-1-yolo26n-seg-t1"
VERSION_NUM = 1

@st.cache_resource
def load_roboflow_model():
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(WORKSPACE_NAME).project(PROJECT_NAME)
    return project.version(VERSION_NUM).model

st.subheader("1. Загрузите снимок микроскопа")
uploaded_file = st.file_uploader("Выберите фото крови (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Исходное изображение", use_container_width=True)
        
    with col2:
        st.subheader("2. Результат ИИ")
        if st.button("🔬 Проверить распознавание", use_container_width=True):
            with st.spinner("Запрос к модели Roboflow..."):
                try:
                    # Сохраняем временный файл для SDK
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        image.convert("RGB").save(tmp_file.name)
                        tmp_path = tmp_file.name

                    # Получаем модель и запускаем предсказание
                    model = load_roboflow_model()
                    prediction = model.predict(tmp_path, confidence=10, overlap=30)
                    
                    # Удаляем временный файл
                    os.remove(tmp_path)
                    
                    res_json = prediction.json()
                    predictions = res_json.get("predictions", [])
                    
                    # Отрисовка на изображении
                    cv_img = np.array(image.convert("RGB"))
                    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
                    
                    counts = {}
                    for p in predictions:
                        cell_class = p.get("class", "Клетка")
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
                    st.image(result_img, caption="Размеченный снимок", use_container_width=True)
                    
                    st.success(f"Обнаружено объектов: {len(predictions)}")
                    if counts:
                        df_res = pd.DataFrame(list(counts.items()), columns=["Тип", "Количество"])
                        st.dataframe(df_res, use_container_width=True)
                    else:
                        st.warning("Объекты не найдены.")
                        
                except Exception as e:
                    st.error(f"Ошибка Roboflow SDK: {e}")
