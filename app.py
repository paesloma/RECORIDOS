import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests
from io import BytesIO

# Configuración inicial
st.set_page_config(page_title="Gestión de Rutas y Técnicos", layout="wide")

def get_route(coords):
    try:
        locs = ";".join([f"{lon},{lat}" for lat, lon in coords])
        url = f"http://router.project-osrm.org/route/v1/driving/{locs}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [[p[1], p[0]] for p in data['routes'][0]['geometry']['coordinates']]
    except: pass
    return coords 

# --- INICIALIZACIÓN ---
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# Parche de seguridad para datos antiguos
for p in st.session_state.puntos:
    if 'id' not in p: p['id'] = str(uuid.uuid4())
    if 'Teléfono' not in p: p['Teléfono'] = "No registrado"

# --- SIDEBAR ---
with st.sidebar:
    st.header("📍 Nueva Parada")
    with st.form("registro"):
        dir_in = st.text_input("Dirección")
        tel_in = st.text_input("Teléfono")
        geo_in = st.text_input("Coordenadas (Lat, Lon)")
        time_in = st.time_input("Horario", datetime.now().time())
        if st.form_submit_button("Agregar"):
            try:
                l1, l2 = geo_in.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), "Dirección": dir_in, 
                    "Teléfono": tel_in, "Latitud": float(l1), 
                    "Longitud": float(l2), "Horario": time_in
                })
                st.rerun()
            except: st.error("Use: lat, lon")
    
    if st.button("🗑️ Limpiar Todo"):
        st.session_state.puntos = []
        st.rerun()

# --- MAPA PRINCIPAL ---
st.subheader("🗺️ Visualización del Recorrido")
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")
    m = folium.Map(location=[df['Latitud'].mean(), df['Longitud'].mean()], zoom_start=14)
    pts = []
    for _, r in df.iterrows():
        pts.append([r['Latitud'], r['Longitud']])
        folium.Marker(pts[-1], popup=f"{r['Dirección']}\n{r['Teléfono']}", icon=folium.Icon(color="red", icon="phone", prefix="fa")).add_to(m)
    
    if len(pts) > 1:
        camino = get_route(pts)
        folium.PolyLine(camino, color="blue", weight=5).add_to(m)
        m.fit_bounds(camino)
    
    st_folium(m, width="100%", height=450)

    # --- TABLA DE GESTIÓN Y EXCEL ---
    st.markdown("---")
    col_t1, col_t2 = st.columns([4, 1])
    col_t1.subheader("📋 Detalle de la Ruta")
    
    # Función para generar Excel
    def to_excel(df_excel):
        output = BytesIO()
        # Convertir horario a string para que Excel no tenga conflictos
        df_export = df_excel.copy()
        df_export['Horario'] = df_export['Horario'].apply(lambda x: x.strftime('%H:%M'))
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.drop(columns=['id']).to_excel(writer, index=False, sheet_name='Ruta')
        return output.getvalue()

    col_t2.download_button(
        label="📥 Descargar Excel",
        data=to_excel(df),
        file_name=f"ruta_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Tabla visual
    st.dataframe(df[['Horario', 'Dirección', 'Teléfono', 'Latitud', 'Longitud']], use_container_width=True)
    
    # Botones de eliminación individuales
    with st.expander("Opciones de edición"):
        for i, r in df.iterrows():
            if st.button(f"Eliminar {r['Dirección']} ({r['Horario']})", key=f"d_{r['id']}"):
                st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != r['id']]
                st.rerun()

# --- TABLA DE TÉCNICOS (REGISTRO GUARDADO) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
data_tecnicos = [
    ["Guayaquil (GYE)", "Carlos Jama", ""],
    ["Guayaquil (GYE)", "Manuel Vera", ""],
    ["Quito (UIO)", "Javier Quiguango", ""],
    ["Quito (UIO)", "Wilson Quiguango", ""],
    ["Cuenca (CUE)", "Juan Diego Quezada", ""],
    ["Cuenca (CUE)", "Juan Farez", ""],
    ["Cuenca (CUE)", "Santiago Farez", ""],
    ["Cuenca (CUE)", "Xavier Ramón", ""],
]
df_tec = pd.DataFrame(data_tecnicos, columns=["Ciudad", "Técnicos", "Órdenes de Servicio Resueltas"])
st.table(df_tec)
st.info(f"**TOTAL NACIONAL: 8 Técnicos**")
