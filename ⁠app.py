import streamlit as st
from PIL import Image
import pandas as pd
import requests
import io

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
                    # Преобразуем фото в оригинальном качестве в байты
                    img_byte_arr = io.BytesIO()
                    image.convert("RGB").save(img_byte_arr, format='JPEG', quality=100)
                    img_bytes = img_byte_arr.getvalue()
                    
                    # 1. Запрос на получение готового размеченного изображения от Roboflow
                    img_url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=10&overlap=30&labels=on&format=image"
                    img_res = requests.post(img_url, files={"file": ("image.jpg", img_bytes, "image/jpeg")})
                    
                    # 2. Запрос на получение JSON с данными подсчета
                    json_url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={ROBOFLOW_API_KEY}&confidence=10&overlap=30"
                    json_res = requests.post(json_url, files={"file": ("image.jpg", img_bytes, "image/jpeg")})
                    res_json = json_res.json()
                    
                    if img_res.status_code == 200:
                        st.image(img_res.content, caption="Размеченный ИИ снимок", use_container_width=True)
                    
                    predictions = res_json.get("predictions", [])
                    st.success(f"Найдено всего объектов: {len(predictions)}")
                    
                    counts = {}
                    for p in predictions:
                        cell_class = p.get("class", "Объект")
                        counts[cell_class] = counts.get(cell_class, 0) + 1
                        
                    if counts:
                        df_result = pd.DataFrame(list(counts.items()), columns=["Тип клетки / объекта", "Количество"])
                        st.dataframe(df_result, use_container_width=True)
                    else:
                        st.warning("Клетки не обнаружены. Попробуйте загрузить снимок из датасета Roboflow.")
                        
                except Exception as e:
                    st.error(f"Ошибка анализа: {e}")
