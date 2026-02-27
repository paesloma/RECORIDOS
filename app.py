import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests # Para consultar la API de rutas

# Configuración
st.set_page_config(page_title="Rastreador de Rutas Reales", layout="wide")

# NOTA: Para rutas reales necesitas una API. 
# OSRM es un servicio gratuito que no requiere llave para pruebas.
def get_route(coords):
    """Obtiene la geometría de la ruta real usando OSRM"""
    # Formato OSRM: lon,lat;lon,lat
    locs = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"http://router.project-osrm.org/route/v1/driving/{locs}?overview=full&geometries=geojson"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        # Retorna la lista de coordenadas del camino real
        return [[p[1], p[0]] for p in data['routes'][0]['geometry']['coordinates']]
    return coords # Si falla, vuelve a línea recta

st.title("📍 Dashboard con Recorrido Real por Calles")

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario", clear_on_submit=True):
        direccion = st.text_input("Nombre / Dirección")
        coords_input = st.text_input("Coordenadas (Lat, Lon)", placeholder="-2.916, -79.037")
        horario = st.time_input("Horario", datetime.now().time())
        if st.form_submit_button("Agregar"):
            try:
                lat_str, lon_str = coords_input.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion, "Latitud": float(lat_str), "Longitud": float(lon_str), "Horario": horario
                })
                st.rerun()
            except: st.error("Formato: lat, lon")

# --- CUERPO ---
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")
    col1, col2 = st.columns([1, 2])

    with col1:
        for i, row in df.iterrows():
            with st.container(border=True):
                st.write(f"**{row['Horario'].strftime('%H:%M')}** - {row['Dirección']}")
                if st.button("Eliminar", key=f"del_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        m = folium.Map(location=[df['Latitud'].mean(), df['Longitud'].mean()], zoom_start=14)
        
        puntos_clave = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            puntos_clave.append(pos)
            folium.Marker(pos, tooltip=row['Dirección']).add_to(m)

        if len(puntos_clave) > 1:
            # ¡AQUÍ ESTÁ EL CAMBIO! Obtenemos el camino por las calles
            camino_real = get_route(puntos_clave)
            folium.PolyLine(camino_real, color="blue", weight=5, opacity=0.7).add_to(m)
            m.fit_bounds(camino_real)

        st_folium(m, width="100%", height=600)
