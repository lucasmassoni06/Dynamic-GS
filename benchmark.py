"""Compara tabulação O(n) com cálculo ingênuo O(n^2)."""

import time
from pathlib import Path

from core.lotacao import carregar_historico, lotacao_ingenuo, tabular_lotacao

DIRETORIO_DADOS = Path(__file__).resolve().parent / "data"


def medir_tempo(funcao, repeticoes: int = 1000) -> float:
    inicio = time.perf_counter()
    for _ in range(repeticoes):
        funcao()
    return (time.perf_counter() - inicio) / repeticoes * 1000


def main() -> None:
    historico = carregar_historico(DIRETORIO_DADOS / "historico_lotacao.csv")
    linha = next(iter(historico))
    registros = historico[linha]
    ultimo_indice = len(registros) - 1

    tempo_tabulacao = medir_tempo(lambda: tabular_lotacao(linha, registros))
    tempo_ingenuo = medir_tempo(
        lambda: [lotacao_ingenuo(linha, registros, i) for i in range(len(registros))]
    )

    print(f"Linha analisada: {linha} ({len(registros)} trechos)\n")
    print(f"Tabulação (O(n)):        {tempo_tabulacao:.4f} ms")
    print(f"Cálculo ingênuo (O(n²)): {tempo_ingenuo:.4f} ms")
    print(f"Ganho:                   {tempo_ingenuo / tempo_tabulacao:.1f}x mais rápido")


if __name__ == "__main__":
    main()