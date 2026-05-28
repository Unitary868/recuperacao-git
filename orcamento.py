import json
import os
from utils import gerar_id_orcamento
from logger import get_logger

log = get_logger("orcamentos")

orcamentos = {}

FICHEIRO_ORCAMENTOS = "orcamentos.json"

# Atributos da entidade Orçamento:
#   id          → identificador único
#   categoria   → categoria associada ao orçamento
#   limite      → valor máximo definido
#   periodo     → período de validade (ex: "mensal", "semanal", "anual")
#   gasto_atual → valor já utilizado

CATEGORIAS_ORC = (
    "Alimentação", "Transporte", "Lazer", "Saúde",
    "Educação", "Habitação", "Vestuário", "Tecnologia",
    "Poupança", "Outros",
)

PERIODOS = ("diário", "semanal", "mensal", "anual")


# ── Persistência ──────────────────────────────────────────────

def guardar_orcamentos():
    with open(FICHEIRO_ORCAMENTOS, "w", encoding="utf-8") as ficheiro:
        json.dump(orcamentos, ficheiro, indent=4, ensure_ascii=False)
    log.debug("Orçamentos guardados em disco.")

def carregar_orcamentos():
    global orcamentos
    if os.path.exists(FICHEIRO_ORCAMENTOS):
        with open(FICHEIRO_ORCAMENTOS, "r", encoding="utf-8") as ficheiro:
            orcamentos = json.load(ficheiro)
        log.debug("Orçamentos carregados do ficheiro (%d registo(s)).", len(orcamentos))
    else:
        orcamentos = {}
        log.debug("Ficheiro de orçamentos não encontrado — a iniciar vazio.")


# ── Helpers internos ──────────────────────────────────────────

def _validar_valor(valor):
    try:
        return float(valor) > 0
    except (TypeError, ValueError):
        return False

def _validar_categoria(categoria):
    return categoria in CATEGORIAS_ORC

def _validar_periodo(periodo):
    return periodo in PERIODOS


# ── CREATE ────────────────────────────────────────────────────

def criar_orcamento(categoria, limite, periodo):
    log.info("CREATE orcamento | categoria=%s | limite=%s | periodo=%s", categoria, limite, periodo)
    carregar_orcamentos()

    if not _validar_categoria(categoria):
        log.error("CREATE falhou | motivo=categoria_invalida | categoria=%s", categoria)
        return 400, f"Categoria inválida. Opções: {', '.join(CATEGORIAS_ORC)}."
    if not _validar_valor(limite):
        log.error("CREATE falhou | motivo=limite_invalido | limite=%s", limite)
        return 400, "Limite inválido. Deve ser um número positivo."
    if not _validar_periodo(periodo):
        log.error("CREATE falhou | motivo=periodo_invalido | periodo=%s", periodo)
        return 400, f"Período inválido. Opções: {', '.join(PERIODOS)}."

    for oid, o in orcamentos.items():
        if o["categoria"] == categoria and o["periodo"] == periodo:
            log.error("CREATE falhou | motivo=duplicado | categoria=%s | periodo=%s | id_existente=%s", categoria, periodo, oid)
            return 409, f"Já existe um orçamento para '{categoria}' ({periodo}) com ID {oid}."

    id_orcamento = gerar_id_orcamento()

    orcamento = {
        "id":          id_orcamento,
        "categoria":   categoria,
        "limite":      float(limite),
        "periodo":     periodo,
        "gasto_atual": 0.0,
    }

    orcamentos[id_orcamento] = orcamento
    guardar_orcamentos()
    log.info("CREATE ok | id=%s | categoria=%s | limite=%.2f | periodo=%s", id_orcamento, categoria, float(limite), periodo)
    return 201, orcamento


# ── READ (listar todos) ───────────────────────────────────────

def listar_orcamentos():
    log.info("READ listar_orcamentos")
    carregar_orcamentos()

    if not orcamentos:
        log.error("READ listar_orcamentos | motivo=sem_registos")
        return 404, "Não existem orçamentos registados."

    log.info("READ listar_orcamentos ok | total=%d", len(orcamentos))
    return 200, orcamentos


# ── READ (consultar individual) ───────────────────────────────

