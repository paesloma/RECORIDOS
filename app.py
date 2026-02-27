import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid

# Configuración
st.set_page_config(page_title="Rastreador de Rutas", layout="wide")

st.title("📍 Dashboard de Recorrido Logístico")

# Inicializar el estado de la sesión de forma segura
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_punto", clear_on_submit=True):
        direccion = st.text_input("Nombre del Punto / Dirección", placeholder="Ej: Entrega 1")
        
        # Casillero único para Latitud y Longitud
        coords_input = st.text_input("Coordenadas (Latitud, Longitud)", placeholder="-2.916000, -79.037895")
        
        horario = st.time_input("Horario de llegada", datetime.now().time())
        submit = st.form_submit_button("Agregar a la ruta")
        
        if submit:
            try:
                # Separar y validar coordenadas
                lat_str, lon_str = coords_input.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                
                # Crear nuevo punto con un ID único garantizado
                nuevo_punto = {
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion if direccion else "Sin nombre",
                    "Latitud": lat,
                    "Longitud": lon,
                    "Horario": horario
                }
                st.session_state.puntos.append(nuevo_punto)
                st.success("Punto agregado.")
            except ValueError:
                st.error("Error: Asegúrate de usar el formato 'latitud, longitud' (ej: -2.91, -78.46)")

    if st.button("Limpiar todo el recorrido"):
        st.session_state.puntos = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
if st.session_state.puntos:
    # Convertir a DataFrame y ordenar por horario
    df = pd.DataFrame(st.session_state.puntos)
    df = df.sort_values(by="Horario")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Gestión de Puntos")
        # Mostrar cada punto con un botón de eliminar
        for i, row in df.iterrows():
            with st.container(border=True):
                st.write(f"**{row['Horario'].strftime('%H:%M')}** - {row['Dirección']}")
                st.caption(f"Coords: {row['Latitud']}, {row['Longitud']}")
                # Usamos el ID único para evitar el KeyError
                if st.button(f"Eliminar", key=f"btn_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        st.subheader("🗺️ Mapa de Ruta")
        # Centrar mapa
        centro = [df.iloc[0]['Latitud'], df.iloc[0]['Longitud']]
        m = folium.Map(location=centro, zoom_start=13)

        puntos_ruta = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            puntos_ruta.append(pos)
            folium.Marker(
                location=pos,
                popup=f"{row['Dirección']} ({row['Horario'].strftime('%H:%M')})",
                tooltip=row['Dirección']
            ).add_to(m)

        if len(puntos_ruta) > 1:
            folium.PolyLine(puntos_ruta, color="blue", weight=3, opacity=0.7).add_to(m)

        st_folium(m, width="100%", height=500)
else:
    st.info("La lista está vacía. Agrega puntos desde el panel lateral usando el formato 'Latitud, Longitud'.")
