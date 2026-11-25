"""Árvore Rubro-Negra para o histórico cronológico do SIGAE."""

from __future__ import annotations

from typing import Any

VERMELHO = True
PRETO = False


class NoRN:
    def __init__(self, chave: Any, valor: Any, cor: bool = VERMELHO) -> None:
        self.chave = chave  # Horario / Timestamp ou ID
        self.valor = valor  # Dados do atendimento
        self.cor = cor
        self.esq = None
        self.dir = None
        self.pai = None


class ArvoreRubroNegra:
    def __init__(self) -> None:
        self.NIL = NoRN(chave=None, valor=None, cor=PRETO)
        self.NIL.esq = self.NIL
        self.NIL.dir = self.NIL
        self.raiz = self.NIL

    def _rotacionar_esquerda(self, x):
        y = x.dir
        x.dir = y.esq
        if y.esq != self.NIL:
            y.esq.pai = x
        y.pai = x.pai
        if x.pai is None:
            self.raiz = y
        elif x == x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y
        y.esq = x
        x.pai = y

    def _rotacionar_direita(self, y):
        x = y.esq
        y.esq = x.dir
        if x.dir != self.NIL:
            x.dir.pai = y
        x.pai = y.pai
        if y.pai is None:
            self.raiz = x
        elif y == y.pai.dir:
            y.pai.dir = x
        else:
            y.pai.esq = x
        x.dir = y
        y.pai = x

    def inserir(self, chave, valor):
        novo = NoRN(chave, valor, cor=VERMELHO)
        novo.esq = self.NIL
        novo.dir = self.NIL

        y = None
        x = self.raiz

        while x != self.NIL:
            y = x
            x = x.esq if novo.chave < x.chave else x.dir

        novo.pai = y
        if y is None:
            self.raiz = novo
        elif novo.chave < y.chave:
            y.esq = novo
        else:
            y.dir = novo

        if novo.pai is None:
            novo.cor = PRETO
            return

        if novo.pai.pai is None:
            return

        self._ajustar_insercao(novo)

    def buscar(self, chave: Any) -> Any | None:
        atual = self.raiz
        while atual != self.NIL:
            if chave == atual.chave:
                return atual.valor
            atual = atual.esq if chave < atual.chave else atual.dir
        return None

    def _ajustar_insercao(self, k):
        while k.pai and k.pai.cor == VERMELHO:
            if k.pai == k.pai.pai.dir:
                u = k.pai.pai.esq
                if u.cor == VERMELHO:
                    u.cor = PRETO
                    k.pai.cor = PRETO
                    k.pai.pai.cor = VERMELHO
                    k = k.pai.pai
                else:
                    if k == k.pai.esq:
                        k = k.pai
                        self._rotacionar_direita(k)
                    k.pai.cor = PRETO
                    k.pai.pai.cor = VERMELHO
                    self._rotacionar_esquerda(k.pai.pai)
            else:
                u = k.pai.pai.dir
                if u.cor == VERMELHO:
                    u.cor = PRETO
                    k.pai.cor = PRETO
                    k.pai.pai.cor = VERMELHO
                    k = k.pai.pai
                else:
                    if k == k.pai.dir:
                        k = k.pai
                        self._rotacionar_esquerda(k)
                    k.pai.cor = PRETO
                    k.pai.pai.cor = VERMELHO
                    self._rotacionar_direita(k.pai.pai)
            if k == self.raiz:
                break
        self.raiz.cor = PRETO

    def em_ordem(self, no=None, resultado=None):
        if resultado is None:
            resultado = []
            no = self.raiz
        if no != self.NIL:
            self.em_ordem(no.esq, resultado)
            resultado.append(
                {
                    "chave": no.chave,
                    "valor": no.valor,
                    "cor": "VERMELHO" if no.cor == VERMELHO else "PRETO",
                }
            )
            self.em_ordem(no.dir, resultado)
        return resultado

    def exportar_estrutura(self, no=None) -> dict[str, Any] | None:
        """Exporta a topologia real da árvore, preservando filhos e cores."""
        if no is None:
            no = self.raiz
        if no == self.NIL:
            return None
        return {
            "chave": no.chave,
            "valor": no.valor,
            "cor": "VERMELHO" if no.cor == VERMELHO else "PRETO",
            "esq": self.exportar_estrutura(no.esq),
            "dir": self.exportar_estrutura(no.dir),
        }

    def validar_propriedades(self) -> dict[str, Any]:
        """Valida ordenação, raiz preta, nós vermelhos e altura negra."""
        if self.raiz == self.NIL:
            return {"ok": True, "altura_negra": 1, "erros": []}

        erros: list[str] = []
        if self.raiz.cor != PRETO:
            erros.append("A raiz deve ser preta.")

        chaves: list[Any] = []

        def visitar(no: NoRN) -> int:
            if no == self.NIL:
                return 1
            chaves.append(no.chave)
            if no.cor == VERMELHO and (no.esq.cor == VERMELHO or no.dir.cor == VERMELHO):
                erros.append(f"Nó vermelho {no.chave!r} possui filho vermelho.")
            altura_esquerda = visitar(no.esq)
            altura_direita = visitar(no.dir)
            if altura_esquerda != altura_direita:
                erros.append(f"Altura negra divergente no nó {no.chave!r}.")
            return min(altura_esquerda, altura_direita) + (1 if no.cor == PRETO else 0)

        altura_negra = visitar(self.raiz)
        ordenadas = [item["chave"] for item in self.em_ordem()]
        if ordenadas != sorted(ordenadas):
            erros.append("A propriedade de busca binária foi violada.")
        return {"ok": not erros, "altura_negra": altura_negra, "erros": erros}
