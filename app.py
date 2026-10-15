import streamlit as st
import requests

# Configuración de la página
st.set_page_config(page_title="Modelo Cuantitativo Tenis Pro", page_icon="🎾", layout="centered")

# ==========================================
# GESTIÓN DE ESTADO PARA EL MENÚ PÍLDORA (ROBUSTA)
# ==========================================
if 'modo_activo' not in st.session_state:
    st.session_state.modo_activo = "api"

st.title("🎾 Modelo Matemático Analítico de Apuestas - Tenis")
st.markdown("Herramienta analítica avanzada para el cálculo de *Dominance Ratio*, probabilidades, líneas justas y detección de valor (+EV).")

st.write("")
col_menu1, col_menu2 = st.columns(2)

with col_menu1:
    tipo_btn_1 = "primary" if st.session_state.modo_activo == "api" else "secondary"
    if st.button("🤖 Usar API en vivo", use_container_width=True, type=tipo_btn_1):
        st.session_state.modo_activo = "api"

with col_menu2:
    tipo_btn_2 = "primary" if st.session_state.modo_activo == "manual" else "secondary"
    if st.button("✍️ Introducir datos manualmente", use_container_width=True, type=tipo_btn_2):
        st.session_state.modo_activo = "manual"

st.divider()

# Configuración general en la barra lateral
API_KEY_DEF = "twjp_c1046afac84884ad567af80d1e77dab9"
with st.sidebar:
    st.header("⚙️ Configuración General")
    api_key_input = st.text_input("API Key de Live Tennis", value=API_KEY_DEF, type="password")
    circuito = st.selectbox("Circuito Base", ["ATP (Masculino)", "WTA (Femenino)"])
    is_atp = "ATP" in circuito

