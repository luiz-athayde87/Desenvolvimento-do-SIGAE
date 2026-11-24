"""
Módulo: Min-Heap de Pacientes (SIGAE)
Objetivo: Gerenciamento da fila de triagem de risco clínico.
Complexidade: O(1) para consulta do topo, O(log n) para inserção e remoção.
"""

class MinHeapPacientes:
    def __init__(self):
        self.heap = []

    def _prioridade_menor(self, p1, p2):
        # Desempate: 1º Grau de Risco (1 a 5), 2º Horário de Chegada, 3º ID
        return (int(p1['prioridade']), float(p1['horario_chegada']), str(p1['id'])) < \
               (int(p2['prioridade']), float(p2['horario_chegada']), str(p2['id']))

    def inserir(self, paciente):
        self.heap.append(paciente)
        self._subir(len(self.heap) - 1)

    def extrair_proximo(self):
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        raiz = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._descer(0)
        return raiz

    def _subir(self, i):
        pai = (i - 1) // 2
        if i > 0 and self._prioridade_menor(self.heap[i], self.heap[pai]):
            self.heap[i], self.heap[pai] = self.heap[pai], self.heap[i]
            self._subir(pai)

    def _descer(self, i):
        menor = i
        esq, dir = 2 * i + 1, 2 * i + 2
        
        if esq < len(self.heap) and self._prioridade_menor(self.heap[esq], self.heap[menor]):
            menor = esq
        if dir < len(self.heap) and self._prioridade_menor(self.heap[dir], self.heap[menor]):
            menor = dir
        if menor != i:
            self.heap[i], self.heap[menor] = self.heap[menor], self.heap[i]
            self._descer(menor)

    def esta_vazia(self):
        return len(self.heap) == 0

    def exportar_array(self):
        return list(self.heap)
