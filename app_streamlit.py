"""Simulador visual de rotas e lotação de ônibus."""

import json
from pathlib import Path

import pydeck as pdk
import streamlit as st

from core.rotas import buscar_rotas, itinerario_linha

DIRETORIO_DADOS = Path(__file__).resolve().parent / "data"

CORES_STATUS = {
    "vazio": [46, 204, 113],
    "parcial": [241, 196, 15],
    "cheio": [231, 76, 60],
}

CORES_LINHA = {
    "L1": [41, 128, 185],
    "L2": [155, 89, 182],
    "L3": [26, 188, 156],
    "L4": [230, 126, 34],
    "L5": [52, 73, 94],
    "L6": [192, 57, 43],
}


@st.cache_data(ttl=5)
def carregar_paradas() -> dict:
    return json.loads((DIRETORIO_DADOS / "paradas.json").read_text(encoding="utf-8"))


@st.cache_data(ttl=5)
def carregar_linhas() -> dict:
    return json.loads((DIRETORIO_DADOS / "linhas.json").read_text(encoding="utf-8"))


@st.cache_data(ttl=5)
def _itinerario_cache(linha_id: str, dia_semana: str, horario: str) -> dict:
    return itinerario_linha(linha_id, dia_semana, horario)


def nome_parada(paradas: dict, parada_id: str) -> str:
    return paradas.get(parada_id, {}).get("nome", parada_id)


def montar_mapa(paradas: dict, caminho: list[str], linhas_rota: list[str]) -> pdk.Deck:
    """Desenha paradas e o trajeto completo da rota, com uma cor por linha."""
    pontos = [
        {
            "id": parada_id,
            "nome": dados["nome"],
            "lat": dados["lat"],
            "lon": dados["lon"],
            "na_rota": parada_id in caminho,
        }
        for parada_id, dados in paradas.items()
    ]

    camadas = [pdk.Layer(
        "ScatterplotLayer",
        data=pontos,
        get_position=["lon", "lat"],
        get_color="na_rota ? [41, 128, 185] : [149, 165, 166]",
        get_radius=180,
        pickable=True,
    )]

    if len(caminho) > 1:
        segmentos = []
        for indice, (origem, destino) in enumerate(zip(caminho, caminho[1:])):
            if origem not in paradas or destino not in paradas:
                continue

            linha_trecho = linhas_rota[indice] if indice < len(linhas_rota) else "L1"
            segmentos.append({
                "path": [
                    [paradas[origem]["lon"], paradas[origem]["lat"]],
                    [paradas[destino]["lon"], paradas[destino]["lat"]],
                ],
                "cor": CORES_LINHA.get(linha_trecho, [100, 100, 100]),
            })

        camadas.append(pdk.Layer(
            "PathLayer",
            data=segmentos,
            get_path="path",
            get_color="cor",
            get_width=8,
            width_min_pixels=4,
        ))

    return pdk.Deck(
        layers=camadas,
        initial_view_state=pdk.ViewState(
            latitude=-23.575,
            longitude=-46.655,
            zoom=11.2,
            pitch=0,
        ),
        tooltip={"text": "{nome}"},
    )


