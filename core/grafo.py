"""Grafo ponderado de paradas de ônibus e caminho mínimo."""

import heapq
from dataclasses import dataclass, field


@dataclass
class Aresta:
    destino: str
    peso: float
    linha: str


@dataclass
class Grafo:
    """Grafo dirigido com lista de adjacência."""
    adjacencia: dict[str, list[Aresta]] = field(default_factory=dict)

    def adicionar_parada(self, parada_id: str) -> None:
        self.adjacencia.setdefault(parada_id, [])

    def adicionar_aresta(self, origem: str, destino: str, peso: float, linha: str) -> None:
        self.adicionar_parada(origem)
        self.adicionar_parada(destino)
        self.adjacencia[origem].append(Aresta(destino, peso, linha))

    def vizinhos(self, parada_id: str) -> list[Aresta]:
        return self.adjacencia.get(parada_id, [])

    def caminho_minimo(self, origem: str, destino: str) -> tuple[float, list[str]]:
        """Dijkstra. Retorna (custo_total, caminho). Custo infinito se inacessível."""
        if origem not in self.adjacencia or destino not in self.adjacencia:
            return float("inf"), []

        distancias = {parada: float("inf") for parada in self.adjacencia}
        anteriores: dict[str, str] = {}
        distancias[origem] = 0

        fila = [(0.0, origem)]
        visitados = set()

        while fila:
            distancia_atual, parada_atual = heapq.heappop(fila)
            if parada_atual in visitados:
                continue
            visitados.add(parada_atual)

            if parada_atual == destino:
                break

            for aresta in self.vizinhos(parada_atual):
                nova_distancia = distancia_atual + aresta.peso
                if nova_distancia < distancias[aresta.destino]:
                    distancias[aresta.destino] = nova_distancia
                    anteriores[aresta.destino] = parada_atual
                    heapq.heappush(fila, (nova_distancia, aresta.destino))

        if distancias[destino] == float("inf"):
            return float("inf"), []

        return distancias[destino], self._reconstruir_caminho(anteriores, origem, destino)

    def _reconstruir_caminho(self, anteriores: dict[str, str], origem: str, destino: str) -> list[str]:
        caminho = [destino]
        atual = destino
        while atual != origem:
            atual = anteriores[atual]
            caminho.append(atual)
        return list(reversed(caminho))