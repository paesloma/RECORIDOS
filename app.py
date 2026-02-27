import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid

# Configuración de página
st.set_page_config(page_title="Rastreador de Rutas", layout="wide")

st.title("📍 Dashboard de Recorrido Logístico")

# Inicialización segura de la sesión
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_punto", clear_on_submit=True):
        direccion = st.text_input("Nombre del Punto / Dirección", placeholder="Ej: Punto de Entrega")
        
        # Campo único para Latitud y Longitud
        coords_input = st.text_input("Coordenadas (Latitud, Longitud)", placeholder="-2.916000, -79.037895")
        
        horario = st.time_input("Horario de llegada", datetime.now().time())
        submit = st.form_submit_button("Agregar a la ruta")
        
        if submit:
            try:
                # Limpiar y separar coordenadas
                lat_str, lon_str = coords_input.replace(" ", "").split(',')
                lat, lon = float(lat_str), float(lon_str)
                
                # Crear diccionario con ID único para evitar KeyErrors
                nuevo_punto = {
                    "id": str(uuid.uuid4()), 
                    "Dirección": direccion if direccion else "Sin nombre",
                    "Latitud": lat,
                    "Longitud": lon,
                    "Horario": horario
                }
                st.session_state.puntos.append(nuevo_punto)
                st.rerun() # Refrescar para mostrar el marcador de inmediato
            except Exception:
                st.error("Formato inválido. Usa: latitud, longitud (ej: -2.91, -78.46)")

    if st.button("Limpiar todo el recorrido"):
        st.session_state.puntos = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
if st.session_state.puntos:
    # Convertir a DataFrame y asegurar que el ID exista
    df = pd.DataFrame(st.session_state.puntos)
    df = df.sort_values(by="Horario")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Puntos en la Ruta")
        for i, row in df.iterrows():
            with st.container(border=True):
                st.write(f"**{row['Horario'].strftime('%H:%M')}** - {row['Dirección']}")
                # Botón de eliminar usando el ID único
                if st.button(f"Eliminar", key=f"btn_{row['id']}"):
                    st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                    st.rerun()

    with col2:
        st.subheader("🗺️ Mapa de Visualización")
        
        # Crear mapa base
        centro_lat = df['Latitud'].mean()
        centro_lon = df['Longitud'].mean()
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

        puntos_ruta = []
        for _, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            puntos_ruta.append(pos)
            
            # Marcador estándar para asegurar visibilidad
            folium.Marker(
                location=pos,
                popup=f"{row['Dirección']} ({row['Horario'].strftime('%H:%M')})",
                tooltip=row['Dirección'],
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

        # Línea de recorrido
        if len(puntos_ruta) > 1:
            folium.PolyLine(puntos_ruta, color="blue", weight=3).add_to(m)
            # Ajustar el mapa automáticamente para que se vean todos los puntos
            m.fit_bounds(puntos_ruta)

        st_folium(m, width="100%", height=600, key="mapa_principal")
else:
    st.info("Introduce una dirección y coordenadas en el panel izquierdo.")
