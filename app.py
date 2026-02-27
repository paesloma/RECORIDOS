import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Rastreador de Rutas", layout="wide")

st.title("📍 Dashboard de Recorrido Logístico")
st.write("Introduce las coordenadas y el horario para visualizar la ruta en el mapa.")

# Inicializar el estado de la sesión para guardar los puntos
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# --- FORMULARIO DE ENTRADA ---
with st.sidebar:
    st.header("Añadir Nuevo Punto")
    with st.form("formulario_punto"):
        direccion = st.text_input("Nombre del Punto / Dirección", "Punto A")
        lat = st.number_input("Latitud", format="%.6f", value=-0.180653) # Default Quito
        lon = st.number_input("Longitud", format="%.6f", value=-78.467834)
        horario = st.time_input("Horario de llegada", datetime.now().time())
        
        submit = st.form_submit_button("Agregar a la ruta")
        
        if submit:
            st.session_state.puntos.append({
                "Dirección": direccion,
                "Latitud": lat,
                "Longitud": lon,
                "Horario": horario
            })

    if st.button("Limpiar todo el recorrido"):
        st.session_state.puntos = []
        st.rerun()

# --- PROCESAMIENTO DE DATOS ---
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos)
    # Ordenar por horario para que el recorrido sea lógico
    df = df.sort_values(by="Horario")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 Puntos Registrados")
        st.dataframe(df, use_container_width=True)

    with col2:
        st.subheader("🗺️ Visualización del Mapa")
        
        # Crear mapa centrado en el primer punto
        centro = [df.iloc[0]['Latitud'], df.iloc[0]['Longitud']]
        m = folium.Map(location=centro, zoom_start=13, control_scale=True)

        # Añadir marcadores y construir lista de coordenadas para la línea
        coords_ruta = []
        for i, row in df.iterrows():
            pos = [row['Latitud'], row['Longitud']]
            coords_ruta.append(pos)
            
            folium.Marker(
                location=pos,
                popup=f"<b>{row['Dirección']}</b><br>Hora: {row['Horario']}",
                tooltip=row['Dirección'],
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        # Dibujar la línea que une los puntos (Recorrido)
        if len(coords_ruta) > 1:
            folium.PolyLine(coords_ruta, color="red", weight=2.5, opacity=0.8).add_to(m)

        # Renderizar mapa en Streamlit
        st_folium(m, width=700, height=500)
else:
    st.info("Usa el panel de la izquierda para añadir tu primer punto de control.")
