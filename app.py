"""Simulador de consulta de lotação e rotas de ônibus."""

import json
from pathlib import Path

from core.rotas import buscar_rotas

DIRETORIO_DADOS = Path(__file__).resolve().parent / "data"


def carregar_paradas() -> dict:
    return json.loads((DIRETORIO_DADOS / "paradas.json").read_text(encoding="utf-8"))


def listar_paradas(paradas: dict) -> None:
    print("\nParadas disponíveis:")
    for parada_id, dados in paradas.items():
        print(f"  {parada_id} - {dados['nome']}")


def exibir_resultado(resultado: dict, paradas: dict) -> None:
    if not resultado["encontrada"]:
        print("\nNenhuma rota encontrada entre as paradas informadas.")
        return

    origem = paradas[resultado["origem"]]["nome"]
    destino = paradas[resultado["destino"]]["nome"]

    print(f"\nRota: {origem} -> {destino}")
    print(f"Tempo total estimado: {resultado['tempo_total_min']} min\n")

    for trecho in resultado["trechos"]:
        nome_origem = paradas[trecho["de"]]["nome"]
        nome_destino = paradas[trecho["para"]]["nome"]
        lotacao = trecho["lotacao"]

        if lotacao:
            info_lotacao = f"{lotacao['status']} ({lotacao['percentual']}%)"
        else:
            info_lotacao = "sem dados"

        print(
            f"  [{trecho['linha']}] {nome_origem} -> {nome_destino} "
            f"| {trecho['tempo_min']} min | lotação: {info_lotacao}"
        )

    veredito = _gerar_veredito(resultado["trechos"])
    print(f"\nVeredito: {veredito}")


def _gerar_veredito(trechos: list[dict]) -> str:
    status = [t["lotacao"]["status"] for t in trechos if t["lotacao"]]

    if not status:
        return "sem dados de lotação para avaliar."
    if "cheio" in status:
        return "evite este horário — há trecho com lotação máxima. Considere esperar o próximo."
    if status.count("parcial") >= 2:
        return "viável, mas vá preparado para trechos com ocupação média."
    return "boa opção — trechos com folga de ocupação."


def main() -> None:
    paradas = carregar_paradas()
    listar_paradas(paradas)

    origem = input("\nParada de origem (ex: P01): ").strip().upper()
    destino = input("Parada de destino (ex: P08): ").strip().upper()

    if origem not in paradas or destino not in paradas:
        print("\nParada inválida. Use um dos códigos listados.")
        return

    exibir_resultado(buscar_rotas(origem, destino), paradas)


if __name__ == "__main__":
    main()