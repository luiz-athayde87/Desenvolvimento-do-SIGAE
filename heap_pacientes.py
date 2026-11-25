"""Min-Heap de pacientes ordenado por risco clínico, chegada e ID."""

from __future__ import annotations

from typing import Any


class MinHeapPacientes:
    def __init__(self) -> None:
        self.heap: list[dict[str, Any]] = []
        self._indices: dict[str, int] = {}

    def _prioridade_menor(self, p1, p2):
        # Desempate: 1º Grau de Risco (1 a 5), 2º Horário de Chegada, 3º ID
        return (int(p1["prioridade"]), float(p1["horario_chegada"]), str(p1["id"])) < (
            int(p2["prioridade"]),
            float(p2["horario_chegada"]),
            str(p2["id"]),
        )

    def inserir(self, paciente: dict[str, Any]) -> None:
        identificador = str(paciente["id"])
        if identificador in self._indices:
            raise ValueError(f"Paciente {identificador} já está na fila.")
        self.heap.append(paciente)
        indice = len(self.heap) - 1
        self._indices[identificador] = indice
        self._subir(indice)

    def topo(self) -> dict[str, Any] | None:
        return self.heap[0] if self.heap else None

    def extrair_proximo(self) -> dict[str, Any] | None:
        if not self.heap:
            return None
        if len(self.heap) == 1:
            removido = self.heap.pop()
            self._indices.pop(str(removido["id"]), None)
            return removido

        raiz = self.heap[0]
        ultimo = self.heap.pop()
        self._indices.pop(str(raiz["id"]), None)
        self.heap[0] = ultimo
        self._indices[str(ultimo["id"])] = 0
        self._descer(0)
        return raiz

    def remover(self, identificador: str) -> dict[str, Any] | None:
        indice = self._indices.get(str(identificador))
        if indice is None:
            return None
        removido = self.heap[indice]
        ultimo = self.heap.pop()
        self._indices.pop(str(identificador), None)
        if indice < len(self.heap):
            self.heap[indice] = ultimo
            self._indices[str(ultimo["id"])] = indice
            self._subir(indice)
            indice_atual = self._indices[str(ultimo["id"])]
            self._descer(indice_atual)
        return removido

    def atualizar_prioridade(self, identificador: str, prioridade: int) -> None:
        indice = self._indices.get(str(identificador))
        if indice is None:
            raise KeyError(f"Paciente {identificador} não está na fila.")
        self.heap[indice]["prioridade"] = int(prioridade)
        self._subir(indice)
        indice_atual = self._indices[str(identificador)]
        self._descer(indice_atual)

    def _trocar(self, primeiro: int, segundo: int) -> None:
        self.heap[primeiro], self.heap[segundo] = self.heap[segundo], self.heap[primeiro]
        self._indices[str(self.heap[primeiro]["id"])] = primeiro
        self._indices[str(self.heap[segundo]["id"])] = segundo

    def _subir(self, i):
        pai = (i - 1) // 2
        if i > 0 and self._prioridade_menor(self.heap[i], self.heap[pai]):
            self._trocar(i, pai)
            self._subir(pai)

    def _descer(self, i):
        menor = i
        esq, dir = 2 * i + 1, 2 * i + 2

        if esq < len(self.heap) and self._prioridade_menor(self.heap[esq], self.heap[menor]):
            menor = esq
        if dir < len(self.heap) and self._prioridade_menor(self.heap[dir], self.heap[menor]):
            menor = dir
        if menor != i:
            self._trocar(i, menor)
            self._descer(menor)

    def esta_vazia(self) -> bool:
        return not self.heap

    def exportar_array(self) -> list[dict[str, Any]]:
        return list(self.heap)
