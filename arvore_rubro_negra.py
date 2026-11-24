"""
Módulo: Árvore Rubro-Negra (SIGAE)
Objetivo: Armazenar histórico de atendimentos com garantia de busca e inserção em O(log n).
"""

VERMELHO = True
PRETO = False

class NoRN:
    def __init__(self, chave, valor, cor=VERMELHO):
        self.chave = chave  # Horario / Timestamp ou ID
        self.valor = valor  # Dados do atendimento
        self.cor = cor
        self.esq = None
        self.dir = None
        self.pai = None

class ArvoreRubroNegra:
    def __init__(self):
        self.NIL = NoRN(chave=None, valor=None, cor=PRETO)
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
            if novo.chave < x.chave:
                x = x.esq
            else:
                x = x.dir
                
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
            resultado.append({"chave": no.chave, "valor": no.valor, "cor": "VERMELHO" if no.cor == VERMELHO else "PRETO"})
            self.em_ordem(no.dir, resultado)
        return resultado
