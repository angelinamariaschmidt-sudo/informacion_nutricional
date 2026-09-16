import streamlit as st
import pandas as pd
import requests
import urllib.parse
import unicodedata

st.set_page_config(page_title="Plataforma Bromatológica - Rotulado y Sellos", layout="wide")

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

# ==============================================================================
# BASE DE DATOS MATRIZ: SARA 2 (Ministerio de Salud de la Nación / ENNyS 2)
# ==============================================================================
SARA2_DICT = {
    # --- ACEITES Y MATERIAS GRASAS ---
    "Aceite de girasol": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de girasol alto oleico": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 9.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de maíz": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 2.0, "edulc": False, "caf": False},
    "Aceite de oliva virgen extra": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 17.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de soja": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.65, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de canola": {"kcal": 892.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.1, "gsat": 7.37, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de coco": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 82.48, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de chía": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 9.86, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite comestible mezcla": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.83, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de uva": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 11.25, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de sésamo": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 14.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Rocío vegetal en aerosol": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada / primer jugo": {"kcal": 899.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.9, "gsat": 49.8, "gtrans": 3.7, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa de cerdo / manteca de cerdo": {"kcal": 898.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.8, "gsat": 39.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa de pollo": {"kcal": 626.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 3.7, "gtot": 68.0, "gsat": 20.25, "gtrans": 0.75, "fibra": 0.0, "sodio": 32.0, "edulc": False, "caf": False},
    "Manteca de vaca": {"kcal": 758.0, "cho": 0.1, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 0.5, "gtot": 84.0, "gsat": 50.93, "gtrans": 3.28, "fibra": 0.0, "sodio": 223.0, "edulc": False, "caf": False},
    "Manteca light": {"kcal": 509.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 3.3, "gtot": 55.1, "gsat": 34.32, "gtrans": 1.01, "fibra": 0.0, "sodio": 218.0, "edulc": False, "caf": False},
    "Margarina vegetal en pan / pote": {"kcal": 559.0, "cho": 0.7, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.2, "gtot": 61.7, "gsat": 27.6, "gtrans": 0.88, "fibra": 0.0, "sodio": 295.0, "edulc": False, "caf": False},
    "Margarina untable light": {"kcal": 472.0, "cho": 0.9, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.2, "gtot": 52.0, "gsat": 23.2, "gtrans": 0.57, "fibra": 0.0, "sodio": 610.0, "edulc": False, "caf": False},

    # --- VERDURAS Y HORTALIZAS (SARA 2) ---
    "Acelga, cruda": {"kcal": 18.0, "cho": 2.1, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.6, "sodio": 213.0, "edulc": False, "caf": False},
    "Acelga, hervida": {"kcal": 16.0, "cho": 2.0, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.9, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 2.1, "sodio": 179.0, "edulc": False, "caf": False},
    "Acelga, pencas, crudas": {"kcal": 8.0, "cho": 0.6, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 1.2, "gtot": 0.1, "gsat": 0.02, "gtrans": 0.0, "fibra": 2.9, "sodio": 150.0, "edulc": False, "caf": False},
    "Acelga, pencas, hervidas": {"kcal": 8.0, "cho": 0.6, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 1.2, "gtot": 0.1, "gsat": 0.02, "gtrans": 0.0, "fibra": 2.9, "sodio": 150.0, "edulc": False, "caf": False},
    "Achicoria, cruda": {"kcal": 12.0, "cho": 0.7, "azuc_tot": 0.7, "azuc_anad": 0.0, "prot": 1.6, "gtot": 0.3, "gsat": 0.07, "gtrans": 0.0, "fibra": 4.0, "sodio": 45.0, "edulc": False, "caf": False},
    "Achicoria, hervida": {"kcal": 12.0, "cho": 0.7, "azuc_tot": 0.7, "azuc_anad": 0.0, "prot": 1.6, "gtot": 0.3, "gsat": 0.07, "gtrans": 0.0, "fibra": 4.0, "sodio": 45.0, "edulc": False, "caf": False},
    "Ají en conserva": {"kcal": 20.0, "cho": 3.2, "azuc_tot": 1.9, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.3, "gsat": 0.05, "gtrans": 0.0, "fibra": 1.9, "sodio": 14.0, "edulc": False, "caf": False},
    "Ají rojo / morrón rojo, crudo": {"kcal": 22.0, "cho": 3.9, "azuc_tot": 4.2, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.3, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.1, "sodio": 4.0, "edulc": False, "caf": False},
    "Ají rojo / morrón rojo, rehogado": {"kcal": 17.0, "cho": 2.9, "azuc_tot": 2.4, "azuc_anad": 0.0, "prot": 0.9, "gtot": 0.2, "gsat": 0.06, "gtrans": 0.0, "fibra": 1.7, "sodio": 4.0, "edulc": False, "caf": False},
    "Ají verde o amarillo, crudo": {"kcal": 22.0, "cho": 3.9, "azuc_tot": 4.2, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.3, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.1, "sodio": 3.0, "edulc": False, "caf": False},
    "Ají verde o amarillo, rehogado": {"kcal": 17.0, "cho": 2.9, "azuc_tot": 2.4, "azuc_anad": 0.0, "prot": 0.9, "gtot": 0.2, "gsat": 0.06, "gtrans": 0.0, "fibra": 1.7, "sodio": 3.0, "edulc": False, "caf": False},
    "Ajo, crudo": {"kcal": 91.0, "cho": 17.9, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 4.4, "gtot": 0.2, "gsat": 0.09, "gtrans": 0.0, "fibra": 2.1, "sodio": 17.0, "edulc": False, "caf": False},
    "Albahaca, cruda": {"kcal": 23.0, "cho": 1.1, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 3.2, "gtot": 0.6, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.6, "sodio": 4.0, "edulc": False, "caf": False},
    "Alcaparras, encurtido": {"kcal": 24.0, "cho": 1.7, "azuc_tot": 0.4, "azuc_anad": 0.0, "prot": 2.4, "gtot": 0.9, "gsat": 0.23, "gtrans": 0.0, "fibra": 3.2, "sodio": 2348.0, "edulc": False, "caf": False},
    "Alcaucil, crudo": {"kcal": 41.0, "cho": 6.5, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 2.9, "gtot": 0.4, "gsat": 0.04, "gtrans": 0.0, "fibra": 5.4, "sodio": 94.0, "edulc": False, "caf": False},
    "Alcaucil, hervido": {"kcal": 40.0, "cho": 6.3, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 2.9, "gtot": 0.3, "gsat": 0.08, "gtrans": 0.0, "fibra": 5.7, "sodio": 94.0, "edulc": False, "caf": False},
    "Apio, crudo": {"kcal": 10.0, "cho": 1.4, "azuc_tot": 1.3, "azuc_anad": 0.0, "prot": 0.7, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.6, "sodio": 80.0, "edulc": False, "caf": False},
    "Apio, hervido": {"kcal": 14.0, "cho": 2.4, "azuc_tot": 1.6, "azuc_anad": 0.0, "prot": 0.8, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.6, "sodio": 91.0, "edulc": False, "caf": False},
    "Arveja, enlatada": {"kcal": 104.0, "cho": 18.3, "azuc_tot": 3.4, "azuc_anad": 0.0, "prot": 6.0, "gtot": 0.8, "gsat": 0.04, "gtrans": 0.0, "fibra": 5.9, "sodio": 88.0, "edulc": False, "caf": False},
    "Arveja, fresca, cruda": {"kcal": 83.0, "cho": 10.9, "azuc_tot": 5.7, "azuc_anad": 0.0, "prot": 8.9, "gtot": 0.4, "gsat": 0.07, "gtrans": 0.0, "fibra": 5.7, "sodio": 38.0, "edulc": False, "caf": False},
    "Arveja, fresca, hervida": {"kcal": 64.0, "cho": 10.1, "azuc_tot": 5.9, "azuc_anad": 0.0, "prot": 5.4, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 5.5, "sodio": 38.0, "edulc": False, "caf": False},
    "Berenjena, cruda": {"kcal": 16.0, "cho": 2.5, "azuc_tot": 3.5, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 3.0, "sodio": 3.0, "edulc": False, "caf": False},
    "Berenjena, hervida": {"kcal": 30.0, "cho": 6.2, "azuc_tot": 2.5, "azuc_anad": 0.0, "prot": 0.8, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 3.2, "sodio": 3.0, "edulc": False, "caf": False},
    "Berro, crudo": {"kcal": 18.0, "cho": 2.2, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.7, "gtot": 0.3, "gsat": 0.02, "gtrans": 0.0, "fibra": 1.1, "sodio": 60.0, "edulc": False, "caf": False},
    "Brócoli, crudo": {"kcal": 27.0, "cho": 2.9, "azuc_tot": 1.7, "azuc_anad": 0.0, "prot": 3.3, "gtot": 0.2, "gsat": 0.11, "gtrans": 0.0, "fibra": 2.6, "sodio": 33.0, "edulc": False, "caf": False},
    "Brócoli, hervido": {"kcal": 29.0, "cho": 3.9, "azuc_tot": 3.3, "azuc_anad": 0.0, "prot": 2.4, "gtot": 0.4, "gsat": 0.08, "gtrans": 0.0, "fibra": 1.4, "sodio": 41.0, "edulc": False, "caf": False},
    "Brotes de soja, crudo": {"kcal": 30.0, "cho": 4.1, "azuc_tot": 4.1, "azuc_anad": 0.0, "prot": 3.0, "gtot": 0.2, "gsat": 0.05, "gtrans": 0.0, "fibra": 1.8, "sodio": 6.0, "edulc": False, "caf": False},
    "Cebolla de verdeo, cruda": {"kcal": 28.0, "cho": 4.7, "azuc_tot": 2.3, "azuc_anad": 0.0, "prot": 1.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 2.6, "sodio": 16.0, "edulc": False, "caf": False},
    "Cebolla, cruda": {"kcal": 36.0, "cho": 7.6, "azuc_tot": 1.7, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.1, "gsat": 0.04, "gtrans": 0.0, "fibra": 4.2, "sodio": 4.0, "edulc": False, "caf": False},
    "Champignones, enlatados": {"kcal": 21.0, "cho": 2.7, "azuc_tot": 2.3, "azuc_anad": 0.0, "prot": 1.9, "gtot": 0.3, "gsat": 0.04, "gtrans": 0.0, "fibra": 2.4, "sodio": 425.0, "edulc": False, "caf": False},
    "Champignones, frescos, crudos": {"kcal": 24.0, "cho": 2.3, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 3.1, "gtot": 0.3, "gsat": 0.05, "gtrans": 0.0, "fibra": 1.0, "sodio": 5.0, "edulc": False, "caf": False},
    "Chaucha, fresca, cruda": {"kcal": 29.0, "cho": 4.3, "azuc_tot": 3.3, "azuc_anad": 0.0, "prot": 2.4, "gtot": 0.2, "gsat": 0.05, "gtrans": 0.0, "fibra": 2.7, "sodio": 23.0, "edulc": False, "caf": False},
    "Chaucha, fresca, hervida": {"kcal": 29.0, "cho": 4.7, "azuc_tot": 3.6, "azuc_anad": 0.0, "prot": 1.9, "gtot": 0.3, "gsat": 0.06, "gtrans": 0.0, "fibra": 3.2, "sodio": 23.0, "edulc": False, "caf": False},
    "Coliflor, crudo": {"kcal": 23.0, "cho": 2.9, "azuc_tot": 1.9, "azuc_anad": 0.0, "prot": 2.4, "gtot": 0.2, "gsat": 0.13, "gtrans": 0.0, "fibra": 2.0, "sodio": 41.0, "edulc": False, "caf": False},
    "Espinaca, cruda": {"kcal": 21.0, "cho": 1.43, "azuc_tot": 0.42, "azuc_anad": 0.0, "prot": 2.86, "gtot": 0.39, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.2, "sodio": 79.0, "edulc": False, "caf": False},
    "Espinaca, hervida": {"kcal": 20.0, "cho": 1.35, "azuc_tot": 0.43, "azuc_anad": 0.0, "prot": 2.97, "gtot": 0.26, "gsat": 0.109, "gtrans": 0.0, "fibra": 2.4, "sodio": 70.0, "edulc": False, "caf": False},
    "Lechuga, cruda": {"kcal": 12.0, "cho": 1.4, "azuc_tot": 1.2, "azuc_anad": 0.0, "prot": 1.2, "gtot": 0.2, "gsat": 0.01, "gtrans": 0.0, "fibra": 1.4, "sodio": 13.0, "edulc": False, "caf": False},
    "Mandioca, cruda": {"kcal": 153.0, "cho": 36.3, "azuc_tot": 1.7, "azuc_anad": 0.0, "prot": 1.4, "gtot": 0.3, "gsat": 0.07, "gtrans": 0.0, "fibra": 1.8, "sodio": 14.0, "edulc": False, "caf": False},
    "Palmitos, enlatados": {"kcal": 25.0, "cho": 2.2, "azuc_tot": 2.4, "azuc_anad": 0.0, "prot": 2.5, "gtot": 0.6, "gsat": 0.13, "gtrans": 0.0, "fibra": 2.4, "sodio": 426.0, "edulc": False, "caf": False},
    "Papa, cruda": {"kcal": 79.0, "cho": 16.9, "azuc_tot": 1.2, "azuc_anad": 0.0, "prot": 2.7, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 2.4, "sodio": 24.0, "edulc": False, "caf": False},
    "Papa, hervida": {"kcal": 81.0, "cho": 18.2, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 1.7, "gtot": 0.1, "gsat": 0.03, "gtrans": 0.0, "fibra": 0.9, "sodio": 5.0, "edulc": False, "caf": False},
    "Puerro, crudo": {"kcal": 38.0, "cho": 6.1, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 2.5, "gtot": 0.4, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.8, "sodio": 81.0, "edulc": False, "caf": False},
    "Rúcula, cruda": {"kcal": 24.0, "cho": 2.1, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 2.6, "gtot": 0.7, "gsat": 0.09, "gtrans": 0.0, "fibra": 1.6, "sodio": 27.0, "edulc": False, "caf": False},
    "Tomate, crudo": {"kcal": 17.0, "cho": 2.9, "azuc_tot": 1.2, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.2, "sodio": 5.0, "edulc": False, "caf": False},
    "Tomate, puré de tomate": {"kcal": 37.0, "cho": 7.1, "azuc_tot": 4.8, "azuc_anad": 0.0, "prot": 1.7, "gtot": 0.2, "gsat": 0.09, "gtrans": 0.0, "fibra": 1.9, "sodio": 67.0, "edulc": False, "caf": False},
    "Zanahoria, cruda": {"kcal": 43.0, "cho": 4.7, "azuc_tot": 2.8, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.2, "gsat": 0.01, "gtrans": 0.0, "fibra": 4.5, "sodio": 22.0, "edulc": False, "caf": False},
    "Zanahoria, hervida": {"kcal": 26.0, "cho": 5.2, "azuc_tot": 3.0, "azuc_anad": 0.0, "prot": 0.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 3.0, "sodio": 58.0, "edulc": False, "caf": False},
    "Zapallito, crudo": {"kcal": 15.0, "cho": 1.0, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 0.8, "gtot": 0.3, "gsat": 0.09, "gtrans": 0.0, "fibra": 2.1, "sodio": 2.0, "edulc": False, "caf": False},
    "Zapallo, crudo": {"kcal": 36.0, "cho": 2.5, "azuc_tot": 1.3, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.1, "gsat": 0.07, "gtrans": 0.0, "fibra": 5.3, "sodio": 3.0, "edulc": False, "caf": False},
    "Zapallo, hervido": {"kcal": 28.0, "cho": 6.2, "azuc_tot": 2.5, "azuc_anad": 0.0, "prot": 0.7, "gtot": 0.1, "gsat": 0.04, "gtrans": 0.0, "fibra": 2.6, "sodio": 3.0, "edulc": False, "caf": False},
    "Zucchini, crudo": {"kcal": 16.0, "cho": 2.1, "azuc_tot": 2.5, "azuc_anad": 0.0, "prot": 1.2, "gtot": 0.3, "gsat": 0.09, "gtrans": 0.0, "fibra": 1.0, "sodio": 8.0, "edulc": False, "caf": False},

    # --- FRUTAS (SARA 2) ---
    "Banana": {"kcal": 92.0, "cho": 20.4, "azuc_tot": 12.2, "azuc_anad": 0.0, "prot": 1.2, "gtot": 0.2, "gsat": 0.112, "gtrans": 0.0, "fibra": 2.6, "sodio": 1.0, "edulc": False, "caf": False},
    "Manzana con piel": {"kcal": 48.0, "cho": 11.4, "azuc_tot": 10.4, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 2.4, "sodio": 1.0, "edulc": False, "caf": False},
    "Naranja": {"kcal": 43.0, "cho": 9.35, "azuc_tot": 9.35, "azuc_anad": 0.0, "prot": 0.94, "gtot": 0.12, "gsat": 0.023, "gtrans": 0.0, "fibra": 2.4, "sodio": 0.0, "edulc": False, "caf": False},
    "Frutilla": {"kcal": 31.0, "cho": 5.7, "azuc_tot": 4.9, "azuc_anad": 0.0, "prot": 0.8, "gtot": 0.6, "gsat": 0.02, "gtrans": 0.0, "fibra": 2.0, "sodio": 2.0, "edulc": False, "caf": False},
    "Limón": {"kcal": 35.0, "cho": 6.5, "azuc_tot": 2.5, "azuc_anad": 0.0, "prot": 0.9, "gtot": 0.6, "gsat": 0.09, "gtrans": 0.0, "fibra": 2.8, "sodio": 6.0, "edulc": False, "caf": False},
    "Palta": {"kcal": 190.0, "cho": 1.8, "azuc_tot": 0.7, "azuc_anad": 0.0, "prot": 1.9, "gtot": 19.5, "gsat": 4.1, "gtrans": 0.0, "fibra": 6.7, "sodio": 7.0, "edulc": False, "caf": False},
    "Pera": {"kcal": 55.0, "cho": 12.1, "azuc_tot": 9.8, "azuc_anad": 0.0, "prot": 0.7, "gtot": 0.4, "gsat": 0.02, "gtrans": 0.0, "fibra": 3.1, "sodio": 2.0, "edulc": False, "caf": False},
    "Uva": {"kcal": 73.0, "cho": 17.2, "azuc_tot": 15.5, "azuc_anad": 0.0, "prot": 0.7, "gtot": 0.2, "gsat": 0.05, "gtrans": 0.0, "fibra": 0.9, "sodio": 2.0, "edulc": False, "caf": False},
    "Uva pasa": {"kcal": 315.0, "cho": 74.8, "azuc_tot": 65.2, "azuc_anad": 0.0, "prot": 3.3, "gtot": 0.3, "gsat": 0.09, "gtrans": 0.0, "fibra": 4.5, "sodio": 26.0, "edulc": False, "caf": False},

    # --- SÉMOLAS, HARINAS Y CEREALES ---
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
    "Almidón de maíz (Maicena)": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Fécula / Almidón de mandioca": {"kcal": 363.0, "cho": 90.4, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Harina de maíz / Polenta": {"kcal": 307.0, "cho": 64.5, "azuc_tot": 0.6, "azuc_anad": 0.0, "prot": 9.1, "gtot": 1.39, "gsat": 0.17, "gtrans": 0.0, "fibra": 8.9, "sodio": 25.0, "edulc": False, "caf": False},
    "Harina de arroz": {"kcal": 348.0, "cho": 77.7, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 6.0, "gtot": 1.4, "gsat": 0.39, "gtrans": 0.0, "fibra": 2.4, "sodio": 0.0, "edulc": False, "caf": False},
    "Premezcla universal SIN TACC": {"kcal": 357.0, "cho": 82.5, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 2.8, "gtot": 1.8, "gsat": 1.0, "gtrans": 0.0, "fibra": 1.0, "sodio": 40.0, "edulc": False, "caf": False},
    "Fideos secos de trigo": {"kcal": 352.0, "cho": 71.5, "azuc_tot": 2.7, "azuc_anad": 0.0, "prot": 13.0, "gtot": 1.5, "gsat": 0.28, "gtrans": 0.0, "fibra": 3.2, "sodio": 6.0, "edulc": False, "caf": False},
    "Fideos frescos al huevo": {"kcal": 285.0, "cho": 54.7, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 11.3, "gtot": 2.3, "gsat": 0.33, "gtrans": 0.0, "fibra": 3.3, "sodio": 26.0, "edulc": False, "caf": False},
    "Lentejas secas": {"kcal": 301.0, "cho": 52.7, "azuc_tot": 2.0, "azuc_anad": 0.0, "prot": 20.8, "gtot": 0.8, "gsat": 0.15, "gtrans": 0.0, "fibra": 10.7, "sodio": 12.0, "edulc": False, "caf": False},
    "Garbanzos secos": {"kcal": 339.0, "cho": 50.8, "azuc_tot": 10.7, "azuc_anad": 0.0, "prot": 20.5, "gtot": 6.0, "gsat": 0.60, "gtrans": 0.0, "fibra": 12.2, "sodio": 24.0, "edulc": False, "caf": False},
    "Porotos secos": {"kcal": 276.0, "cho": 45.3, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 21.1, "gtot": 1.1, "gsat": 0.07, "gtrans": 0.0, "fibra": 15.2, "sodio": 8.0, "edulc": False, "caf": False},

    # --- LÁCTEOS, QUESOS Y HUEVOS ---
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

    # --- AZÚCARES, DULCES Y CONDIMENTOS ---
    "Azúcar blanca refinada común": {"kcal": 400.0, "cho": 100.0, "azuc_tot": 99.8, "azuc_anad": 99.8, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Miel pura de abejas": {"kcal": 330.0, "cho": 82.2, "azuc_tot": 82.1, "azuc_anad": 82.1, "prot": 0.3, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.2, "sodio": 4.0, "edulc": False, "caf": False},
    "Dulce de leche común": {"kcal": 315.0, "cho": 57.4, "azuc_tot": 49.7, "azuc_anad": 44.0, "prot": 6.5, "gtot": 6.6, "gsat": 4.07, "gtrans": 0.33, "fibra": 0.0, "sodio": 138.0, "edulc": False, "caf": False},
    "Sal fina de mesa común (NaCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 40000.0, "edulc": False, "caf": False},
    "Polvo de hornear": {"kcal": 96.0, "cho": 23.9, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.1, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.2, "sodio": 7893.0, "edulc": False, "caf": False},
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
    
    col_a, col_b = st.columns(2)
    with col_a:
        peso_cocido = st.number_input("Peso neto final tras cocción o merma (g)", min_value=1.0, value=500.0)
    with col_b:
        porcion = st.number_input("Tamaño de la porción según CAA (g)", min_value=1.0, value=50.0)

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

    # Panel de acceso a bases de datos de referencia (Prioridad secundaria si no está en SARA 2)
    with st.expander("🌐 Bases de Datos Internacionales y Comerciales de Respaldo"):
        st.write("Si el alimento o marca no figura en SARA 2, consultá estas bases oficiales de referencia:")
        
        busq_term = filtro_texto.strip() if filtro_texto else "alimento"
        term_enc = urllib.parse.quote(busq_term)

        # Fila 1: Bases Latinoamericanas y Comerciales
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

        st.divider()

        # Fila 2: Bases Globales de Alto Rango
        b4, b5, b6, b7 = st.columns(4)
        with b4:
            st.markdown("**USDA FoodData Central (EE.UU.)**")
            st.link_button("Buscar USDA", f"https://fdc.nal.usda.gov/fdc-app.html#/?query={term_enc}")
        with b5:
            st.markdown("**CIQUAL (Francia - ANSES)**")
            st.link_button("Abrir CIQUAL", "https://ciqual.anses.fr/")
        with b6:
            st.markdown("**CoFID (Reino Unido)**")
            st.link_button("Abrir CoFID", "https://www.gov.uk/government/publications/composition-of-foods-integrated-dataset-cofid")
        with b7:
            st.markdown("**FAO / INFOODS**")
            st.link_button("Abrir FAO", "https://www.fao.org/infoods/infoods/tables-and-databases/es/")

    # Formulario para incorporar alimento manual o externo
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

        # Porcentajes de Valor Diario (%VD) según CAA Cap. V
        vd_kcal = round((p_kcal / 2000.0) * 100)
        vd_cho = round((p_cho / 300.0) * 100)
        vd_prot = round((p_prot / 75.0) * 100)
        vd_gtot = round((p_gtot / 55.0) * 100)
        vd_gsat = round((p_gsat / 22.0) * 100)
        vd_fibra = round((p_fibra / 25.0) * 100)
        vd_sodio = round((p_sodio / 2000.0) * 100)

        # Algoritmo Ley 27.642 (Etapa 2 definitiva)
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
