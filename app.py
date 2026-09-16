import streamlit as st
import pandas as pd
import requests
import urllib.parse
import unicodedata
import os
import base64
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Plataforma Bromatológica - Ecomeg", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def normalizar_col(c):
    return ''.join(ch for ch in unicodedata.normalize('NFD', str(c).strip().lower()) if unicodedata.category(ch) != 'Mn')

def obtener_usuarios():
    try:
        df = conn.read(worksheet="usuarios", ttl="0s")
        if df is not None and not df.empty:
            df = df.dropna(how="all")
            df.columns = [normalizar_col(c) for c in df.columns]
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["usuario", "clave", "rol", "token_sesion", "estado"])

def registrar_evento(usuario, accion, detalle=""):
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_met = conn.read(worksheet="metricas", ttl="0s")
        if df_met is not None and not df_met.empty:
            df_met = df_met.dropna(how="all")
            df_met.columns = [normalizar_col(c) for c in df_met.columns]
        else:
            df_met = pd.DataFrame(columns=["fecha_hora", "usuario", "accion", "detalle"])
        
        nueva_fila = pd.DataFrame([{"fecha_hora": ahora, "usuario": usuario, "accion": accion, "detalle": detalle}])
        df_act = pd.concat([df_met, nueva_fila], ignore_index=True)
        conn.update(worksheet="metricas", data=df_act)
    except Exception:
        pass

# --- GESTIÓN DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.rol = "cliente"
    st.session_state.token = ""

def login():
    st.markdown("### Acceso Exclusivo - Plataforma Bromatológica Ecomeg®")
    u_ing = st.text_input("Usuario")
    c_ing = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        df_u = obtener_usuarios()
        
        if "usuario" not in df_u.columns or "clave" not in df_u.columns:
            st.error("Error en las columnas de Google Sheets. Deben llamarse: usuario, clave, rol, token_sesion, estado.")
            return

        u_limpio = str(u_ing).strip().lower()
        c_limpio = str(c_ing).strip()
        
        filtro = (df_u["usuario"].astype(str).str.strip().str.lower() == u_limpio) & (df_u["clave"].astype(str).str.strip() == c_limpio)
        coincidencia = df_u[filtro]

        if not coincidencia.empty:
            fila = coincidencia.iloc[0]
            estado_cuenta = str(fila.get("estado", "activo")).strip().lower()
            
            if estado_cuenta == "activo":
                nuevo_token = str(uuid.uuid4())
                rol_usuario = str(fila.get("rol", "cliente")).strip().lower()

                st.session_state.autenticado = True
                st.session_state.usuario = str(fila.get("usuario")).strip()
                st.session_state.rol = rol_usuario
                st.session_state.token = nuevo_token

                if rol_usuario != "admin":
                    df_u.loc[filtro, "token_sesion"] = nuevo_token
                    try:
                        conn.update(worksheet="usuarios", data=df_u)
                    except Exception:
                        pass

                registrar_evento(st.session_state.usuario, "Inicio de sesión", f"Rol: {rol_usuario}")
                st.rerun()
            else:
                st.error("Suscripción inactiva. Comuníquese con la administración.")
        else:
            st.error("Usuario o clave incorrectos.")

if not st.session_state.autenticado:
    login()
    st.stop()

# Control de sesión única para clientes
if st.session_state.rol != "admin":
    df_verif = obtener_usuarios()
    if "usuario" in df_verif.columns and "token_sesion" in df_verif.columns:
        match_u = df_verif[df_verif["usuario"].astype(str).str.strip().str.lower() == st.session_state.usuario.lower()]
        if not match_u.empty:
            token_en_base = str(match_u.iloc[0].get("token_sesion", ""))
            if token_en_base and token_en_base != st.session_state.token:
                st.session_state.autenticado = False
                st.error("Se detectó un nuevo inicio de sesión con esta cuenta en otro equipo. Esta sesión fue finalizada.")
                st.stop()

