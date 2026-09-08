import streamlit as st
from PIL import Image
import pandas as pd
from roboflow import Roboflow

st.set_page_config(page_title="BloodScan AI", layout="wide")
st.title("BloodScan AI — Анализ снимка крови")

# ==========================================
# 1. ВСТАВЬ СВОИ ДАННЫЕ ИЗ ROBOFLOW СЮДА:
# ==========================================
ROBOFLOW_API_KEY = "rf_pzHlWjxsfSYLletbkunx4p4DRQk1"
PROJECT_ID = "import streamlit as st
from PIL import Image
import pandas as pd
from roboflow import Roboflow

st.set_page_config(page_title="BloodScan AI", layout="wide")
st.title("BloodScan AI — Анализ снимка крови")

# ==========================================
# 1. ВСТАВЬ СВОИ ДАННЫЕ ИЗ ROBOFLOW СЮДА:
# ==========================================
ROBOFLOW_API_KEY = "rf_pzHlWjxsfSYLletbkunx4p4DRQk1"
PROJECT_ID = " import streamlit as st
from PIL import Image
import pandas as pd
from roboflow import Roboflow

st.set_page_config(page_title="BloodScan AI", layout="wide")
st.title("BloodScan AI — Анализ снимка крови")

# ==========================================
# 1. ВСТАВЬ СВОИ ДАННЫЕ ИЗ ROBOFLOW СЮДА:
# ==========================================
ROBOFLOW_API_KEY = "rf_pzHlWjxsfSYLletbkunx4p4DRQk1"
PROJECT_ID = "aia-zum/complete-blood-cell-analysis-1-yolo26n-seg-t1"
VERSION_NUM = 1  

@st.cache_resource
def get_model():
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project(PROJECT_ID)
    return project.version(VERSION_NUM).model

