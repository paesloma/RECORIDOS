import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import uuid
import requests
from io import BytesIO

# 1. Configuración de página
st.set_page_config(page_title="Gestión de Rutas Final", layout="wide")

# Función para ruta real
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

# 2. INICIALIZACIÓN SEGURA (Evita el KeyError)
if 'puntos' not in st.session_state:
    st.session_state.puntos = []

# Limpieza automática de datos antiguos para evitar que la app se rompa
puntos_limpios = []
for p in st.session_state.puntos:
    if isinstance(p, dict) and 'id' in p and 'Teléfono' in p and 'Fecha' in p:
        puntos_limpios.append(p)
st.session_state.puntos = puntos_limpios

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📍 Nueva Parada")
    with st.form("registro_final", clear_on_submit=True):
        dir_in = st.text_input("Dirección / Cliente")
        tel_in = st.text_input("Teléfono / Contacto")
        geo_in = st.text_input("Coordenadas (Lat, Lon)")
        
        # Fecha y Hora dinámicas
        fecha_in = st.date_input("Fecha de ruta", datetime.now().date())
        time_in = st.time_input("Horario", datetime.now().time())
        
        if st.form_submit_button("Agregar"):
            try:
                l1, l2 = geo_in.replace(" ", "").split(',')
                st.session_state.puntos.append({
                    "id": str(uuid.uuid4()), 
                    "Fecha": fecha_in,
                    "Horario": time_in,
                    "Dirección": dir_in if dir_in else "Sin nombre", 
                    "Teléfono": tel_in if tel_in else "S/N", 
                    "Latitud": float(l1), 
                    "Longitud": float(l2)
                })
                st.rerun()
            except: st.error("Formato incorrecto. Use: lat, lon")
    
    st.markdown("---")
    if st.button("🚨 RESETEO FORZADO", help="Usa esto si sigues viendo errores rojos"):
        st.session_state.puntos = []
        st.rerun()

# --- MAPA PRINCIPAL ---
st.subheader("🗺️ Visualización del Recorrido")
if st.session_state.puntos:
    df = pd.DataFrame(st.session_state.puntos).sort_values(by=["Fecha", "Horario"])
    
    m = folium.Map(location=[df['Latitud'].mean(), df['Longitud'].mean()], zoom_start=14)
    pts = []
    for _, r in df.iterrows():
        pts.append([r['Latitud'], r['Longitud']])
        folium.Marker(
            pts[-1], 
            popup=f"<b>{r['Dirección']}</b><br>Tel: {r['Teléfono']}<br>Hora: {r['Horario']}", 
            icon=folium.Icon(color="red", icon="phone", prefix="fa")
        ).add_to(m)
    
    if len(pts) > 1:
        camino = get_route(pts)
        folium.PolyLine(camino, color="blue", weight=5).add_to(m)
        m.fit_bounds(camino)
    
    st_folium(m, width="100%", height=450, key="mapa_v3")

    # --- TABLA Y EXCEL ---
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    col1.subheader("📋 Detalle de la Ruta")
    
    def to_excel(df_in):
        output = BytesIO()
        df_out = df_in.copy()
        df_out['Fecha'] = df_out['Fecha'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_out['Horario'] = df_out['Horario'].apply(lambda x: x.strftime('%H:%M'))
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_out.drop(columns=['id']).to_excel(writer, index=False)
        return output.getvalue()

    col2.download_button(
        "📥 Descargar Excel",
        data=to_excel(df),
        file_name=f"ruta_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Mostrar tabla limpia
    st.dataframe(df[['Fecha', 'Horario', 'Dirección', 'Teléfono', 'Latitud', 'Longitud']], use_container_width=True)

    # Botones para eliminar individuales
    with st.expander("🗑️ Gestionar / Eliminar puntos"):
        for i, row in df.iterrows():
            if st.button(f"Eliminar: {row['Dirección']} ({row['Horario']})", key=row['id']):
                st.session_state.puntos = [p for p in st.session_state.puntos if p['id'] != row['id']]
                st.rerun()
else:
    st.info("Agrega tu primer punto en el panel lateral.")
