import streamlit as st
import pandas as pd
from google import genai

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Plataforma Bromatológica - Rotulado y Sellos", layout="wide")

# --- CONTROL DE ACCESO (LOGIN) ---
CLAVES_VALIDAS = ["bromatologia2026", "catamarca2026", "admin123"]

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.markdown("### Acceso Exclusivo - Capacitación Bromatología")
    st.write("Ingrese la clave provista para acceder a las herramientas técnicas.")
    clave = st.text_input("Clave de acceso / Email habilitado", type="password")
    if st.button("Ingresar"):
        if clave in CLAVES_VALIDAS:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta o usuario no registrado.")

if not st.session_state.autenticado:
    login()
    st.stop()

# --- SI EL USUARIO ESTÁ AUTENTICADO, SE MUESTRA LA PLATAFORMA ---
st.sidebar.success("Sesión iniciada")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.autenticado = False
    st.rerun()

tab1, tab2 = st.tabs(["📊 Calculadora Nutricional & Sellos", "💬 Asistente Técnico Normativo"])

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Composición Centesimal, Porción y Sellos (Ley 27.642)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        peso_cocido = st.number_input("Peso final del producto tras elaboración/cocción (g)", min_value=1.0, value=500.0)
    with col_b:
        porcion = st.number_input("Tamaño de la porción según Anexo CAA (g)", min_value=1.0, value=50.0)

    st.subheader("Ingredientes de la formulación")
    datos_base = [
        {"Ingrediente": "Harina 000", "Gramos": 300.0, "Kcal/100g": 350.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 1.2, "Grasa_Sat_g": 0.3, "Sodio_mg": 2.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Azúcar común", "Gramos": 120.0, "Kcal/100g": 390.0, "Azúcar_Añadido_g": 100.0, "Grasa_Tot_g": 0.0, "Grasa_Sat_g": 0.0, "Sodio_mg": 1.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Margarina vegetal", "Gramos": 80.0, "Kcal/100g": 720.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 80.0, "Grasa_Sat_g": 20.0, "Sodio_mg": 120.0, "Edulcorante": False, "Cafeina": False}
    ]
    df_ing = st.data_editor(pd.DataFrame(datos_base), num_rows="dynamic", use_container_width=True)

    if st.button("Calcular Tabla y Sellos", type="primary"):
        # Cálculo de totales absolutos
        tot_kcal = sum((row["Gramos"] * row["Kcal/100g"]) / 100.0 for _, row in df_ing.iterrows())
        tot_azucar_anadido = sum((row["Gramos"] * row["Azúcar_Añadido_g"]) / 100.0 for _, row in df_ing.iterrows())
        tot_grasa_tot = sum((row["Gramos"] * row["Grasa_Tot_g"]) / 100.0 for _, row in df_ing.iterrows())
        tot_grasa_sat = sum((row["Gramos"] * row["Grasa_Sat_g"]) / 100.0 for _, row in df_ing.iterrows())
        tot_sodio = sum((row["Gramos"] * row["Sodio_mg"]) / 100.0 for _, row in df_ing.iterrows())
        tiene_edulcorante = any(df_ing["Edulcorante"])
        tiene_cafeina = any(df_ing["Cafeina"])

        # Base 100 g
        f_100 = 100.0 / peso_cocido
        c_kcal = tot_kcal * f_100
        c_azucar = tot_azucar_anadido * f_100
        c_grasa_tot = tot_grasa_tot * f_100
        c_grasa_sat = tot_grasa_sat * f_100
        c_sodio = tot_sodio * f_100

        # Evaluación de sellos según Ley 27.642 (Etapa 2)
        sellos = []
        if c_azucar > 0 and c_kcal > 0 and ((c_azucar * 4.0) / c_kcal) >= 0.10:
            sellos.append("EXCESO EN AZÚCARES")
        if c_grasa_tot > 0 and c_kcal > 0 and ((c_grasa_tot * 9.0) / c_kcal) >= 0.30:
            sellos.append("EXCESO EN GRASAS TOTALES")
        if c_grasa_sat > 0 and c_kcal > 0 and ((c_grasa_sat * 9.0) / c_kcal) >= 0.10:
            sellos.append("EXCESO EN GRASAS SATURADAS")
        if c_sodio > 0 and ((c_kcal > 0 and (c_sodio / c_kcal) >= 1.0) or (c_sodio >= 300.0)):
            sellos.append("EXCESO EN SODIO")
        if any(s in ["EXCESO EN AZÚCARES", "EXCESO EN GRASAS TOTALES", "EXCESO EN GRASAS SATURADAS"] for s in sellos) and c_kcal >= 275.0:
            sellos.append("EXCESO EN CALORÍAS")

        st.subheader("Resultados:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Energía (100 g):** {c_kcal:.1f} kcal")
            st.markdown(f"**Energía por porción ({porcion:.0f} g):** {(c_kcal * porcion / 100.0):.1f} kcal")
            st.markdown(f"**Sodio (100 g):** {c_sodio:.1f} mg")
        with c2:
            st.markdown("### Sellos Frontales Obligatorios:")
            if sellos:
                for s in sellos:
                    st.error(f"🛑 **{s}**")
            else:
                st.success("No requiere sellos de advertencia.")

            if tiene_edulcorante:
                st.warning("⚠️ **CONTIENE EDULCORANTES, NO RECOMENDABLE EN NIÑOS/AS**")
            if tiene_cafeina:
                st.warning("⚠️ **CONTIENE CAFEÍNA, EVITAR EN NIÑOS/AS**")

# ==========================================
# PESTAÑA 2: ASISTENTE TÉCNICO NORMATIVO
# ==========================================
with tab2:
    st.header("Asistente Técnico en CAA y Ley 27.642")
    st.write("Escribí tu consulta regulatoria sobre rotulado, porciones, claims o cálculo de sellos.")

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    pregunta = st.chat_input("Escribí tu consulta bromatológica aquí...")
    if pregunta:
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)

        try:
            # Conexión nativa con la API de Gemini
            client = genai.Client()
            system_instruction = (
                "Sos un asesor bromatológico especialista en el Código Alimentario Argentino (CAA Cap. IV y V) "
                "y la Ley 27.642 con su Decreto 151/2022. Respondé de forma técnica, precisa y citando normativa."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=pregunta,
                config=dict(system_instruction=system_instruction)
            )
            respuesta_texto = response.text
        except Exception as e:
            respuesta_texto = "El bot está listo. Recordá configurar la variable GEMINI_API_KEY en los secretos de Streamlit para habilitar respuestas automáticas."

        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
        with st.chat_message("assistant"):
            st.markdown(respuesta_texto)
