"""Min-Heap de médicos disponíveis com operações O(log n)."""

from __future__ import annotations

from typing import Any


class MinHeapMedicos:
    def __init__(self) -> None:
        self.heap: list[dict[str, Any]] = []
        self._ids: set[str] = set()

    def _carga_menor(self, m1: dict[str, Any], m2: dict[str, Any]) -> bool:
        # Desempate: 1º Menor número de atendimentos, 2º Tempo sem atender, 3º ID
        chave_m1 = (
            int(m1["atendimentos_concluidos"]),
            float(m1["ultimo_atendimento"]),
            str(m1["id"]),
        )
        chave_m2 = (
            int(m2["atendimentos_concluidos"]),
            float(m2["ultimo_atendimento"]),
            str(m2["id"]),
        )
        return chave_m1 < chave_m2

    def inserir(self, medico: dict[str, Any]) -> None:
        identificador = str(medico["id"])
        if medico.get("situacao") != "Disponivel":
            raise ValueError("Apenas médicos disponíveis podem entrar no heap.")
        if identificador in self._ids:
            raise ValueError(f"Médico {identificador} já está disponível no heap.")
        self.heap.append(medico)
        self._ids.add(identificador)
        self._subir(len(self.heap) - 1)

    def topo(self) -> dict[str, Any] | None:
        return self.heap[0] if self.heap else None

    def obter_medico_disponivel(self) -> dict[str, Any] | None:
        if not self.heap:
            return None
        if len(self.heap) == 1:
            medico = self.heap.pop()
            self._ids.remove(str(medico["id"]))
            return medico
        medico = self.heap[0]
        ultimo = self.heap.pop()
        self._ids.remove(str(medico["id"]))
        self.heap[0] = ultimo
        self._descer(0)
        return medico

    extrair_proximo = obter_medico_disponivel

    def _subir(self, indice: int) -> None:
        while indice > 0:
            pai = (indice - 1) // 2
            if not self._carga_menor(self.heap[indice], self.heap[pai]):
                return
            self.heap[indice], self.heap[pai] = self.heap[pai], self.heap[indice]
            indice = pai

    def _descer(self, indice: int) -> None:
        while True:
            menor = indice
            esquerda, direita = 2 * indice + 1, 2 * indice + 2
            if esquerda < len(self.heap) and self._carga_menor(
                self.heap[esquerda], self.heap[menor]
            ):
                menor = esquerda
            if direita < len(self.heap) and self._carga_menor(self.heap[direita], self.heap[menor]):
                menor = direita
            if menor == indice:
                return
            self.heap[indice], self.heap[menor] = self.heap[menor], self.heap[indice]
            indice = menor

    def exportar_array(self) -> list[dict[str, Any]]:
        return list(self.heap)