def exibir_itinerario(dia_semana: str, horario: str) -> None:
    """Seção de clique na linha: mostra o trajeto completo."""
    linhas = carregar_linhas()
    paradas = carregar_paradas()

    rotulo_dia = {"util": "dia útil", "sabado": "sábado", "domingo": "domingo"}[dia_semana]

    st.subheader("Itinerário por linha")
    st.caption(
        f"Trajeto completo e lotação estimada para {horario} ({rotulo_dia}). "
        f"Clique em uma linha para expandir."
    )

    for linha_id, dados in linhas.items():
        with st.expander(f"[{linha_id}] {dados['nome']}"):
            itinerario = _itinerario_cache(linha_id, dia_semana, horario)

            if not itinerario["encontrada"]:
                st.warning("Linha sem dados.")
                continue

            st.caption(
                f"{len(itinerario['paradas'])} paradas · "
                f"~{itinerario['tempo_total_min']} min de ponta a ponta · "
                f"opera das {itinerario['primeira_partida']} às {itinerario['ultima_partida']}"
            )

            for parada in itinerario["paradas"]:
                coluna_nome, coluna_lotacao = st.columns([3, 1])
                nome = nome_parada(paradas, parada["parada"])

                with coluna_nome:
                    horario_parada = parada["horario"] or "--:--"
                    st.markdown(f"**{parada['ordem']}.** {nome} · `{horario_parada}`")

                with coluna_lotacao:
                    lotacao = parada["lotacao"]
                    if lotacao:
                        cor = CORES_STATUS[lotacao["status"]]
                        st.markdown(
                            f"<div style='background:rgb({cor[0]},{cor[1]},{cor[2]});"
                            f"color:white;padding:6px;border-radius:6px;text-align:center;"
                            f"font-size:0.85em;font-weight:600;'>"
                            f"{lotacao['status']} · {lotacao['percentual']}%</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("sem dados")


def exibir_trechos(resultado: dict, paradas: dict) -> None:
    st.subheader("Trechos da rota")

    for trecho in resultado["trechos"]:
        lotacao = trecho["lotacao"]
        origem = nome_parada(paradas, trecho["de"])
        destino = nome_parada(paradas, trecho["para"])

        coluna_info, coluna_lotacao = st.columns([3, 1])

        with coluna_info:
            st.markdown(
                f"**[{trecho['linha']}]** {origem} → {destino}  \n"
                f"⏱ {trecho['tempo_min']} min"
            )

        with coluna_lotacao:
            if lotacao:
                cor = CORES_STATUS[lotacao["status"]]
                st.markdown(
                    f"<div style='background:rgb({cor[0]},{cor[1]},{cor[2]});"
                    f"color:white;padding:8px;border-radius:6px;text-align:center;"
                    f"font-weight:600;'>{lotacao['status']} · {lotacao['percentual']}%</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("sem dados")

        st.divider()


def exibir_veredito(resultado: dict) -> None:
    status = [t["lotacao"]["status"] for t in resultado["trechos"] if t["lotacao"]]

    if not status:
        st.info("Sem dados de lotação para avaliar.")
    elif "cheio" in status:
        st.error("Evite este horário — há trecho com lotação máxima. Considere esperar o próximo.")
    elif status.count("parcial") >= 2:
        st.warning("Viável, mas vá preparado para trechos com ocupação média.")
    else:
        st.success("Boa opção — trechos com folga de ocupação.")


def main() -> None:
    st.set_page_config(page_title="Simulador de Ônibus", page_icon="🚌", layout="wide")
    st.title("🚌 Simulador de Rotas e Lotação")
    st.caption("Projeto CitizenTech — Grafos + Tabulação")

    paradas = carregar_paradas()
    opcoes = {pid: f"{pid} — {dados['nome']}" for pid, dados in paradas.items()}

    st.sidebar.header("Filtros")
    dia_semana = st.sidebar.selectbox(
        "Dia da semana",
        options=["util", "sabado", "domingo"],
        format_func=lambda d: {"util": "Dia útil", "sabado": "Sábado", "domingo": "Domingo"}[d],
    )
    horario_partida = st.sidebar.time_input("Horário de partida", value=None)

    st.sidebar.divider()

    if st.sidebar.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.caption(
        "A lotação é interpolada entre os blocos do histórico para refletir o horário escolhido."
    )

    coluna_origem, coluna_destino = st.columns(2)

    with coluna_origem:
        origem = st.selectbox("Origem", options=list(opcoes), format_func=opcoes.get)

    with coluna_destino:
        destino = st.selectbox(
            "Destino",
            options=list(opcoes),
            format_func=opcoes.get,
            index=len(opcoes) - 1,
        )

    if origem == destino:
        st.warning("Escolha paradas diferentes para calcular a rota.")
        return

    horario_str = horario_partida.strftime("%H:%M") if horario_partida else "07:00"
    resultado = buscar_rotas(origem, destino, dia_semana, horario_str)

    if resultado.get("fora_de_operacao"):
        st.warning(f"🚫 {resultado['mensagem']}")
        st.info(
            f"**Horário de operação neste dia:** "
            f"das {resultado['primeira_partida']} às {resultado['ultima_partida']}"
        )
        st.divider()
        exibir_itinerario(dia_semana, horario_str)
        return

    if not resultado["encontrada"]:
        st.error("Nenhuma rota encontrada entre as paradas informadas.")
        return

    linhas_rota = [trecho["linha"] for trecho in resultado["trechos"]]

    coluna_mapa, coluna_resumo = st.columns([2, 1])

    with coluna_mapa:
        st.pydeck_chart(montar_mapa(paradas, resultado["caminho"], linhas_rota))

    with coluna_resumo:
        st.metric("Tempo total estimado", f"{resultado['tempo_total_min']} min")
        st.metric("Paradas no trajeto", len(resultado["caminho"]))
        st.metric("Trechos", len(resultado["trechos"]))

        if horario_partida:
            st.metric("Partida", horario_partida.strftime("%H:%M"))

        st.markdown("**Linhas na rota**")
        for linha_id in dict.fromkeys(linhas_rota):
            cor = CORES_LINHA.get(linha_id, [100, 100, 100])
            st.markdown(
                f"<span style='display:inline-block;width:12px;height:12px;"
                f"background:rgb({cor[0]},{cor[1]},{cor[2]});border-radius:3px;"
                f"margin-right:6px;'></span> {linha_id}",
                unsafe_allow_html=True,
            )

    st.divider()
    exibir_trechos(resultado, paradas)
    exibir_veredito(resultado)

    st.divider()
    exibir_itinerario(dia_semana, horario_str)


if __name__ == "__main__":
    main()