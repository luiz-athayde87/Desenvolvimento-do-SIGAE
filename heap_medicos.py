"""
Módulo: Min-Heap de Médicos (SIGAE)
Objetivo: Distribuição equitativa de consultas entre profissionais disponíveis.
Complexidade: O(1) para consulta do próximo médico disponível,
              O(log n) para inserção, remoção do topo e atualização de carga.
"""

from typing import Any


class MinHeapMedicos:
    SITUACAO_DISPONIVEL = "Disponivel"

    def __init__(self) -> None:
        self.heap: list[dict[str, Any]] = []

    def _chave_ordenacao(self, medico: dict[str, Any]) -> tuple[int, float, str]:
        return (
            int(medico["atendimentos_concluidos"]),
            float(medico["ultimo_atendimento"]),
            str(medico["id"]),
        )

    def _carga_menor(self, m1: dict[str, Any], m2: dict[str, Any]) -> bool:
        return self._chave_ordenacao(m1) < self._chave_ordenacao(m2)

    def _normalizar_medico(self, medico: dict[str, Any]) -> dict[str, Any]:
        for campo in ("id", "atendimentos_concluidos", "ultimo_atendimento", "situacao"):
            if campo not in medico:
                raise ValueError(f"Campo obrigatório ausente no cadastro do médico: '{campo}'.")

        medico_id = str(medico["id"]).strip()
        if not medico_id:
            raise ValueError("O ID do médico não pode ser vazio.")

        situacao = str(medico["situacao"]).strip().capitalize()
        return {
            **medico,
            "id": medico_id,
            "atendimentos_concluidos": int(medico["atendimentos_concluidos"]),
            "ultimo_atendimento": float(medico["ultimo_atendimento"]),
            "situacao": situacao,
        }

    def inserir(self, medico: dict[str, Any]) -> bool:
        normalizado = self._normalizar_medico(medico)
        if normalizado["situacao"] != self.SITUACAO_DISPONIVEL:
            return False

        for i, atual in enumerate(self.heap):
            if atual["id"] == normalizado["id"]:
                self.heap[i] = normalizado
                self._subir(i)
                self._descer(i)
                return True

        self.heap.append(normalizado)
        self._subir(len(self.heap) - 1)
        return True

    def espiar_proximo(self) -> dict[str, Any] | None:
        return self.heap[0] if self.heap else None

    def obter_medico_disponivel(self) -> dict[str, Any] | None:
        if not self.heap:
            return None

        proximo = self.heap[0]
        ultimo = self.heap.pop()
        if self.heap:
            self.heap[0] = ultimo
            self._descer(0)
        return proximo

    def atualizar_carga(
        self,
        medico_id: str,
        atendimentos_concluidos: int | None = None,
        ultimo_atendimento: float | None = None,
        situacao: str | None = None,
    ) -> bool:
        chave_id = str(medico_id).strip()
        for i, medico in enumerate(self.heap):
            if medico["id"] == chave_id:
                if atendimentos_concluidos is not None:
                    medico["atendimentos_concluidos"] = int(atendimentos_concluidos)
                if ultimo_atendimento is not None:
                    medico["ultimo_atendimento"] = float(ultimo_atendimento)
                if situacao is not None:
                    nova_situacao = str(situacao).strip().capitalize()
                    medico["situacao"] = nova_situacao
                    if nova_situacao != self.SITUACAO_DISPONIVEL:
                        ultimo = self.heap.pop()
                        if i < len(self.heap):
                            self.heap[i] = ultimo
                            self._subir(i)
                            self._descer(i)
                        return True

                self._subir(i)
                self._descer(i)
                return True

        return False

    def _subir(self, i: int) -> None:
        while i > 0:
            pai = (i - 1) // 2
            if self._carga_menor(self.heap[i], self.heap[pai]):
                self.heap[i], self.heap[pai] = self.heap[pai], self.heap[i]
                i = pai
            else:
                break

    def _descer(self, i: int) -> None:
        tamanho = len(self.heap)
        while True:
            menor = i
            esq = 2 * i + 1
            dir = 2 * i + 2

            if esq < tamanho and self._carga_menor(self.heap[esq], self.heap[menor]):
                menor = esq
            if dir < tamanho and self._carga_menor(self.heap[dir], self.heap[menor]):
                menor = dir

            if menor != i:
                self.heap[i], self.heap[menor] = self.heap[menor], self.heap[i]
                i = menor
            else:
                break

    def exportar_array(self) -> list[dict[str, Any]]:
        return list(self.heap)
