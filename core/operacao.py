"""Janela de operação das linhas e validação de horário."""

OPERACAO = {
    "util": {"primeira": "05:30", "ultima": "23:30"},
    "sabado": {"primeira": "06:00", "ultima": "23:00"},
    "domingo": {"primeira": "07:00", "ultima": "22:00"},
}


def _para_minutos(horario: str) -> int:
    hora, minuto = map(int, horario.split(":"))
    return hora * 60 + minuto


def verificar_operacao(dia_semana: str, horario: str) -> dict:
    """Verifica se há ônibus circulando no dia e horário informados."""
    janela = OPERACAO.get(dia_semana)
    if not janela:
        return {
            "operando": False,
            "primeira_partida": None,
            "ultima_partida": None,
            "mensagem": "Dia da semana inválido.",
        }

    primeira = janela["primeira"]
    ultima = janela["ultima"]
    minutos_pedido = _para_minutos(horario)

    if minutos_pedido < _para_minutos(primeira):
        return {
            "operando": False,
            "primeira_partida": primeira,
            "ultima_partida": ultima,
            "mensagem": (
                f"Não há ônibus disponível neste horário. "
                f"A operação começa às {primeira}."
            ),
        }

    if minutos_pedido > _para_minutos(ultima):
        return {
            "operando": False,
            "primeira_partida": primeira,
            "ultima_partida": ultima,
            "mensagem": (
                f"Não há ônibus disponível neste horário. "
                f"A última partida é às {ultima} e a operação reinicia às {primeira}."
            ),
        }

    return {
        "operando": True,
        "primeira_partida": primeira,
        "ultima_partida": ultima,
        "mensagem": f"Operação normal — partidas das {primeira} às {ultima}.",
    }


def horario_mais_proximo(dia_semana: str, horario: str) -> str:
    """Retorna o bloco de horário do histórico mais próximo do pedido."""
    from pathlib import Path

    from core.lotacao import carregar_historico

    historico = carregar_historico(
        Path(__file__).resolve().parent.parent / "data" / "historico_lotacao.csv"
    )

    horarios = sorted({
        registro["horario"].split(":")[0] + ":00"
        for (dia, _), registros in historico.items()
        if dia == dia_semana
        for registro in registros
    })

    if not horarios:
        return horario

    minutos_pedido = _para_minutos(horario)
    return min(horarios, key=lambda h: abs(_para_minutos(h) - minutos_pedido))