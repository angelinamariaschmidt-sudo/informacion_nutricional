import streamlit as st
import pandas as pd
from google import genai

st.set_page_config(page_title="Plataforma Bromatológica - Rotulado y Sellos", layout="wide")

# --- CONTROL DE ACCESO ---
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

st.sidebar.success("Sesión iniciada")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.autenticado = False
    st.rerun()

tab1, tab2 = st.tabs(["📊 Calculadora Nutricional & Sellos", "💬 Asistente Técnico Normativo"])

# ==========================================
# BASE DE DATOS DE COMPOSICIÓN (ARGENFOODS / CAA)
# ==========================================
BASE_ALIMENTOS = {
    "Harina de trigo 000": {"kcal": 350.0, "azucar_anadido": 0.0, "grasa_tot": 1.2, "grasa_sat": 0.3, "sodio": 2.0, "edulcorante": False, "cafeina": False},
    "Harina de trigo 0000": {"kcal": 353.0, "azucar_anadido": 0.0, "grasa_tot": 0.9, "grasa_sat": 0.2, "sodio": 2.0, "edulcorante": False, "cafeina": False},
    "Azúcar común": {"kcal": 390.0, "azucar_anadido": 100.0, "grasa_tot": 0.0, "grasa_sat": 0.0, "sodio": 1.0, "edulcorante": False, "cafeina": False},
    "Aceite de girasol": {"kcal": 900.0, "azucar_anadido": 0.0, "grasa_tot": 100.0, "grasa_sat": 11.0, "sodio": 0.0, "edulcorante": False, "cafeina": False},
    "Aceite de maíz": {"kcal": 900.0, "azucar_anadido": 0.0, "grasa_tot": 100.0, "grasa_sat": 13.0, "sodio": 0.0, "edulcorante": False, "cafeina": False},
    "Grasa vacuna refinada": {"kcal": 890.0, "azucar_anadido": 0.0, "grasa_tot": 99.0, "grasa_sat": 48.0, "sodio": 0.0, "edulcorante": False, "cafeina": False},
    "Margarina vegetal": {"kcal": 720.0, "azucar_anadido": 0.0, "grasa_tot": 80.0, "grasa_sat": 20.0, "sodio": 150.0, "edulcorante": False, "cafeina": False},
    "Manteca": {"kcal": 740.0, "azucar_anadido": 0.0, "grasa_tot": 82.0, "grasa_sat": 52.0, "sodio": 15.0, "edulcorante": False, "cafeina": False},
    "Sal común (Cloruro de sodio)": {"kcal": 0.0, "azucar_anadido": 0.0, "grasa_tot": 0.0, "grasa_sat": 0.0, "sodio": 38758.0, "edulcorante": False, "cafeina": False},
    "Agua potable": {"kcal": 0.0, "azucar_anadido": 0.0, "grasa_tot": 0.0, "grasa_sat": 0.0, "sodio": 5.0, "edulcorante": False, "cafeina": False},
    "Huevo entero": {"kcal": 150.0, "azucar_anadido": 0.0, "grasa_tot": 10.0, "grasa_sat": 3.1, "sodio": 140.0, "edulcorante": False, "cafeina": False},
    "Leche entera líquida": {"kcal": 60.0, "azucar_anadido": 0.0, "grasa_tot": 3.0, "grasa_sat": 1.9, "sodio": 50.0, "edulcorante": False, "cafeina": False},
    "Cacao en polvo": {"kcal": 320.0, "azucar_anadido": 0.0, "grasa_tot": 12.0, "grasa_sat": 7.0, "sodio": 20.0, "edulcorante": False, "cafeina": True},
    "Edulcorante no calórico (ej. Estevia)": {"kcal": 0.0, "azucar_anadido": 0.0, "grasa_tot": 0.0, "grasa_sat": 0.0, "sodio": 10.0, "edulcorante": True, "cafeina": False}
}

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Composición Centesimal, Porción y Sellos (Ley 27.642)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        peso_cocido = st.number_input("Peso final tras cocción o merma (g)", min_value=1.0, value=500.0)
    with col_b:
        porcion = st.number_input("Tamaño de la porción según CAA (g)", min_value=1.0, value=50.0)

    st.subheader("1. Agregar ingrediente desde la base de datos")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        ing_elegido = st.selectbox("Seleccionar ingrediente:", list(BASE_ALIMENTOS.keys()))
    with col2:
        gramos_ing = st.number_input("Cantidad (gramos):", min_value=1.0, value=100.0, step=5.0)
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Agregar a la receta"):
            if "receta" not in st.session_state:
                st.session_state.receta = []
            datos = BASE_ALIMENTOS[ing_elegido]
            st.session_state.receta.append({
                "Ingrediente": ing_elegido,
                "Gramos": float(gramos_ing),
                "Kcal/100g": datos["kcal"],
                "Azúcar_Añadido_g": datos["azucar_anadido"],
                "Grasa_Tot_g": datos["grasa_tot"],
                "Grasa_Sat_g": datos["grasa_sat"],
                "Sodio_mg": datos["sodio"],
                "Edulcorante": datos["edulcorante"],
                "Cafeina": datos["cafeina"]
            })
            st.rerun()

    # Receta inicial por defecto si está vacía
    if "receta" not in st.session_state:
        st.session_state.receta = [
            {"Ingrediente": "Harina de trigo 000", "Gramos": 300.0, "Kcal/100g": 350.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 1.2, "Grasa_Sat_g": 0.3, "Sodio_mg": 2.0, "Edulcorante": False, "Cafeina": False},
            {"Ingrediente": "Sal común (Cloruro de sodio)", "Gramos": 10.0, "Kcal/100g": 0.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 0.0, "Grasa_Sat_g": 0.0, "Sodio_mg": 38758.0, "Edulcorante": False, "Cafeina": False},
            {"Ingrediente": "Grasa vacuna refinada", "Gramos": 80.0, "Kcal/100g": 890.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 99.0, "Grasa_Sat_g": 48.0, "Sodio_mg": 0.0, "Edulcorante": False, "Cafeina": False}
        ]

    st.subheader("2. Formulación actual (editable)")
    df_actual = pd.DataFrame(st.session_state.receta)
    df_editado = st.data_editor(df_actual, num_rows="dynamic", use_container_width=True)

    col_btn1, col_btn2 = st.columns([2, 8])
    with col_btn1:
        calcular = st.button("Calcular Tabla y Sellos", type="primary")
    with col_btn2:
        if st.button("Vaciar receta"):
            st.session_state.receta = []
            st.rerun()

    if calcular:
        # Reemplazo preventivo de None por 0 para evitar errores de NaN
        df_limpio = df_editado.fillna(0)
        
        tot_kcal = sum((float(row["Gramos"]) * float(row["Kcal/100g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_azucar = sum((float(row["Gramos"]) * float(row["Azúcar_Añadido_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_grasa_tot = sum((float(row["Gramos"]) * float(row["Grasa_Tot_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_grasa_sat = sum((float(row["Gramos"]) * float(row["Grasa_Sat_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_sodio = sum((float(row["Gramos"]) * float(row["Sodio_mg"])) / 100.0 for _, row in df_limpio.iterrows())
        tiene_edulcorante = any(df_limpio["Edulcorante"])
        tiene_cafeina = any(df_limpio["Cafeina"])

        f_100 = 100.0 / peso_cocido
        c_kcal = tot_kcal * f_100
        c_azucar = tot_azucar * f_100
        c_grasa_tot = tot_grasa_tot * f_100
        c_grasa_sat = tot_grasa_sat * f_100
        c_sodio = tot_sodio * f_100

        # Algoritmo Ley 27.642 (Etapa 2 definitiva / Perfil OPS)
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

        st.markdown("---")
        st.subheader("Resultados del Análisis:")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"**Valor Energético (100 g):** {c_kcal:.1f} kcal")
            st.markdown(f"**Valor Energético por Porción ({porcion:.0f} g):** {(c_kcal * porcion / 100.0):.1f} kcal")
            st.markdown(f"**Azúcares añadidos (100 g):** {c_azucar:.1f} g")
            st.markdown(f"**Grasas Totales (100 g):** {c_grasa_tot:.1f} g")
            st.markdown(f"**Grasas Saturadas (100 g):** {c_grasa_sat:.1f} g")
            st.markdown(f"**Sodio (100 g):** {c_sodio:.1f} mg")
        with r2:
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
# PESTAÑA 2: ASISTENTE TÉCNICO
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
        except Exception:
            respuesta_texto = "El bot está listo. Recordá configurar la variable GEMINI_API_KEY en los secretos de Streamlit para habilitar respuestas automáticas."

        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
        with st.chat_message("assistant"):
            st.markdown(respuesta_texto)
