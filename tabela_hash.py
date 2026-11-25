"""Tabela Hash determinística com encadeamento separado e redimensionamento."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


from typing import Any


class TabelaHash:
    """Índice educacional com operações O(1) em média.

    A função de dispersão FNV-1a é determinística entre processos, permitindo
    que o inspetor visual apresente os mesmos buckets após uma reinicialização.
    """

    FATOR_CARGA_MAXIMO = 0.75

    def __init__(self, tamanho_inicial: int = 16) -> None:
        if tamanho_inicial < 4:
            raise ValueError("O tamanho inicial deve ser pelo menos 4.")
        self.tamanho = self._proximo_primo(tamanho_inicial)
        self.tabela: list[list[list[Any]]] = [[] for _ in range(self.tamanho)]
        self.quantidade = 0
        self.fator_carga_maximo = fator_carga_maximo

    @staticmethod
    def _proximo_primo(numero: int) -> int:
        def primo(valor: int) -> bool:
            if valor < 2:
                return False
            divisor = 2
            while divisor * divisor <= valor:
                if valor % divisor == 0:
                    return False
                divisor += 1
            return True

        candidato = numero
        while not primo(candidato):
            candidato += 1
        return candidato

    def _funcao_hash(self, chave: object) -> int:
        hash_atual = 2_166_136_261
        for byte in str(chave).encode("utf-8"):
            hash_atual ^= byte
            hash_atual = (hash_atual * 16_777_619) & 0xFFFFFFFF
        return hash_atual % self.tamanho

    @property
    def fator_carga(self) -> float:
        return self.quantidade / self.tamanho

    def inserir(self, chave: object, valor: Any) -> bool:
        """Insere ou atualiza uma chave; retorna ``True`` apenas se for nova."""
        indice = self._funcao_hash(chave)
        bucket = self.tabela[indice]
        for i, item in enumerate(bucket):
            if item[0] == chave:
                bucket[i] = [chave, valor]
                return False

        bucket.append([chave, valor])
        self.quantidade += 1
        if self.fator_carga >= self.FATOR_CARGA_MAXIMO:
            self._redimensionar(self._proximo_primo(self.tamanho * 2))
        return True

    def buscar(self, chave: object) -> Any | None:
        for chave_atual, valor in self.tabela[self._funcao_hash(chave)]:
            if chave_atual == chave:
                return valor
        return None

    def remover(self, chave: object) -> bool:
        bucket = self.tabela[self._funcao_hash(chave)]
        for i, item in enumerate(bucket):
            if item[0] == chave_norm:
                del bucket[i]
                self.quantidade -= 1
                return True

        return False

    def _redimensionar(self, novo_tamanho: int) -> None:
        itens = list(self.itens())
        self.tamanho = novo_tamanho
        self.tabela = [[] for _ in range(self.tamanho)]
        self.quantidade = 0
        for chave, valor in itens:
            self.inserir(chave, valor)

    def itens(self) -> Iterator[tuple[object, Any]]:
        for bucket in self.tabela:
            yield from bucket

    def exportar_buckets(self) -> list[dict[str, Any]]:
        return [
            {
                "bucket_id": indice,
                "itens": [{"chave": chave, "valor": valor} for chave, valor in bucket],
            }
            for indice, bucket in enumerate(self.tabela)
        ]
