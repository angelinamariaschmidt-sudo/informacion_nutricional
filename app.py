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

def obtener_usuarios():
    try:
        df = conn.read(worksheet="usuarios", ttl="0s")
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=["usuario", "clave", "rol", "token_sesion", "estado"])

def registrar_evento(usuario, accion, detalle=""):
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_met = conn.read(worksheet="metricas", ttl="0s").dropna(how="all")
        nueva_fila = pd.DataFrame([{"fecha_hora": ahora, "usuario": usuario, "accion": accion, "detalle": detalle}])
        df_actualizado = pd.concat([df_met, nueva_fila], ignore_index=True)
        conn.update(worksheet="metricas", data=df_actualizado)
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
    u_ingresado = st.text_input("Usuario")
    c_ingresada = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        df_usuarios = obtener_usuarios()
        coincidencia = df_usuarios[(df_usuarios["usuario"] == u_ingresado) & (df_usuarios["clave"] == c_ingresada)]

        if not coincidencia.empty:
            fila = coincidencia.iloc[0]
            if str(fila.get("estado", "")).lower() == "activo":
                nuevo_token = str(uuid.uuid4())
                st.session_state.autenticado = True
                st.session_state.usuario = u_ingresado
                st.session_state.rol = str(fila.get("rol", "cliente")).lower()
                st.session_state.token = nuevo_token

                # Los clientes registran token único en la hoja para invalidar sesiones previas
                if st.session_state.rol != "admin":
                    df_usuarios.loc[df_usuarios["usuario"] == u_ingresado, "token_sesion"] = nuevo_token
                    conn.update(worksheet="usuarios", data=df_usuarios)

                registrar_evento(u_ingresado, "Inicio de sesión", f"Rol: {st.session_state.rol}")
                st.rerun()
            else:
                st.error("Su suscripción se encuentra inactiva. Contacte al administrador.")
        else:
            st.error("Usuario o clave incorrectos.")

if not st.session_state.autenticado:
    login()
    st.stop()

# Validación continua de sesión única para clientes
if st.session_state.rol != "admin":
    df_actual = obtener_usuarios()
    token_remoto = df_actual.loc[df_actual["usuario"] == st.session_state.usuario, "token_sesion"].values
    if len(token_remoto) > 0 and str(token_remoto[0]) != str(st.session_state.token):
        st.session_state.autenticado = False
        st.error("Se inició sesión con esta cuenta en otro dispositivo. Esta sesión fue cerrada.")
        st.stop()

# --- BARRA LATERAL ---
st.sidebar.markdown(f"**Conectado:** `{st.session_state.usuario}`")
st.sidebar.markdown(f"**Nivel de acceso:** `{'Administrador' if st.session_state.rol == 'admin' else 'Licencia Individual'}`")
if st.sidebar.button("Cerrar Sesión"):
    registrar_evento(st.session_state.usuario, "Cierre de sesión")
    st.session_state.autenticado = False
    st.rerun()

# --- GESTIÓN DE PESTAÑAS (ADMIN VS CLIENTE) ---
if st.session_state.rol == "admin":
    tab1, tab2, tab3 = st.tabs(["📊 Calculadora & Sellos", "💬 Asistente Técnico", "📈 Panel de Auditoría (Admin)"])
else:
    tab1, tab2 = st.tabs(["📊 Calculadora & Sellos", "💬 Asistente Técnico"])

def normalizar(texto):
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto).lower()) if unicodedata.category(c) != 'Mn')

