import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Rastreador de Rutas Pro", layout="wide")

st.title("📍 Dashboard de Recorrido Logístico")
st.write("Introduce coordenadas (lat, lon) y horario para visualizar y gestionar tu ruta.")

# Inicializar el estado de la sesión
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- PANEL DE CONTROL (BARRA LATERAL) ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_punto", clear_on_submit=True):
        direccion = st.text_input("Nombre del Punto / Dirección", placeholder="Ej: Bodega Central")
        
        # Un solo casillero para coordenadas separado por coma
        coords_input = st.text_input("Coordenadas (Latitud, Longitud)", placeholder="-2.916000, -79.037895")
        
        horario = st.time_input("Horario de llegada", datetime.now().time())
        submit = st.form_submit_button("Agregar a la ruta")
        
        if submit:
            try:
                # Procesar el casillero de coordenadas único
                lat_str, lon_str = coords_input.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                
                st.session_state.puntos.append({
                    "id": datetime.now().timestamp(), # ID único para eliminar
                    "Dirección": direccion,
                    "Latitud": lat,
                    "Longitud": lon,
                    "Horario": horario
                })
                st.success("Punto agregado correctamente.")
            except ValueError:
                st.error("Formato de coordenadas incorrecto. Usa: latitud, longitud")

    if st.button("Limpiar todo el recorrido"):
        st.session_state.puntos = []
        st.rerun()

# --- VISUALIZACIÓN Y GESTIÓN ---
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by="Horario")

    col1, col2 = st.columns([1.2, 2])

    with col1:
        st.subheader("📋 Gestión de Puntos")
        # Mostrar puntos con opción de eliminar
        for index, row in df.iterrows():
            with st.expander(f"{row['Horario'].strftime('%H:%M')} - {row['Dirección']}"):
                st.write(f"📍 {row['Latitud']}, {row['Longitud']}")
                if st.button(f"Eliminar punto", key=f"del_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        st.subheader("🗺️ Visualización del Mapa")
        centro = [df.iloc[0]['Latitud'], df.iloc[0]['Longitud']]
        m = folium.Map(location=centro, zoom_start=13)

        coords_ruta = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            coords_ruta.append(pos)
            folium.Marker(
                location=pos,
                popup=f"{row['Dirección']} ({row['Horario']})",
                icon=folium.Icon(color="blue")
            ).add_to(m)

        if len(coords_ruta) > 1:
            folium.PolyLine(coords_ruta, color="red", weight=2.5).add_to(m)

        st_folium(m, width=700, height=500)
else:
    st.info("Introduce coordenadas en el formato 'lat, lon' (ejemplo: -2.916, -79.037) para comenzar.")