# --- BARRA LATERAL ---
st.sidebar.markdown(f"**Usuario:** `{st.session_state.usuario}`")
st.sidebar.markdown(f"**Perfil:** `{'Administrador' if st.session_state.rol == 'admin' else 'Cliente'}`")
if st.sidebar.button("Cerrar Sesión"):
    registrar_evento(st.session_state.usuario, "Cierre de sesión")
    st.session_state.autenticado = False
    st.rerun()

if st.session_state.rol == "admin":
    tab1, tab2, tab3 = st.tabs(["📊 Calculadora & Sellos", "💬 Asistente Técnico", "📈 Auditoría y Clientes"])
else:
    tab1, tab2 = st.tabs(["📊 Calculadora & Sellos", "💬 Asistente Técnico"])

def normalizar_texto(t):
    if not t:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(t).lower()) if unicodedata.category(c) != 'Mn')

def obtener_logo_base64():
    archivos = ["Logo ECOMEG Transparente.png", "Logo ECOMEG Transparente.PNG", "logo_ecomeg.png", "ecomeg (R).png"]
    for arch in archivos:
        if os.path.exists(arch):
            with open(arch, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

# ==============================================================================
# BASE DE DATOS UNIFICADA: SARA 2 + ARGENFOODS (UNLu)
# ==============================================================================
BASE_NUTRICIONAL = {
    # --- MATERIA GRASA / ACEITES ---
    "Aceite de girasol [SARA 2]": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de oliva virgen extra [SARA 2]": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 17.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de maíz [SARA 2]": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 15.2, "gtrans": 0.0, "fibra": 0.0, "sodio": 2.0, "edulc": False, "caf": False},
    "Aceite de soja [ARGENFOODS]": {"kcal": 884.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 14.4, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada [SARA 2]": {"kcal": 899.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.9, "gsat": 49.8, "gtrans": 3.7, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Manteca de vaca [SARA 2]": {"kcal": 758.0, "cho": 0.1, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 0.5, "gtot": 84.0, "gsat": 50.93, "gtrans": 3.28, "fibra": 0.0, "sodio": 223.0, "edulc": False, "caf": False},
    "Margarina vegetal [SARA 2]": {"kcal": 559.0, "cho": 0.7, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.2, "gtot": 61.7, "gsat": 27.6, "gtrans": 0.88, "fibra": 0.0, "sodio": 295.0, "edulc": False, "caf": False},

    # --- FARINÁCEOS, SÉMOLAS Y LEGUMBRES ---
    "Sémola de trigo / Semolín candeal [SARA 2]": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Gluten puro de trigo en polvo [SARA 2]": {"kcal": 370.0, "cho": 13.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 75.0, "gtot": 1.9, "gsat": 0.3, "gtrans": 0.0, "fibra": 1.5, "sodio": 70.0, "edulc": False, "caf": False},
    "Harina de trigo 000 fortificada [SARA 2]": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo 0000 fortificada [SARA 2]": {"kcal": 353.0, "cho": 74.0, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 11.6, "gtot": 0.9, "gsat": 0.15, "gtrans": 0.0, "fibra": 2.5, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo integral [SARA 2]": {"kcal": 308.0, "cho": 58.8, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 11.4, "gtot": 3.0, "gsat": 0.43, "gtrans": 0.0, "fibra": 12.6, "sodio": 16.0, "edulc": False, "caf": False},
    "Harina de maíz / Polenta [ARGENFOODS]": {"kcal": 361.0, "cho": 76.8, "azuc_tot": 0.6, "azuc_anad": 0.0, "prot": 6.9, "gtot": 1.4, "gsat": 0.2, "gtrans": 0.0, "fibra": 7.3, "sodio": 1.0, "edulc": False, "caf": False},
    "Almidón de maíz (Maicena) [ARGENFOODS]": {"kcal": 381.0, "cho": 91.3, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.3, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 0.9, "sodio": 9.0, "edulc": False, "caf": False},
    "Fécula de mandioca [ARGENFOODS]": {"kcal": 360.0, "cho": 88.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.6, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 0.4, "sodio": 14.0, "edulc": False, "caf": False},
    "Arroz blanco pulido [ARGENFOODS]": {"kcal": 360.0, "cho": 79.3, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 6.6, "gtot": 0.6, "gsat": 0.18, "gtrans": 0.0, "fibra": 1.3, "sodio": 5.0, "edulc": False, "caf": False},
    "Lentejas secas [ARGENFOODS]": {"kcal": 338.0, "cho": 60.0, "azuc_tot": 2.0, "azuc_anad": 0.0, "prot": 25.0, "gtot": 1.0, "gsat": 0.15, "gtrans": 0.0, "fibra": 11.0, "sodio": 6.0, "edulc": False, "caf": False},
    "Porotos secos [ARGENFOODS]": {"kcal": 333.0, "cho": 60.3, "azuc_tot": 2.2, "azuc_anad": 0.0, "prot": 23.6, "gtot": 0.8, "gsat": 0.12, "gtrans": 0.0, "fibra": 15.0, "sodio": 12.0, "edulc": False, "caf": False},

    # --- VEGETALES Y HORTALIZAS ---
    "Acelga, cruda [SARA 2]": {"kcal": 18.0, "cho": 2.1, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.6, "sodio": 213.0, "edulc": False, "caf": False},
    "Acelga, hervida [SARA 2]": {"kcal": 16.0, "cho": 2.0, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.9, "gtot": 0.1, "gsat": 0.01, "gtrans": 0.0, "fibra": 2.1, "sodio": 179.0, "edulc": False, "caf": False},
    "Espinaca, cruda [SARA 2]": {"kcal": 21.0, "cho": 1.43, "azuc_tot": 0.42, "azuc_anad": 0.0, "prot": 2.86, "gtot": 0.39, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.2, "sodio": 79.0, "edulc": False, "caf": False},
    "Ajo, crudo [SARA 2]": {"kcal": 91.0, "cho": 17.9, "azuc_tot": 2.1, "azuc_anad": 0.0, "prot": 4.4, "gtot": 0.2, "gsat": 0.09, "gtrans": 0.0, "fibra": 2.1, "sodio": 17.0, "edulc": False, "caf": False},
    "Cebolla, cruda [SARA 2]": {"kcal": 36.0, "cho": 7.6, "azuc_tot": 1.7, "azuc_anad": 0.0, "prot": 1.1, "gtot": 0.1, "gsat": 0.04, "gtrans": 0.0, "fibra": 1.7, "sodio": 4.0, "edulc": False, "caf": False},
    "Tomate perita maduro [ARGENFOODS]": {"kcal": 18.0, "cho": 3.9, "azuc_tot": 2.6, "azuc_anad": 0.0, "prot": 0.9, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.2, "sodio": 5.0, "edulc": False, "caf": False},
    "Papa blanca, cruda [ARGENFOODS]": {"kcal": 77.0, "cho": 17.5, "azuc_tot": 0.8, "azuc_anad": 0.0, "prot": 2.0, "gtot": 0.1, "gsat": 0.03, "gtrans": 0.0, "fibra": 2.2, "sodio": 6.0, "edulc": False, "caf": False},
    "Zanahoria fresca [ARGENFOODS]": {"kcal": 41.0, "cho": 9.6, "azuc_tot": 4.7, "azuc_anad": 0.0, "prot": 0.9, "gtot": 0.2, "gsat": 0.04, "gtrans": 0.0, "fibra": 2.8, "sodio": 69.0, "edulc": False, "caf": False},
    "Calabaza / Zapallo anco [ARGENFOODS]": {"kcal": 26.0, "cho": 6.5, "azuc_tot": 2.2, "azuc_anad": 0.0, "prot": 1.0, "gtot": 0.1, "gsat": 0.02, "gtrans": 0.0, "fibra": 0.5, "sodio": 1.0, "edulc": False, "caf": False},

    # --- CACAO, DULCES Y CHOCOLATES ---
    "Cacao en polvo amargo [ARGENFOODS]": {"kcal": 355.0, "cho": 49.0, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 19.6, "gtot": 11.0, "gsat": 6.5, "gtrans": 0.0, "fibra": 28.0, "sodio": 21.0, "edulc": False, "caf": True},
    "Chocolate semi-amargo / cobertura [ARGENFOODS]": {"kcal": 530.0, "cho": 55.0, "azuc_tot": 48.0, "azuc_anad": 48.0, "prot": 5.5, "gtot": 32.0, "gsat": 19.0, "gtrans": 0.0, "fibra": 6.0, "sodio": 15.0, "edulc": False, "caf": True},
    "Chocolate con leche [ARGENFOODS]": {"kcal": 540.0, "cho": 59.0, "azuc_tot": 52.0, "azuc_anad": 50.0, "prot": 7.5, "gtot": 30.0, "gsat": 18.0, "gtrans": 0.3, "fibra": 3.0, "sodio": 85.0, "edulc": False, "caf": True},

    # --- LÁCTEOS, HUEVOS Y CARNES ---
    "Huevo entero [SARA 2]": {"kcal": 156.0, "cho": 0.4, "azuc_tot": 0.4, "azuc_anad": 0.0, "prot": 12.0, "gtot": 11.8, "gsat": 3.18, "gtrans": 0.0, "fibra": 0.0, "sodio": 135.0, "edulc": False, "caf": False},
    "Leche entera pasteurizada [ARGENFOODS]": {"kcal": 61.0, "cho": 4.7, "azuc_tot": 4.7, "azuc_anad": 0.0, "prot": 3.2, "gtot": 3.3, "gsat": 2.1, "gtrans": 0.1, "fibra": 0.0, "sodio": 50.0, "edulc": False, "caf": False},
    "Leche entera en polvo [ARGENFOODS]": {"kcal": 496.0, "cho": 38.0, "azuc_tot": 38.0, "azuc_anad": 0.0, "prot": 26.0, "gtot": 26.0, "gsat": 16.5, "gtrans": 1.0, "fibra": 0.0, "sodio": 370.0, "edulc": False, "caf": False},
    "Queso cuartirolo / cremoso [ARGENFOODS]": {"kcal": 298.0, "cho": 1.5, "azuc_tot": 1.0, "azuc_anad": 0.0, "prot": 19.5, "gtot": 23.5, "gsat": 14.8, "gtrans": 0.7, "fibra": 0.0, "sodio": 510.0, "edulc": False, "caf": False},
    "Queso duro rallar (Sardo / Reggianito) [ARGENFOODS]": {"kcal": 392.0, "cho": 2.0, "azuc_tot": 0.5, "azuc_anad": 0.0, "prot": 33.0, "gtot": 28.0, "gsat": 17.5, "gtrans": 0.8, "fibra": 0.0, "sodio": 950.0, "edulc": False, "caf": False},
    "Carne vacuna magra (Cuadril) [ARGENFOODS]": {"kcal": 140.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 22.0, "gtot": 5.8, "gsat": 2.3, "gtrans": 0.2, "fibra": 0.0, "sodio": 65.0, "edulc": False, "caf": False},
    "Pollo pechuga fresca [ARGENFOODS]": {"kcal": 120.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 22.5, "gtot": 3.0, "gsat": 0.9, "gtrans": 0.0, "fibra": 0.0, "sodio": 70.0, "edulc": False, "caf": False},

    # --- CONDIMENTOS Y AZÚCARES ---
    "Azúcar blanco común [SARA 2]": {"kcal": 400.0, "cho": 100.0, "azuc_tot": 99.8, "azuc_anad": 99.8, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Miel de abejas pura [ARGENFOODS]": {"kcal": 304.0, "cho": 82.4, "azuc_tot": 82.0, "azuc_anad": 82.0, "prot": 0.3, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.2, "sodio": 4.0, "edulc": False, "caf": False},
    "Sal de mesa común (NaCl) [SARA 2]": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 40000.0, "edulc": False, "caf": False},
    "Agua potable [SARA 2]": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 5.0, "edulc": False, "caf": False}
}