def obtener_imagen_base64():
    posibles = ["Logo ECOMEG Transparente.png", "Logo ECOMEG Transparente.PNG", "logo_ecomeg.png", "ecomeg (R).png"]
    for nom in posibles:
        if os.path.exists(nom):
            with open(nom, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

# ==============================================================================
# BASE DE DATOS SARA 2 (Oficial)
# ==============================================================================
SARA2_DICT = {
    "Aceite de girasol": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 10.6, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Aceite de oliva virgen extra": {"kcal": 900.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 100.0, "gsat": 17.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Grasa vacuna refinada": {"kcal": 899.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 99.9, "gsat": 49.8, "gtrans": 3.7, "fibra": 0.0, "sodio": 0.0, "edulc": False, "caf": False},
    "Manteca de vaca": {"kcal": 758.0, "cho": 0.1, "azuc_tot": 0.1, "azuc_anad": 0.0, "prot": 0.5, "gtot": 84.0, "gsat": 50.93, "gtrans": 3.28, "fibra": 0.0, "sodio": 223.0, "edulc": False, "caf": False},
    "Sémola de trigo / Semolín candeal": {"kcal": 336.0, "cho": 72.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 12.7, "gtot": 1.1, "gsat": 0.15, "gtrans": 0.0, "fibra": 3.9, "sodio": 1.0, "edulc": False, "caf": False},
    "Gluten puro de trigo en polvo": {"kcal": 370.0, "cho": 13.8, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 75.0, "gtot": 1.9, "gsat": 0.3, "gtrans": 0.0, "fibra": 1.5, "sodio": 70.0, "edulc": False, "caf": False},
    "Harina de trigo 000 fortificada": {"kcal": 329.0, "cho": 69.8, "azuc_tot": 0.3, "azuc_anad": 0.0, "prot": 10.3, "gtot": 1.0, "gsat": 0.16, "gtrans": 0.0, "fibra": 4.0, "sodio": 7.0, "edulc": False, "caf": False},
    "Harina de trigo 0000 fortificada": {"kcal": 353.0, "cho": 74.0, "azuc_tot": 0.2, "azuc_anad": 0.0, "prot": 11.6, "gtot": 0.9, "gsat": 0.15, "gtrans": 0.0, "fibra": 2.5, "sodio": 7.0, "edulc": False, "caf": False},
    "Acelga, cruda": {"kcal": 18.0, "cho": 2.1, "azuc_tot": 1.1, "azuc_anad": 0.0, "prot": 1.8, "gtot": 0.2, "gsat": 0.03, "gtrans": 0.0, "fibra": 1.6, "sodio": 213.0, "edulc": False, "caf": False},
    "Espinaca, cruda": {"kcal": 21.0, "cho": 1.43, "azuc_tot": 0.42, "azuc_anad": 0.0, "prot": 2.86, "gtot": 0.39, "gsat": 0.06, "gtrans": 0.0, "fibra": 2.2, "sodio": 79.0, "edulc": False, "caf": False},
    "Huevo entero": {"kcal": 156.0, "cho": 0.4, "azuc_tot": 0.4, "azuc_anad": 0.0, "prot": 12.0, "gtot": 11.8, "gsat": 3.18, "gtrans": 0.0, "fibra": 0.0, "sodio": 135.0, "edulc": False, "caf": False},
    "Queso Cremoso": {"kcal": 310.0, "cho": 2.5, "azuc_tot": 1.8, "azuc_anad": 0.0, "prot": 20.4, "gtot": 24.9, "gsat": 13.66, "gtrans": 0.73, "fibra": 0.0, "sodio": 704.0, "edulc": False, "caf": False},
    "Azúcar blanca común": {"kcal": 400.0, "cho": 100.0, "azuc_tot": 99.8, "azuc_anad": 99.8, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 1.0, "edulc": False, "caf": False},
    "Sal fina de mesa común (NaCl)": {"kcal": 0.0, "cho": 0.0, "azuc_tot": 0.0, "azuc_anad": 0.0, "prot": 0.0, "gtot": 0.0, "gsat": 0.0, "gtrans": 0.0, "fibra": 0.0, "sodio": 40000.0, "edulc": False, "caf": False}
}

lista_alimentos_completa = sorted(list(SARA2_DICT.keys()))

if "receta" not in st.session_state:
    st.session_state.receta = [
        {"Ingrediente": "Sémola de trigo / Semolín candeal", "Gramos": 300.0, "Kcal": 336.0, "Carbohidratos_g": 72.8, "Azucares_Tot_g": 0.0, "Azucar_Anadido_g": 0.0, "Proteinas_g": 12.7, "Grasa_Tot_g": 1.1, "Grasa_Sat_g": 0.15, "Grasa_Trans_g": 0.0, "Fibra_g": 3.9, "Sodio_mg": 1.0, "Edulcorante": False, "Cafeina": False}
    ]

# ==========================================
# PESTAÑA 1: CALCULADORA NUTRICIONAL
# ==========================================
with tab1:
    st.header("Cálculo de Rotulado Nutricional y Sellos (CAA Cap. V & Ley 27.642)")

    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
    with col_p1:
        nombre_prod = st.text_input("Denominación del producto:", value="Pasta Seca al Huevo")
    with col_p2:
        peso_cocido = st.number_input("Peso neto tras cocción (g)", min_value=1.0, value=500.0)
    with col_p3:
        porcion = st.number_input("Porción reglamentaria (g)", min_value=1.0, value=80.0)

    st.markdown("---")
    st.subheader("1. Búsqueda de Ingredientes (Prioridad: SARA 2)")
    c_f1, c_f2 = st.columns([2, 3])
    with c_f1:
        filtro_txt = st.text_input("Filtrar alimento:", placeholder="Ej: semola, aceite, acelga...")

    if filtro_txt.strip():
        opciones = [a for a in lista_alimentos_completa if normalizar(filtro_txt) in normalizar(a)]
    else:
        opciones = lista_alimentos_completa

    with c_f2:
        ing_elegido = st.selectbox("Coincidencias en SARA 2:", opciones) if opciones else None

    if ing_elegido:
        c_g1, c_g2 = st.columns([3, 1])
        with c_g1:
            gr_ing = st.number_input(f"Gramos de '{ing_elegido}':", min_value=0.1, value=100.0, step=5.0)
        with c_g2:
            st.write("")
            st.write("")
            if st.button("➕ Incorporar"):
                d = SARA2_DICT[ing_elegido]
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
    st.subheader("2. Formulación activa")
    df_ed = st.data_editor(pd.DataFrame(st.session_state.receta), num_rows="dynamic", use_container_width=True)

    c_b1, c_b2 = st.columns([2, 8])
    with c_b1:
        btn_calc = st.button("Calcular Tabla y Sellos", type="primary")
    with c_b2:
        if st.button("Vaciar"):
            st.session_state.receta = []
            st.rerun()

    if btn_calc:
        registrar_evento(st.session_state.usuario, "Cálculo Nutricional", f"Producto: {nombre_prod}")
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
        if sellos and c_kcal >= 275.0:
            sellos.append("EXCESO EN CALORÍAS")

        st.markdown("---")
        st.subheader("Resultados Reglamentarios")
        col_res1, col_res2 = st.columns([3, 2])
        with col_res1:
            st.table(pd.DataFrame({
                "Nutriente": ["Valor energético", "Carbohidratos", "  Azúcares añadidos", "Proteínas", "Grasas totales", "Grasas saturadas", "Grasas trans", "Fibra alimentaria", "Sodio"],
                "Cada 100 g": [f"{c_kcal:.0f} kcal", f"{c_cho:.1f} g", f"{c_az_anad:.1f} g", f"{c_prot:.1f} g", f"{c_gt:.1f} g", f"{c_gs:.1f} g", f"{c_gtr:.1f} g", f"{c_fib:.1f} g", f"{c_sod:.1f} mg"],
                f"Por porción ({porcion:.0f} g)": [f"{p_kcal:.0f} kcal", f"{p_cho:.1f} g", f"{p_az_anad:.1f} g", f"{p_prot:.1f} g", f"{p_gt:.1f} g", f"{p_gs:.1f} g", f"{p_gtr:.1f} g", f"{p_fib:.1f} g", f"{p_sod:.1f} mg"],
                "%VD*": [f"{vd_kcal}%", f"{vd_cho}%", "-", f"{vd_prot}%", f"{vd_gt}%", f"{vd_gs}%", "-", f"{vd_fib}%", f"{vd_sod}%"]
            }))
        with col_res2:
            st.markdown("### Sellos Frontales (Ley 27.642)")
            if sellos:
                for s in sellos:
                    st.error(f"🛑 **{s}**")
            else:
                st.success("Sin sellos de advertencia.")

        # Generador HTML con Logo Ecomeg
        logo_b64 = obtener_imagen_base64()
        logo_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 70px; object-fit: contain;" />' if logo_b64 else '<h2>Ecomeg®</h2>'
        html_informe = f"""
        <div style="font-family: sans-serif; max-width: 750px; margin: auto; padding: 20px; border: 1px solid #ccc; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2E7D32; padding-bottom: 10px;">
                <div><h2 style="margin: 0;">{nombre_prod}</h2><small>Informe Bromatológico Oficial</small></div>
                <div>{logo_tag}</div>
            </div>
            <p style="margin-top: 15px;"><strong>Porción:</strong> {porcion:.0f} g | <strong>Peso Neto:</strong> {peso_cocido:.0f} g</p>
            <p><strong>Valor Energético:</strong> {p_kcal:.0f} kcal ({vd_kcal}% VD) | <strong>Sodio:</strong> {p_sod:.1f} mg ({vd_sod}% VD)</p>
            <p><strong>Sellos Ley 27.642:</strong> {', '.join(sellos) if sellos else 'Sin sellos obligatorios'}</p>
            <button onclick="window.print()" style="background: #2E7D32; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">🖨️ Imprimir / Guardar PDF</button>
        </div>
        """
        st.components.v1.html(html_informe, height=350, scrolling=True)

# ==========================================
# PESTAÑA 2: ASISTENTE TÉCNICO
# ==========================================
with tab2:
    st.header("Asistente Técnico Normativo")
    preg = st.chat_input("Escribí tu consulta sobre rotulado...")
    if preg:
        registrar_evento(st.session_state.usuario, "Consulta Asistente", preg[:50])
        st.write(f"Consulta registrada: {preg}")

# ==========================================
# PESTAÑA 3: AUDITORÍA (SOLO ADMIN)
# ==========================================
if st.session_state.rol == "admin":
    with tab3:
        st.header("Panel de Métricas y Auditoría de Clientes")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.subheader("Usuarios y Estado de Licencias")
            st.dataframe(obtener_usuarios(), use_container_width=True)
        with col_m2:
            st.subheader("Registro de Actividad en Tiempo Real")
            try:
                df_act = conn.read(worksheet="metricas", ttl="0s").dropna(how="all")
                st.dataframe(df_act.tail(50), use_container_width=True)
            except Exception:
                st.info("Sin registros de métricas aún.")
