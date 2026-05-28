import json
import os
from utils import gerar_id_pagamento
from logger import get_logger

log = get_logger("pagamentos")

pagamentos = {}

FICHEIRO_PAGAMENTOS = "pagamentos.json"

# Atributos da entidade Pagamento:
#   id           → identificador único
#   descricao    → descrição do pagamento
#   valor        → montante pago
#   data         → data do pagamento (YYYY-MM-DD)
#   metodo       → forma de pagamento
#   id_transacao → transação associada (opcional)

METODOS_PAG = ("MB Way", "Transferência", "Multibanco", "Dinheiro", "Cartão")


# ── Persistência ──────────────────────────────────────────────

def guardar_pagamentos():
    with open(FICHEIRO_PAGAMENTOS, "w", encoding="utf-8") as ficheiro:
        json.dump(pagamentos, ficheiro, indent=4, ensure_ascii=False)
    log.debug("Pagamentos guardados em disco.")

def carregar_pagamentos():
    global pagamentos
    if os.path.exists(FICHEIRO_PAGAMENTOS):
        with open(FICHEIRO_PAGAMENTOS, "r", encoding="utf-8") as ficheiro:
            pagamentos = json.load(ficheiro)
        log.debug("Pagamentos carregados do ficheiro (%d registo(s)).", len(pagamentos))
    else:
        pagamentos = {}
        log.debug("Ficheiro de pagamentos não encontrado — a iniciar vazio.")


# ── Helpers internos ──────────────────────────────────────────

def _validar_valor(valor):
    try:
        return float(valor) > 0
    except (TypeError, ValueError):
        return False

def _validar_metodo(metodo):
    return metodo in METODOS_PAG

