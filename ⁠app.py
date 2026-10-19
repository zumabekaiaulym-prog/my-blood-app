import streamlit as st
import pandas as pd
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="BloodScan AI", layout="wide")

st.title("BloodScan AI — Гематологический Экспресс-Анализатор")

# Данные пациента (слева в меню)
st.sidebar.header("Данные пациента")
name = st.sidebar.text_input("ФИО Пациента", "Иванов И.И.")
age = st.sidebar.number_input("Возраст", value=30)
gender = st.sidebar.selectbox("Пол", ["Мужской", "Женский"])

col1, col2, col3 = st.columns([1.2, 2, 1.2])

# Колонка 1: Камера
with col1:
    st.subheader("Входное Изображение")
    picture = st.camera_input("Сделать снимок с камеры iPad")
    st.button("Захватить снимок", use_container_width=True)

# Колонка 2: Результаты
with col2:
    st.subheader("Результаты Анализа")
    st.info("ИИ-Маска / Рентген сегментация")
    if picture:
        st.image(picture, caption="Загруженный снимок")
    
    st.subheader("МОРФОЛОГИЯ КЛЕТОК")
    data = {
        "Тип клеток": ["Neutrophils", "Lymphocytes", "Plasmodium (Malaria)"],
        "Кол-во": ["72%", "12%", "0"],
        "Норма": ["47-72%", "19-37%", "0"],
        "Статус": ["Норма", "Понижено", "Не обнаружено"]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# Колонка 3: Логи и Риски
with col3:
    st.subheader("Лог процессов")
    st.code(
        f"[{datetime.now().strftime('%H:%M:%S')}] - Загрузка снимка...\n"
        f"[{datetime.now().strftime('%H:%M:%S')}] - Обработка RGB...\n"
        f"[{datetime.now().strftime('%H:%M:%S')}] - ИИ распознавание завершено.",
        language="bash"
    )
    
    st.subheader("Риски болезней")
    st.warning("• Анемия: Средний риск")
    st.success("• Паразиты: Не обнаружено")
    st.button("Сформировать PDF-отчет", use_container_width=True)
