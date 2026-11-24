"""
Módulo Principal: Servidor Web Flask (SIGAE)
Objetivo: Integrar a Tabela Hash, Min-Heap de Pacientes, Min-Heap de Médicos, Árvore Rubro-Negra e Árvore AVL em uma aplicação Web completa.
"""

from flask import Flask, render_template, request, jsonify
import time

from tabela_hash import TabelaHash
from heap_pacientes import MinHeapPacientes
from heap_medicos import MinHeapMedicos
from arvore_rubro_negra import ArvoreRubroNegra
from arvore_avl import ArvoreAVL

app = Flask(__name__)

# --- INSTÂNCIAS GLOBAIS DAS ESTRUTURAS DE DADOS ---
tabela_hash = TabelaHash()
heap_pacientes = MinHeapPacientes()
heap_medicos = MinHeapMedicos()
historico_rn = ArvoreRubroNegra()
arvore_avl = ArvoreAVL()
horario_simulado = 10.00

def carregar_dados_iniciais():
    global horario_simulado, tabela_hash, heap_pacientes, heap_medicos, historico_rn, arvore_avl
    
    tabela_hash = TabelaHash()
    heap_pacientes = MinHeapPacientes()
    heap_medicos = MinHeapMedicos()
    historico_rn = ArvoreRubroNegra()
    arvore_avl = ArvoreAVL()
    horario_simulado = 10.00

    # 1. Cadastrar Médicos Iniciais
    medicos_iniciais = [
        {'id': 'M101', 'nome': 'Dr. Carlos', 'atendimentos_concluidos': 0, 'ultimo_atendimento': 0.0, 'situacao': 'Disponivel'},
        {'id': 'M102', 'nome': 'Dra. Beatriz', 'atendimentos_concluidos': 0, 'ultimo_atendimento': 0.0, 'situacao': 'Disponivel'},
        {'id': 'M103', 'nome': 'Dr. André', 'atendimentos_concluidos': 0, 'ultimo_atendimento': 0.0, 'situacao': 'Disponivel'}
    ]
    for m in medicos_iniciais:
        tabela_hash.inserir(m['id'], m)
        heap_medicos.inserir(m)

    # 2. Cadastrar Pacientes Iniciais (Simulação de Triagem)
    pacientes_iniciais = [
        {'id': 'P01', 'nome': 'João Silva', 'prioridade': 4, 'horario_chegada': 10.00, 'situacao': 'Aguardando'},
        {'id': 'P02', 'nome': 'Maria Oliveira', 'prioridade': 1, 'horario_chegada': 10.02, 'situacao': 'Aguardando'}, # EMERGÊNCIA
        {'id': 'P03', 'nome': 'Pedro Souza', 'prioridade': 2, 'horario_chegada': 10.01, 'situacao': 'Aguardando'}   # MUITO URGENTE
    ]
    for p in pacientes_iniciais:
        tabela_hash.inserir(p['id'], p)
        heap_pacientes.inserir(p)

carregar_dados_iniciais()

# --- ROTAS FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/estado', methods=['GET'])
def obter_estado():
    return jsonify({
        'heap_pacientes': heap_pacientes.exportar_array(),
        'heap_medicos': heap_medicos.exportar_array(),
        'tabela_hash': tabela_hash.exportar_buckets(),
        'historico_rn': historico_rn.em_ordem(),
        'arvore_avl': arvore_avl.exportar_estrutura()
    })

@app.route('/api/paciente', methods=['POST'])
def cadastrar_paciente():
    global horario_simulado
    dados = request.get_json()
    
    horario_simulado += 0.01
    paciente = {
        'id': str(dados.get('id')),
        'nome': str(dados.get('nome')),
        'prioridade': int(dados.get('prioridade')),
        'horario_chegada': round(horario_simulado, 2),
        'situacao': 'Aguardando'
    }
    
    tabela_hash.inserir(paciente['id'], paciente)
    heap_pacientes.inserir(paciente)
    
    return jsonify({'sucesso': True, 'paciente': paciente})

@app.route('/api/medico', methods=['POST'])
def cadastrar_medico():
    dados = request.get_json()
    medico = {
        'id': str(dados.get('id')),
        'nome': str(dados.get('nome')),
        'atendimentos_concluidos': 0,
        'ultimo_atendimento': 0.0,
        'situacao': str(dados.get('situacao', 'Disponivel'))
    }
    
    tabela_hash.inserir(medico['id'], medico)
    heap_medicos.inserir(medico)
    
    return jsonify({'sucesso': True, 'medico': medico})

@app.route('/api/chamar', methods=['POST'])
def chamar_proximo():
    global horario_simulado
    if heap_pacientes.esta_vazia():
        return jsonify({'sucesso': False, 'mensagem': 'Nenhum paciente aguardando na fila de triagem.'})
    
    medico = heap_medicos.obter_medico_disponivel()
    if not medico:
        return jsonify({'sucesso': False, 'mensagem': 'Nenhum médico disponível no momento.'})
    
    paciente = heap_pacientes.extrair_proximo()
    horario_simulado += 0.05
    horario_atendimento = round(horario_simulado, 2)

    # Registro nas Estruturas de Dados
    registro = {
        'paciente': paciente['nome'],
        'medico': medico['nome'],
        'prioridade': paciente['prioridade']
    }

    # Inserção na Árvore Rubro-Negra (Histórico em O(log n))
    historico_rn.inserir(horario_atendimento, registro)

    # Inserção na Árvore AVL
    arvore_avl.inserir_no(horario_atendimento, registro)

    # Atualiza Tabela Hash e Heap de Médicos
    paciente['situacao'] = 'Em Atendimento'
    tabela_hash.inserir(paciente['id'], paciente)

    medico['atendimentos_concluidos'] += 1
    medico['ultimo_atendimento'] = horario_atendimento
    medico['situacao'] = 'Disponivel'
    tabela_hash.inserir(medico['id'], medico)
    heap_medicos.inserir(medico)

    return jsonify({
        'sucesso': True,
        'paciente': paciente['nome'],
        'medico': medico['nome'],
        'prioridade': paciente['prioridade'],
        'horario': horario_atendimento
    })

@app.route('/api/buscar/<id_busca>', methods=['GET'])
def buscar_hash(id_busca):
    resultado = tabela_hash.buscar(id_busca)
    if resultado:
        return jsonify({'encontrado': True, 'dados': resultado})
    return jsonify({'encontrado': False})

@app.route('/api/reset', methods=['POST'])
def reset():
    carregar_dados_iniciais()
    return jsonify({'sucesso': True})

if __name__ == '__main__':
    print("Iniciando Servidor Flask do SIGAE na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
