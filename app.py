import streamlit as st
import requests

# Configuración de la página
st.set_page_config(page_title="Modelo Cuantitativo Tenis", page_icon="🎾", layout="centered")

st.title("🎾 Modelo Cuantitativo de Apuestas - Tenis")
st.markdown("Inserta el apellido de un tenista para escanear la cartelera de la API, calcular el *Dominance Ratio* y ver las líneas de valor (+EV).")

# API Key por defecto
API_KEY_DEF = "twjp_c1046afac84884ad567af80d1e77dab9"

with st.sidebar:
    st.header("⚙️ Configuración")
    api_key_input = st.text_input("API Key de Live Tennis", value=API_KEY_DEF, type="password")
    circuito = st.selectbox("Circuito", ["ATP (Masculino)", "WTA (Femenino)"])

# Caja de entrada principal
jugador_buscado = st.text_input("🔍 Buscar tenista por apellido (Ej: Zverev, Sakkari, Alcaraz):", "")

if st.button("🚀 Analizar Partido", type="primary"):
    if not jugador_buscado.strip():
        st.warning("⚠️ Por favor ingresa el nombre o apellido de un tenista.")
    else:
        headers = {"x-api-key": api_key_input, "Content-Type": "application/json"}
        url_partidos = "https://api.livetennisapi.com/api/public/v1/matches?status=upcoming"
        
        with st.spinner("Consultando la API y calculando métricas..."):
            try:
                response = requests.get(url_partidos, headers=headers)
                if response.status_code != 200:
                    st.error(f"❌ Error de conexión con la API (Código: {response.status_code})")
                else:
                    lista_partidos = response.json().get('data', [])
                    partido_encontrado = None
                    
                    for match in lista_partidos:
                        if match.get('is_doubles', False):
                            continue
                        p1 = match.get('players', {}).get('p1', {})
                        p2 = match.get('players', {}).get('p2', {})
                        if jugador_buscado.lower() in str(p1.get('name', '')).lower() or jugador_buscado.lower() in str(p2.get('name', '')).lower():
                            partido_encontrado = match
                            break
                    
                    if not partido_encontrado:
                        st.info(f"🔍 No se encontró ningún partido próximo para '{jugador_buscado}'.")
                    else:
                        p1_data = partido_encontrado['players']['p1']
                        p2_data = partido_encontrado['players']['p2']
                        torneo = partido_encontrado.get('tournament', 'Torneo Oficial')
                        superficie = partido_encontrado.get('surface', 'hard').upper()
                        
                        r1 = p1_data.get('ranking') or p1_data.get('itf_ranking') or 100
                        r2 = p2_data.get('ranking') or p2_data.get('itf_ranking') or 100
                        nombre_1 = p1_data.get('name', 'Jugador 1')
                        nombre_2 = p2_data.get('name', 'Jugador 2')
                        
                        is_atp = "ATP" in circuito
                        hold_base = 78.0 if is_atp else 62.0
                        break_base = 22.0 if is_atp else 36.0
                        base_juegos = 22.5 if is_atp else 21.5
                        
                        factor_r1 = max(0, (100 - r1) * 0.15)
                        factor_r2 = max(0, (100 - r2) * 0.15)
                        
                        limite_hold = 92.0 if is_atp else 85.0
                        hold_1 = round(min(limite_hold, hold_base + (factor_r1 * 0.4)), 1)
                        break_1 = round(min(45.0, break_base + (factor_r1 * 0.3)), 1)
                        dr_1 = round(hold_1 / (100 - break_1), 2) if (100 - break_1) > 0 else 1.0
                        
                        hold_2 = round(min(limite_hold, hold_base + (factor_r2 * 0.4)), 1)
                        break_2 = round(min(45.0, break_base + (factor_r2 * 0.3)), 1)
                        dr_2 = round(hold_2 / (100 - break_2), 2) if (100 - break_2) > 0 else 1.0
                        
                        diff_dr = round(dr_1 - dr_2, 2)
                        hold_sum = round(hold_1 + hold_2, 1)
                        
                        prob_1 = round((dr_1 / (dr_1 + dr_2)) * 100, 1)
                        prob_2 = round(100 - prob_1, 1)
                        
                        desviacion_hold = hold_sum - (156.0 if is_atp else 120.0)
                        juegos_proyectados = round(base_juegos - (desviacion_hold * 0.15), 1)
                        linea_totales_justa = round(juegos_proyectados * 2) / 2
                        margen_juegos_abs = round(abs(diff_dr) * (12.5 if is_atp else 11.0), 1)
                        
                        favorita = nombre_1 if diff_dr >= 0 else nombre_2
                        underdog = nombre_2 if diff_dr >= 0 else nombre_1
                        
                        st.success(f"🏆 Torneo: **{torneo}** | Superficie: **{superficie}**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(label=f"⚔️ {nombre_1} (Rank {r1})", value=f"{prob_1}% Prob.", delta=f"DR: {dr_1}")
                            st.write(f"Hold: {hold_1}% | Break: {break_1}%")
                        with col2:
                            st.metric(label=f"⚔️ {nombre_2} (Rank {r2})", value=f"{prob_2}% Prob.", delta=f"DR: {dr_2}")
                            st.write(f"Hold: {hold_2}% | Break: {break_2}%")
                            
                        st.divider()
                        st.subheader("📐 Proyecciones Matemáticas")
                        
                        mcol1, mcol2, mcol3 = st.columns(3)
                        mcol1.metric("Total Juegos Proyectados", f"{juegos_proyectados}", f"Línea Justa: {linea_totales_justa}")
                        mcol2.metric("Margen Esperado", f"{margen_juegos_abs} juegos", f"A favor de {favorita}")
                        mcol3.metric("Favorito Modelo", favorita)
                        
                        st.info(f"💡 **Recomendación Cuantitativa (+EV):**\n\n"
                                f"• **O/U Totales:** Buscar OVER si el casino publica por debajo de **{linea_totales_justa}** / Buscar UNDER si está por encima.\n\n"
                                f"• **Hándicap sugerido:** Revisar línea para entrar con **{favorita}** o proteger al underdog **{underdog}**.")
                                
            except Exception as e:
                st.error(f"Ocurrió un error al procesar la solicitud: {e}")