import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ============================================================
# НАСТРОЙКИ
# ============================================================

st.set_page_config(
    page_title="BloodScan AI",
    page_icon="🩸",
    layout="wide"
)

DATA_FILE = "patients.json"


# ============================================================
# ЛОКАЛЬНОЕ ХРАНЕНИЕ
# ============================================================

def load_patients():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {}


def save_patients(patients):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(patients, file, ensure_ascii=False, indent=4)


patients = load_patients()


# ============================================================
# СОЗДАНИЕ ПАЦИЕНТА
# ============================================================

def create_patient(name, age, gender):
    patient_id = f"Patient #{len(patients) + 1:03d}"

    patients[patient_id] = {
        "name": name,
        "age": age,
        "gender": gender,
        "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "analyses": []
    }

    save_patients(patients)
    return patient_id


# ============================================================
# АНАЛИЗ
# ============================================================

def demo_analysis(neutrophils, lymphocytes, plasmodium):
    results = []

    # Нейтрофилы
    if 47 <= neutrophils <= 72:
        neut_status = "Норма"
    elif neutrophils < 47:
        neut_status = "Понижено"
    else:
        neut_status = "Повышено"

    # Лимфоциты
    if 19 <= lymphocytes <= 37:
        lymph_status = "Норма"
    elif lymphocytes < 19:
        lymph_status = "Понижено"
    else:
        lymph_status = "Повышено"

    # Плазмодий
    if plasmodium == 0:
        parasite_status = "Не обнаружено"
    else:
        parasite_status = "Обнаружено"

    results.append({
        "Тип клеток": "Neutrophils",
        "Значение": f"{neutrophils}%",
        "Референс": "47–72%",
        "Статус": neut_status
    })

    results.append({
        "Тип клеток": "Lymphocytes",
        "Значение": f"{lymphocytes}%",
        "Референс": "19–37%",
        "Статус": lymph_status
    })

    results.append({
        "Тип клеток": "Plasmodium",
        "Значение": str(plasmodium),
        "Референс": "0",
        "Статус": parasite_status
    })

    # Демонстрационный общий вывод
    abnormal = sum(
        1 for item in results
        if item["Статус"] not in ["Норма", "Не обнаружено"]
    )

    if abnormal == 0:
        conclusion = "Значимых отклонений в демонстрационных данных не обнаружено."
        risk = "Низкий"
    elif abnormal == 1:
        conclusion = "Обнаружено одно отклонение. Требуется дополнительная оценка."
        risk = "Средний"
    else:
        conclusion = "Обнаружено несколько отклонений. Требуется медицинская оценка."
        risk = "Высокий"

    return results, conclusion, risk


# ============================================================
# ЗАГОЛОВОК
# ============================================================

st.title("🩸 BloodScan AI")
st.caption("Портативная система экспресс-анализа крови — демонстрационный прототип")


# ============================================================
# БОКОВОЕ МЕНЮ
# ============================================================

st.sidebar.header("👥 Пациенты")

patient_list = list(patients.keys())

if patient_list:
    selected_patient = st.sidebar.selectbox(
        "Выберите пациента",
        patient_list
    )
else:
    selected_patient = None
    st.sidebar.info("Пациентов пока нет.")


st.sidebar.divider()

st.sidebar.subheader("➕ Новый пациент")

new_name = st.sidebar.text_input(
    "Имя / ID пациента",
    placeholder="Patient 001"
)

new_age = st.sidebar.number_input(
    "Возраст",
    min_value=0,
    max_value=120,
    value=18
)

new_gender = st.sidebar.selectbox(
    "Пол",
    ["Мужской", "Женский", "Не указан"]
)

if st.sidebar.button("Создать пациента", use_container_width=True):

    if new_name.strip():
        new_id = create_patient(
            new_name,
            new_age,
            new_gender
        )

        st.sidebar.success(f"{new_id} создан")
        st.rerun()
    else:
        st.sidebar.error("Введите имя или ID пациента.")


# ============================================================
# ЕСЛИ НЕТ ПАЦИЕНТОВ
# ============================================================

if not selected_patient:

    st.info(
        "Создайте первого пациента в меню слева, "
        "чтобы начать анализ."
    )

    st.markdown("""
    ### Возможности прототипа

    🩸 Анализ тестовых показателей крови  
    👥 Несколько пациентов  
    💾 Локальное сохранение данных  
    📊 История анализов  
    📷 Загрузка изображения  
    🏕️ Возможность работы без интернета при локальном запуске
    """)

    st.stop()


