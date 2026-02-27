import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests

# Configuración de pantalla completa
st.set_page_config(page_title="Mapa de Rutas Crítico", layout="wide")

def get_route(coords):
    """Calcula la ruta real por calles"""
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

# --- LIMPIEZA DE DATOS (Solución al KeyError) ---
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# Asegurar que cada punto tenga todas las columnas necesarias
for p in st.session_state.puntos:
    if 'id' not in p: p['id'] = str(uuid.uuid4())
    if 'Teléfono' not in p: p['Teléfono'] = "No registrado"
    if 'Dirección' not in p: p['Dirección'] = "Sin nombre"

# --- SIDEBAR: ENTRADA DE DATOS ---
with st.sidebar:
    st.header("📍 Registro de Parada")
    with st.form("form_registro", clear_on_submit=True):
        direccion = st.text_input("Nombre / Dirección")
        telefono = st.text_input("Teléfono de Contacto")
        coords_input = st.text_input("Coordenadas (Lat, Lon)", placeholder="-2.91, -79.03")
        horario = st.time_input("Horario", datetime.now().time())
        
        if st.form_submit_button("Agregar Punto"):
            try:
                lat_str, lon_str = coords_input.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion if direccion else "Punto Nuevo",
                    "Teléfono": telefono if telefono else "S/N",
                    "Latitud": float(lat_str), 
                    "Longitud": float(lon_str), 
                    "Horario": horario
                })
                st.rerun()
            except:
                st.error("Formato: latitud, longitud")

    if st.button("🗑️ Reiniciar todo"):
        st.session_state.puntos = []
        st.rerun()

# --- CUERPO PRINCIPAL: MAPA PRIMERO ---
st.subheader("🗺️ Visualización del Recorrido Real")

if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")
    
    # Mapa en la parte superior
    centro = [df['Latitud'].mean(), df['Longitud'].mean()]
    m = folium.Map(location=centro, zoom_start=14)
    
    puntos_ruta = []
    for _, row in df.iterrows():
        pos = [row['Latitud'], row['Longitud']]
        puntos_ruta.append(pos)
        
        popup_info = f"<b>{row['Dirección']}</b><br>📞 {row['Teléfono']}<br>⌚ {row['Horario']}"
        folium.Marker(
            location=pos,
            popup=folium.Popup(popup_info, max_width=250),
            icon=folium.Icon(color="red", icon="phone", prefix="fa")
        ).add_to(m)

    if len(puntos_ruta) > 1:
        camino = get_route(puntos_ruta)
        folium.PolyLine(camino, color="blue", weight=5, opacity=0.7).add_to(m)
        m.fit_bounds(camino)

    # Renderizado del mapa
    st_folium(m, width="100%", height=500, key="mapa_full")

    # --- PARTE INFERIOR: TABLA DE GESTIÓN ---
    st.markdown("---")
    st.subheader("📋 Información Detallada de la Ruta")
    
    # Crear columnas para simular una tabla con botones de acción
    cols = st.columns([2, 2, 2, 2, 1])
    cols[0].write("**Horario**")
    cols[1].write("**Dirección**")
    cols[2].write("**Teléfono**")
    cols[3].write("**Coordenadas**")
    cols[4].write("**Acción**")

    for i, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        c1.write(row['Horario'].strftime('%H:%M'))
        c2.write(row['Dirección'])
        c3.write(row['Teléfono'])
        c4.write(f"{row['Latitud']:.4f}, {row['Longitud']:.4f}")
        if c5.button("Eliminar", key=f"del_{row['id']}"):
            st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
            st.rerun()
else:
    st.info("Agrega puntos en el panel lateral para visualizar el recorrido.")
