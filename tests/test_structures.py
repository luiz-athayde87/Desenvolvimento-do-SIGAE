from __future__ import annotations

import random

import pytest

from arvore_avl import ArvoreAVL
from arvore_rubro_negra import ArvoreRubroNegra
from heap_medicos import MinHeapMedicos
from heap_pacientes import MinHeapPacientes
from tabela_hash import TabelaHash


def paciente(identificador: str, prioridade: int, chegada: float) -> dict:
    return {
        "id": identificador,
        "nome": identificador,
        "prioridade": prioridade,
        "horario_chegada": chegada,
        "situacao": "Aguardando",
    }


def medico(identificador: str, concluidos: int = 0, ultimo: float = 0.0) -> dict:
    return {
        "id": identificador,
        "nome": identificador,
        "atendimentos_concluidos": concluidos,
        "ultimo_atendimento": ultimo,
        "situacao": "Disponivel",
    }


def test_hash_atualiza_sem_duplicar_e_redimensiona() -> None:
    tabela = TabelaHash(4)
    for indice in range(20):
        tabela.inserir(f"P{indice}", {"valor": indice})
    tabela.inserir("P3", {"valor": 99})

    assert tabela.quantidade == 20
    assert tabela.buscar("P3") == {"valor": 99}
    assert tabela.tamanho > 4
    assert tabela.fator_carga < tabela.FATOR_CARGA_MAXIMO
    assert tabela.remover("P3") is True
    assert tabela.buscar("P3") is None


def test_hash_encadeia_colisoes_reais_sem_perder_registros() -> None:
    tabela = TabelaHash(5)
    chaves_por_bucket: dict[int, list[str]] = {}
    colisao: list[str] | None = None
    for indice in range(100):
        chave = f"COL-{indice}"
        bucket = tabela._funcao_hash(chave)
        chaves_por_bucket.setdefault(bucket, []).append(chave)
        if len(chaves_por_bucket[bucket]) == 2:
            colisao = chaves_por_bucket[bucket]
            break

    assert colisao is not None
    primeira, segunda = colisao
    tabela.inserir(primeira, {"id": primeira})
    tabela.inserir(segunda, {"id": segunda})

    bucket = tabela.tabela[tabela._funcao_hash(primeira)]
    assert len(bucket) == 2
    assert tabela.buscar(primeira) == {"id": primeira}
    assert tabela.buscar(segunda) == {"id": segunda}


def test_heap_pacientes_respeita_risco_fifo_e_id() -> None:
    heap = MinHeapPacientes()
    entradas = [
        paciente("P04", 4, 10.0),
        paciente("P02", 1, 10.2),
        paciente("P01", 1, 10.1),
        paciente("P03", 1, 10.1),
    ]
    for item in entradas:
        heap.inserir(item)

    ordem = [heap.extrair_proximo()["id"] for _ in entradas]
    assert ordem == ["P01", "P03", "P02", "P04"]


def test_heap_pacientes_impede_duplicidade_e_reclassifica() -> None:
    heap = MinHeapPacientes()
    heap.inserir(paciente("P01", 5, 10.0))
    heap.inserir(paciente("P02", 3, 10.1))

    with pytest.raises(ValueError):
        heap.inserir(paciente("P01", 1, 10.2))

    heap.atualizar_prioridade("P01", 1)
    assert heap.topo()["id"] == "P01"
    assert heap.remover("P01")["id"] == "P01"
    assert heap.topo()["id"] == "P02"


def test_heap_medicos_extrai_por_carga_e_desempate() -> None:
    heap = MinHeapMedicos()
    for item in [medico("M03", 2, 1.0), medico("M02", 0, 2.0), medico("M01", 0, 1.0)]:
        heap.inserir(item)

    assert heap.obter_medico_disponivel()["id"] == "M01"
    assert heap.obter_medico_disponivel()["id"] == "M02"
    assert heap.obter_medico_disponivel()["id"] == "M03"


def test_avl_exporta_busca_e_mantem_invariantes() -> None:
    arvore = ArvoreAVL()
    valores = list(range(100))
    random.Random(42).shuffle(valores)
    for valor in valores:
        arvore.inserir_no(valor, {"valor": valor})

    exportada = arvore.exportar_estrutura()
    assert exportada is not None
    assert arvore.buscar(37) == {"valor": 37}
    assert arvore.buscar(999) is None
    assert arvore.validar() is True


def test_rubro_negra_mantem_invariantes_em_sequencias_adversas() -> None:
    arvore = ArvoreRubroNegra()
    valores = list(range(150))
    random.Random(7).shuffle(valores)
    for valor in valores:
        arvore.inserir(valor, {"valor": valor})
        assert arvore.validar_propriedades()["ok"] is True

    assert arvore.buscar(80) == {"valor": 80}
    assert [item["chave"] for item in arvore.em_ordem()] == sorted(valores)

    exportada = arvore.exportar_estrutura()
    assert exportada is not None
    assert exportada["cor"] == "PRETO"

    def contar_nos(no: dict | None) -> int:
        if no is None:
            return 0
        return 1 + contar_nos(no["esq"]) + contar_nos(no["dir"])

    assert contar_nos(exportada) == len(valores)


def test_rubro_negra_remove_folhas_raiz_e_nos_internos_com_balanceamento() -> None:
    arvore = ArvoreRubroNegra()
    valores = list(range(120))
    random.Random(17).shuffle(valores)
    for valor in valores:
        arvore.inserir((valor, f"P{valor:03d}"), {"id": f"P{valor:03d}"})

    ordem_remocao = valores.copy()
    random.Random(31).shuffle(ordem_remocao)
    for valor in ordem_remocao:
        chave = (valor, f"P{valor:03d}")
        assert arvore.remover(chave) == {"id": f"P{valor:03d}"}
        assert arvore.buscar(chave) is None
        assert arvore.validar_propriedades()["ok"] is True

    assert arvore.exportar_estrutura() is None
    assert arvore.remover((999, "P999")) is None