# ============================================================
# ДАННЫЕ ПАЦИЕНТА
# ============================================================

patient = patients[selected_patient]

col1, col2, col3 = st.columns([1.2, 2, 1.2])


# ============================================================
# КОЛОНКА 1 — ПАЦИЕНТ И ИЗОБРАЖЕНИЕ
# ============================================================

with col1:

    st.subheader("👤 Пациент")

    st.write(f"**ID:** {selected_patient}")
    st.write(f"**Имя:** {patient['name']}")
    st.write(f"**Возраст:** {patient['age']}")
    st.write(f"**Пол:** {patient['gender']}")

    st.divider()

    st.subheader("📷 Снимок")

    picture = st.camera_input(
        "Сделать снимок"
    )

    uploaded_picture = st.file_uploader(
        "Или загрузить изображение",
        type=["png", "jpg", "jpeg"]
    )

    if picture:
        st.image(
            picture,
            caption="Снимок с камеры",
            use_container_width=True
        )

    elif uploaded_picture:
        st.image(
            uploaded_picture,
            caption="Загруженное изображение",
            use_container_width=True
        )


# ============================================================
# КОЛОНКА 2 — ПОКАЗАТЕЛИ
# ============================================================

with col2:

    st.subheader("🔬 Показатели анализа")

    st.caption(
        "Демонстрационные значения. "
        "Они не являются результатом реального медицинского анализа."
    )

    neutrophils = st.number_input(
        "Neutrophils (%)",
        min_value=0.0,
        max_value=100.0,
        value=72.0,
        step=0.1
    )

    lymphocytes = st.number_input(
        "Lymphocytes (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=0.1
    )

    plasmodium = st.number_input(
        "Plasmodium",
        min_value=0,
        max_value=1,
        value=0,
        step=1
    )

    if st.button(
        "🧠 Запустить анализ",
        use_container_width=True
    ):

        results, conclusion, risk = demo_analysis(
            neutrophils,
            lymphocytes,
            plasmodium
        )

        analysis = {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "results": results,
            "conclusion": conclusion,
            "risk": risk
        }

        patients[selected_patient]["analyses"].append(
            analysis
        )

        save_patients(patients)

        st.success("Анализ сохранён!")

        st.session_state["last_analysis"] = analysis


# ============================================================
# ПОСЛЕДНИЙ РЕЗУЛЬТАТ
# ============================================================

with col2:

    if patients[selected_patient]["analyses"]:

        last_analysis = patients[selected_patient]["analyses"][-1]

        st.divider()
        st.subheader("📊 Последний результат")

        df = pd.DataFrame(
            last_analysis["results"]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.write(
            f"**Уровень внимания:** {last_analysis['risk']}"
        )

        st.info(
            last_analysis["conclusion"]
        )

        st.warning(
            "⚠️ Это демонстрационный вывод прототипа, "
            "а не медицинский диагноз."
        )


# ============================================================
# КОЛОНКА 3 — ИСТОРИЯ
# ============================================================

with col3:

    st.subheader("📋 История")

    analyses = patient["analyses"]

    if analyses:

        st.write(
            f"Всего анализов: **{len(analyses)}**"
        )

        for i, analysis in enumerate(
            reversed(analyses),
            start=1
        ):

            with st.expander(
                f"Анализ #{len(analyses) - i + 1} — "
                f"{analysis['date']}"
            ):

                st.write(
                    f"Уровень внимания: **{analysis['risk']}**"
                )

                history_df = pd.DataFrame(
                    analysis["results"]
                )

                st.dataframe(
                    history_df,
                    use_container_width=True,
                    hide_index=True
                )

    else:

        st.info(
            "У этого пациента пока нет анализов."
        )


# ============================================================
# СТАТУС СИСТЕМЫ
# ============================================================

st.divider()

st.subheader("🏕️ Статус системы")

c1, c2, c3 = st.columns(3)

with c1:
    st.success("💾 Локальное сохранение")

with c2:
    st.success("👥 Несколько пациентов")

with c3:
    st.success("📊 История анализов")


st.caption(
    "Примечание: для полноценной медицинской системы "
    "алгоритм диагностики должен быть клинически валидирован."
)
