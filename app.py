import streamlit as st
import pandas as pd
import requests

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

# ==========================================================
# BASE OFICIAL DE COMPOSICIÓN DE ALIMENTOS (SARA 2 - ENNyS 2)
# ==========================================================
SARA2_DICT = {
    # Cereales, Harinas y Legumbres
    "Harina de trigo 000 fortificada": {"kcal": 329.0, "azucar": 0.0, "gtot": 1.0, "gsat": 0.16, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo 0000 fortificada": {"kcal": 353.0, "azucar": 0.0, "gtot": 0.9, "gsat": 0.15, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo integral": {"kcal": 308.0, "azucar": 0.0, "gtot": 3.0, "gsat": 0.43, "sodio": 16.0, "edulc": False, "caf": False},
    "Harina leudante": {"kcal": 329.0, "azucar": 0.0, "gtot": 1.0, "gsat": 0.16, "sodio": 714.0, "edulc": False, "caf": False},
    "Almidón de maíz (Maicena)": {"kcal": 363.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.01, "sodio": 9.0, "edulc": False, "caf": False},
    "Almidón de mandioca / Tapioca": {"kcal": 363.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.01, "sodio": 9.0, "edulc": False, "caf": False},
    "Harina de maíz / Polenta": {"kcal": 307.0, "azucar": 0.0, "gtot": 1.39, "gsat": 0.17, "sodio": 25.0, "edulc": False, "caf": False},
    "Harina de arroz": {"kcal": 348.0, "azucar": 0.0, "gtot": 1.4, "gsat": 0.39, "sodio": 0.0, "edulc": False, "caf": False},
    "Harina de avena / Avena arrollada": {"kcal": 357.0, "azucar": 0.0, "gtot": 7.5, "gsat": 1.52, "sodio": 2.0, "edulc": False, "caf": False},
    "Harina de cebada": {"kcal": 328.0, "azucar": 0.0, "gtot": 1.7, "gsat": 0.34, "sodio": 4.0, "edulc": False, "caf": False},
    "Harina de centeno": {"kcal": 333.0, "azucar": 0.0, "gtot": 0.9, "gsat": 0.15, "sodio": 2.0, "edulc": False, "caf": False},
    "Harina de garbanzos": {"kcal": 338.0, "azucar": 0.0, "gtot": 6.7, "gsat": 0.69, "sodio": 64.0, "edulc": False, "caf": False},
    "Harina de soja": {"kcal": 338.0, "azucar": 0.0, "gtot": 8.9, "gsat": 1.29, "sodio": 9.0, "edulc": False, "caf": False},
    "Harina de quinoa": {"kcal": 304.0, "azucar": 0.0, "gtot": 1.0, "gsat": 0.12, "sodio": 2.0, "edulc": False, "caf": False},
    "Harina de algarrobo": {"kcal": 221.0, "azucar": 0.0, "gtot": 0.7, "gsat": 0.09, "sodio": 35.0, "edulc": False, "caf": False},
    "Salvado de trigo": {"kcal": 216.0, "azucar": 0.0, "gtot": 5.5, "gsat": 0.89, "sodio": 27.0, "edulc": False, "caf": False},
    "Salvado de avena": {"kcal": 246.0, "azucar": 0.0, "gtot": 7.0, "gsat": 1.33, "sodio": 4.0, "edulc": False, "caf": False},
    "Gérmen de trigo": {"kcal": 334.0, "azucar": 0.0, "gtot": 9.7, "gsat": 1.67, "sodio": 12.0, "edulc": False, "caf": False},
    "Arroz blanco": {"kcal": 339.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.05, "sodio": 4.0, "edulc": False, "caf": False},
    "Arroz integral": {"kcal": 350.0, "azucar": 0.0, "gtot": 3.2, "gsat": 0.59, "sodio": 5.0, "edulc": False, "caf": False},
    "Fideos secos de trigo": {"kcal": 352.0, "azucar": 0.0, "gtot": 1.5, "gsat": 0.28, "sodio": 6.0, "edulc": False, "caf": False},
    "Arveja seca cruda": {"kcal": 311.0, "azucar": 0.0, "gtot": 2.9, "gsat": 0.41, "sodio": 16.0, "edulc": False, "caf": False},
    "Garbanzos secos": {"kcal": 339.0, "azucar": 0.0, "gtot": 6.0, "gsat": 0.60, "sodio": 24.0, "edulc": False, "caf": False},
    "Lentejas secas": {"kcal": 301.0, "azucar": 0.0, "gtot": 0.8, "gsat": 0.15, "sodio": 12.0, "edulc": False, "caf": False},
    "Porotos secos": {"kcal": 276.0, "azucar": 0.0, "gtot": 1.1, "gsat": 0.07, "sodio": 8.0, "edulc": False, "caf": False},
    "Soja texturizada": {"kcal": 283.0, "azucar": 0.0, "gtot": 1.2, "gsat": 0.21, "sodio": 20.0, "edulc": False, "caf": False},
    
    # Grasas, Aceites y Semillas
    "Aceite de girasol": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 10.6, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de girasol alto oleico": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 9.6, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de maíz": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 15.2, "sodio": 2.0, "edulc": False, "caf": False},
    "Aceite de oliva": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 17.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de soja": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 15.65, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de canola": {"kcal": 892.0, "azucar": 0.0, "gtot": 99.1, "gsat": 7.37, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de coco": {"kcal": 900.0, "azucar": 0.0, "gtot": 100.0, "gsat": 82.48, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada": {"kcal": 899.0, "azucar": 0.0, "gtot": 99.9, "gsat": 49.8, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa de cerdo refinada": {"kcal": 898.0, "azucar": 0.0, "gtot": 99.8, "gsat": 39.2, "sodio": 0.0, "edulc": False, "caf": False},
    "Manteca": {"kcal": 758.0, "azucar": 0.0, "gtot": 84.0, "gsat": 50.93, "sodio": 223.0, "edulc": False, "caf": False},
    "Margarina vegetal": {"kcal": 559.0, "azucar": 0.0, "gtot": 61.7, "gsat": 27.6, "sodio": 295.0, "edulc": False, "caf": False},
    "Semillas de girasol peladas": {"kcal": 592.0, "azucar": 0.0, "gtot": 51.5, "gsat": 4.46, "sodio": 9.0, "edulc": False, "caf": False},
    "Semillas de chía": {"kcal": 374.0, "azucar": 0.0, "gtot": 30.7, "gsat": 3.33, "sodio": 16.0, "edulc": False, "caf": False},
    "Semillas de lino": {"kcal": 459.0, "azucar": 0.0, "gtot": 42.2, "gsat": 3.66, "sodio": 30.0, "edulc": False, "caf": False},
    "Semillas de sésamo": {"kcal": 565.0, "azucar": 0.0, "gtot": 49.7, "gsat": 6.96, "sodio": 11.0, "edulc": False, "caf": False},
    "Nuez": {"kcal": 690.0, "azucar": 0.0, "gtot": 67.4, "gsat": 6.13, "sodio": 3.0, "edulc": False, "caf": False},
    "Almendra": {"kcal": 570.0, "azucar": 0.0, "gtot": 49.9, "gsat": 3.8, "sodio": 1.0, "edulc": False, "caf": False},
    "Maní tostado sin sal": {"kcal": 596.0, "azucar": 0.0, "gtot": 49.7, "gsat": 7.72, "sodio": 6.0, "edulc": False, "caf": False},

    # Azúcares, Mieles y Dulces
    "Azúcar blanca común": {"kcal": 400.0, "azucar": 99.8, "gtot": 0.0, "gsat": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Azúcar impalpable": {"kcal": 399.0, "azucar": 97.8, "gtot": 0.0, "gsat": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Azúcar mascabo / morena": {"kcal": 393.0, "azucar": 97.0, "gtot": 0.0, "gsat": 0.0, "sodio": 28.0, "edulc": False, "caf": False},
    "Miel": {"kcal": 330.0, "azucar": 82.1, "gtot": 0.0, "gsat": 0.0, "sodio": 4.0, "edulc": False, "caf": False},
    "Jarabe de glucosa": {"kcal": 339.0, "azucar": 40.2, "gtot": 0.0, "gsat": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Dulce de leche común": {"kcal": 315.0, "azucar": 44.0, "gtot": 6.6, "gsat": 4.07, "sodio": 138.0, "edulc": False, "caf": False},
    "Dulce de batata": {"kcal": 255.0, "azucar": 52.0, "gtot": 0.1, "gsat": 0.0, "sodio": 19.0, "edulc": False, "caf": False},
    "Dulce de membrillo": {"kcal": 269.0, "azucar": 52.0, "gtot": 0.1, "gsat": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Mermelada con azúcar": {"kcal": 273.0, "azucar": 43.7, "gtot": 0.1, "gsat": 0.01, "sodio": 32.0, "edulc": False, "caf": False},
    "Cacao amargo en polvo": {"kcal": 285.0, "azucar": 0.0, "gtot": 13.7, "gsat": 8.07, "sodio": 21.0, "edulc": False, "caf": False},
    "Chocolate semiamargo": {"kcal": 547.0, "azucar": 36.7, "gtot": 38.3, "gsat": 22.03, "sodio": 10.0, "edulc": False, "caf": False},
    "Chocolate con leche": {"kcal": 522.0, "azucar": 44.0, "gtot": 29.7, "gsat": 18.51, "sodio": 79.0, "edulc": False, "caf": False},

    # Lácteos y Huevos
    "Leche entera líquida": {"kcal": 58.0, "azucar": 0.0, "gtot": 2.9, "gsat": 1.87, "sodio": 57.0, "edulc": False, "caf": False},
    "Leche parcialmente descremada": {"kcal": 44.0, "azucar": 0.0, "gtot": 1.4, "gsat": 0.95, "sodio": 55.0, "edulc": False, "caf": False},
    "Leche entera en polvo": {"kcal": 480.0, "azucar": 0.0, "gtot": 24.8, "gsat": 15.54, "sodio": 404.0, "edulc": False, "caf": False},
    "Leche descremada en polvo": {"kcal": 360.0, "azucar": 0.0, "gtot": 1.0, "gsat": 0.5, "sodio": 563.0, "edulc": False, "caf": False},
    "Crema de leche (36% grasa)": {"kcal": 347.0, "azucar": 0.0, "gtot": 36.1, "gsat": 23.03, "sodio": 27.0, "edulc": False, "caf": False},
    "Huevo entero": {"kcal": 156.0, "azucar": 0.0, "gtot": 11.8, "gsat": 3.18, "sodio": 135.0, "edulc": False, "caf": False},
    "Huevo - Clara": {"kcal": 51.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.0, "sodio": 186.0, "edulc": False, "caf": False},
    "Huevo - Yema": {"kcal": 339.0, "azucar": 0.0, "gtot": 28.7, "gsat": 10.33, "sodio": 65.0, "edulc": False, "caf": False},
    "Queso Cremoso": {"kcal": 310.0, "azucar": 0.0, "gtot": 24.9, "gsat": 13.66, "sodio": 704.0, "edulc": False, "caf": False},
    "Queso Cuartirolo": {"kcal": 280.0, "azucar": 0.0, "gtot": 21.4, "gsat": 13.66, "sodio": 360.0, "edulc": False, "caf": False},
    "Queso Muzzarella": {"kcal": 278.0, "azucar": 0.0, "gtot": 19.3, "gsat": 13.9, "sodio": 486.0, "edulc": False, "caf": False},
    "Queso de máquina / Barra (Tibo)": {"kcal": 356.0, "azucar": 0.0, "gtot": 27.4, "gsat": 17.61, "sodio": 819.0, "edulc": False, "caf": False},
    "Queso Pategrás / Mar del Plata": {"kcal": 332.0, "azucar": 0.0, "gtot": 25.6, "gsat": 21.27, "sodio": 720.0, "edulc": False, "caf": False},
    "Queso Reggianito / Sardo": {"kcal": 381.0, "azucar": 0.0, "gtot": 25.0, "gsat": 14.85, "sodio": 1175.0, "edulc": False, "caf": False},
    "Queso Parmesano": {"kcal": 350.0, "azucar": 0.0, "gtot": 24.4, "gsat": 13.5, "sodio": 1804.0, "edulc": False, "caf": False},
    "Queso Azul": {"kcal": 368.0, "azucar": 0.0, "gtot": 31.1, "gsat": 19.26, "sodio": 1210.0, "edulc": False, "caf": False},
    "Queso Port Salut": {"kcal": 225.0, "azucar": 0.0, "gtot": 12.9, "gsat": 7.15, "sodio": 55.0, "edulc": False, "caf": False},
    "Queso untable clásico": {"kcal": 284.0, "azucar": 0.0, "gtot": 27.0, "gsat": 16.0, "sodio": 409.0, "edulc": False, "caf": False},
    "Ricota": {"kcal": 169.0, "azucar": 0.0, "gtot": 11.8, "gsat": 7.28, "sodio": 146.0, "edulc": False, "caf": False},

    # Carnes y Pescados
    "Carne vacuna magra (nalga/peceto)": {"kcal": 138.0, "azucar": 0.0, "gtot": 5.5, "gsat": 2.15, "sodio": 60.0, "edulc": False, "caf": False},
    "Carne vacuna semigrasa (roast beef)": {"kcal": 176.0, "azucar": 0.0, "gtot": 10.1, "gsat": 4.12, "sodio": 61.0, "edulc": False, "caf": False},
    "Carne vacuna picada común": {"kcal": 210.0, "azucar": 0.0, "gtot": 14.4, "gsat": 6.04, "sodio": 52.0, "edulc": False, "caf": False},
    "Pollo pechuga sin piel": {"kcal": 114.0, "azucar": 0.0, "gtot": 2.6, "gsat": 0.69, "sodio": 45.0, "edulc": False, "caf": False},
    "Pollo entero con piel": {"kcal": 208.0, "azucar": 0.0, "gtot": 15.5, "gsat": 4.41, "sodio": 69.0, "edulc": False, "caf": False},
    "Carne de cerdo magra": {"kcal": 206.0, "azucar": 0.0, "gtot": 14.8, "gsat": 4.92, "sodio": 57.0, "edulc": False, "caf": False},
    "Bondiola (fiambre)": {"kcal": 264.0, "azucar": 0.0, "gtot": 22.0, "gsat": 7.94, "sodio": 1250.0, "edulc": False, "caf": False},
    "Jamón cocido": {"kcal": 107.0, "azucar": 0.0, "gtot": 3.3, "gsat": 1.1, "sodio": 800.0, "edulc": False, "caf": False},
    "Jamón crudo": {"kcal": 319.0, "azucar": 0.0, "gtot": 22.6, "gsat": 7.94, "sodio": 2130.0, "edulc": False, "caf": False},
    "Salame": {"kcal": 372.0, "azucar": 0.0, "gtot": 31.7, "gsat": 11.42, "sodio": 1358.0, "edulc": False, "caf": False},
    "Salchicha de Viena": {"kcal": 226.0, "azucar": 0.0, "gtot": 17.2, "gsat": 6.08, "sodio": 1297.0, "edulc": False, "caf": False},
    "Merluza filet fresco": {"kcal": 80.0, "azucar": 0.0, "gtot": 1.3, "gsat": 0.3, "sodio": 91.0, "edulc": False, "caf": False},
    "Atún enlatado al natural": {"kcal": 86.0, "azucar": 0.0, "gtot": 1.0, "gsat": 0.21, "sodio": 247.0, "edulc": False, "caf": False},
    "Atún enlatado en aceite": {"kcal": 190.0, "azucar": 0.0, "gtot": 8.2, "gsat": 1.53, "sodio": 416.0, "edulc": False, "caf": False},

    # Hortalizas y Frutas
    "Cebolla": {"kcal": 36.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.04, "sodio": 4.0, "edulc": False, "caf": False},
    "Zanahoria": {"kcal": 43.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.01, "sodio": 22.0, "edulc": False, "caf": False},
    "Tomate redondo": {"kcal": 17.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.03, "sodio": 5.0, "edulc": False, "caf": False},
    "Tomate puré / triturado": {"kcal": 37.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.09, "sodio": 67.0, "edulc": False, "caf": False},
    "Morrón / Ají rojo": {"kcal": 22.0, "azucar": 0.0, "gtot": 0.3, "gsat": 0.06, "sodio": 4.0, "edulc": False, "caf": False},
    "Ajo": {"kcal": 91.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.09, "sodio": 17.0, "edulc": False, "caf": False},
    "Espinaca": {"kcal": 21.0, "azucar": 0.0, "gtot": 0.39, "gsat": 0.06, "sodio": 79.0, "edulc": False, "caf": False},
    "Acelga": {"kcal": 18.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.03, "sodio": 213.0, "edulc": False, "caf": False},
    "Papa": {"kcal": 79.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.03, "sodio": 24.0, "edulc": False, "caf": False},
    "Batata": {"kcal": 73.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.02, "sodio": 6.0, "edulc": False, "caf": False},
    "Zapallo": {"kcal": 36.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.07, "sodio": 3.0, "edulc": False, "caf": False},
    "Manzana": {"kcal": 48.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.03, "sodio": 1.0, "edulc": False, "caf": False},
    "Banana": {"kcal": 92.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.112, "sodio": 1.0, "edulc": False, "caf": False},
    "Naranja": {"kcal": 43.0, "azucar": 0.0, "gtot": 0.12, "gsat": 0.023, "sodio": 0.0, "edulc": False, "caf": False},
    "Limón - Jugo exprimido": {"kcal": 30.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.04, "sodio": 1.0, "edulc": False, "caf": False},
    "Frutilla": {"kcal": 31.0, "azucar": 0.0, "gtot": 0.6, "gsat": 0.02, "sodio": 2.0, "edulc": False, "caf": False},
    "Uvas": {"kcal": 73.0, "azucar": 0.0, "gtot": 0.2, "gsat": 0.05, "sodio": 2.0, "edulc": False, "caf": False},
    "Pasas de uva": {"kcal": 315.0, "azucar": 0.0, "gtot": 0.3, "gsat": 0.09, "sodio": 26.0, "edulc": False, "caf": False},

    # Sales, Aditivos y Otros
    "Sal común de mesa (NaCl)": {"kcal": 0.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 40000.0, "edulc": False, "caf": False},
    "Sal modificada (66% Cloruro de Sodio)": {"kcal": 0.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 26400.0, "edulc": False, "caf": False},
    "Sal sin sodio (Cloruro de Potasio)": {"kcal": 0.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Polvo de hornear": {"kcal": 96.0, "azucar": 0.0, "gtot": 0.1, "gsat": 0.0, "sodio": 7893.0, "edulc": False, "caf": False},
    "Levadura fresca prensada": {"kcal": 91.0, "azucar": 0.0, "gtot": 1.9, "gsat": 0.24, "sodio": 30.0, "edulc": False, "caf": False},
    "Vinagre": {"kcal": 1.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 8.0, "edulc": False, "caf": False},
    "Agua potable": {"kcal": 0.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 5.0, "edulc": False, "caf": False},
    "Edulcorante no calórico": {"kcal": 0.0, "azucar": 0.0, "gtot": 0.0, "gsat": 0.0, "sodio": 10.0, "edulc": True, "caf": False},
    "Café instantáneo / infusión": {"kcal": 355.0, "azucar": 0.0, "gtot": 0.5, "gsat": 0.2, "sodio": 37.0, "edulc": False, "caf": True}
}

lista_alimentos_ordenada = sorted(list(SARA2_DICT.keys()))

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

    st.subheader(f"1. Seleccionar ingrediente ({len(lista_alimentos_ordenada)} disponibles)")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        ing_elegido = st.selectbox("Escribí o elegí de la lista:", lista_alimentos_ordenada)
    with col2:
        gramos_ing = st.number_input("Cantidad a formular (gramos):", min_value=0.1, value=100.0, step=5.0)
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Agregar a la receta"):
            if "receta" not in st.session_state:
                st.session_state.receta = []
            datos = SARA2_DICT[ing_elegido]
            st.session_state.receta.append({
                "Ingrediente": ing_elegido,
                "Gramos": float(gramos_ing),
                "Kcal/100g": float(datos["kcal"]),
                "Azúcar_Añadido_g": float(datos["azucar"]),
                "Grasa_Tot_g": float(datos["gtot"]),
                "Grasa_Sat_g": float(datos["gsat"]),
                "Sodio_mg": float(datos["sodio"]),
                "Edulcorante": bool(datos["edulc"]),
                "Cafeina": bool(datos["caf"])
            })
            st.rerun()

    if "receta" not in st.session_state:
        st.session_state.receta = [
            {"Ingrediente": "Harina de trigo 000 fortificada", "Gramos": 300.0, "Kcal/100g": 329.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 1.0, "Grasa_Sat_g": 0.16, "Sodio_mg": 7.0, "Edulcorante": False, "Cafeina": False},
            {"Ingrediente": "Sal común de mesa (NaCl)", "Gramos": 10.0, "Kcal/100g": 0.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 0.0, "Grasa_Sat_g": 0.0, "Sodio_mg": 40000.0, "Edulcorante": False, "Cafeina": False},
            {"Ingrediente": "Grasa vacuna refinada", "Gramos": 80.0, "Kcal/100g": 899.0, "Azúcar_Añadido_g": 0.0, "Grasa_Tot_g": 99.9, "Grasa_Sat_g": 49.8, "Sodio_mg": 0.0, "Edulcorante": False, "Cafeina": False}
        ]

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
        
        tot_kcal = sum((float(row["Gramos"]) * float(row["Kcal/100g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_azucar = sum((float(row["Gramos"]) * float(row["Azúcar_Añadido_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_grasa_tot = sum((float(row["Gramos"]) * float(row["Grasa_Tot_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_grasa_sat = sum((float(row["Gramos"]) * float(row["Grasa_Sat_g"])) / 100.0 for _, row in df_limpio.iterrows())
        tot_sodio = sum((float(row["Gramos"]) * float(row["Sodio_mg"])) / 100.0 for _, row in df_limpio.iterrows())
        tiene_edulcorante = any(df_limpio["Edulcorante"])
        tiene_cafeina = any(df_limpio["Cafeina"])

        f_100 = 100.0 / peso_cocido
        c_kcal = tot_kcal * f_100
        c_kj = c_kcal * 4.184
        c_azucar = tot_azucar * f_100
        c_grasa_tot = tot_grasa_tot * f_100
        c_grasa_sat = tot_grasa_sat * f_100
        c_sodio = tot_sodio * f_100

        p_kcal = c_kcal * porcion / 100.0
        p_kj = c_kj * porcion / 100.0
        vd_kcal = round((p_kcal / 2000.0) * 100)

        # Algoritmo Ley 27.642 (Etapa 2 definitiva)
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
        st.subheader("Resultados del Rótulo Nutricional:")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("#### Valor Energético (CAA Cap. V)")
            st.markdown(f"• **Cada 100 g:** {c_kcal:.0f} kcal = {c_kj:.0f} kJ")
            st.markdown(f"• **Por porción ({porcion:.0f} g):** {p_kcal:.0f} kcal = {p_kj:.0f} kJ (%VD: {vd_kcal}%)")
            st.markdown("#### Nutrientes Críticos (Ley 27.642)")
            st.markdown(f"• **Azúcares añadidos (100 g):** {c_azucar:.1f} g")
            st.markdown(f"• **Grasas Totales (100 g):** {c_grasa_tot:.1f} g")
            st.markdown(f"• **Grasas Saturadas (100 g):** {c_grasa_sat:.1f} g")
            st.markdown(f"• **Sodio (100 g):** {c_sodio:.1f} mg")
        with r2:
            st.markdown("### Sellos Frontales y Leyendas Obligatorias:")
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
