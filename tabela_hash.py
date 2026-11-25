"""
Módulo: Tabela Hash (SIGAE)
Objetivo: Armazenamento, busca e remoção de cadastros por ID.
Colisões: Encadeamento separado.
Complexidade: O(1) médio para busca, inserção e remoção.
"""

from typing import Any


class TabelaHash:
    def __init__(self, tamanho_inicial: int = 16, fator_carga_maximo: float = 0.75):
        if tamanho_inicial < 1:
            raise ValueError("O tamanho inicial deve ser positivo.")
        if not 0 < fator_carga_maximo <= 1:
            raise ValueError("Fator de carga deve estar entre 0 e 1.")

        self.tamanho = tamanho_inicial
        self.tabela: list[list[list[Any]]] = [[] for _ in range(self.tamanho)]
        self.quantidade = 0
        self.fator_carga_maximo = fator_carga_maximo

    def _normalizar_chave(self, chave: Any) -> str:
        if chave is None:
            raise ValueError("A chave não pode ser vazia.")

        chave_normalizada = str(chave).strip()
        if not chave_normalizada:
            raise ValueError("A chave não pode ser vazia.")

        return chave_normalizada

    def _indice_para_chave_normalizada(self, chave_normalizada: str) -> int:
        return hash(chave_normalizada) % self.tamanho

    def _fator_carga(self) -> float:
        return self.quantidade / self.tamanho

    def _redimensionar(self) -> None:
        tabela_antiga = self.tabela
        self.tamanho *= 2
        self.tabela = [[] for _ in range(self.tamanho)]

        for bucket in tabela_antiga:
            for chave, valor in bucket:
                indice = self._indice_para_chave_normalizada(chave)
                self.tabela[indice].append([chave, valor])

    def inserir(self, chave: Any, valor: Any) -> bool:
        chave_norm = self._normalizar_chave(chave)
        indice = self._indice_para_chave_normalizada(chave_norm)
        bucket = self.tabela[indice]

        for item in bucket:
            if item[0] == chave_norm:
                item[1] = valor
                return True

        bucket.append([chave_norm, valor])
        self.quantidade += 1

        if self._fator_carga() > self.fator_carga_maximo:
            self._redimensionar()

        return True

    def buscar(self, chave: Any) -> Any | None:
        chave_norm = self._normalizar_chave(chave)
        indice = self._indice_para_chave_normalizada(chave_norm)

        for item in self.tabela[indice]:
            if item[0] == chave_norm:
                return item[1]

        return None

    def existe(self, chave: Any) -> bool:
        chave_norm = self._normalizar_chave(chave)
        indice = self._indice_para_chave_normalizada(chave_norm)
        return any(item[0] == chave_norm for item in self.tabela[indice])

    def remover(self, chave: Any) -> bool:
        chave_norm = self._normalizar_chave(chave)
        indice = self._indice_para_chave_normalizada(chave_norm)
        bucket = self.tabela[indice]

        for i, item in enumerate(bucket):
            if item[0] == chave_norm:
                del bucket[i]
                self.quantidade -= 1
                return True

        return False

    def obter_quantidade(self) -> int:
        return self.quantidade

    def exportar_buckets(self) -> list[dict[str, Any]]:
        return [
            {
                "bucket_id": idx,
                "itens": [{"chave": chave, "valor": valor} for chave, valor in bucket],
            }
            for idx, bucket in enumerate(self.tabela)
        ]

    def __len__(self) -> int:
        return self.quantidade

    def __contains__(self, chave: Any) -> bool:
        return self.existe(chave)