# ==========================================
# 2. ЗАГРУЗКА СНИМКА КРОВИ
# ==========================================
st.subheader("1. Загрузите снимок с микроскопа")
uploaded_file = st.file_uploader("IMG_0978", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Исходный снимок", use_column_width=True)
    
    # ==========================================
    # 3. РАБОТА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА
    # ==========================================
    with col2:
        st.subheader("2. Результат работы ИИ")
        if st.button("🔬 Проанализировать через ИИ"):
            with st.spinner("ИИ считает клетки крови..."):
                try:
                    # Сохраняем во временный файл
                    image.save("temp_blood.jpg")
                    
                    # Запрос к твоей модели Roboflow
                    model = get_model()
                    prediction = model.predict("temp_blood.jpg", confidence=40, overlap=30)
                    
                    # Сохраняем снимок с нарисованными рамками вокруг клеток
                    prediction.save("result_blood.jpg")
                    st.image("result_blood.jpg", caption="Размеченный ИИ снимок", use_column_width=True)
                    
                    # Получаем список найденных клеток
                    json_data = prediction.json()
                    predictions_list = json_data.get("predictions", [])
                    
                    # Считаем количество каждого типа клеток
                    counts = {}
                    for item in predictions_list:
                        cell_type = item["class"]
                        counts[cell_type] = counts.get(cell_type, 0) + 1
                    
                    st.success(f"Найдено всего клеток: {len(predictions_list)}")
                    
                    # Выводим реальную таблицу подсчета
                    if counts:
                        df_result = pd.DataFrame(list(counts.items()), columns=["Тип клетки", "Количество"])
                        st.dataframe(df_result, use_container_width=True)
                    else:
                        st.warning("ИИ не нашел знакомых клеток на этой фотографии.")
                        
                except Exception as e:
                    st.error(f"Ошибка подключения к Roboflow: {e}")
"
VERSION_NUM = 1  # Номер версии твоей модели

@st.cache_resource
def get_model():
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project(PROJECT_ID)
    return project.version(VERSION_NUM).model

# ==========================================
# 2. ЗАГРУЗКА СНИМКА КРОВИ
# ==========================================
st.subheader("1. Загрузите снимок с микроскопа")
uploaded_file = st.file_uploader("Выберите фото крови (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Исходный снимок", use_column_width=True)
    
    # ==========================================
    # 3. РАБОТА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА
    # ==========================================
    with col2:
        st.subheader("2. Результат работы ИИ")
        if st.button("🔬 Проанализировать через ИИ"):
            with st.spinner("ИИ считает клетки крови..."):
                try:
                    # Сохраняем во временный файл
                    image.save("temp_blood.jpg")
                    
                    # Запрос к твоей модели Roboflow
                    model = get_model()
                    prediction = model.predict("temp_blood.jpg", confidence=40, overlap=30)
                    
                    # Сохраняем снимок с нарисованными рамками вокруг клеток
                    prediction.save("result_blood.jpg")
                    st.image("result_blood.jpg", caption="Размеченный ИИ снимок", use_column_width=True)
                    
                    # Получаем список найденных клеток
                    json_data = prediction.json()
                    predictions_list = json_data.get("predictions", [])
                    
                    # Считаем количество каждого типа клеток
                    counts = {}
                    for item in predictions_list:
                        cell_type = item["class"]
                        counts[cell_type] = counts.get(cell_type, 0) + 1
                    
                    st.success(f"Найдено всего клеток: {len(predictions_list)}")
                    
                    # Выводим реальную таблицу подсчета
                    if counts:
                        df_result = pd.DataFrame(list(counts.items()), columns=["Тип клетки", "Количество"])
                        st.dataframe(df_result, use_container_width=True)
                    else:
                        st.warning("ИИ не нашел знакомых клеток на этой фотографии.")
                        
                except Exception as e:
                    st.error(f"Ошибка подключения к Roboflow: {e}")
"
VERSION_NUM = 1  # Номер версии твоей модели

@st.cache_resource
def get_model():
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project(PROJECT_ID)
    return project.version(VERSION_NUM).model

# ==========================================
# 2. ЗАГРУЗКА СНИМКА КРОВИ
# ==========================================
st.subheader("1. Загрузите снимок с микроскопа")
uploaded_file = st.file_uploader("Выберите фото крови (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Исходный снимок", use_column_width=True)
    
    # ==========================================
    # 3. РАБОТА ИСКУССТВЕННОГО ИНТЕЛЛЕКТА
    # ==========================================
    with col2:
        st.subheader("2. Результат работы ИИ")
        if st.button("🔬 Проанализировать через ИИ"):
            with st.spinner("ИИ считает клетки крови..."):
                try:
                    # Сохраняем во временный файл
                    image.save("temp_blood.jpg")
                    
                    # Запрос к твоей модели Roboflow
                    model = get_model()
                    prediction = model.predict("temp_blood.jpg", confidence=40, overlap=30)
                    
                    # Сохраняем снимок с нарисованными рамками вокруг клеток
                    prediction.save("result_blood.jpg")
                    st.image("result_blood.jpg", caption="Размеченный ИИ снимок", use_column_width=True)
                    
                    # Получаем список найденных клеток
                    json_data = prediction.json()
                    predictions_list = json_data.get("predictions", [])
                    
                    # Считаем количество каждого типа клеток
                    counts = {}
                    for item in predictions_list:
                        cell_type = item["class"]
                        counts[cell_type] = counts.get(cell_type, 0) + 1
                    
                    st.success(f"Найдено всего клеток: {len(predictions_list)}")
                    
                    # Выводим реальную таблицу подсчета
                    if counts:
                        df_result = pd.DataFrame(list(counts.items()), columns=["Тип клетки", "Количество"])
                        st.dataframe(df_result, use_container_width=True)
                    else:
                        st.warning("ИИ не нашел знакомых клеток на этой фотографии.")
                        
                except Exception as e:
                    st.error(f"Ошибка подключения к Roboflow: {e}")
