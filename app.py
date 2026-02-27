import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests

# Configuración
st.set_page_config(page_title="Rastreador Logístico con Contacto", layout="wide")

def get_route(coords):
    """Obtiene la geometría de la ruta real usando OSRM"""
    try:
        locs = ";".join([f"{lon},{lat}" for lat, lon in coords])
        url = f"http://router.project-osrm.org/route/v1/driving/{locs}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [[p[1], p[0]] for p in data['routes'][0]['geometry']['coordinates']]
    except:
        pass
    return coords 

st.title("📍 Dashboard de Recorrido y Contactos")

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_contacto", clear_on_submit=True):
        direccion = st.text_input("Nombre / Dirección", placeholder="Ej: Cliente Juan")
        
        # NUEVO: Campo de Teléfono
        telefono = st.text_input("Teléfono de Contacto", placeholder="0987654321")
        
        coords_input = st.text_input("Coordenadas (Lat, Lon)", placeholder="-2.916, -79.037")
        horario = st.time_input("Horario", datetime.now().time())
        
        if st.form_submit_button("Agregar a la ruta"):
            try:
                lat_str, lon_str = coords_input.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion if direccion else "Sin nombre",
                    "Teléfono": telefono if telefono else "No registrado",
                    "Latitud": float(lat_str), 
                    "Longitud": float(lon_str), 
                    "Horario": horario
                })
                st.rerun()
            except:
                st.error("Formato de coordenadas incorrecto. Usa: lat, lon")

    if st.button("Limpiar todo"):
        st.session_state.puntos = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Gestión de Puntos")
        for i, row in df.iterrows():
            with st.container(border=True):
                st.write(f"**{row['Horario'].strftime('%H:%M')}** - {row['Dirección']}")
                st.write(f"📞 Tel: {row['Teléfono']}") # Visualización del teléfono
                if st.button(f"Eliminar", key=f"del_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        st.subheader("🗺️ Ruta por Calles")
        m = folium.Map(location=[df['Latitud'].mean(), df['Longitud'].mean()], zoom_start=14)
        
        puntos_clave = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            puntos_clave.append(pos)
            
            # Marcador con información de contacto en el popup
            folium.Marker(
                pos, 
                popup=f"<b>{row['Dirección']}</b><br>📞 {row['Teléfono']}<br>⏰ {row['Horario'].strftime('%H:%M')}",
                tooltip=row['Dirección'],
                icon=folium.Icon(color="red", icon="phone", prefix="fa")
            ).add_to(m)

        if len(puntos_clave) > 1:
            camino_real = get_route(puntos_clave)
            folium.PolyLine(camino_real, color="blue", weight=5).add_to(m)
            m.fit_bounds(camino_real)

        st_folium(m, width="100%", height=600)