# ==========================================
# BLOQUE 1: USAR API EN VIVO
# ==========================================
if st.session_state.modo_activo == "api":
    st.subheader("📡 Búsqueda Automática por API")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        jugador_buscado = st.text_input("🔍 Buscar tenista por apellido (Ej: Zverev, Sakkari, Alcaraz):", "", key="input_api")
    with col_s2:
        superficie_seleccionada = st.selectbox(
            "🌍 Superficie / Pista", 
            ["Hard (Dura)", "Clay (Arcilla)", "Grass (Hierba)", "Indoor Hard (Dura Tech)"],
            key="sup_api"
        )

    if st.button("🚀 Analizar desde API", type="primary", key="btn_api"):
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
                            st.info(f"🔍 No se encontró ningún partido próximo para '{jugador_buscado}' en la API. ¡Prueba a usar el modo manual!")
                        else:
                            st.session_state.partido_data = partido_encontrado
                            st.session_state.sup_activa = superficie_seleccionada
                            
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar la API: {e}")

    if 'partido_data' in st.session_state:
        match = st.session_state.partido_data
        p1_data = match['players']['p1']
        p2_data = match['players']['p2']
        torneo = match.get('tournament', 'Torneo Oficial')
        
        r1 = p1_data.get('ranking') or p1_data.get('itf_ranking') or 100
        r2 = p2_data.get('ranking') or p2_data.get('itf_ranking') or 100
        nombre_1 = p1_data.get('name', 'Jugador 1')
        nombre_2 = p2_data.get('name', 'Jugador 2')
        sup_sel = st.session_state.sup_activa
        
        if "Clay" in sup_sel:
            hold_base = 76.0 if is_atp else 59.0
            break_base = 24.0 if is_atp else 39.0
            base_juegos = 22.0 if is_atp else 21.0
        elif "Grass" in sup_sel:
            hold_base = 82.0 if is_atp else 66.0
            break_base = 18.0 if is_atp else 32.0
            base_juegos = 23.0 if is_atp else 22.0
        elif "Indoor" in sup_sel:
            hold_base = 81.0 if is_atp else 64.0
            break_base = 19.0 if is_atp else 34.0
            base_juegos = 23.0 if is_atp else 22.0
        else:
            hold_base = 78.0 if is_atp else 62.0
            break_base = 22.0 if is_atp else 36.0
            base_juegos = 22.5 if is_atp else 21.5
        
        factor_r1 = max(0, (100 - r1) * 0.15)
        factor_r2 = max(0, (100 - r2) * 0.15)
        
        limite_hold = 93.0 if is_atp else 86.0
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
        
        suma_esperada_hold = (hold_base * 2)
        desviacion_hold = hold_sum - suma_esperada_hold
        juegos_proyectados = round(base_juegos - (desviacion_hold * 0.15), 1)
        linea_totales_justa = round(juegos_proyectados * 2) / 2
        
        factor_multiplicador = 12.5 if is_atp else 11.0
        margen_juegos_abs = round(abs(diff_dr) * factor_multiplicador, 1)
        
        favorita = nombre_1 if diff_dr >= 0 else nombre_2
        underdog = nombre_2 if diff_dr >= 0 else nombre_1
        
        st.success(f"🏆 Torneo: **{torneo}** | Pista: **{sup_sel}**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label=f"⚔️ {nombre_1} (Rank {r1})", value=f"{prob_1}% Prob.", delta=f"DR: {dr_1}")
            st.write(f"Hold: {hold_1}% | Break: {break_1}%")
        with col2:
            st.metric(label=f"⚔️ {nombre_2} (Rank {r2})", value=f"{prob_2}% Prob.", delta=f"DR: {dr_2}")
            st.write(f"Hold: {hold_2}% | Break: {break_2}%")
            
        st.divider()
        st.subheader("📐 Proyecciones Matemáticas del Modelo")
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Juegos Proyectados", f"{juegos_proyectados}", f"Línea Justa: {linea_totales_justa}")
        mcol2.metric("Margen Proyectado", f"{margen_juegos_abs} juegos", f"A favor de {favorita}")
        mcol3.metric("Favorito Teórico", favorita)
        
        # Auditoría contra Casino
        st.divider()
        st.subheader("🎰 Busqueda de valor contra Líneas del Casino (+EV)")
        st.markdown("Ingresa las líneas reales que publica tu casa de apuestas:")
        
        ccol1, ccol2, ccol3 = st.columns(3)
        with ccol1:
            linea_casino_total = st.number_input("Línea Totales Casino (O/U)", min_value=12.5, max_value=45.5, value=float(linea_totales_justa), step=0.5, key="c_tot_api")
        with ccol2:
            handicap_casino_fav = st.number_input(f"Hándicap Casino ({favorita})", min_value=-15.0, max_value=0.0, value=-3.5, step=0.5, key="c_fav_api")
        with ccol3:
            handicap_casino_dog = st.number_input(f"Hándicap Casino ({underdog})", min_value=0.0, max_value=15.0, value=3.5, step=0.5, key="c_dog_api")
        
        st.markdown("---")
        st.markdown("### 💡 Diagnóstico de Valor Estricto:")
        
        # 1. Totales
        if linea_casino_total < linea_totales_justa - 1.5:
            st.success(f"📈 **OVER Detectado:** El casino ofrece una línea baja de **{linea_casino_total}**, mientras tu modelo proyecta **{juegos_proyectados}**. Hay margen sólido para el OVER.")
        elif linea_casino_total > linea_totales_justa + 1.5:
            st.success(f"📉 **UNDER Detectado:** El casino ofrece una línea alta de **{linea_casino_total}**, mientras tu modelo proyecta **{juegos_proyectados}**. Hay margen sólido para el UNDER.")
        else:
            st.info(f"⚖️ **Totales sin valor claro:** La línea del casino ({linea_casino_total}) está alineada con la justa del modelo ({linea_totales_justa}).")
            
        # 2. Hándicap Favorito (Estricto: El hándicap del casino debe ser MENOR que el margen esperado del modelo)
        if abs(handicap_casino_fav) < (margen_juegos_abs - 1.5):
            st.success(f"🔥 **Valor en el Favorito ({favorita}):** El casino te pide cubrir un hándicap de solo `{handicap_casino_fav}`, pero tu modelo espera un margen de `-{margen_juegos_abs}`. ¡Hay ventaja a favor del favorito!")
        else:
            st.info(f"🛡️ **Sin valor claro en el Favorito:** El hándicap del casino (`{handicap_casino_fav}`) es demasiado alto para el margen proyectado.")

        # 3. Hándicap Underdog (Estricto: El hándicap positivo del casino debe ser MAYOR al margen esperado para que realmente sea un "regalo")
        if handicap_casino_dog > (margen_juegos_abs + 1.5):
            st.success(f"🐕 **Valor Real en el Underdog ({underdog}):** El casino te está regalando un hándicap de `+{handicap_casino_dog}`, cuando tu modelo proyecta que la diferencia real será menor (`{margen_juegos_abs}`). ¡Excelente valor en el perro!")
        else:
            st.info(f"🛡️ **Sin valor claro en el Underdog:** El hándicap `+{handicap_casino_dog}` del casino es ajustado y no supera con margen el hándicap real esperado.")

# ==========================================
# BLOQUE 2: INTRODUCIR DATOS MANUALMENTE
# ==========================================
else:
    st.subheader("✍️ Auditoría Manual (Datos de Tennis Abstract)")
    
    col_j1, col_j2 = st.columns(2)
    
    with col_j1:
        st.markdown("### Jugador / Tenista A")
        nombre_1 = st.text_input("Nombre Tenista A", "Jugador 1", key="n1_man")
        hold_1 = st.number_input("Hold% (SvcG W%) A", min_value=40.0, max_value=98.0, value=78.0, step=0.1, key="h1_man")
        break_1 = st.number_input("Break% (RetG W%) A", min_value=5.0, max_value=60.0, value=22.0, step=0.1, key="b1_man")
        
    with col_j2:
        st.markdown("### Jugador / Tenista B")
        nombre_2 = st.text_input("Nombre Tenista B", "Jugador 2", key="n2_man")
        hold_2 = st.number_input("Hold% (SvcG W%) B", min_value=40.0, max_value=98.0, value=75.0, step=0.1, key="h2_man")
        break_2 = st.number_input("Break% (RetG W%) B", min_value=5.0, max_value=60.0, value=20.0, step=0.1, key="b2_man")
        
    if st.button("🧮 Calcular Modelo Manual", type="primary", key="btn_manual"):
        st.session_state.calculo_manual_hecho = True
        st.session_state.m_n1 = nombre_1
        st.session_state.m_n2 = nombre_2
        st.session_state.m_h1 = hold_1
        st.session_state.m_b1 = break_1
        st.session_state.m_h2 = hold_2
        st.session_state.m_b2 = break_2

    if st.session_state.get('calculo_manual_hecho', False):
        n1 = st.session_state.m_n1
        n2 = st.session_state.m_n2
        h1 = st.session_state.m_h1
        b1 = st.session_state.m_b1
        h2 = st.session_state.m_h2
        b2 = st.session_state.m_b2
        
        dr_1 = round(h1 / (100 - b1), 2) if (100 - b1) > 0 else 1.0
        dr_2 = round(h2 / (100 - b2), 2) if (100 - b2) > 0 else 1.0
        
        diff_dr = round(dr_1 - dr_2, 2)
        hold_sum = round(h1 + h2, 1)
        
        prob_1 = round((dr_1 / (dr_1 + dr_2)) * 100, 1)
        prob_2 = round(100 - prob_1, 1)
        
        base_juegos = 22.5 if is_atp else 21.5
        desviacion_hold = hold_sum - (156.0 if is_atp else 120.0)
        juegos_proyectados = round(base_juegos - (desviacion_hold * 0.15), 1)
        linea_totales_justa = round(juegos_proyectados * 2) / 2
        
        factor_multiplicador = 12.5 if is_atp else 11.0
        margen_juegos_abs = round(abs(diff_dr) * factor_multiplicador, 1)
        
        favorita = n1 if diff_dr >= 0 else n2
        underdog = n2 if diff_dr >= 0 else n1
        
        st.success("📊 **Resultados del Análisis Manual:**")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric(label=f"⚔️ {n1}", value=f"{prob_1}% Prob.", delta=f"DR: {dr_1}")
        with col_r2:
            st.metric(label=f"⚔️ {n2}", value=f"{prob_2}% Prob.", delta=f"DR: {dr_2}")
            
        st.divider()
        st.subheader("📐 Proyecciones Matemáticas del Modelo")
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Juegos Proyectados", f"{juegos_proyectados}", f"Línea Justa: {linea_totales_justa}")
        mcol2.metric("Margen Proyectado", f"{margen_juegos_abs} juegos", f"A favor de {favorita}")
        mcol3.metric("Favorito Teórico", favorita)
        
        st.divider()
        st.subheader("🎰 Busqueda de valor contra Líneas del Casino (+EV)")
        st.markdown("Ingresa las líneas reales que publica tu casa de apuestas:")
        
        ccol1, ccol2, ccol3 = st.columns(3)
        with ccol1:
            linea_casino_total = st.number_input("Línea Totales Casino (O/U)", min_value=12.5, max_value=45.5, value=float(linea_totales_justa), step=0.5, key="c_tot_man")
        with ccol2:
            handicap_casino_fav = st.number_input(f"Hándicap Casino ({favorita})", min_value=-15.0, max_value=0.0, value=-3.5, step=0.5, key="c_fav_man")
        with ccol3:
            handicap_casino_dog = st.number_input(f"Hándicap Casino ({underdog})", min_value=0.0, max_value=15.0, value=3.5, step=0.5, key="c_dog_man")
        
        st.markdown("---")
        st.markdown("### 💡 Diagnóstico de Valor Estricto:")
        
        if linea_casino_total < linea_totales_justa - 1.5:
            st.success(f"📈 **OVER Detectado:** El casino ofrece una línea baja de **{linea_casino_total}**, mientras tu modelo proyecta **{juegos_proyectados}**. Hay margen sólido para el OVER.")
        elif linea_casino_total > linea_totales_justa + 1.5:
            st.success(f"📉 **UNDER Detectado:** El casino ofrece una línea alta de **{linea_casino_total}**, mientras tu modelo proyecta **{juegos_proyectados}**. Hay margen sólido para el UNDER.")
        else:
            st.info(f"⚖️ **Totales sin valor claro:** La línea del casino ({linea_casino_total}) está alineada con la justa del modelo ({linea_totales_justa}).")
            
        if abs(handicap_casino_fav) < (margen_juegos_abs - 1.5):
            st.success(f"🔥 **Valor en el Favorito ({favorita}):** El casino te pide cubrir un hándicap de solo `{handicap_casino_fav}`, pero tu modelo espera un margen de `-{margen_juegos_abs}`. ¡Hay ventaja a favor del favorito!")
        else:
            st.info(f"🛡️ **Sin valor claro en el Favorito:** El hándicap del casino (`{handicap_casino_fav}`) es demasiado alto para el margen proyectado.")

        if handicap_casino_dog > (margen_juegos_abs + 1.5):
            st.success(f"🐕 **Valor Real en el Underdog ({underdog}):** El casino te está regalando un hándicap de `+{handicap_casino_dog}`, cuando tu modelo proyecta que la diferencia real será menor (`{margen_juegos_abs}`). ¡Excelente valor en el underdog!")
        else:
            st.info(f"🛡️ **Sin valor claro en el Underdog:** El hándicap `+{handicap_casino_dog}` del casino es ajustado y no supera con margen el hándicap real esperado.")