def consultar_orcamento(id_orcamento):
    log.info("READ consultar_orcamento | id=%s", id_orcamento)
    carregar_orcamentos()

    if id_orcamento not in orcamentos:
        log.error("READ consultar_orcamento | motivo=nao_encontrado | id=%s", id_orcamento)
        return 404, "Orçamento não encontrado."

    log.info("READ consultar_orcamento ok | id=%s", id_orcamento)
    return 200, orcamentos[id_orcamento]


# ── UPDATE ────────────────────────────────────────────────────

def atualizar_orcamento(id_orcamento, limite=None, categoria=None, periodo=None):
    log.info("UPDATE orcamento | id=%s | limite=%s | categoria=%s | periodo=%s", id_orcamento, limite, categoria, periodo)
    carregar_orcamentos()

    if id_orcamento not in orcamentos:
        log.error("UPDATE orcamento | motivo=nao_encontrado | id=%s", id_orcamento)
        return 404, "Orçamento não encontrado."

    if limite is not None:
        if not _validar_valor(limite):
            log.error("UPDATE orcamento | motivo=limite_invalido | id=%s | limite=%s", id_orcamento, limite)
            return 400, "Limite inválido. Deve ser um número positivo."
        orcamentos[id_orcamento]["limite"] = float(limite)

    if categoria is not None:
        if not _validar_categoria(categoria):
            log.error("UPDATE orcamento | motivo=categoria_invalida | id=%s | categoria=%s", id_orcamento, categoria)
            return 400, f"Categoria inválida. Opções: {', '.join(CATEGORIAS_ORC)}."
        for oid, o in orcamentos.items():
            if o["categoria"] == categoria and o["periodo"] == orcamentos[id_orcamento]["periodo"] and oid != id_orcamento:
                log.error("UPDATE orcamento | motivo=duplicado | id=%s | categoria=%s", id_orcamento, categoria)
                return 409, "Já existe um orçamento para esta categoria e período."
        orcamentos[id_orcamento]["categoria"] = categoria

    if periodo is not None:
        if not _validar_periodo(periodo):
            log.error("UPDATE orcamento | motivo=periodo_invalido | id=%s | periodo=%s", id_orcamento, periodo)
            return 400, f"Período inválido. Opções: {', '.join(PERIODOS)}."
        orcamentos[id_orcamento]["periodo"] = periodo

    guardar_orcamentos()
    log.info("UPDATE orcamento ok | id=%s", id_orcamento)
    return 200, orcamentos[id_orcamento]


# ── DELETE ────────────────────────────────────────────────────

def remover_orcamento(id_orcamento):
    log.info("DELETE orcamento | id=%s", id_orcamento)
    carregar_orcamentos()

    if id_orcamento not in orcamentos:
        log.error("DELETE orcamento | motivo=nao_encontrado | id=%s", id_orcamento)
        return 404, "Orçamento não encontrado."

    del orcamentos[id_orcamento]
    guardar_orcamentos()
    log.info("DELETE orcamento ok | id=%s", id_orcamento)
    return 200, id_orcamento


# ── Registar gasto (chamado ao adicionar uma despesa) ─────────

def registar_gasto(id_orcamento, valor):
    log.info("GASTO registar | id=%s | valor=%s", id_orcamento, valor)
    carregar_orcamentos()

    if id_orcamento not in orcamentos:
        log.error("GASTO registar | motivo=nao_encontrado | id=%s", id_orcamento)
        return 404, "Orçamento não encontrado."
    if not _validar_valor(valor):
        log.error("GASTO registar | motivo=valor_invalido | id=%s | valor=%s", id_orcamento, valor)
        return 400, "Valor inválido."

    orcamentos[id_orcamento]["gasto_atual"] += float(valor)
    restante = orcamentos[id_orcamento]["limite"] - orcamentos[id_orcamento]["gasto_atual"]
    categoria = orcamentos[id_orcamento]["categoria"]

    guardar_orcamentos()

    if restante < 0:
        log.error("GASTO registar | LIMITE EXCEDIDO | id=%s | categoria=%s | excesso=%.2f€", id_orcamento, categoria, abs(restante))
        return 200, f"AVISO: Orçamento '{categoria}' excedido em {abs(round(restante, 2))}€!"

    log.info("GASTO registar ok | id=%s | categoria=%s | restante=%.2f€", id_orcamento, categoria, restante)
    return 200, f"Gasto registado. Restam {round(restante, 2)}€ no orçamento '{categoria}'."