response.raise_for_status()
                        res_json = response.json()
                    except requests.RequestException as exc:
                        st.error(f"Не удалось связаться с сервисом анализа: {exc}")
                        st.stop()
                    except ValueError:
                        st.error("Сервис анализа вернул ответ в неизвестном формате.")
                        st.stop()
                    if not isinstance(res_json, dict) or "predictions" not in res_json:
                        st.error("В ответе сервиса нет списка predictions. Проверьте модель и формат ответа.")
                        st.stop()
                    
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
                    st.dataframe(pd.DataFrame(list(counts.items()), columns=["Тип", "Количество"]), use_container_width=True)
                    
                    obs = [t["obs_normal"]]
                    recs = [t["rec_normal"]]
                    
                    save_analysis(
                        st.session_state.get('doc_name'), st.session_state.get('doc_role'), 
                        st.session_state.get('clinic_name'), p_id, p_name, p_dob, "Мужской",
                        len(predictions), counts, obs, recs
                    )
                    
                    # ГЕНЕРАЦИЯ PDF
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
# 6. РАЗДЕЛ: СТАТИСТИКА & СРАВНЕНИЕ
# ==========================================
elif page == t["nav_stats"]:
    st.title(t["comparison_title"])
    
    curr_id = st.session_state.get("selected_patient_id", "115002084")
    p_history = get_patient_history(curr_id)
    
    st.write(f"👤 Пациент: **{st.session_state.get('selected_patient_name', 'Иванов Иван Иванович')}** (ID: {curr_id})")
    
    if p_history.empty:
        st.info("Для этого пациента пока нет сохранённых анализов. Выполните анализ, чтобы увидеть динамику.")
    else:
        st.subheader("Количество обнаруженных объектов по анализам")
        p_history = p_history.copy()
        p_history["timestamp"] = pd.to_datetime(p_history["timestamp"], errors="coerce")
        p_history["total_count"] = pd.to_numeric(p_history["total_count"], errors="coerce")
        chart_data = p_history.dropna(subset=["timestamp", "total_count"]).set_index("timestamp")[["total_count"]]
        if not chart_data.empty:
            st.line_chart(chart_data.rename(columns={"total_count": "Обнаружено объектов"}))

        st.subheader("История анализов")
        display_cols = [
            col for col in
            ["timestamp", "patient_name", "total_count", "doctor_name", "clinic"]
            if col in p_history.columns
        ]
        st.dataframe(p_history[display_cols], use_container_width=True, hide_index=True)

        st.caption(
            "График показывает число объектов, обнаруженных моделью, а не медицинский диагноз. "
            "Сравнение клинических показателей требует подтверждённых лабораторных данных."
        )

# ==========================================
# 7. РАЗДЕЛ: НАСТРОЙКИ
# ==========================================
elif page == t["nav_settings"]:
    st.title(t["nav_settings"])
    with st.form("settings_form"):
        clinic_value = st.text_input("Название клиники", value=st.session_state.get("clinic_name", ""))
        doctor_value = st.text_input("ФИО специалиста", value=st.session_state.get("doc_name", ""))
        role_value = st.text_input("Должность / роль", value=st.session_state.get("doc_role", ""))
        save_settings = st.form_submit_button("Сохранить изменения", use_container_width=True)
    if save_settings:
        st.session_state["clinic_name"] = clinic_value.strip()
        st.session_state["doc_name"] = doctor_value.strip()
        st.session_state["doc_role"] = role_value.strip()
        st.success("Настройки сохранены для текущего сеанса.")