def _validar_data(data_texto):
    from datetime import datetime
    try:
        datetime.strptime(data_texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ── CREATE ────────────────────────────────────────────────────

def criar_pagamento(descricao, valor, data, metodo, id_transacao=None):
    log.info("CREATE pagamento | descricao=%s | valor=%s | data=%s | metodo=%s", descricao, valor, data, metodo)
    carregar_pagamentos()

    if not descricao or not descricao.strip():
        log.error("CREATE falhou | motivo=descricao_vazia")
        return 400, "Descrição obrigatória."
    if not _validar_valor(valor):
        log.error("CREATE falhou | motivo=valor_invalido | valor=%s", valor)
        return 400, "Valor inválido. Deve ser um número positivo."
    if not _validar_data(data):
        log.error("CREATE falhou | motivo=data_invalida | data=%s", data)
        return 400, "Data inválida. Utilize o formato YYYY-MM-DD."
    if not _validar_metodo(metodo):
        log.error("CREATE falhou | motivo=metodo_invalido | metodo=%s", metodo)
        return 400, f"Método inválido. Opções: {', '.join(METODOS_PAG)}."

    id_pagamento = gerar_id_pagamento()

    pagamento = {
        "id":           id_pagamento,
        "descricao":    descricao.strip(),
        "valor":        float(valor),
        "data":         data,
        "metodo":       metodo,
        "id_transacao": id_transacao,
    }

    pagamentos[id_pagamento] = pagamento
    guardar_pagamentos()
    log.info("CREATE ok | id=%s | valor=%.2f | metodo=%s", id_pagamento, float(valor), metodo)
    return 201, pagamento


# ── READ (listar todos) ───────────────────────────────────────

def listar_pagamentos(metodo=None):
    log.info("READ listar_pagamentos | filtro_metodo=%s", metodo)
    carregar_pagamentos()

    if not pagamentos:
        log.error("READ listar_pagamentos | motivo=sem_registos")
        return 404, "Não existem pagamentos registados."

    if metodo is not None:
        if not _validar_metodo(metodo):
            log.error("READ listar_pagamentos | motivo=metodo_invalido | metodo=%s", metodo)
            return 400, f"Método inválido. Opções: {', '.join(METODOS_PAG)}."
        filtrado = {k: v for k, v in pagamentos.items() if v["metodo"] == metodo}
        if not filtrado:
            log.error("READ listar_pagamentos | motivo=sem_resultados | metodo=%s", metodo)
            return 404, f"Sem pagamentos com método '{metodo}'."
        log.info("READ listar_pagamentos ok | metodo=%s | total=%d", metodo, len(filtrado))
        return 200, filtrado

    log.info("READ listar_pagamentos ok | total=%d", len(pagamentos))
    return 200, pagamentos


# ── READ (consultar individual) ───────────────────────────────

def consultar_pagamento(id_pagamento):
    log.info("READ consultar_pagamento | id=%s", id_pagamento)
    carregar_pagamentos()

    if id_pagamento not in pagamentos:
        log.error("READ consultar_pagamento | motivo=nao_encontrado | id=%s", id_pagamento)
        return 404, "Pagamento não encontrado."

    log.info("READ consultar_pagamento ok | id=%s", id_pagamento)
    return 200, pagamentos[id_pagamento]


# ── UPDATE ────────────────────────────────────────────────────

def atualizar_pagamento(id_pagamento, descricao=None, valor=None, data=None, metodo=None, id_transacao=None):
    log.info("UPDATE pagamento | id=%s | descricao=%s | valor=%s | data=%s | metodo=%s", id_pagamento, descricao, valor, data, metodo)
    carregar_pagamentos()

    if id_pagamento not in pagamentos:
        log.error("UPDATE pagamento | motivo=nao_encontrado | id=%s", id_pagamento)
        return 404, "Pagamento não encontrado."

    if descricao is not None:
        if not descricao.strip():
            log.error("UPDATE pagamento | motivo=descricao_vazia | id=%s", id_pagamento)
            return 400, "Descrição não pode ser vazia."
        pagamentos[id_pagamento]["descricao"] = descricao.strip()

    if valor is not None:
        if not _validar_valor(valor):
            log.error("UPDATE pagamento | motivo=valor_invalido | id=%s | valor=%s", id_pagamento, valor)
            return 400, "Valor inválido. Deve ser um número positivo."
        pagamentos[id_pagamento]["valor"] = float(valor)

    if data is not None:
        if not _validar_data(data):
            log.error("UPDATE pagamento | motivo=data_invalida | id=%s | data=%s", id_pagamento, data)
            return 400, "Data inválida. Utilize o formato YYYY-MM-DD."
        pagamentos[id_pagamento]["data"] = data

    if metodo is not None:
        if not _validar_metodo(metodo):
            log.error("UPDATE pagamento | motivo=metodo_invalido | id=%s | metodo=%s", id_pagamento, metodo)
            return 400, f"Método inválido. Opções: {', '.join(METODOS_PAG)}."
        pagamentos[id_pagamento]["metodo"] = metodo

    if id_transacao is not None:
        pagamentos[id_pagamento]["id_transacao"] = id_transacao

    guardar_pagamentos()
    log.info("UPDATE pagamento ok | id=%s", id_pagamento)
    return 200, pagamentos[id_pagamento]


# ── DELETE ────────────────────────────────────────────────────

def remover_pagamento(id_pagamento):
    log.info("DELETE pagamento | id=%s", id_pagamento)
    carregar_pagamentos()

    if id_pagamento not in pagamentos:
        log.error("DELETE pagamento | motivo=nao_encontrado | id=%s", id_pagamento)
        return 404, "Pagamento não encontrado."

    del pagamentos[id_pagamento]
    guardar_pagamentos()
    log.info("DELETE pagamento ok | id=%s", id_pagamento)
    return 200, id_pagamento


# ── HELPERS para o main ───────────────────────────────────────

def total_pagamentos():
    log.info("HELPER total_pagamentos")
    carregar_pagamentos()

    total = sum(v["valor"] for v in pagamentos.values())
    log.info("HELPER total_pagamentos ok | total=%.2f€", total)
    return 200, round(total, 2)

def pagamentos_por_metodo():
    log.info("HELPER pagamentos_por_metodo")
    carregar_pagamentos()

    resumo = {}
    for p in pagamentos.values():
        resumo[p["metodo"]] = resumo.get(p["metodo"], 0.0) + p["valor"]

    log.info("HELPER pagamentos_por_metodo ok | metodos=%s", list(resumo.keys()))
    return 200, {k: round(v, 2) for k, v in resumo.items()}