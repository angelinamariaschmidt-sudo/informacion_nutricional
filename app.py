import streamlit as st
import pandas as pd
import requests
import urllib.parse
import unicodedata
import os
import base64

st.set_page_config(page_title="Plataforma Bromatológica - Ecomeg", layout="wide")

# --- CONTROL DE ACCESO ---
CLAVES_VALIDAS = ["bromatologia2026", "ecomeg2026", "infonutri2026"]

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

def normalizar(texto):
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto).lower()) if unicodedata.category(c) != 'Mn')

def obtener_imagen_base64():
    # Nombres posibles con los que pudo haberse subido el archivo a GitHub
    posibles_nombres = [
        "Logo ECOMEG Transparente.png",
        "Logo ECOMEG Transparente.PNG",
        "Logo Ecomeg Transparente.png",
        "logo_ecomeg.png",
        "ecomeg (R).png",
        "Logo ECOMEG Transparente.jpg",
        "Logo ECOMEG Transparente.jpeg"
    ]
    for nombre in posibles_nombres:
        if os.path.exists(nombre):
            with open(nombre, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    return ""

# ==============================================================================
# BASE DE DATOS MATRIZ: SARA 2 (Ministerio de Salud de la Nación / ENNyS 2)
# ==============================================================================
SARA2_DICT = {
    # Aceites y Grasas
    "Aceite de girasol": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de girasol alto oleico": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 9.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de maíz": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 2.0, "edulc": False, "caf": False},
    "Aceite de oliva virgen extra": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 17.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de soja": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.65, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de canola": {"kcal": 892.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.1, "gsat": 7.37, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de coco": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 82.48, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de chía": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 9.86, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite comestible mezcla": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.83, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada / primer jugo": {"kcal": 899.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.9, "gsat": 49.8, "gtrans": 3.7, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa de cerdo refinada": {"kcal": 898.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.8, "gsat": 39.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Manteca de vaca": {"kcal": 758.0, "cho": 0.1, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 0.5, "gtot": 84.0, "gsat": 50.93, "gtrans": 3.28, "fibra": 0.0, "sodio": 223.0, "edulc": False, "caf": False},
    "Margarina vegetal": {"kcal": 559.0, "cho": 0.7, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.2, "gtot": 61.7, "gsat": 27.6, "gtrans": 0.88, "fibra": 0.0, "sodio": 295.0, "edulc": False, "caf": False},

    # Verduras
    "Acelga, cruda": {"kcal": 18.0, "cho": 2.1, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.6, "sodio": 213.0, "edulc": False, "caf": False},
    "Acelga, hervida": {"kcal": 16.0, "cho": 2.0, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.9, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 2.1, "sodio": 179.0, "edulc": False, "caf": False},
    "Ajo, crudo": {"kcal": 91.0, "cho": 17.9, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 4.4, "gtot": 0.2, "gsat": 0.09, "gtrans": 0.0, "fibra": 2.1, "sodio": 17.0, "edulc": False, "caf": False},
    "Cebolla, cruda": {"kcal": 36.0, "cho": 7.6, "azuc_tot": 1.7, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.1, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.7, "sodio": 4.0, "edulc": False, "caf": False},
    "Espinaca, cruda": {"kcal": 21.0, "cho": 1.43, "azuc_tot": 0.42, "azuc_anad": 0.0, "prot": 2.86, "gtot": 0.39, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.2, "sodio": 79.0, "edulc": False, "caf": False},
    "Espinaca, hervida": {"kcal": 20.0, "cho": 1.35, "azuc_tot": 0.43, "azuc_anad": 0.0, "prot": 2.97, "gtot": 0.26, "gsat": 0.109, "gtrans": 0.0, "fibra": 2.4, "sodio": 70.0, "edulc": False, "caf": False},
    "Papa, cruda": {"kcal": 79.0, "cho": 16.9, "azuc_tot": 1.2, "azuc_anad": 0.0, "prot": 2.7, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 2.4, "sodio": 24.0, "edulc": False, "caf": False},
    "Papa, hervida": {"kcal": 81.0, "cho": 18.2, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 1.7, "gtot": 0.1, "gsat": 0.03, "gtrans": 0.0, "fibra": 0.9, "sodio": 5.0, "edulc": False, "caf": False},
    "Tomate, crudo": {"kcal": 17.0, "cho": 2.9, "azuc_tot": 1.2, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.2, "sodio": 5.0, "edulc": False, "caf": False},
    "Zanahoria, cruda": {"kcal": 43.0, "cho": 4.7, "azuc_tot": 2.8, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.2, "gsat": 0.01, "gtrans": 0.0, "fibra": 4.5, "sodio": 22.0, "edulc": False, "caf": False},
    "Zapallo, crudo": {"kcal": 36.0, "cho": 2.5, "azuc_tot": 1.3, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.1, "gsat": 0.07, "gtrans": 0.0, "fibra": 5.3, "sodio": 3.0, "edulc": False, "caf": False},

    # Cereales, Sémolas y Harinas
    "Sémola de trigo / Semolín candeal": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Semolín para pastas secas o frescas": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Gluten puro de trigo en polvo": {"kcal": 370.0, "cho": 13.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 75.0, "gtot": 1.9, "gsat": 0.3, "gtrans": 0.0, "fibra": 1.5, "sodio": 70.0, "edulc": False, "caf": False},
    "Harina de trigo 000 fortificada": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo 0000 fortificada": {"kcal": 353.0, "cho": 74.0, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 11.6, "gtot": 0.9, "gsat": 0.15, "gtrans": 0.0, "fibra": 2.5, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo integral": {"kcal": 308.0, "cho": 58.8, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 11.4, "gtot": 3.0, "gsat": 0.43, "gtrans": 0.0, "fibra": 12.6, "sodio": 16.0, "edulc": False, "caf": False},
    "Harina leudante": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 714.0, "edulc": False, "caf": False},
    "Avena arrollada instantánea": {"kcal": 357.0, "cho": 56.9, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 15.6, "gtot": 7.5, "gsat": 1.52, "gtrans": 0.0, "fibra": 10.4, "sodio": 2.0, "edulc": False, "caf": False},
    "Almidón de maíz (Maicena)": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Fécula / Almidón de mandioca": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Premezcla universal SIN TACC": {"kcal": 357.0, "cho": 82.5, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 2.8, "gtot": 1.8, "gsat": 1.0, "gtrans": 0.0, "fibra": 1.0, "sodio": 40.0, "edulc": False, "caf": False},

    # Lácteos y Huevos
    "Leche entera líquida": {"kcal": 58.0, "cho": 4.8, "azuc_tot": 4.8, "azuc_anad": 0.0, "prot": 3.1, "gtot": 2.9, "gsat": 1.87, "gtrans": 0.13, "fibra": 0.0, "sodio": 57.0, "edulc": False, "caf": False},
    "Leche entera en polvo": {"kcal": 480.0, "cho": 38.4, "azuc_tot": 38.4, "azuc_anad": 0.0, "prot": 25.8, "gtot": 24.8, "gsat": 15.54, "gtrans": 1.06, "fibra": 0.0, "sodio": 404.0, "edulc": False, "caf": False},
    "Huevo entero": {"kcal": 156.0, "cho": 0.4, "azuc_tot": 0.4, "azuc_anad": 0.0, "prot": 12.0, "gtot": 11.8, "gsat": 3.18, "gtrans": 0.0, "fibra": 0.0, "sodio": 135.0, "edulc": False, "caf": False},
    "Queso Cremoso": {"kcal": 310.0, "cho": 2.5, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 20.4, "gtot": 24.9, "gsat": 13.66, "gtrans": 0.73, "fibra": 0.0, "sodio": 704.0, "edulc": False, "caf": False},
    "Queso Muzzarella": {"kcal": 278.0, "cho": 2.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 23.6, "gtot": 19.3, "gsat": 13.9, "gtrans": 0.58, "fibra": 0.0, "sodio": 486.0, "edulc": False, "caf": False},

    # Azúcares y Condimentos
    "Azúcar blanca refinada común": {"kcal": 400.0, "cho": 100.0, "azuc_tot": 99.8, "azuc_anad": 99.8, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Sal fina de mesa común (NaCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 40000.0, "edulc": False, "caf": False},
    "Agua potable": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 5.0, "edulc": False, "caf": False}
}

lista_alimentos_completa = sorted(list(SARA2_DICT.keys()))

def receta_inicial():
    return [
        {"Ingrediente": "Sémola de trigo / Semolín candeal", "Gramos": 300.0, "Kcal": 336.0, "Carbohidratos_g": 72.8, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 12.7, "Grasa_Tot_g": 1.1, "Grasa_Sat_g": 0.15, "Grasa_Trans_g": 0.0, "Fibra_g": 3.9, "Sodio_mg": 1.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Aceite de girasol", "Gramos": 30.0, "Kcal": 900.0, "Carbohidratos_g": 0.0, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 0.0, "Grasa_Tot_g": 100.0, "Grasa_Sat_g": 10.6, "Grasa_Trans_g": 0.0, "Fibra_g": 0.0, "Sodio_mg": 0.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Sal fina de mesa común (NaCl)", "Gramos": 5.0, "Kcal": 0.0, "Carbohidratos_g": 0.0, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 0.0, "Grasa_Tot_g": 0.0, "Grasa_Sat_g": 0.0, "Grasa_Trans_g": 0.0, "Fibra_g": 0.0, "Sodio_mg": 40000.0, "Edulcorante": False, "Cafeina": False}
    ]

if "receta" not in st.session_state or not isinstance(st.session_state.receta, list):
    st.session_state.receta = receta_inicial()
else:
    if st.session_state.receta and "Carbohidratos_g" not in st.session_state.receta[0]:
        st.session_state.receta = receta_inicial()

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Rotulado Nutricional y Sellos (CAA Cap. V & Ley 27.642)")
    
    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
    with col_p1:
        nombre_producto = st.text_input("Denominación de venta del producto elaborado:", value="Fideos Secos de Semolín Candeal")
    with col_p2:
        peso_cocido = st.number_input("Peso neto final / cocido (g)", min_value=1.0, value=500.0)
    with col_p3:
        porcion = st.number_input("Porción reglamentaria CAA (g)", min_value=1.0, value=80.0)

    st.markdown("---")
    st.subheader("1. Selección y Búsqueda de Ingredientes (Prioridad: SARA 2)")

    c_f1, c_f2 = st.columns([2, 3])
    with c_f1:
        filtro_texto = st.text_input("Filtrar por letras o palabras:", placeholder="Ej: aceite, acelga, semola, gluten, grasa...")

    if filtro_texto.strip():
        termino_norm = normalizar(filtro_texto.strip())
        opciones_filtradas = [ali for ali in lista_alimentos_completa if termino_norm in normalizar(ali)]
    else:
        opciones_filtradas = lista_alimentos_completa

    with c_f2:
        if opciones_filtradas:
            ing_elegido = st.selectbox(f"Ingredientes de SARA 2 ({len(opciones_filtradas)} encontrados):", opciones_filtradas)
        else:
            st.warning("No encontrado en SARA 2. Utilizá los buscadores de referencia externa abajo.")
            ing_elegido = None

    if ing_elegido:
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            gramos_ing = st.number_input(f"Gramos de '{ing_elegido}' a formular:", min_value=0.1, value=100.0, step=5.0)
        with col_g2:
            st.write("")
            st.write("")
            if st.button("➕ Agregar a la receta"):
                datos = SARA2_DICT[ing_elegido]
                st.session_state.receta.append({
                    "Ingrediente": ing_elegido,
                    "Gramos": float(gramos_ing),
                    "Kcal": float(datos["kcal"]),
                    "Carbohidratos_g": float(datos["cho"]),
                    "Azucares_Tot_g": float(datos["azuc_tot"]),
                    "Azucar_Anadido_g": float(datos["azuc_anad"]),
                    "Proteinas_g": float(datos["prot"]),
                    "Grasa_Tot_g": float(datos["gtot"]),
                    "Grasa_Sat_g": float(datos["gsat"]),
                    "Grasa_Trans_g": float(datos["gtrans"]),
                    "Fibra_g": float(datos["fibra"]),
                    "Sodio_mg": float(datos["sodio"]),
                    "Edulcorante": bool(datos["edulc"]),
                    "Cafeina": bool(datos["caf"])
                })
                st.success(f"'{ing_elegido}' sumado a la formulación.")
                st.rerun()

    # Panel de acceso a bases de respaldo
    with st.expander("🌐 Bases de Datos Internacionales y Comerciales de Respaldo"):
        st.write("Si el alimento o marca no figura en SARA 2, consultá estas bases oficiales de referencia:")
        busq_term = filtro_texto.strip() if filtro_texto else "alimento"
        term_enc = urllib.parse.quote(busq_term)

        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown("**ARGENFOODS (UNLu / Arg)**")
            st.link_button("Abrir ARGENFOODS", "http://www.argenfoods.unlu.edu.ar/Tablas/Tabla.htm")
        with b2:
            st.markdown("**FatSecret Argentina (Marcas)**")
            st.link_button(f"Buscar '{busq_term}'", f"https://www.fatsecret.com.ar/calor%C3%ADas-nutrici%C3%B3n/search?q={term_enc}")
        with b3:
            st.markdown("**Dieta y Nutrición**")
            st.link_button(f"Buscar '{busq_term}'", f"https://www.dietaynutricion.net/tabla-de-calorias-nutricional/?q={term_enc}")

    # Formulario manual para insumos externos
    with st.expander("➕ Cargar ingrediente manual o desde otra base (valores cada 100 g)"):
        c_m1, c_m2, c_m3 = st.columns([3, 2, 2])
        with c_m1:
            nombre_man = st.text_input("Nombre del ingrediente / insumo:")
        with c_m2:
            gramos_man = st.number_input("Gramos usados:", min_value=0.1, value=50.0, step=5.0)
        with c_m3:
            kcal_man = st.number_input("Kcal / 100g:", min_value=0.0, value=250.0)

        c_m4, c_m5, c_m6, c_m7 = st.columns(4)
        with c_m4:
            cho_man = st.number_input("Carbohidratos (g/100g):", min_value=0.0, value=30.0)
        with c_m5:
            azuc_tot_man = st.number_input("Azúcares totales (g/100g):", min_value=0.0, value=5.0)
        with c_m6:
            azuc_anad_man = st.number_input("Azúcares añadidos (g/100g):", min_value=0.0, value=0.0)
        with c_m7:
            prot_man = st.number_input("Proteínas (g/100g):", min_value=0.0, value=8.0)

        c_m8, c_m9, c_m10, c_m11 = st.columns(4)
        with c_m8:
            gtot_man = st.number_input("Grasas totales (g/100g):", min_value=0.0, value=2.0)
        with c_m9:
            gsat_man = st.number_input("Grasas saturadas (g/100g):", min_value=0.0, value=0.5)
        with c_m10:
            gtrans_man = st.number_input("Grasas trans (g/100g):", min_value=0.0, value=0.0)
        with c_m11:
            fibra_man = st.number_input("Fibra alimentaria (g/100g):", min_value=0.0, value=2.0)

        c_m12, c_m13, c_m14 = st.columns([2, 1, 1])
        with c_m12:
            sodio_man = st.number_input("Sodio (mg/100g):", min_value=0.0, value=50.0)
        with c_m13:
            edulc_man = st.checkbox("¿Edulcorante?")
        with c_m14:
            caf_man = st.checkbox("¿Cafeína?")

        if st.button("📥 Incorporar a la receta"):
            if nombre_man.strip():
                st.session_state.receta.append({
                    "Ingrediente": nombre_man.strip(),
                    "Gramos": float(gramos_man),
                    "Kcal": float(kcal_man),
                    "Carbohidratos_g": float(cho_man),
                    "Azucares_Tot_g": float(azuc_tot_man),
                    "Azucar_Anadido_g": float(azuc_anad_man),
                    "Proteinas_g": float(prot_man),
                    "Grasa_Tot_g": float(gtot_man),
                    "Grasa_Sat_g": float(gsat_man),
                    "Grasa_Trans_g": float(gtrans_man),
                    "Fibra_g": float(fibra_man),
                    "Sodio_mg": float(sodio_man),
                    "Edulcorante": bool(edulc_man),
                    "Cafeina": bool(caf_man)
                })
                st.success(f"'{nombre_man}' agregado.")
                st.rerun()
            else:
                st.warning("Completá el nombre del producto.")

    st.markdown("---")
    st.subheader("2. Formulación del producto (tabla editable)")
    df_actual = pd.DataFrame(st.session_state.receta)
    df_editado = st.data_editor(df_actual, num_rows="dynamic", use_container_width=True)

    col_btn1, col_btn2 = st.columns([2, 8])
    with col_btn1:
        calcular = st.button("Calcular Tabla y Sellos", type="primary")
    with col_btn2:
        if st.button("Vaciar formulación"):
            st.session_state.receta = []
            st.rerun()

    if calcular:
        df_limpio = df_editado.fillna(0)
        
        def val(row, key_nueva, key_vieja=None):
            if key_nueva in row:
                return float(row[key_nueva])
            if key_vieja and key_vieja in row:
                return float(row[key_vieja])
            return 0.0

        tot_kcal = sum((val(row, "Gramos") * val(row, "Kcal", "Kcal/100g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_cho = sum((val(row, "Gramos") * val(row, "Carbohidratos_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_azuc_tot = sum((val(row, "Gramos") * val(row, "Azucares_Tot_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_azuc_anad = sum((val(row, "Gramos") * val(row, "Azucar_Anadido_g", "Azúcar_Añadido_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_prot = sum((val(row, "Gramos") * val(row, "Proteinas_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_gtot = sum((val(row, "Gramos") * val(row, "Grasa_Tot_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_gsat = sum((val(row, "Gramos") * val(row, "Grasa_Sat_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_gtrans = sum((val(row, "Gramos") * val(row, "Grasa_Trans_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_fibra = sum((val(row, "Gramos") * val(row, "Fibra_g")) / 100.0 for _, row in df_limpio.iterrows())
        tot_sodio = sum((val(row, "Gramos") * val(row, "Sodio_mg")) / 100.0 for _, row in df_limpio.iterrows())
        
        tiene_edulcorante = any(bool(row.get("Edulcorante", False)) for _, row in df_limpio.iterrows())
        tiene_cafeina = any(bool(row.get("Cafeina", False)) for _, row in df_limpio.iterrows())

        # Concentración cada 100 g
        f_100 = 100.0 / peso_cocido
        c_kcal = tot_kcal * f_100
        c_kj = c_kcal * 4.184
        c_cho = tot_cho * f_100
        c_azuc_tot = tot_azuc_tot * f_100
        c_azuc_anad = tot_azuc_anad * f_100
        c_prot = tot_prot * f_100
        c_gtot = tot_gtot * f_100
        c_gsat = tot_gsat * f_100
        c_gtrans = tot_gtrans * f_100
        c_fibra = tot_fibra * f_100
        c_sodio = tot_sodio * f_100

        # Valores por porción
        f_porc = porcion / 100.0
        p_kcal = c_kcal * f_porc
        p_kj = c_kj * f_porc
        p_cho = c_cho * f_porc
        p_azuc_tot = c_azuc_tot * f_porc
        p_azuc_anad = c_azuc_anad * f_porc
        p_prot = c_prot * f_porc
        p_gtot = c_gtot * f_porc
        p_gsat = c_gsat * f_porc
        p_gtrans = c_gtrans * f_porc
        p_fibra = c_fibra * f_porc
        p_sodio = c_sodio * f_porc

        # %VD (CAA Cap. V)
        vd_kcal = round((p_kcal / 2000.0) * 100)
        vd_cho = round((p_cho / 300.0) * 100)
        vd_prot = round((p_prot / 75.0) * 100)
        vd_gtot = round((p_gtot / 55.0) * 100)
        vd_gsat = round((p_gsat / 22.0) * 100)
        vd_fibra = round((p_fibra / 25.0) * 100)
        vd_sodio = round((p_sodio / 2000.0) * 100)

        # Algoritmo Ley 27.642
        sellos = []
        if c_azuc_anad > 0 and c_kcal > 0 and ((c_azuc_anad * 4.0) / c_kcal) >= 0.10:
            sellos.append("EXCESO EN AZÚCARES")
        if c_gtot > 0 and c_kcal > 0 and ((c_gtot * 9.0) / c_kcal) >= 0.30:
            sellos.append("EXCESO EN GRASAS TOTALES")
        if c_gsat > 0 and c_kcal > 0 and ((c_gsat * 9.0) / c_kcal) >= 0.10:
            sellos.append("EXCESO EN GRASAS SATURADAS")
        if c_sodio > 0 and ((c_kcal > 0 and (c_sodio / c_kcal) >= 1.0) or (c_sodio >= 300.0)):
            sellos.append("EXCESO EN SODIO")
        if any(s in ["EXCESO EN AZÚCARES", "EXCESO EN GRASAS TOTALES", "EXCESO EN GRASAS SATURADAS"] for s in sellos) and c_kcal >= 275.0:
            sellos.append("EXCESO EN CALORÍAS")

        st.markdown("---")
        st.subheader("Resultados del Rótulo y Evaluación Normativa:")

        r1, r2 = st.columns([3, 2])
        with r1:
            st.markdown(f"#### **INFORMACIÓN NUTRICIONAL (Porción: {porcion:.0f} g)**")
            
            tabla_rotulo = pd.DataFrame({
                "Nutriente": [
                    "Valor energético",
                    "Carbohidratos",
                    "  de los cuales: Azúcares totales",
                    "  Azúcares añadidos",
                    "Proteínas",
                    "Grasas totales",
                    "Grasas saturadas",
                    "Grasas trans",
                    "Fibra alimentaria",
                    "Sodio"
                ],
                "Cada 100 g": [
                    f"{c_kcal:.0f} kcal = {c_kj:.0f} kJ",
                    f"{c_cho:.1f} g",
                    f"{c_azuc_tot:.1f} g",
                    f"{c_azuc_anad:.1f} g",
                    f"{c_prot:.1f} g",
                    f"{c_gtot:.1f} g",
                    f"{c_gsat:.1f} g",
                    f"{c_gtrans:.1f} g",
                    f"{c_fibra:.1f} g",
                    f"{c_sodio:.1f} mg"
                ],
                f"Por porción ({porcion:.0f} g)": [
                    f"{p_kcal:.0f} kcal = {p_kj:.0f} kJ",
                    f"{p_cho:.1f} g",
                    f"{p_azuc_tot:.1f} g",
                    f"{p_azuc_anad:.1f} g",
                    f"{p_prot:.1f} g",
                    f"{p_gtot:.1f} g",
                    f"{p_gsat:.1f} g",
                    f"{p_gtrans:.1f} g",
                    f"{p_fibra:.1f} g",
                    f"{p_sodio:.1f} mg"
                ],
                "%VD*": [
                    f"{vd_kcal}%",
                    f"{vd_cho}%",
                    "-",
                    "-",
                    f"{vd_prot}%",
                    f"{vd_gtot}%",
                    f"{vd_gsat}%",
                    "-",
                    f"{vd_fibra}%",
                    f"{vd_sodio}%"
                ]
            })
            st.table(tabla_rotulo)
            st.caption("*% Valores Diarios con base a una dieta de 2.000 kcal u 8.400 kJ (CAA Cap. V).")

        with r2:
            st.markdown("### Sellos Frontales y Advertencias (Ley 27.642):")
            if sellos:
                for s in sellos:
                    st.error(f"🛑 **{s}**")
            else:
                st.success("No requiere sellos de advertencia.")

            if tiene_edulcorante:
                st.warning("⚠️ **CONTIENE EDULCORANTES, NO RECOMENDABLE EN NIÑOS/AS**")
            if tiene_cafeina:
                st.warning("⚠️ **CONTIENE CAFEÍNA, EVITAR EN NIÑOS/AS**")

        # ==============================================================================
        # SECCIÓN DE IMPRESIÓN OFICIAL CON LOGO ECOMEG
        # ==============================================================================
        st.markdown("---")
        st.subheader("🖨️ Informe Oficial de Rotulado Nutricional para Impresión")

        logo_b64 = obtener_imagen_base64()
        if logo_b64:
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 75px; width: auto; object-fit: contain; margin-bottom: 10px;" />'
        else:
            logo_html = '<h2 style="color: #2E7D32; margin: 0; font-family: sans-serif;">Ecomeg®</h2>'

        sellos_html = ""
        if sellos:
            sellos_html += '<div style="margin-top: 15px;">'
            for s in sellos:
                sellos_html += f'<span style="background-color: #000; color: #fff; padding: 6px 12px; margin-right: 8px; font-weight: bold; border-radius: 4px; display: inline-block; margin-bottom: 5px; font-size: 13px;">🛑 {s}</span>'
            sellos_html += '</div>'
        else:
            sellos_html = '<p style="color: green; font-weight: bold; margin-top: 10px;">Producto exento de sellos de advertencia frontal (Ley 27.642).</p>'

        leyendas_html = ""
        if tiene_edulcorante:
            leyendas_html += '<div style="background-color: #fff3cd; color: #856404; padding: 6px; border: 1px solid #ffeeba; margin-top: 6px; font-weight: bold; font-size: 12px;">⚠️ CONTIENE EDULCORANTES, NO RECOMENDABLE EN NIÑOS/AS</div>'
        if tiene_cafeina:
            leyendas_html += '<div style="background-color: #fff3cd; color: #856404; padding: 6px; border: 1px solid #ffeeba; margin-top: 6px; font-weight: bold; font-size: 12px;">⚠️ CONTIENE CAFEÍNA, EVITAR EN NIÑOS/AS</div>'

        filas_ingredientes = "".join(
            f"<tr><td style='padding: 4px 8px; border-bottom: 1px solid #ddd;'>{r['Ingrediente']}</td><td style='padding: 4px 8px; border-bottom: 1px solid #ddd; text-align: right;'>{r['Gramos']:.1f} g</td></tr>"
            for _, r in df_limpio.iterrows()
        )

        plantilla_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Informe Nutricional - {nombre_producto}</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; margin: 20px; }}
                .contenedor {{ max-width: 800px; margin: auto; border: 1px solid #bbb; padding: 25px; border-radius: 6px; background-color: #fff; }}
                .encabezado {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2E7D32; padding-bottom: 10px; margin-bottom: 15px; }}
                table.nutri {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
                table.nutri th, table.nutri td {{ border: 1px solid #333; padding: 6px 10px; }}
                table.nutri th {{ background-color: #f2f2f2; text-align: left; }}
                .btn-print {{ background-color: #2E7D32; color: white; padding: 10px 20px; border: none; font-size: 14px; font-weight: bold; border-radius: 4px; cursor: pointer; margin-bottom: 15px; }}
                @media print {{
                    .btn-print {{ display: none; }}
                    body {{ margin: 0; }}
                    .contenedor {{ border: none; padding: 0; }}
                }}
            </style>
        </head>
        <body>
            <div class="contenedor">
                <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
                <div class="encabezado">
                    <div>
                        <h2 style="margin: 0; color: #222;">{nombre_producto}</h2>
                        <small style="color: #666;">Informe Técnico de Rotulado Bromatológico (CAA Cap. V & Ley 27.642)</small>
                    </div>
                    <div>
                        {logo_html}
                    </div>
                </div>

                <div style="font-size: 13px; margin-bottom: 15px;">
                    <strong>Peso neto elaborado:</strong> {peso_cocido:.0f} g &nbsp;|&nbsp; 
                    <strong>Porción de referencia:</strong> {porcion:.0f} g
                </div>

                <h4 style="margin-bottom: 5px;">INFORMACIÓN NUTRICIONAL</h4>
                <table class="nutri">
                    <thead>
                        <tr>
                            <th>Nutriente</th>
                            <th style="text-align: right;">Cada 100 g</th>
                            <th style="text-align: right;">Por porción ({porcion:.0f} g)</th>
                            <th style="text-align: center;">% VD*</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td><strong>Valor energético</strong></td><td style="text-align: right;">{c_kcal:.0f} kcal = {c_kj:.0f} kJ</td><td style="text-align: right;">{p_kcal:.0f} kcal = {p_kj:.0f} kJ</td><td style="text-align: center;">{vd_kcal}%</td></tr>
                        <tr><td><strong>Carbohidratos</strong></td><td style="text-align: right;">{c_cho:.1f} g</td><td style="text-align: right;">{p_cho:.1f} g</td><td style="text-align: center;">{vd_cho}%</td></tr>
                        <tr><td style="padding-left: 20px;">de los cuales: Azúcares totales</td><td style="text-align: right;">{c_azuc_tot:.1f} g</td><td style="text-align: right;">{p_azuc_tot:.1f} g</td><td style="text-align: center;">-</td></tr>
                        <tr><td style="padding-left: 20px;">Azúcares añadidos</td><td style="text-align: right;">{c_azuc_anad:.1f} g</td><td style="text-align: right;">{p_azuc_anad:.1f} g</td><td style="text-align: center;">-</td></tr>
                        <tr><td><strong>Proteínas</strong></td><td style="text-align: right;">{c_prot:.1f} g</td><td style="text-align: right;">{p_prot:.1f} g</td><td style="text-align: center;">{vd_prot}%</td></tr>
                        <tr><td><strong>Grasas totales</strong></td><td style="text-align: right;">{c_gtot:.1f} g</td><td style="text-align: right;">{p_gtot:.1f} g</td><td style="text-align: center;">{vd_gtot}%</td></tr>
                        <tr><td style="padding-left: 20px;">Grasas saturadas</td><td style="text-align: right;">{c_gsat:.1f} g</td><td style="text-align: right;">{p_gsat:.1f} g</td><td style="text-align: center;">{vd_gsat}%</td></tr>
                        <tr><td style="padding-left: 20px;">Grasas trans</td><td style="text-align: right;">{c_gtrans:.1f} g</td><td style="text-align: right;">{p_gtrans:.1f} g</td><td style="text-align: center;">-</td></tr>
                        <tr><td><strong>Fibra alimentaria</strong></td><td style="text-align: right;">{c_fibra:.1f} g</td><td style="text-align: right;">{p_fibra:.1f} g</td><td style="text-align: center;">{vd_fibra}%</td></tr>
                        <tr><td><strong>Sodio</strong></td><td style="text-align: right;">{c_sodio:.1f} mg</td><td style="text-align: right;">{p_sodio:.1f} mg</td><td style="text-align: center;">{vd_sodio}%</td></tr>
                    </tbody>
                </table>
                <p style="font-size: 11px; color: #666; margin-top: 5px;">*% Valores Diarios con base a una dieta de 2.000 kcal u 8.400 kJ (CAA Cap. V). Sus valores diarios pueden ser mayores o menores según sus necesidades energéticas.</p>

                <h4 style="margin-bottom: 5px; margin-top: 20px;">Sellos y Advertencias Obligatorias (Ley 27.642)</h4>
                {sellos_html}
                {leyendas_html}

                <h4 style="margin-bottom: 5px; margin-top: 20px;">Fórmula de Ingredientes</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background-color: #f7f7f7;">
                            <th style="padding: 4px 8px; border-bottom: 2px solid #ddd; text-align: left;">Ingrediente declarado</th>
                            <th style="padding: 4px 8px; border-bottom: 2px solid #ddd; text-align: right;">Masa neta</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_ingredientes}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px; font-size: 11px; color: #888; text-align: center;">
                    Dictamen técnico generado por el Sistema de Rotulado Ecomeg® - Base SARA 2 (Ministerio de Salud de la Nación / ENNyS 2).
                </div>
            </div>
        </body>
        </html>
        """

        # Vista previa interactiva
        st.components.v1.html(plantilla_html, height=850, scrolling=True)

        # Botón para descargar archivo HTML
        st.download_button(
            label="💾 Descargar Rótulo en formato HTML Imprimible (con Logo Ecomeg)",
            data=plantilla_html,
            file_name=f"Rotulo_{normalizar(nombre_producto)}.html",
            mime="text/html"
        )

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

        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            respuesta_texto = "Falta configurar GEMINI_API_KEY en Secrets de Streamlit."
        else:
            with st.spinner("Consultando normativa..."):
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key
                    }
                    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                    list_res = requests.get(list_url, timeout=10)
                    
                    modelo_a_usar = None
                    if list_res.status_code == 200:
                        modelos = list_res.json().get("models", [])
                        for m in modelos:
                            if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m.get("name", ""):
                                modelo_a_usar = m.get("name")
                                break
                    if not modelo_a_usar:
                        modelo_a_usar = "models/gemini-2.5-flash"

                    url = f"https://generativelanguage.googleapis.com/v1beta/{modelo_a_usar}:generateContent"
                    body = {
                        "contents": [{"parts": [{"text": pregunta}]}],
                        "systemInstruction": {
                            "parts": [{
                                "text": (
                                    "Sos un asesor bromatológico especialista en el Código Alimentario Argentino (CAA Cap. IV y V) "
                                    "y la Ley 27.642 con su Decreto 151/2022. Respondé de forma técnica, precisa y citando normativa."
                                )
                            }]
                        }
                    }
                    r = requests.post(url, headers=headers, json=body, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        respuesta_texto = data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        respuesta_texto = f"Error {r.status_code}: {r.text}"
                except Exception as e:
                    respuesta_texto = f"Error al procesar la solicitud: {str(e)}"

        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
        with st.chat_message("assistant"):
            st.markdown(respuesta_texto)
