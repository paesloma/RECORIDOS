import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests

# Configuración de la página
st.set_page_config(page_title="Rastreador Logístico Pro", layout="wide")

def get_route(coords):
    """Obtiene la ruta real por calles usando OSRM"""
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

st.title("📍 Dashboard de Recorrido Logístico")

# --- INICIALIZACIÓN Y LIMPIEZA DE DATOS VIEJOS ---
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# Validar que todos los puntos existentes tengan los campos necesarios para evitar el KeyError
for p in st.session_state.puntos:
    if 'id' not in p: p['id'] = str(uuid.uuid4())
    if 'Teléfono' not in p: p['Teléfono'] = "No registrado"

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_principal", clear_on_submit=True):
        direccion = st.text_input("Nombre / Dirección", placeholder="Ej: Cliente Central")
        telefono = st.text_input("Teléfono de Contacto", placeholder="0987654321")
        coords_input = st.text_input("Coordenadas (Latitud, Longitud)", placeholder="-2.916, -79.037")
        horario = st.time_input("Horario estimado", datetime.now().time())
        
        if st.form_submit_button("Agregar a la ruta"):
            try:
                # Limpieza de entrada de coordenadas
                lat_str, lon_str = coords_input.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion if direccion else "Sin nombre",
                    "Teléfono": telefono if telefono else "S/N",
                    "Latitud": float(lat_str), 
                    "Longitud": float(lon_str), 
                    "Horario": horario
                })
                st.rerun()
            except:
                st.error("Error: Usa el formato 'latitud, longitud'")

    if st.button("🗑️ Borrar toda la ruta"):
        st.session_state.puntos = []
        st.rerun()

# --- VISUALIZACIÓN ---
if st.session_state.puntos:
    # Creamos el DataFrame y ordenamos
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Gestión de Puntos")
        for i, row in df.iterrows():
            with st.expander(f"⏰ {row['Horario'].strftime('%H:%M')} - {row['Dirección']}", expanded=True):
                st.write(f"📞 **Tel:** {row['Teléfono']}")
                st.caption(f"📍 {row['Latitud']}, {row['Longitud']}")
                if st.button(f"Eliminar Punto", key=f"del_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        st.subheader("🗺️ Mapa de Recorrido Real")
        # Centrar mapa en el promedio de los puntos
        m = folium.Map(location=[df['Latitud'].mean(), df['Longitud'].mean()], zoom_start=14)
        
        puntos_ruta = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            puntos_ruta.append(pos)
            
            # Marcador con información completa
            popup_text = f"<b>{row['Dirección']}</b><br>📞 {row['Teléfono']}<br>⌚ {row['Horario'].strftime('%H:%M')}"
            folium.Marker(
                location=pos,
                popup=folium.Popup(popup_text, max_width=200),
                tooltip=row['Dirección'],
                icon=folium.Icon(color="red", icon="phone", prefix="fa")
            ).add_to(m)

        if len(puntos_ruta) > 1:
            camino = get_route(puntos_ruta)
            folium.PolyLine(camino, color="blue", weight=4, opacity=0.7).add_to(m)
            m.fit_bounds(camino) # Ajuste automático del zoom

        st_folium(m, width="100%", height=600, key="mapa_dinamico")
else:
    st.info("La ruta está vacía. Agrega puntos desde el panel lateral.")
