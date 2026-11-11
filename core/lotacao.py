"""Cálculo de lotação por trecho usando tabulação e interpolação."""

import csv
from dataclasses import dataclass
from pathlib import Path

CAPACIDADE_ONIBUS = 60


@dataclass
class TrechoLotacao:
    linha: str
    parada: str
    horario: str
    passageiros: int
    percentual: float
    status: str


def _para_minutos(horario: str) -> int:
    hora, minuto = map(int, horario.split(":"))
    return hora * 60 + minuto


def carregar_historico(caminho: Path) -> dict[tuple[str, str], list[dict]]:
    """Agrupa os registros por (dia_semana, linha), ignorando linhas inválidas."""
    historico: dict[tuple[str, str], list[dict]] = {}

    with caminho.open(encoding="utf-8") as arquivo:
        for registro in csv.DictReader(arquivo):
            linha = (registro.get("linha") or "").strip()
            dia = (registro.get("dia_semana") or "").strip()

            if not linha or linha == "linha":
                continue

            historico.setdefault((dia, linha), []).append({
                "parada": registro["parada"].strip(),
                "horario": registro["horario"].strip(),
                "embarques": int(registro["embarques"]),
                "desembarques": int(registro["desembarques"]),
            })

    return historico


def classificar(percentual: float) -> str:
    if percentual < 50:
        return "vazio"
    if percentual < 85:
        return "parcial"
    return "cheio"


def tabular_lotacao(linha: str, registros: list[dict]) -> list[TrechoLotacao]:
    """
    Tabulação: preenche a tabela de ocupação em ordem sequencial.
    ocupacao[i] = ocupacao[i-1] + embarques[i] - desembarques[i]
    Complexidade O(n).
    """
    tabela: list[TrechoLotacao] = []
    ocupacao_atual = 0

    for registro in registros:
        ocupacao_atual += registro["embarques"] - registro["desembarques"]
        ocupacao_atual = max(0, ocupacao_atual)
        percentual = round(ocupacao_atual / CAPACIDADE_ONIBUS * 100, 1)

        tabela.append(TrechoLotacao(
            linha=linha,
            parada=registro["parada"],
            horario=registro["horario"],
            passageiros=ocupacao_atual,
            percentual=percentual,
            status=classificar(percentual),
        ))

    return tabela


def lotacao_ingenuo(linha: str, registros: list[dict], indice: int) -> int:
    """Versão ingênua O(n) por consulta — usada só no benchmark."""
    ocupacao = 0
    for registro in registros[: indice + 1]:
        ocupacao += registro["embarques"] - registro["desembarques"]
        ocupacao = max(0, ocupacao)
    return ocupacao


def _dividir_em_blocos(registros: list[dict]) -> list[list[dict]]:
    """
    Divide os registros de uma linha em blocos de partida.

    Cada bloco começa quando o horário volta no tempo — sinal de que
    uma nova viagem começou.
    """
    blocos: list[list[dict]] = []
    bloco_atual: list[dict] = []
    ultimo_minuto = -1

    for registro in registros:
        minuto = _para_minutos(registro["horario"])
        if minuto < ultimo_minuto and bloco_atual:
            blocos.append(bloco_atual)
            bloco_atual = []
        bloco_atual.append(registro)
        ultimo_minuto = minuto

    if bloco_atual:
        blocos.append(bloco_atual)

    return blocos


def _ocupacao_por_parada(bloco: list[dict]) -> list[int]:
    """Tabula a ocupação acumulada parada por parada dentro de um bloco."""
    ocupacao = []
    acumulado = 0
    for registro in bloco:
        acumulado += registro["embarques"] - registro["desembarques"]
        acumulado = max(0, acumulado)
        ocupacao.append(acumulado)
    return ocupacao


def interpolar_lotacao(registros: list[dict], horario_pedido: str) -> list[TrechoLotacao]:
    """
    Interpola a ocupação entre os blocos de horário do histórico.

    Encontra os dois blocos vizinhos ao horário pedido e calcula a
    ocupação proporcional de cada parada. Fora do intervalo coberto,
    usa o bloco mais próximo.
    """
    if not registros:
        return []

    blocos = _dividir_em_blocos(registros)
    if not blocos:
        return []

    partidas = [_para_minutos(bloco[0]["horario"]) for bloco in blocos]
    minutos_pedido = _para_minutos(horario_pedido)

    indice_anterior = None
    indice_proximo = None

    for indice, partida in enumerate(partidas):
        if partida <= minutos_pedido:
            indice_anterior = indice
        elif indice_proximo is None:
            indice_proximo = indice
            break

    # Fora do intervalo: usa o bloco mais próximo
    if indice_anterior is None:
        bloco = blocos[0]
        ocupacao = _ocupacao_por_parada(bloco)
        return _montar_tabela(registros[0]["parada"] if False else bloco, ocupacao, horario_pedido)

    if indice_proximo is None:
        bloco = blocos[-1]
        ocupacao = _ocupacao_por_parada(bloco)
        return _montar_tabela(bloco, ocupacao, horario_pedido)

    min_anterior = partidas[indice_anterior]
    min_proximo = partidas[indice_proximo]
    fracao = (minutos_pedido - min_anterior) / (min_proximo - min_anterior)

    ocupacao_anterior = _ocupacao_por_parada(blocos[indice_anterior])
    ocupacao_proximo = _ocupacao_por_parada(blocos[indice_proximo])

    total = min(len(ocupacao_anterior), len(ocupacao_proximo))
    ocupacao_interpolada = [
        round(ocupacao_anterior[i] * (1 - fracao) + ocupacao_proximo[i] * fracao)
        for i in range(total)
    ]

    return _montar_tabela(blocos[indice_anterior], ocupacao_interpolada, horario_pedido)


def _montar_tabela(bloco: list[dict], ocupacao: list[int], horario: str) -> list[TrechoLotacao]:
    """Converte ocupação numérica em TrechoLotacao com percentual e status."""
    tabela = []
    for indice, valor in enumerate(ocupacao):
        percentual = round(valor / CAPACIDADE_ONIBUS * 100, 1)
        tabela.append(TrechoLotacao(
            linha="",
            parada=bloco[indice]["parada"],
            horario=horario,
            passageiros=valor,
            percentual=percentual,
            status=classificar(percentual),
        ))
    return tabela