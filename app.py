import streamlit as st
import pandas as pd
import requests
import urllib.parse
import unicodedata

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

def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto).lower()) if unicodedata.category(c) != 'Mn')

# ==========================================================
# BASE DE COMPOSICIÓN SARA 2 COMPLETA (Macronutrientes CAA)
# ==========================================================
SARA2_DICT = {
    # Cereales, Sémolas, Harinas y Legumbres
    "Sémola de trigo / Semolín candeal": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Semolín para pastas secas o frescas": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Gluten puro de trigo en polvo": {"kcal": 370.0, "cho": 13.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 75.0, "gtot": 1.9, "gsat": 0.3, "gtrans": 0.0, "fibra": 1.5, "sodio": 70.0, "edulc": False, "caf": False},
    "Seitán / Carne vegetal de gluten": {"kcal": 120.0, "cho": 4.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 21.0, "gtot": 1.5, "gsat": 0.2, "gtrans": 0.0, "fibra": 0.6, "sodio": 350.0, "edulc": False, "caf": False},
    "Pan de gluten": {"kcal": 231.0, "cho": 40.8, "azuc_tot": 3.0, "azuc_anad": 0.0, "prot": 12.1, "gtot": 2.2, "gsat": 0.33, "gtrans": 0.0, "fibra": 1.4, "sodio": 404.0, "edulc": False, "caf": False},
    "Tostadas de gluten": {"kcal": 335.0, "cho": 61.3, "azuc_tot": 3.5, "azuc_anad": 0.2, "prot": 20.0, "gtot": 1.1, "gsat": 0.1, "gtrans": 0.0, "fibra": 3.5, "sodio": 325.0, "edulc": False, "caf": False},
    "Harina de trigo 000 fortificada": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo 0000 fortificada": {"kcal": 353.0, "cho": 74.0, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 11.6, "gtot": 0.9, "gsat": 0.15, "gtrans": 0.0, "fibra": 2.5, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo integral": {"kcal": 308.0, "cho": 58.8, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 11.4, "gtot": 3.0, "gsat": 0.43, "gtrans": 0.0, "fibra": 12.6, "sodio": 16.0, "edulc": False, "caf": False},
    "Harina leudante": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 714.0, "edulc": False, "caf": False},
    "Salvado de trigo": {"kcal": 216.0, "cho": 64.5, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 15.5, "gtot": 5.5, "gsat": 0.89, "gtrans": 0.0, "fibra": 44.7, "sodio": 27.0, "edulc": False, "caf": False},
    "Salvado de avena": {"kcal": 246.0, "cho": 50.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 17.3, "gtot": 7.0, "gsat": 1.33, "gtrans": 0.0, "fibra": 15.4, "sodio": 4.0, "edulc": False, "caf": False},
    "Gérmen de trigo": {"kcal": 334.0, "cho": 38.6, "azuc_tot": 16.0, "azuc_anad": 0.0, "prot": 23.2, "gtot": 9.7, "gsat": 1.67, "gtrans": 0.0, "fibra": 13.2, "sodio": 12.0, "edulc": False, "caf": False},
    "Avena arrollada instantánea / tradicional": {"kcal": 357.0, "cho": 56.9, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 15.6, "gtot": 7.5, "gsat": 1.52, "gtrans": 0.0, "fibra": 10.4, "sodio": 2.0, "edulc": False, "caf": False},
    "Harina de maíz / Polenta": {"kcal": 307.0, "cho": 64.5, "azuc_tot": 0.6, "azuc_anad": 0.0, "prot": 9.1, "gtot": 1.39, "gsat": 0.17, "gtrans": 0.0, "fibra": 8.9, "sodio": 25.0, "edulc": False, "caf": False},
    "Almidón de maíz (Maicena)": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Fécula / Almidón de mandioca": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Harina de arroz": {"kcal": 348.0, "cho": 77.7, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 6.0, "gtot": 1.4, "gsat": 0.39, "gtrans": 0.0, "fibra": 2.4, "sodio": 0.0, "edulc": False, "caf": False},
    "Harina de algarrobo": {"kcal": 221.0, "cho": 49.1, "azuc_tot": 49.1, "azuc_anad": 0.0, "prot": 4.6, "gtot": 0.7, "gsat": 0.09, "gtrans": 0.0, "fibra": 39.8, "sodio": 35.0, "edulc": False, "caf": False},
    "Harina de almendras": {"kcal": 570.0, "cho": 9.1, "azuc_tot": 4.4, "azuc_anad": 0.0, "prot": 21.2, "gtot": 49.9, "gsat": 3.8, "gtrans": 0.0, "fibra": 12.5, "sodio": 1.0, "edulc": False, "caf": False},
    "Harina de garbanzos": {"kcal": 338.0, "cho": 47.0, "azuc_tot": 10.9, "azuc_anad": 0.0, "prot": 22.4, "gtot": 6.7, "gsat": 0.69, "gtrans": 0.0, "fibra": 10.8, "sodio": 64.0, "edulc": False, "caf": False},
    "Harina de soja activa": {"kcal": 338.0, "cho": 14.6, "azuc_tot": 9.3, "azuc_anad": 0.0, "prot": 49.8, "gtot": 8.9, "gsat": 1.29, "gtrans": 0.0, "fibra": 16.0, "sodio": 9.0, "edulc": False, "caf": False},
    "Premezcla universal SIN TACC": {"kcal": 357.0, "cho": 82.5, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 2.8, "gtot": 1.8, "gsat": 1.0, "gtrans": 0.0, "fibra": 1.0, "sodio": 40.0, "edulc": False, "caf": False},
    "Premezcla para bizcochuelo SIN TACC": {"kcal": 377.0, "cho": 82.0, "azuc_tot": 51.4, "azuc_anad": 51.1, "prot": 3.6, "gtot": 3.8, "gsat": 1.9, "gtrans": 0.0, "fibra": 1.0, "sodio": 311.0, "edulc": False, "caf": False},
    "Arroz blanco": {"kcal": 339.0, "cho": 77.5, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 6.9, "gtot": 0.2, "gsat": 0.05, "gtrans": 0.0, "fibra": 1.7, "sodio": 4.0, "edulc": False, "caf": False},
    "Arroz integral": {"kcal": 350.0, "cho": 72.7, "azuc_tot": 0.7, "azuc_anad": 0.0, "prot": 7.5, "gtot": 3.2, "gsat": 0.59, "gtrans": 0.0, "fibra": 3.6, "sodio": 5.0, "edulc": False, "caf": False},
    "Fideos secos de trigo": {"kcal": 352.0, "cho": 71.5, "azuc_tot": 2.7, "azuc_anad": 0.0, "prot": 13.0, "gtot": 1.5, "gsat": 0.28, "gtrans": 0.0, "fibra": 3.2, "sodio": 6.0, "edulc": False, "caf": False},
    "Fideos frescos al huevo": {"kcal": 285.0, "cho": 54.7, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 11.3, "gtot": 2.3, "gsat": 0.33, "gtrans": 0.0, "fibra": 3.3, "sodio": 26.0, "edulc": False, "caf": False},
    "Arveja seca cruda": {"kcal": 311.0, "cho": 49.1, "azuc_tot": 3.1, "azuc_anad": 0.0, "prot": 22.0, "gtot": 2.9, "gsat": 0.41, "gtrans": 0.0, "fibra": 12.2, "sodio": 16.0, "edulc": False, "caf": False},
    "Garbanzos secos": {"kcal": 339.0, "cho": 50.8, "azuc_tot": 10.7, "azuc_anad": 0.0, "prot": 20.5, "gtot": 6.0, "gsat": 0.60, "gtrans": 0.0, "fibra": 12.2, "sodio": 24.0, "edulc": False, "caf": False},
    "Lentejas secas": {"kcal": 301.0, "cho": 52.7, "azuc_tot": 2.0, "azuc_anad": 0.0, "prot": 20.8, "gtot": 0.8, "gsat": 0.15, "gtrans": 0.0, "fibra": 10.7, "sodio": 12.0, "edulc": False, "caf": False},
    "Porotos secos": {"kcal": 276.0, "cho": 45.3, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 21.1, "gtot": 1.1, "gsat": 0.07, "gtrans": 0.0, "fibra": 15.2, "sodio": 8.0, "edulc": False, "caf": False},
    "Soja texturizada": {"kcal": 283.0, "cho": 16.4, "azuc_tot": 7.3, "azuc_anad": 0.0, "prot": 51.5, "gtot": 1.2, "gsat": 0.21, "gtrans": 0.0, "fibra": 17.5, "sodio": 20.0, "edulc": False, "caf": False},

    # Panificados y Masas
    "Pan francés / Felipe": {"kcal": 268.0, "cho": 57.0, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 8.4, "gtot": 0.7, "gsat": 0.13, "gtrans": 0.0, "fibra": 2.8, "sodio": 400.0, "edulc": False, "caf": False},
    "Pan de molde blanco / lactal": {"kcal": 244.0, "cho": 46.7, "azuc_tot": 3.5, "azuc_anad": 3.5, "prot": 9.4, "gtot": 2.2, "gsat": 0.73, "gtrans": 0.0, "fibra": 3.5, "sodio": 415.0, "edulc": False, "caf": False},
    "Pan de molde integral / salvado": {"kcal": 225.0, "cho": 40.7, "azuc_tot": 5.9, "azuc_anad": 5.9, "prot": 10.9, "gtot": 2.1, "gsat": 0.53, "gtrans": 0.0, "fibra": 7.4, "sodio": 447.0, "edulc": False, "caf": False},
    "Pan árabe / pita": {"kcal": 261.0, "cho": 53.5, "azuc_tot": 1.3, "azuc_anad": 1.3, "prot": 9.1, "gtot": 1.2, "gsat": 0.17, "gtrans": 0.0, "fibra": 2.2, "sodio": 536.0, "edulc": False, "caf": False},
    "Pan rallado clásico": {"kcal": 371.0, "cho": 67.5, "azuc_tot": 5.7, "azuc_anad": 4.5, "prot": 13.4, "gtot": 5.3, "gsat": 0.7, "gtrans": 0.0, "fibra": 4.5, "sodio": 732.0, "edulc": False, "caf": False},
    "Galletitas de agua crackers con grasa": {"kcal": 451.0, "cho": 71.3, "azuc_tot": 1.3, "azuc_anad": 0.0, "prot": 12.2, "gtot": 13.0, "gsat": 6.0, "gtrans": 1.4, "fibra": 2.8, "sodio": 566.0, "edulc": False, "caf": False},
    "Galletitas de agua crackers con aceite": {"kcal": 438.0, "cho": 71.3, "azuc_tot": 1.3, "azuc_anad": 0.0, "prot": 12.2, "gtot": 11.6, "gsat": 1.16, "gtrans": 0.0, "fibra": 2.8, "sodio": 566.0, "edulc": False, "caf": False},
    "Galletitas de salvado / integrales": {"kcal": 411.0, "cho": 56.5, "azuc_tot": 1.2, "azuc_anad": 1.2, "prot": 15.8, "gtot": 10.6, "gsat": 3.16, "gtrans": 0.0, "fibra": 9.8, "sodio": 543.0, "edulc": False, "caf": False},
    "Masa de tarta / empanadas clásica": {"kcal": 337.0, "cho": 47.6, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 6.7, "gtot": 13.3, "gsat": 6.7, "gtrans": 0.9, "fibra": 1.7, "sodio": 561.0, "edulc": False, "caf": False},

    # Grasas y Aceites
    "Aceite de girasol refinado": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de girasol alto oleico": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 9.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de maíz refinado": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 2.0, "edulc": False, "caf": False},
    "Aceite de oliva virgen extra": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 17.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada / primer jugo": {"kcal": 899.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.9, "gsat": 49.8, "gtrans": 3.7, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Manteca de vaca": {"kcal": 758.0, "cho": 0.1, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 0.5, "gtot": 84.0, "gsat": 50.93, "gtrans": 3.28, "fibra": 0.0, "sodio": 223.0, "edulc": False, "caf": False},
    "Margarina vegetal": {"kcal": 559.0, "cho": 0.7, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.2, "gtot": 61.7, "gsat": 27.6, "gtrans": 0.88, "fibra": 0.0, "sodio": 295.0, "edulc": False, "caf": False},

    # Azúcares y Dulces
    "Azúcar blanca refinada común": {"kcal": 400.0, "cho": 100.0, "azuc_tot": 99.8, "azuc_anad": 99.8, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Miel pura de abejas": {"kcal": 330.0, "cho": 82.2, "azuc_tot": 82.1, "azuc_anad": 82.1, "prot": 0.3, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.2, "sodio": 4.0, "edulc": False, "caf": False},
    "Dulce de leche común": {"kcal": 315.0, "cho": 57.4, "azuc_tot": 49.7, "azuc_anad": 44.0, "prot": 6.5, "gtot": 6.6, "gsat": 4.07, "gtrans": 0.33, "fibra": 0.0, "sodio": 138.0, "edulc": False, "caf": False},
    "Dulce de batata": {"kcal": 255.0, "cho": 62.5, "azuc_tot": 52.0, "azuc_anad": 52.0, "prot": 0.9, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 2.5, "sodio": 19.0, "edulc": False, "caf": False},
    "Dulce de membrillo": {"kcal": 269.0, "cho": 66.7, "azuc_tot": 52.0, "azuc_anad": 52.0, "prot": 0.4, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 4.1, "sodio": 0.0, "edulc": False, "caf": False},
    "Cacao amargo en polvo": {"kcal": 285.0, "cho": 20.9, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 19.6, "gtot": 13.7, "gsat": 8.07, "gtrans": 0.0, "fibra": 37.0, "sodio": 21.0, "edulc": False, "caf": True},
    "Chocolate cobertura semiamargo": {"kcal": 547.0, "cho": 44.4, "azuc_tot": 36.7, "azuc_anad": 36.7, "prot": 6.1, "gtot": 38.3, "gsat": 22.03, "gtrans": 0.08, "fibra": 8.0, "sodio": 10.0, "edulc": False, "caf": False},

    # Lácteos, Quesos y Huevos
    "Leche entera líquida": {"kcal": 58.0, "cho": 4.8, "azuc_tot": 4.8, "azuc_anad": 0.0, "prot": 3.1, "gtot": 2.9, "gsat": 1.87, "gtrans": 0.13, "fibra": 0.0, "sodio": 57.0, "edulc": False, "caf": False},
    "Leche parcialmente descremada": {"kcal": 44.0, "cho": 4.6, "azuc_tot": 4.6, "azuc_anad": 0.0, "prot": 3.2, "gtot": 1.4, "gsat": 0.95, "gtrans": 0.09, "fibra": 0.0, "sodio": 55.0, "edulc": False, "caf": False},
    "Leche entera en polvo": {"kcal": 480.0, "cho": 38.4, "azuc_tot": 38.4, "azuc_anad": 0.0, "prot": 25.8, "gtot": 24.8, "gsat": 15.54, "gtrans": 1.06, "fibra": 0.0, "sodio": 404.0, "edulc": False, "caf": False},
    "Crema de leche (36% grasa)": {"kcal": 347.0, "cho": 2.8, "azuc_tot": 2.9, "azuc_anad": 0.0, "prot": 2.8, "gtot": 36.1, "gsat": 23.03, "gtrans": 1.24, "fibra": 0.0, "sodio": 27.0, "edulc": False, "caf": False},
    "Huevo entero": {"kcal": 156.0, "cho": 0.4, "azuc_tot": 0.4, "azuc_anad": 0.0, "prot": 12.0, "gtot": 11.8, "gsat": 3.18, "gtrans": 0.0, "fibra": 0.0, "sodio": 135.0, "edulc": False, "caf": False},
    "Huevo - Clara": {"kcal": 51.0, "cho": 0.7, "azuc_tot": 0.7, "azuc_anad": 0.0, "prot": 11.6, "gtot": 0.2, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 186.0, "edulc": False, "caf": False},
    "Huevo - Yema": {"kcal": 339.0, "cho": 3.6, "azuc_tot": 0.6, "azuc_anad": 0.0, "prot": 16.6, "gtot": 28.7, "gsat": 10.33, "gtrans": 0.1, "fibra": 0.0, "sodio": 65.0, "edulc": False, "caf": False},
    "Queso Cremoso": {"kcal": 310.0, "cho": 2.5, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 20.4, "gtot": 24.9, "gsat": 13.66, "gtrans": 0.73, "fibra": 0.0, "sodio": 704.0, "edulc": False, "caf": False},
    "Queso Muzzarella": {"kcal": 278.0, "cho": 2.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 23.6, "gtot": 19.3, "gsat": 13.9, "gtrans": 0.58, "fibra": 0.0, "sodio": 486.0, "edulc": False, "caf": False},
    "Queso de máquina / Barra (Tibo)": {"kcal": 356.0, "cho": 2.2, "azuc_tot": 2.2, "azuc_anad": 0.0, "prot": 24.9, "gtot": 27.4, "gsat": 17.61, "gtrans": 0.82, "fibra": 0.0, "sodio": 819.0, "edulc": False, "caf": False},
    "Queso Port Salut": {"kcal": 225.0, "cho": 1.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 26.3, "gtot": 12.9, "gsat": 7.15, "gtrans": 0.39, "fibra": 0.0, "sodio": 55.0, "edulc": False, "caf": False},
    "Queso Reggianito / Sardo": {"kcal": 381.0, "cho": 3.2, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 35.8, "gtot": 25.0, "gsat": 14.85, "gtrans": 0.75, "fibra": 0.0, "sodio": 1175.0, "edulc": False, "caf": False},
    "Queso untable clásico": {"kcal": 284.0, "cho": 3.2, "azuc_tot": 3.2, "azuc_anad": 0.0, "prot": 7.1, "gtot": 27.0, "gsat": 16.0, "gtrans": 0.7, "fibra": 0.0, "sodio": 409.0, "edulc": False, "caf": False},
    "Ricota entera": {"kcal": 169.0, "cho": 4.0, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 11.6, "gtot": 11.8, "gsat": 7.28, "gtrans": 0.35, "fibra": 0.0, "sodio": 146.0, "edulc": False, "caf": False},

    # Carnes y Embutidos
    "Carne vacuna magra (nalga/peceto)": {"kcal": 138.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 22.2, "gtot": 5.5, "gsat": 2.15, "gtrans": 0.23, "fibra": 0.0, "sodio": 60.0, "edulc": False, "caf": False},
    "Carne vacuna semigrasa (roast beef)": {"kcal": 176.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 21.3, "gtot": 10.1, "gsat": 4.12, "gtrans": 0.4, "fibra": 0.0, "sodio": 61.0, "edulc": False, "caf": False},
    "Pollo pechuga sin piel": {"kcal": 114.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 22.5, "gtot": 2.6, "gsat": 0.69, "gtrans": 0.01, "fibra": 0.0, "sodio": 45.0, "edulc": False, "caf": False},
    "Carne de cerdo magra": {"kcal": 206.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 18.2, "gtot": 14.8, "gsat": 4.92, "gtrans": 0.03, "fibra": 0.0, "sodio": 57.0, "edulc": False, "caf": False},
    "Jamón cocido": {"kcal": 107.0, "cho": 1.0, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 18.4, "gtot": 3.3, "gsat": 1.1, "gtrans": 0.01, "fibra": 0.0, "sodio": 800.0, "edulc": False, "caf": False},
    "Jamón crudo": {"kcal": 319.0, "cho": 0.2, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 28.8, "gtot": 22.6, "gsat": 7.94, "gtrans": 0.71, "fibra": 0.0, "sodio": 2130.0, "edulc": False, "caf": False},
    "Salchicha de Viena": {"kcal": 226.0, "cho": 2.6, "azuc_tot": 2.4, "azuc_anad": 0.0, "prot": 15.3, "gtot": 17.2, "gsat": 6.08, "gtrans": 0.7, "fibra": 0.0, "sodio": 1297.0, "edulc": False, "caf": False},

    # Sales, Condimentos y Otros
    "Sal fina de mesa común (NaCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 40000.0, "edulc": False, "caf": False},
    "Sal modificada (66% NaCl / 33% KCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 26400.0, "edulc": False, "caf": False},
    "Sal sin sodio (100% KCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Polvo de hornear": {"kcal": 96.0, "cho": 23.9, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.2, "sodio": 7893.0, "edulc": False, "caf": False},
    "Bicarbonato de sodio puro": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 27360.0, "edulc": False, "caf": False},
    "Levadura fresca prensada": {"kcal": 91.0, "cho": 10.0, "azuc_tot": 8.1, "azuc_anad": 0.0, "prot": 8.4, "gtot": 1.9, "gsat": 0.24, "gtrans": 0.0, "fibra": 8.1, "sodio": 30.0, "edulc": False, "caf": False},
    "Vinagre blanco de alcohol": {"kcal": 1.0, "cho": 0.3, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 8.0, "edulc": False, "caf": False},
    "Agua potable": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 5.0, "edulc": False, "caf": False},
    "Edulcorante no calórico": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 10.0, "edulc": True, "caf": False}
}

