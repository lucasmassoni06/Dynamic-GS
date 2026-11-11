"""Integra grafo de paradas com tabulação de lotação."""

import json
from pathlib import Path

from core.grafo import Grafo
from core.lotacao import (
    TrechoLotacao,
    carregar_historico,
    interpolar_lotacao,
    tabular_lotacao,
)

DIRETORIO_DADOS = Path(__file__).resolve().parent.parent / "data"


def construir_grafo() -> Grafo:
    linhas = json.loads((DIRETORIO_DADOS / "linhas.json").read_text(encoding="utf-8"))
    grafo = Grafo()

    for linha_id, dados in linhas.items():
        paradas = dados["paradas"]
        tempo = dados["tempo_entre_paradas_min"]

        for origem, destino in zip(paradas, paradas[1:]):
            grafo.adicionar_aresta(origem, destino, tempo, linha_id)
            grafo.adicionar_aresta(destino, origem, tempo, linha_id)

    return grafo


def construir_tabela_lotacao(
    dia_semana: str = "util",
    horario: str | None = None,
) -> dict[str, list[TrechoLotacao]]:
    """
    Tabula a lotação de todas as linhas para o dia escolhido.

    Se `horario` for informado, interpola a ocupação entre os blocos
    do histórico para refletir o horário exato pedido.
    """
    historico = carregar_historico(DIRETORIO_DADOS / "historico_lotacao.csv")
    tabela: dict[str, list[TrechoLotacao]] = {}

    for (dia, linha), registros in historico.items():
        if dia != dia_semana:
            continue

        if horario:
            trechos = interpolar_lotacao(registros, horario)
            for trecho in trechos:
                trecho.linha = linha
            tabela[linha] = trechos
        else:
            tabela[linha] = tabular_lotacao(linha, registros)

    return tabela


def buscar_rotas(origem: str, destino: str, dia_semana: str = "util", horario: str = "07:00") -> dict:
    from core.operacao import verificar_operacao

    operacao = verificar_operacao(dia_semana, horario)

    if not operacao["operando"]:
        return {
            "encontrada": False,
            "fora_de_operacao": True,
            "origem": origem,
            "destino": destino,
            "dia_semana": dia_semana,
            "horario_pedido": horario,
            "primeira_partida": operacao["primeira_partida"],
            "ultima_partida": operacao["ultima_partida"],
            "mensagem": operacao["mensagem"],
        }

    grafo = construir_grafo()
    tabela = construir_tabela_lotacao(dia_semana, horario)

    custo, caminho = grafo.caminho_minimo(origem, destino)

    if custo == float("inf"):
        return {"encontrada": False, "origem": origem, "destino": destino}

    trechos = []
    for parada_origem, parada_destino in zip(caminho, caminho[1:]):
        aresta = next(
            (a for a in grafo.vizinhos(parada_origem) if a.destino == parada_destino),
            None,
        )
        lotacao = _lotacao_do_trecho(tabela, aresta.linha if aresta else "", parada_origem)
        trechos.append({
            "de": parada_origem,
            "para": parada_destino,
            "linha": aresta.linha if aresta else "?",
            "tempo_min": aresta.peso if aresta else 0,
            "lotacao": lotacao,
        })

    return {
        "encontrada": True,
        "origem": origem,
        "destino": destino,
        "dia_semana": dia_semana,
        "horario_pedido": horario,
        "horario_considerado": horario,
        "tempo_total_min": custo,
        "caminho": caminho,
        "trechos": trechos,
    }


def itinerario_linha(linha_id: str, dia_semana: str = "util", horario: str | None = None) -> dict:
    """Retorna o trajeto completo de uma linha com a lotação de cada parada."""
    linhas = json.loads((DIRETORIO_DADOS / "linhas.json").read_text(encoding="utf-8"))

    if linha_id not in linhas:
        return {"encontrada": False, "linha": linha_id}

    from core.operacao import OPERACAO

    janela = OPERACAO.get(dia_semana, OPERACAO["util"])
    dados = linhas[linha_id]
    tabela = construir_tabela_lotacao(dia_semana, horario)
    lotacoes = {t.parada: t for t in tabela.get(linha_id, [])}

    paradas = []
    for indice, parada in enumerate(dados["paradas"]):
        lotacao = lotacoes.get(parada)
        paradas.append({
            "parada": parada,
            "ordem": indice + 1,
            "horario": lotacao.horario if lotacao else None,
            "lotacao": {
                "passageiros": lotacao.passageiros,
                "percentual": lotacao.percentual,
                "status": lotacao.status,
            } if lotacao else None,
        })

    return {
        "encontrada": True,
        "linha": linha_id,
        "nome": dados["nome"],
        "paradas": paradas,
        "primeira_partida": janela["primeira"],
        "ultima_partida": janela["ultima"],
        "tempo_total_min": dados["tempo_entre_paradas_min"] * (len(dados["paradas"]) - 1),
    }


def _lotacao_do_trecho(tabela: dict, linha: str, parada: str) -> dict | None:
    for trecho in tabela.get(linha, []):
        if trecho.parada == parada:
            return {
                "passageiros": trecho.passageiros,
                "percentual": trecho.percentual,
                "status": trecho.status,
            }
    return None