lista_alimentos_completa = sorted(list(BASE_NUTRICIONAL.keys()))

# Inicialización completamente vacía
if "receta" not in st.session_state:
    st.session_state.receta = []

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Rotulado Nutricional y Sellos (CAA Cap. V & Ley 27.642)")

    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
    with col_p1:
        nombre_prod = st.text_input("Denominación de venta del producto:", value="", placeholder="Ej: Galletitas de avena, Pan de molde, Mermelada...")
    with col_p2:
        peso_cocido = st.number_input("Peso neto final (g)", min_value=1.0, value=500.0)
    with col_p3:
        porcion = st.number_input("Porción reglamentaria CAA (g)", min_value=1.0, value=80.0)

    st.markdown("---")
    st.subheader("1. Buscador Integrado (SARA 2 y ARGENFOODS)")
    
    c_f1, c_f2 = st.columns([2, 3])
    with c_f1:
        filtro_txt = st.text_input("Buscar insumo en ambas bases:", placeholder="Ej: semola, chocolate, soja, arroz, queso...")

    if filtro_txt.strip():
        opciones = [a for a in lista_alimentos_completa if normalizar_texto(filtro_txt) in normalizar_texto(a)]
    else:
        opciones = lista_alimentos_completa

    with c_f2:
        ing_elegido = st.selectbox(f"Coincidencias oficiales ({len(opciones)} disponibles):", opciones) if opciones else None

    if ing_elegido:
        c_g1, c_g2 = st.columns([3, 1])
        with c_g1:
            gr_ing = st.number_input(f"Gramos de '{ing_elegido}':", min_value=0.1, value=100.0, step=5.0)
        with c_g2:
            st.write("")
            st.write("")
            if st.button("➕ Incorporar a la receta"):
                d = BASE_NUTRICIONAL[ing_elegido]
                st.session_state.receta.append({
                    "Ingrediente": ing_elegido, "Gramos": float(gr_ing), "Kcal": float(d["kcal"]),
                    "Carbohidratos_g": float(d["cho"]), "Azucares_Tot_g": float(d["azuc_tot"]),
                    "Azucar_Anadido_g": float(d["azuc_anad"]), "Proteinas_g": float(d["prot"]),
                    "Grasa_Tot_g": float(d["gtot"]), "Grasa_Sat_g": float(d["gsat"]),
                    "Grasa_Trans_g": float(d["gtrans"]), "Fibra_g": float(d["fibra"]),
                    "Sodio_mg": float(d["sodio"]), "Edulcorante": bool(d["edulc"]), "Cafeina": bool(d["caf"])
                })
                st.rerun()

    st.markdown("---")
    st.subheader("2. Formulación actual")
    df_ed = st.data_editor(pd.DataFrame(st.session_state.receta), num_rows="dynamic", use_container_width=True)

    c_b1, c_b2 = st.columns([2, 8])
    with c_b1:
        btn_calc = st.button("Calcular Tabla y Sellos", type="primary")
    with c_b2:
        if st.button("Vaciar formulación"):
            st.session_state.receta = []
            st.rerun()

    if btn_calc:
        if df_ed.empty or len(df_ed) == 0:
            st.warning("Agregá al menos un ingrediente para realizar el cálculo.")
        else:
            prod_nombre_final = nombre_prod.strip() if nombre_prod.strip() else "Producto Sin Denominación"
            registrar_evento(st.session_state.usuario, "Cálculo Nutricional", f"Producto: {prod_nombre_final}")
            df_l = df_ed.fillna(0)

            def v(row, k):
                return float(row.get(k, 0.0))

            tot_kcal = sum((v(r, "Gramos") * v(r, "Kcal")) / 100.0 for _, r in df_l.iterrows())
            tot_cho = sum((v(r, "Gramos") * v(r, "Carbohidratos_g")) / 100.0 for _, r in df_l.iterrows())
            tot_az_tot = sum((v(r, "Gramos") * v(r, "Azucares_Tot_g")) / 100.0 for _, r in df_l.iterrows())
            tot_az_anad = sum((v(r, "Gramos") * v(r, "Azucar_Anadido_g")) / 100.0 for _, r in df_l.iterrows())
            tot_prot = sum((v(r, "Gramos") * v(r, "Proteinas_g")) / 100.0 for _, r in df_l.iterrows())
            tot_gt = sum((v(r, "Gramos") * v(r, "Grasa_Tot_g")) / 100.0 for _, r in df_l.iterrows())
            tot_gs = sum((v(r, "Gramos") * v(r, "Grasa_Sat_g")) / 100.0 for _, r in df_l.iterrows())
            tot_gtr = sum((v(r, "Gramos") * v(r, "Grasa_Trans_g")) / 100.0 for _, r in df_l.iterrows())
            tot_fib = sum((v(r, "Gramos") * v(r, "Fibra_g")) / 100.0 for _, r in df_l.iterrows())
            tot_sod = sum((v(r, "Gramos") * v(r, "Sodio_mg")) / 100.0 for _, r in df_l.iterrows())

            tiene_edulcorante = any(bool(r.get("Edulcorante", False)) for _, r in df_l.iterrows())
            tiene_cafeina = any(bool(r.get("Cafeina", False)) for _, r in df_l.iterrows())

            f100 = 100.0 / peso_cocido
            c_kcal, c_kj = tot_kcal * f100, tot_kcal * f100 * 4.184
            c_cho, c_az_tot, c_az_anad = tot_cho * f100, tot_az_tot * f100, tot_az_anad * f100
            c_prot, c_gt, c_gs = tot_prot * f100, tot_gt * f100, tot_gs * f100
            c_gtr, c_fib, c_sod = tot_gtr * f100, tot_fib * f100, tot_sod * f100

            f_p = porcion / 100.0
            p_kcal, p_kj = c_kcal * f_p, c_kj * f_p
            p_cho, p_az_tot, p_az_anad = c_cho * f_p, c_az_tot * f_p, c_az_anad * f_p
            p_prot, p_gt, p_gs = c_prot * f_p, c_gt * f_p, c_gs * f_p
            p_gtr, p_fib, p_sod = c_gtr * f_p, c_fib * f_p, c_sod * f_p

            vd_kcal, vd_cho = round((p_kcal / 2000.0) * 100), round((p_cho / 300.0) * 100)
            vd_prot, vd_gt = round((p_prot / 75.0) * 100), round((p_gt / 55.0) * 100)
            vd_gs, vd_fib, vd_sod = round((p_gs / 22.0) * 100), round((p_fib / 25.0) * 100), round((p_sod / 2000.0) * 100)

            sellos = []
            if c_az_anad > 0 and c_kcal > 0 and ((c_az_anad * 4.0) / c_kcal) >= 0.10:
                sellos.append("EXCESO EN AZÚCARES")
            if c_gt > 0 and c_kcal > 0 and ((c_gt * 9.0) / c_kcal) >= 0.30:
                sellos.append("EXCESO EN GRASAS TOTALES")
            if c_gs > 0 and c_kcal > 0 and ((c_gs * 9.0) / c_kcal) >= 0.10:
                sellos.append("EXCESO EN GRASAS SATURADAS")
            if c_sod > 0 and ((c_kcal > 0 and (c_sod / c_kcal) >= 1.0) or (c_sod >= 300.0)):
                sellos.append("EXCESO EN SODIO")
            if any(s in ["EXCESO EN AZÚCARES", "EXCESO EN GRASAS TOTALES", "EXCESO EN GRASAS SATURADAS"] for s in sellos) and c_kcal >= 275.0:
                sellos.append("EXCESO EN CALORÍAS")

            st.markdown("---")
            st.subheader("Resultados del Rótulo y Evaluación Normativa:")

            col_res1, col_res2 = st.columns([3, 2])
            with col_res1:
                st.markdown(f"#### **INFORMACIÓN NUTRICIONAL (Porción: {porcion:.0f} g)**")
                st.table(pd.DataFrame({
                    "Nutriente": [
                        "Valor energético", "Carbohidratos", "  de los cuales: Azúcares totales",
                        "  Azúcares añadidos", "Proteínas", "Grasas totales", "Grasas saturadas",
                        "Grasas trans", "Fibra alimentaria", "Sodio"
                    ],
                    "Cada 100 g": [
                        f"{c_kcal:.0f} kcal = {c_kj:.0f} kJ", f"{c_cho:.1f} g", f"{c_az_tot:.1f} g",
                        f"{c_az_anad:.1f} g", f"{c_prot:.1f} g", f"{c_gt:.1f} g", f"{c_gs:.1f} g",
                        f"{c_gtr:.1f} g", f"{c_fib:.1f} g", f"{c_sod:.1f} mg"
                    ],
                    f"Por porción ({porcion:.0f} g)": [
                        f"{p_kcal:.0f} kcal = {p_kj:.0f} kJ", f"{p_cho:.1f} g", f"{p_az_tot:.1f} g",
                        f"{p_az_anad:.1f} g", f"{p_prot:.1f} g", f"{p_gt:.1f} g", f"{p_gs:.1f} g",
                        f"{p_gtr:.1f} g", f"{p_fib:.1f} g", f"{p_sod:.1f} mg"
                    ],
                    "%VD*": [
                        f"{vd_kcal}%", f"{vd_cho}%", "-", "-", f"{vd_prot}%", f"{vd_gt}%",
                        f"{vd_gs}%", "-", f"{vd_fib}%", f"{vd_sod}%"
                    ]
                }))
                st.caption("*% Valores Diarios con base a una dieta de 2.000 kcal u 8.400 kJ (CAA Cap. V).")

            with col_res2:
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

            # HTML DE IMPRESIÓN CON LOGO ECOMEG
            st.markdown("---")
            st.subheader("🖨️ Informe Oficial de Rotulado para Impresión")

            logo_b64 = obtener_logo_base64()
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 75px; object-fit: contain;" />' if logo_b64 else '<h2>Ecomeg®</h2>'
            sellos_print = "".join([f'<span style="background-color: #000; color: #fff; padding: 5px 10px; margin-right: 5px; font-weight: bold; border-radius: 4px; display: inline-block;">🛑 {s}</span>' for s in sellos]) if sellos else '<p style="color: green; font-weight: bold;">Sin sellos obligatorios (Ley 27.642).</p>'

            html_print = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #222; }}
                    .box {{ max-width: 800px; margin: auto; border: 1px solid #ccc; padding: 25px; border-radius: 6px; }}
                    .top {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2E7D32; padding-bottom: 10px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
                    th, td {{ border: 1px solid #333; padding: 6px 8px; }}
                    th {{ background: #f2f2f2; text-align: left; }}
                    .btn-p {{ background: #2E7D32; color: #fff; border: none; padding: 10px 18px; font-weight: bold; border-radius: 4px; cursor: pointer; margin-bottom: 15px; }}
                    @media print {{ .btn-p {{ display: none; }} .box {{ border: none; padding: 0; }} }}
                </style>
            </head>
            <body>
                <div class="box">
                    <button class="btn-p" onclick="window.print()">🖨️ Imprimir / Guardar en PDF</button>
                    <div class="top">
                        <div><h2 style="margin:0;">{prod_nombre_final}</h2><small>Dictamen Bromatológico Oficial - CAA Cap. V</small></div>
                        <div>{logo_html}</div>
                    </div>
                    <p><strong>Peso Neto:</strong> {peso_cocido:.0f} g | <strong>Porción de referencia:</strong> {porcion:.0f} g</p>
                    <table>
                        <tr><th>Nutriente</th><th style="text-align:right;">Cada 100 g</th><th style="text-align:right;">Porción ({porcion:.0f} g)</th><th style="text-align:center;">% VD*</th></tr>
                        <tr><td><strong>Valor energético</strong></td><td style="text-align:right;">{c_kcal:.0f} kcal = {c_kj:.0f} kJ</td><td style="text-align:right;">{p_kcal:.0f} kcal = {p_kj:.0f} kJ</td><td style="text-align:center;">{vd_kcal}%</td></tr>
                        <tr><td><strong>Carbohidratos</strong></td><td style="text-align:right;">{c_cho:.1f} g</td><td style="text-align:right;">{p_cho:.1f} g</td><td style="text-align:center;">{vd_cho}%</td></tr>
                        <tr><td style="padding-left:15px;">de los cuales: Azúcares totales</td><td style="text-align:right;">{c_az_tot:.1f} g</td><td style="text-align:right;">{p_az_tot:.1f} g</td><td style="text-align:center;">-</td></tr>
                        <tr><td style="padding-left:15px;">Azúcares añadidos</td><td style="text-align:right;">{c_az_anad:.1f} g</td><td style="text-align:right;">{p_az_anad:.1f} g</td><td style="text-align:center;">-</td></tr>
                        <tr><td><strong>Proteínas</strong></td><td style="text-align:right;">{c_prot:.1f} g</td><td style="text-align:right;">{p_prot:.1f} g</td><td style="text-align:center;">{vd_prot}%</td></tr>
                        <tr><td><strong>Grasas totales</strong></td><td style="text-align:right;">{c_gt:.1f} g</td><td style="text-align:right;">{p_gt:.1f} g</td><td style="text-align:center;">{vd_gt}%</td></tr>
                        <tr><td style="padding-left:15px;">Grasas saturadas</td><td style="text-align:right;">{c_gs:.1f} g</td><td style="text-align:right;">{p_gs:.1f} g</td><td style="text-align:center;">{vd_gs}%</td></tr>
                        <tr><td style="padding-left:15px;">Grasas trans</td><td style="text-align:right;">{c_gtr:.1f} g</td><td style="text-align:right;">{p_gtr:.1f} g</td><td style="text-align:center;">-</td></tr>
                        <tr><td><strong>Fibra alimentaria</strong></td><td style="text-align:right;">{c_fib:.1f} g</td><td style="text-align:right;">{p_fib:.1f} g</td><td style="text-align:center;">{vd_fib}%</td></tr>
                        <tr><td><strong>Sodio</strong></td><td style="text-align:right;">{c_sod:.1f} mg</td><td style="text-align:right;">{p_sod:.1f} mg</td><td style="text-align:center;">{vd_sod}%</td></tr>
                    </table>
                    <h4 style="margin-top:20px;">Sellos de Advertencia (Ley 27.642)</h4>
                    <div>{sellos_print}</div>
                </div>
            </body>
            </html>
            """
            st.components.v1.html(html_print, height=600, scrolling=True)

# ==========================================
# PESTAÑA 2: ASISTENTE TÉCNICO REGULATORIO
# ==========================================
with tab2:
    st.header("Asistente Técnico en CAA y Ley 27.642")
    st.write("Consultá dudas sobre claims nutricionales, denominaciones oficiales o rótulos.")

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    pregunta = st.chat_input("Escribí tu consulta bromatológica aquí...")
    if pregunta:
        registrar_evento(st.session_state.usuario, "Consulta Asistente", pregunta[:70])
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)

        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            respuesta_texto = "Falta configurar GEMINI_API_KEY en los Secrets de Streamlit."
        else:
            with st.spinner("Consultando marco regulatorio argentino..."):
                try:
                    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
                    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"
                    body = {
                        "contents": [{"parts": [{"text": pregunta}]}],
                        "systemInstruction": {
                            "parts": [{
                                "text": (
                                    "Sos un asesor bromatológico experto en el Código Alimentario Argentino (CAA Cap. IV y V) "
                                    "y la Ley 27.642 de Promoción de la Alimentación Saludable. Respondé de forma técnica, clara y precisa."
                                )
                            }]
                        }
                    }
                    r = requests.post(url, headers=headers, json=body, timeout=30)
                    if r.status_code == 200:
                        respuesta_texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        respuesta_texto = f"Error de comunicación ({r.status_code}): {r.text}"
                except Exception as ex:
                    respuesta_texto = f"Error al procesar la respuesta: {str(ex)}"

        st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
        with st.chat_message("assistant"):
            st.markdown(respuesta_texto)

# ==========================================
# PESTAÑA 3: AUDITORÍA Y CLIENTES (ADMIN)
# ==========================================
if st.session_state.rol == "admin":
    with tab3:
        st.header("Panel de Métricas y Auditoría de Licencias")
        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            st.subheader("Cuentas de Usuarios")
            st.dataframe(obtener_usuarios(), use_container_width=True)
        with c_adm2:
            st.subheader("Registro de Actividad")
            try:
                df_act = conn.read(worksheet="metricas", ttl="0s").dropna(how="all")
                st.dataframe(df_act.tail(50), use_container_width=True)
            except Exception:
                st.info("Sin registros aún.")