lista_alimentos_completa = sorted(list(SARA2_DICT.keys()))

# Función auxiliar para crear receta inicial estándar
def receta_inicial():
    return [
        {"Ingrediente": "Sémola de trigo / Semolín candeal", "Gramos": 300.0, "Kcal": 336.0, "Carbohidratos_g": 72.8, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 12.7, "Grasa_Tot_g": 1.1, "Grasa_Sat_g": 0.15, "Grasa_Trans_g": 0.0, "Fibra_g": 3.9, "Sodio_mg": 1.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Huevo entero", "Gramos": 100.0, "Kcal": 156.0, "Carbohidratos_g": 0.4, "Azucares_Tot_g": 0.4, "Azucar_Anadido_g": 0.0, "Proteinas_g": 12.0, "Grasa_Tot_g": 11.8, "Grasa_Sat_g": 3.18, "Grasa_Trans_g": 0.0, "Fibra_g": 0.0, "Sodio_mg": 135.0, "Edulcorante": False, "Cafeina": False},
        {"Ingrediente": "Sal fina de mesa común (NaCl)", "Gramos": 5.0, "Kcal": 0.0, "Carbohidratos_g": 0.0, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 0.0, "Grasa_Tot_g": 0.0, "Grasa_Sat_g": 0.0, "Grasa_Trans_g": 0.0, "Fibra_g": 0.0, "Sodio_mg": 40000.0, "Edulcorante": False, "Cafeina": False}
    ]

# Verificación de estructura previa en sesión
if "receta" not in st.session_state or not isinstance(st.session_state.receta, list):
    st.session_state.receta = receta_inicial()
else:
    # Si la receta guardada tiene las columnas viejas, se reinicia de manera limpia
    if st.session_state.receta and "Carbohidratos_g" not in st.session_state.receta[0]:
        st.session_state.receta = receta_inicial()

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Rotulado Nutricional y Sellos (CAA Cap. V & Ley 27.642)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        peso_cocido = st.number_input("Peso neto final tras cocción o merma (g)", min_value=1.0, value=500.0)
    with col_b:
        porcion = st.number_input("Tamaño de la porción según CAA (g)", min_value=1.0, value=50.0)

    st.markdown("---")
    st.subheader("1. Selección y Búsqueda de Ingredientes")

    c_f1, c_f2 = st.columns([2, 3])
    with c_f1:
        filtro_texto = st.text_input("Filtrar por letras o palabras:", placeholder="Ej: semo, trigo, gluten, aceite...")

    if filtro_texto.strip():
        termino_norm = normalizar(filtro_texto.strip())
        opciones_filtradas = [ali for ali in lista_alimentos_completa if termino_norm in normalizar(ali)]
    else:
        opciones_filtradas = lista_alimentos_completa

    with c_f2:
        if opciones_filtradas:
            ing_elegido = st.selectbox(f"Ingredientes disponibles ({len(opciones_filtradas)} encontrados):", opciones_filtradas)
        else:
            st.warning("No se encontraron coincidencias en la base interna.")
            ing_elegido = None

    if ing_elegido:
        col_g1, col_g2 = st.columns([3, 1])
        with col_g1:
            gramos_ing = st.number_input(f"Gramos de '{ing_elegido}' a incorporar:", min_value=0.1, value=100.0, step=5.0)
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
                st.success(f"'{ing_elegido}' agregado a la formulación.")
                st.rerun()

    # Panel de consulta externa
    with st.expander("🔍 Consultar en línea (FatSecret Argentina / Dieta y Nutrición)"):
        st.write("Buscá marcas o materias primas y copiá los valores por 100 g:")
        col_busq1, col_busq2, col_busq3 = st.columns([3, 1.5, 1.5])
        with col_busq1:
            termino_web = st.text_input("Término a buscar:", value=filtro_texto if filtro_texto else "")
        with col_busq2:
            st.write("")
            st.write("")
            if termino_web.strip():
                term_fs = urllib.parse.quote(termino_web.strip())
                st.link_button("🌐 FatSecret Arg", f"https://www.fatsecret.com.ar/calor%C3%ADas-nutrici%C3%B3n/search?q={term_fs}")
            else:
                st.link_button("🌐 FatSecret Arg", "https://www.fatsecret.com.ar/calor%C3%ADas-nutrici%C3%B3n/")
        with col_busq3:
            st.write("")
            st.write("")
            if termino_web.strip():
                term_dynet = urllib.parse.quote(termino_web.strip())
                st.link_button("🥗 Dieta y Nutrición", f"https://www.dietaynutricion.net/tabla-de-calorias-nutricional/?q={term_dynet}")
            else:
                st.link_button("🥗 Dieta y Nutrición", "https://www.dietaynutricion.net/tabla-de-calorias-nutricional/")

    # Formulario para ingrediente manual externo
    with st.expander("➕ Cargar ingrediente manual o externo (valores cada 100 g)"):
        c_m1, c_m2, c_m3 = st.columns([3, 2, 2])
        with c_m1:
            nombre_man = st.text_input("Nombre del ingrediente:")
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
        
        # Lectura robusta con fallback para compatibilidad
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

        # Porcentajes de Valor Diario (%VD) según CAA Cap. V
        vd_kcal = round((p_kcal / 2000.0) * 100)
        vd_cho = round((p_cho / 300.0) * 100)
        vd_prot = round((p_prot / 75.0) * 100)
        vd_gtot = round((p_gtot / 55.0) * 100)
        vd_gsat = round((p_gsat / 22.0) * 100)
        vd_fibra = round((p_fibra / 25.0) * 100)
        vd_sodio = round((p_sodio / 2000.0) * 100)

        # Sellos Frontales Ley 27.642 (Etapa 2 definitiva)
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
