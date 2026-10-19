from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# VAI CHOVER? | SIMMA — protótipo v3
# Previsão de modelo via Open-Meteo. Não representa observação
# de estação meteorológica nem alerta oficial de Defesa Civil.
# ============================================================

st.set_page_config(
    page_title="Vai chover? | SIMMA",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "https://api.open-meteo.com/v1/forecast"
SATELLITE_URL = "https://www.cptec.inpe.br/dsat/"

# Coordenadas aproximadas dos centros municipais. Rever se o projeto
# passar a usar uma estação local ou uma coordenada operacional definida.
LOCAIS = {
    "Canarana–MT": (-13.55, -52.27),
    "Água Boa–MT": (-14.05, -52.16),
    "Querência–MT": (-12.61, -52.21),
    "Nova Xavantina–MT": (-14.67, -52.35),
    "Gaúcha do Norte–MT": (-13.18, -53.26),
    "Ribeirão Cascalheira–MT": (-12.94, -51.82),
}

WEATHER_CODES = {
    0: "Céu limpo", 1: "Predominantemente limpo", 2: "Parcialmente nublado",
    3: "Nublado", 45: "Nevoeiro", 48: "Nevoeiro com geada",
    51: "Garoa fraca", 53: "Garoa moderada", 55: "Garoa intensa",
    56: "Garoa congelante fraca", 57: "Garoa congelante intensa",
    61: "Chuva fraca", 63: "Chuva moderada", 65: "Chuva forte",
    66: "Chuva congelante fraca", 67: "Chuva congelante forte",
    71: "Neve fraca", 73: "Neve moderada", 75: "Neve forte", 77: "Grãos de neve",
    80: "Pancadas fracas", 81: "Pancadas moderadas", 82: "Pancadas fortes",
    85: "Pancadas de neve fracas", 86: "Pancadas de neve fortes",
    95: "Trovoada", 96: "Trovoada com granizo fraco", 99: "Trovoada com granizo forte",
}

# Setas representam PARA ONDE o vento sopra. O campo meteorológico
# wind_direction_10m representa de onde o vento vem; por isso somamos 180°.
ARROWS_16 = ["↑", "↗", "↗", "↗", "→", "↘", "↘", "↘", "↓", "↙", "↙", "↙", "←", "↖", "↖", "↖"]


def rotulo_tempo(codigo):
    try:
        return WEATHER_CODES.get(int(codigo), "Condição não identificada")
    except (TypeError, ValueError):
        return "Condição não identificada"


def direcao_cardinal(graus):
    if pd.isna(graus):
        return "—"
    pontos = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"]
    return pontos[int((float(graus) + 22.5) // 45) % 8]


def seta_vento(graus_de_origem):
    if pd.isna(graus_de_origem):
        return "•"
    graus_para_onde_sopra = (float(graus_de_origem) + 180) % 360
    return ARROWS_16[int((graus_para_onde_sopra + 11.25) // 22.5) % 16]


def fmt(valor, casas=1):
    try:
        if pd.isna(valor):
            return "—"
        return f"{float(valor):.{casas}f}"
    except (TypeError, ValueError):
        return "—"


@st.cache_data(ttl=600, show_spinner=False)
def obter_previsao(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "America/Sao_Paulo",
        "forecast_days": 3,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day",
            "precipitation", "rain", "showers", "weather_code", "cloud_cover",
            "pressure_msl", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
        ]),
        "hourly": ",".join([
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
            "precipitation_probability", "precipitation", "rain", "showers", "cloud_cover",
            "pressure_msl", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "weather_code",
        ]),
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_probability_max", "precipitation_sum", "rain_sum", "wind_speed_10m_max",
        ]),
    }
    response = requests.get(API_URL, params=params, timeout=25)
    response.raise_for_status()
    return response.json()


def criar_mapa_vento(local, latitude, longitude, atual):
    direcao = atual.get("wind_direction_10m")
    velocidade = atual.get("wind_speed_10m")
    rajada = atual.get("wind_gusts_10m")
    seta = seta_vento(direcao)
    card = direcao_cardinal(direcao)
    rotulo = f"{seta}  {fmt(velocidade, 0)} km/h"
    hover = (
        f"{local}<br>Vento: {fmt(velocidade, 1)} km/h<br>"
        f"Rajadas: {fmt(rajada, 1)} km/h<br>Direção de origem: {fmt(direcao, 0)}° ({card})<br>"
        f"Seta: sentido para onde o vento sopra"
    )
    fig = go.Figure()
    fig.add_trace(go.Scattermap(
        lat=[latitude], lon=[longitude], mode="markers+text",
        marker={"size": 25, "color": "#21c7b7", "opacity": 0.96},
        text=[rotulo], textposition="top center",
        textfont={"size": 16, "color": "#102a43"},
        hovertext=[hover], hoverinfo="text", name="Vento estimado",
    ))
    fig.update_layout(
        map={"style": "open-street-map", "center": {"lat": latitude, "lon": longitude}, "zoom": 8},
        margin={"l": 0, "r": 0, "t": 8, "b": 0}, height=430,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2f8"}, showlegend=False,
    )
    return fig


def carregar_logo():
    pasta = Path(__file__).parent / "assets"
    candidatos = [
        pasta / "logo_simma.png", pasta / "logo_simma.webp",
        pasta / "logo_simma.jpg", pasta / "logo_simma.jpeg",
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return None


st.markdown("""
<style>
:root { --navy:#0b2035; --panel:#102d46; --teal:#21c7b7; --muted:#a9c0d2; }
.stApp { background: linear-gradient(145deg, #071726 0%, #0b2035 52%, #102b42 100%); }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }
[data-testid="stMetric"] { background:rgba(18,48,73,.86); border:1px solid rgba(130,185,215,.22); padding:13px 16px; border-radius:12px; }
[data-testid="stMetricLabel"] { color:#b8cede; }
[data-testid="stMetricValue"] { color:#f4f9fc; }
h1,h2,h3 { color:#f1f7fb; }
.brand-subtitle { color:#a9c0d2; margin-top:-0.7rem; }
.brand-kicker { color:#21c7b7; font-weight:700; letter-spacing:.11em; font-size:.76rem; }
.panel-note { color:#afc5d5; font-size:.86rem; }
div[data-testid="stTabs"] button { font-weight:600; }
</style>
""", unsafe_allow_html=True)

# Cabeçalho com logotipo oficial, caso o arquivo tenha sido colocado em assets/.
logo = carregar_logo()
header_left, header_right = st.columns([1, 5], vertical_alignment="center")
with header_left:
    if logo:
        st.image(str(logo), use_container_width=True)
    else:
        st.markdown("<div class='brand-kicker'>SIMMA</div><div style='font-size:2.0rem;font-weight:750;color:#f1f7fb;line-height:1.1'>Vai chover?</div>", unsafe_allow_html=True)
with header_right:
    st.markdown("<div class='brand-kicker'>SISTEMA INTEGRADO DE MONITORAMENTO METEOROLÓGICO E AMBIENTAL</div>", unsafe_allow_html=True)
    st.markdown("<p class='brand-subtitle'>Previsão meteorológica • Canarana e região • Protótipo experimental v3</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Configurações")
    local = st.selectbox("Município principal", list(LOCAIS.keys()), index=0)
    horizonte = st.selectbox("Horizonte dos gráficos", ["Próximas 24 horas", "Próximas 48 horas", "Próximas 72 horas"], index=0)
    if st.button("↻ Atualizar dados", use_container_width=True):
        obter_previsao.clear()
        st.rerun()
    st.divider()
    st.markdown("**Fontes dos dados**")
    st.markdown("[Open-Meteo — previsão](https://open-meteo.com/)")
    st.markdown("[CPTEC/INPE — satélite](https://www.cptec.inpe.br/dsat/)")
    st.markdown("[INMET — estações meteorológicas](https://portal.inmet.gov.br/servicos/esta%C3%A7%C3%B5es-autom%C3%A1ticas)")
    st.caption("As setas representam o sentido estimado para onde o vento sopra, calculado a partir da direção de origem fornecida pelo modelo.")

lat, lon = LOCAIS[local]
try:
    with st.spinner(f"Consultando a previsão para {local}..."):
        dados = obter_previsao(lat, lon)
except requests.RequestException as exc:
    st.error("Não foi possível consultar a Open-Meteo neste momento. Verifique a conexão e tente novamente.")
    st.caption(f"Detalhe técnico: {exc}")
    st.stop()
except (ValueError, KeyError) as exc:
    st.error("A resposta recebida da fonte meteorológica não pôde ser interpretada.")
    st.caption(f"Detalhe técnico: {exc}")
    st.stop()

atual = dados.get("current", {})
horario_atual = atual.get("time", "—")
condicao = rotulo_tempo(atual.get("weather_code"))

st.caption(f"📍 {local}  |  Horário da fonte: {horario_atual}  |  Condição prevista: {condicao}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Temperatura", f"{fmt(atual.get('temperature_2m'))} °C")
c2.metric("Sensação térmica", f"{fmt(atual.get('apparent_temperature'))} °C")
c3.metric("Umidade relativa", f"{fmt(atual.get('relative_humidity_2m'), 0)} %")
c4.metric("Precipitação atual do modelo", f"{fmt(atual.get('precipitation'))} mm")
c5, c6, c7, c8 = st.columns(4)
c5.metric("Nebulosidade", f"{fmt(atual.get('cloud_cover'), 0)} %")
c6.metric("Pressão ao nível do mar", f"{fmt(atual.get('pressure_msl'))} hPa")
c7.metric("Vento estimado", f"{fmt(atual.get('wind_speed_10m'))} km/h")
c8.metric("Rajadas estimadas", f"{fmt(atual.get('wind_gusts_10m'))} km/h")

hourly = dados.get("hourly", {})
df_all = pd.DataFrame(hourly)
if df_all.empty or "time" not in df_all:
    st.error("A fonte não retornou dados horários para este município.")
    st.stop()
df_all["time"] = pd.to_datetime(df_all["time"])
limite_horas = {"Próximas 24 horas": 24, "Próximas 48 horas": 48, "Próximas 72 horas": 72}[horizonte]
inicio = pd.to_datetime(horario_atual) if horario_atual != "—" else df_all["time"].min()
df = df_all[df_all["time"] >= inicio].head(limite_horas).copy()
if df.empty:
    df = df_all.head(limite_horas).copy()

# Navegação principal. O conteúdo dos recursos fica separado para reduzir poluição visual.
tab_painel, tab_municipios, tab_sat, tab_metodo = st.tabs(["Painel meteorológico", "Mapas por município", "Satélite", "Sobre e fontes"])

with tab_painel:
    st.subheader("Vai chover nas próximas horas?")
    proximas = df.head(6)
    prob = pd.to_numeric(proximas.get("precipitation_probability", pd.Series(dtype=float)), errors="coerce")
    chuva = pd.to_numeric(proximas.get("precipitation", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    prob_max = prob.max() if not prob.empty else float("nan")
    if pd.notna(prob_max) and prob_max >= 70:
        st.warning(f"Sinal de atenção na previsão: probabilidade horária máxima de chuva de {prob_max:.0f}% nas próximas 6 horas; acumulado previsto no período de {chuva:.1f} mm.")
    elif pd.notna(prob_max) and prob_max >= 30:
        st.info(f"A previsão indica possibilidade de chuva nas próximas 6 horas. Probabilidade horária máxima: {prob_max:.0f}%; acumulado previsto: {chuva:.1f} mm.")
    elif pd.notna(prob_max):
        st.success(f"A previsão indica baixa probabilidade de chuva nas próximas 6 horas. Acumulado previsto: {chuva:.1f} mm.")
    else:
        st.info("A probabilidade de precipitação não está disponível para o período selecionado.")
    st.caption("Síntese automática de previsão de modelo — não é garantia de ocorrência, nem alerta oficial.")

    # Alertas experimentais baseados somente na previsão consultada.
    st.subheader("Indicadores de atenção meteorológica")
    alertas = []
    prob6 = pd.to_numeric(df.head(6).get("precipitation_probability", pd.Series(dtype=float)), errors="coerce")
    chuva6 = pd.to_numeric(df.head(6).get("precipitation", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    rajada_max = pd.to_numeric(df.head(6).get("wind_gusts_10m", pd.Series(dtype=float)), errors="coerce").max()
    sensacao_max = pd.to_numeric(df.head(6).get("apparent_temperature", pd.Series(dtype=float)), errors="coerce").max()
    if not prob6.empty and pd.notna(prob6.max()) and prob6.max() >= 70:
        alertas.append(("Chuva", f"Probabilidade horária chega a {prob6.max():.0f}% nas próximas 6 horas; acumulado previsto {chuva6:.1f} mm."))
    if pd.notna(rajada_max) and rajada_max >= 50:
        alertas.append(("Rajadas", f"Rajadas de vento previstas de até {rajada_max:.0f} km/h nas próximas 6 horas."))
    if pd.notna(sensacao_max) and sensacao_max >= 35:
        alertas.append(("Calor", f"Sensação térmica prevista de até {sensacao_max:.1f} °C nas próximas 6 horas."))
    if alertas:
        for tipo, texto in alertas:
            st.warning(f"**{tipo}:** {texto}")
    else:
        st.info("Nenhum dos critérios experimentais de atenção configurados foi atingido nas próximas 6 horas. Isso não significa ausência de risco meteorológico.")
    st.caption("Critérios demonstrativos do protótipo, sem validação operacional. Não substituem avisos oficiais do INMET, Defesa Civil ou autoridades locais.")

    st.subheader(f"Previsão horária — {horizonte.lower()}")
    col_a, col_b = st.columns(2)
    with col_a:
        if "precipitation_probability" in df:
            fig = px.bar(df, x="time", y="precipitation_probability", labels={"time":"Horário", "precipitation_probability":"Probabilidade (%)"}, title="Probabilidade de precipitação por hora")
            fig.update_yaxes(range=[0, 100])
            fig.update_layout(template="plotly_dark", height=340, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)
        if "precipitation" in df:
            fig = px.bar(df, x="time", y="precipitation", labels={"time":"Horário", "precipitation":"Precipitação (mm)"}, title="Precipitação prevista por hora")
            fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        temp_cols = [c for c in ["temperature_2m", "apparent_temperature", "dew_point_2m"] if c in df]
        if temp_cols:
            temp_long = df[["time"] + temp_cols].melt(id_vars="time", var_name="Variável", value_name="Temperatura (°C)")
            nomes = {"temperature_2m":"Temperatura do ar", "apparent_temperature":"Sensação térmica", "dew_point_2m":"Ponto de orvalho"}
            temp_long["Variável"] = temp_long["Variável"].map(nomes).fillna(temp_long["Variável"])
            fig = px.line(temp_long, x="time", y="Temperatura (°C)", color="Variável", markers=True, title="Evolução térmica", labels={"time":"Horário"})
            fig.update_layout(template="plotly_dark", height=340, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)
        vento_cols = [c for c in ["wind_speed_10m", "wind_gusts_10m"] if c in df]
        if vento_cols:
            vento_long = df[["time"] + vento_cols].melt(id_vars="time", var_name="Variável", value_name="Velocidade (km/h)")
            vento_long["Variável"] = vento_long["Variável"].map({"wind_speed_10m":"Velocidade do vento", "wind_gusts_10m":"Rajadas"}).fillna(vento_long["Variável"])
            fig = px.line(vento_long, x="time", y="Velocidade (km/h)", color="Variável", markers=True, title="Vento e rajadas", labels={"time":"Horário"})
            fig.update_layout(template="plotly_dark", height=320, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Resumo dos próximos dias")
    daily = dados.get("daily", {})
    if daily:
        dfd = pd.DataFrame(daily)
        if "time" in dfd:
            dfd["time"] = pd.to_datetime(dfd["time"]).dt.strftime("%d/%m/%Y")
            if "weather_code" in dfd:
                dfd["Condição"] = dfd["weather_code"].apply(rotulo_tempo)
            dfd = dfd.rename(columns={
                "time":"Data", "temperature_2m_max":"Máxima (°C)", "temperature_2m_min":"Mínima (°C)",
                "precipitation_probability_max":"Prob. máxima de chuva (%)", "precipitation_sum":"Precipitação prevista (mm)",
                "rain_sum":"Chuva prevista (mm)", "wind_speed_10m_max":"Vento máximo (km/h)",
            })
            colunas = [c for c in ["Data", "Condição", "Máxima (°C)", "Mínima (°C)", "Prob. máxima de chuva (%)", "Precipitação prevista (mm)", "Vento máximo (km/h)"] if c in dfd]
            st.dataframe(dfd[colunas], use_container_width=True, hide_index=True)

    with st.expander("Consultar tabela horária completa / exportar CSV"):
        tabela = df.copy()
        if "weather_code" in tabela:
            tabela["Condição"] = tabela["weather_code"].apply(rotulo_tempo)
        if "wind_direction_10m" in tabela:
            tabela["Direção de origem do vento"] = tabela["wind_direction_10m"].apply(lambda x: f"{fmt(x, 0)}° {direcao_cardinal(x)}")
            tabela["Seta (sentido do vento)"] = tabela["wind_direction_10m"].apply(seta_vento)
        tabela = tabela.rename(columns={
            "time":"Horário", "temperature_2m":"Temperatura (°C)", "relative_humidity_2m":"Umidade relativa (%)",
            "dew_point_2m":"Ponto de orvalho (°C)", "apparent_temperature":"Sensação térmica (°C)",
            "precipitation_probability":"Probabilidade de chuva (%)", "precipitation":"Precipitação (mm)",
            "cloud_cover":"Nebulosidade (%)", "pressure_msl":"Pressão ao nível do mar (hPa)",
            "wind_speed_10m":"Vento (km/h)", "wind_gusts_10m":"Rajadas (km/h)",
        })
        st.dataframe(tabela, use_container_width=True, hide_index=True)
        st.download_button("Baixar dados horários em CSV", data=tabela.to_csv(index=False).encode("utf-8-sig"), file_name=f"previsao_{local.split('–')[0].lower().replace(' ', '_')}.csv", mime="text/csv")

with tab_municipios:
    st.subheader("Mapas municipais com direção estimada do vento")
    st.markdown("Cada aba mostra o centro aproximado do município e a direção do vento prevista pelo modelo Open-Meteo para o horário indicado.")
    st.info("A seta aponta para onde o vento sopra. A direção meteorológica original informa de onde o vento vem. As posições são coordenadas aproximadas, não limites oficiais dos municípios.")
    tabs_cidades = st.tabs(list(LOCAIS.keys()))
    for city_tab, (nome, coords) in zip(tabs_cidades, LOCAIS.items()):
        with city_tab:
            clat, clon = coords
            try:
                with st.spinner(f"Carregando previsão para {nome}..."):
                    city_data = obter_previsao(clat, clon)
                city_current = city_data.get("current", {})
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Temperatura", f"{fmt(city_current.get('temperature_2m'))} °C")
                mc2.metric("Vento", f"{fmt(city_current.get('wind_speed_10m'))} km/h")
                mc3.metric("Rajadas", f"{fmt(city_current.get('wind_gusts_10m'))} km/h")
                direction = city_current.get("wind_direction_10m")
                mc4.metric("Direção de origem", f"{fmt(direction, 0)}° {direcao_cardinal(direction)}")
                st.plotly_chart(criar_mapa_vento(nome, clat, clon, city_current), use_container_width=True, config={"displayModeBar": False})
                st.caption(f"Horário do modelo: {city_current.get('time', '—')} • Seta: {seta_vento(direction)} • Condição: {rotulo_tempo(city_current.get('weather_code'))}")
            except requests.RequestException:
                st.warning(f"Não foi possível carregar a previsão de {nome} neste momento. Tente atualizar os dados.")

with tab_sat:
    st.subheader("Imagens de satélite — CPTEC/INPE")
    st.markdown("A fonte oficial disponibiliza produtos de satélite e animações. A incorporação direta depende de o site permitir exibição dentro de outro sistema; se o quadro abaixo não carregar, use o botão para abrir o visualizador oficial.")
    st.link_button("Abrir visualizador oficial do CPTEC/INPE (GOES-19)", SATELLITE_URL, use_container_width=True)
    exibir = st.checkbox("Tentar exibir o visualizador dentro do painel", value=True)
    if exibir:
        try:
            components.iframe(SATELLITE_URL, height=650, scrolling=True)
        except Exception:
            st.warning("Não foi possível incorporar o visualizador nesta sessão. Abra pelo botão acima.")
    st.caption("Crédito: CPTEC/INPE. Os produtos estão sujeitos às condições de uso e reprodução definidas pelo provedor. Este protótipo não baixa nem redistribui imagens de satélite.")

with tab_metodo:
    st.subheader("Sobre o protótipo")
    st.markdown("**Vai chover?** é um protótipo de visualização de previsão meteorológica associado à identidade institucional da SIMMA — Sistema Integrado de Monitoramento Meteorológico e Ambiental.")
    st.markdown("**Fonte principal:** Open-Meteo Forecast API. A previsão é referente às coordenadas aproximadas dos centros municipais e não deve ser apresentada como observação medida em estação local.")
    st.markdown("**Direção do vento:** a API fornece a direção meteorológica de origem (de onde o vento vem). A seta é calculada no sentido para onde o vento sopra, acrescentando 180° à direção de origem. O modelo estima a condição; não é uma medição em tempo real de estação.")
    st.markdown("**Alertas:** os indicadores são regras demonstrativas aplicadas à previsão. Não são avisos oficiais e precisam de avaliação técnica e validação antes de qualquer uso operacional.")
    st.markdown("**Satélite:** o acesso é feito ao visualizador oficial do CPTEC/INPE. A incorporação pode ser bloqueada pelo próprio site; o link alternativo permanece disponível.")
    st.markdown("**Logo oficial da SIMMA:** incluída em `assets/logo_simma.png` e exibida automaticamente no cabeçalho.")
    st.markdown("**Fontes úteis:** [Open-Meteo](https://open-meteo.com/), [CPTEC/INPE DSAT](https://www.cptec.inpe.br/dsat/), [INMET](https://portal.inmet.gov.br/). Verifique as condições atuais de uso, atribuição e licenciamento antes de publicar ou usar comercialmente.")

st.divider()
st.markdown("<div class='panel-note'>SIMMA • Vai chover? — versão 3 experimental • Dados de previsão fornecidos por Open-Meteo. A disponibilidade depende dos provedores externos. Não utilize este protótipo como única fonte para decisões de segurança.</div>", unsafe_allow_html=True)
