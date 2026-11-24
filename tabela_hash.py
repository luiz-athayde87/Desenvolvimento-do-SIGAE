"""
Módulo: Tabela Hash (SIGAE)
Objetivo: Armazenamento e busca instantânea de cadastros por ID.
Complexidade: O(1) médio para busca, inserção e remoção.
"""

class TabelaHash:
    def __init__(self, tamanho_inicial=16):
        self.tamanho = tamanho_inicial
        self.tabela = [[] for _ in range(self.tamanho)]
        self.quantidade = 0

    def _funcao_hash(self, chave):
        return abs(hash(str(chave))) % self.tamanho

    def inserir(self, chave, valor):
        indice = self._funcao_hash(chave)
        bucket = self.tabela[indice]
        
        for i, item in enumerate(bucket):
            if item[0] == chave:
                bucket[i] = [chave, valor]
                return
        
        bucket.append([chave, valor])
        self.quantidade += 1

    def buscar(self, chave):
        indice = self._funcao_hash(chave)
        bucket = self.tabela[indice]
        
        for item in bucket:
            if item[0] == chave:
                return item[1]
        return None

    def remover(self, chave):
        indice = self._funcao_hash(chave)
        bucket = self.tabela[indice]
        
        for i, item in enumerate(bucket):
            if item[0] == chave:
                del bucket[i]
                self.quantidade -= 1
                return True
        return False

    def exportar_buckets(self):
        resultado = []
        for idx, bucket in enumerate(self.tabela):
            itens = [{"chave": k, "valor": v} for k, v in bucket]
            resultado.append({"bucket_id": idx, "itens": itens})
        return resultado
