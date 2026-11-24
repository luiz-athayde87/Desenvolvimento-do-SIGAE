"""
Módulo: Min-Heap de Médicos (SIGAE)
Objetivo: Distribuição equitativa de consultas entre profissionais disponíveis.
Complexidade: O(1) para seleção do topo, O(log n) para atualização de carga.
"""

class MinHeapMedicos:
    def __init__(self):
        self.heap = []

    def _carga_menor(self, m1, m2):
        # Desempate: 1º Menor número de atendimentos, 2º Tempo sem atender, 3º ID
        return (int(m1['atendimentos_concluidos']), float(m1['ultimo_atendimento']), str(m1['id'])) < \
               (int(m2['atendimentos_concluidos']), float(m2['ultimo_atendimento']), str(m2['id']))

    def inserir(self, medico):
        self.heap.append(medico)
        self._reordenar()

    def obter_medico_disponivel(self):
        for i, medico in enumerate(self.heap):
            if medico['situacao'] == 'Disponivel':
                medico_selecionado = self.heap.pop(i)
                self._reordenar()
                return medico_selecionado
        return None

    def _reordenar(self):
        for i in range(len(self.heap) // 2, -1, -1):
            self._descer(i)

    def _descer(self, i):
        menor = i
        esq, dir = 2 * i + 1, 2 * i + 2
        
        if esq < len(self.heap) and self._carga_menor(self.heap[esq], self.heap[menor]):
            menor = esq
        if dir < len(self.heap) and self._carga_menor(self.heap[dir], self.heap[menor]):
            menor = dir
        if menor != i:
            self.heap[i], self.heap[menor] = self.heap[menor], self.heap[i]
            self._descer(menor)

    def exportar_array(self):
        return list(self.heap)
