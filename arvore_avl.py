"""
Módulo: Árvore AVL (SIGAE)
Objetivo: Manter altura mínima estrita para busca de alta frequência em tempo O(log n).
"""

class NoAVL:
    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.altura = 1
        self.esq = None
        self.dir = None

class ArvoreAVL:
    def __init__(self):
        self.raiz = None

    def obter_altura(self, no):
        return no.altura if no else 0

    def obter_fator_balanco(self, no):
        return self.obter_altura(no.esq) - self.obter_altura(no.dir) if no else 0

    def _rotacao_direita(self, z):
        y = z.esq
        T3 = y.dir
        y.dir = z
        z.esq = T3
        z.altura = 1 + max(self.obter_altura(z.esq), self.obter_altura(z.dir))
        y.altura = 1 + max(self.obter_altura(y.esq), self.obter_altura(y.dir))
        return y

    def _rotacao_esquerda(self, z):
        y = z.dir
        T2 = y.esq
        y.esq = z
        z.dir = T2
        z.altura = 1 + max(self.obter_altura(z.esq), self.obter_altura(z.dir))
        y.altura = 1 + max(self.obter_altura(y.esq), self.obter_altura(y.dir))
        return y

    def inserir_no(self, chave, valor):
        self.raiz = self._inserir(self.raiz, chave, valor)

    def _inserir(self, no, chave, valor):
        if not no:
            return NoAVL(chave, valor)
        
        if chave < no.chave:
            no.esq = self._inserir(no.esq, chave, valor)
        elif chave > no.chave:
            no.dir = self._inserir(no.dir, chave, valor)
        else:
            no.valor = valor
            return no

        no.altura = 1 + max(self.obter_altura(no.esq), self.obter_altura(no.dir))
        fb = self.obter_fator_balanco(no)

        if fb > 1 and chave < no.esq.chave:
            return self._rotacao_direita(no)
        if fb < -1 and chave > no.dir.chave:
            return self._rotacao_esquerda(no)
        if fb > 1 and chave > no.esq.chave:
            no.esq = self._rotacao_esquerda(no.esq)
            return self._rotacao_direita(no)
        if fb < -1 and chave < no.dir.chave:
            no.dir = self._rotacao_direita(no.dir)
            return self._rotacao_esquerda(no)

        return no

    def exportar_estrutura(self, no=None):
        if no is None:
            no = self.raiz
        if not no:
            return None
        return {
            "chave": no.chave,
            "valor": no.valor,
            "altura": no.altura,
            "fator_balanco": self.obter_fator_balanco(no),
            "esq": self.exportar_estrutura(no.esq),
            "dir": self.exportar_estrutura(no.dir)
        }
