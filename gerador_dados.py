"""Gera o histórico de lotação sintético com curva de demanda realista."""

import csv
import json
from pathlib import Path

DIRETORIO_DADOS = Path(__file__).resolve().parent / "data"

CAPACIDADE_ONIBUS = 60

PERFIS = {
    ("util", "06:00"): {"embarque_inicial": 30, "entrada": 0.30, "saida": 0.18},
    ("util", "07:00"): {"embarque_inicial": 58, "entrada": 0.55, "saida": 0.12},
    ("util", "12:00"): {"embarque_inicial": 14, "entrada": 0.15, "saida": 0.20},
    ("util", "18:00"): {"embarque_inicial": 56, "entrada": 0.52, "saida": 0.10},
    ("util", "22:00"): {"embarque_inicial": 8, "entrada": 0.10, "saida": 0.25},
    ("sabado", "10:00"): {"embarque_inicial": 20, "entrada": 0.22, "saida": 0.20},
    ("sabado", "16:00"): {"embarque_inicial": 18, "entrada": 0.20, "saida": 0.22},
    ("domingo", "10:00"): {"embarque_inicial": 10, "entrada": 0.12, "saida": 0.22},
    ("domingo", "16:00"): {"embarque_inicial": 9, "entrada": 0.10, "saida": 0.24},
}

AGENDA = [
    ("util", "06:00"), ("util", "07:00"), ("util", "12:00"),
    ("util", "18:00"), ("util", "22:00"),
    ("sabado", "10:00"), ("sabado", "16:00"),
    ("domingo", "10:00"), ("domingo", "16:00"),
]


def somar_minutos(horario: str, minutos: int) -> str:
    hora, minuto = map(int, horario.split(":"))
    total = hora * 60 + minuto + minutos
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def gerar_registros_linha(linha_id: str, dados: dict) -> list[dict]:
    paradas = dados["paradas"]
    intervalo = dados["tempo_entre_paradas_min"]
    registros = []

    for dia, horario_inicio in AGENDA:
        perfil = PERFIS[(dia, horario_inicio)]
        passageiros = 0

        for indice, parada in enumerate(paradas):
            horario = somar_minutos(horario_inicio, indice * intervalo)
            ultima = indice == len(paradas) - 1

            if indice == 0:
                embarques = perfil["embarque_inicial"]
                desembarques = 0
            elif ultima:
                embarques = 0
                desembarques = passageiros
            else:
                embarques = max(0, int(CAPACIDADE_ONIBUS * perfil["entrada"]))
                desembarques = max(0, int(passageiros * perfil["saida"]))

            passageiros += embarques - desembarques

            if passageiros > CAPACIDADE_ONIBUS:
                passageiros = CAPACIDADE_ONIBUS

            registros.append({
                "dia_semana": dia,
                "linha": linha_id,
                "parada": parada,
                "horario": horario,
                "embarques": embarques,
                "desembarques": desembarques,
            })

    return registros


def main() -> None:
    linhas = json.loads((DIRETORIO_DADOS / "linhas.json").read_text(encoding="utf-8"))

    registros = []
    for linha_id, dados in linhas.items():
        registros.extend(gerar_registros_linha(linha_id, dados))

    caminho = DIRETORIO_DADOS / "historico_lotacao.csv"
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=["dia_semana", "linha", "parada", "horario", "embarques", "desembarques"],
        )
        escritor.writeheader()
        escritor.writerows(registros)

    linhas_geradas = sorted({r["linha"] for r in registros})
    print(f"Gerados {len(registros)} registros em {caminho.name}")
    print(f"Linhas cobertas: {', '.join(linhas_geradas)}")


if __name__ == "__main__":
    main()