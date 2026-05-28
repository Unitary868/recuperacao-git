import json
import os
from utils import gerar_id_transacao
from logger import get_logger

log = get_logger("transacoes")

transacoes = {}

FICHEIRO_TRANSACOES = "transacoes.json"

# Atributos da entidade Transação:
#   id           → identificador único
#   tipo         → "receita" ou "despesa"
#   descricao    → descrição do movimento
#   valor        → montante em euros
#   categoria    → tipo de transação
#   id_conta     → conta associada
#   id_orcamento → orçamento associado (opcional)

CATEGORIAS = (
    "Alimentação", "Transporte", "Lazer", "Saúde",
    "Educação", "Habitação", "Vestuário", "Tecnologia",
    "Poupança", "Salário", "Freelance", "Outros",
)


# ── Persistência ──────────────────────────────────────────────

def guardar_transacoes():
    with open(FICHEIRO_TRANSACOES, "w", encoding="utf-8") as ficheiro:
        json.dump(transacoes, ficheiro, indent=4, ensure_ascii=False)
    log.debug("Transações guardadas em disco.")

def carregar_transacoes():
    global transacoes
    if os.path.exists(FICHEIRO_TRANSACOES):
        with open(FICHEIRO_TRANSACOES, "r", encoding="utf-8") as ficheiro:
            transacoes = json.load(ficheiro)
        log.debug("Transações carregadas do ficheiro (%d registo(s)).", len(transacoes))
    else:
        transacoes = {}
        log.debug("Ficheiro de transações não encontrado — a iniciar vazio.")


# ── Helpers internos ──────────────────────────────────────────

def _validar_valor(valor):
    try:
        return float(valor) > 0
    except (TypeError, ValueError):
        return False


# ── CREATE ────────────────────────────────────────────────────

def adicionar_transacao(tipo, descricao, valor, categoria, id_conta, id_orcamento=None):
    log.info("CREATE transacao | tipo=%s | descricao=%s | valor=%s | categoria=%s | id_conta=%s", tipo, descricao, valor, categoria, id_conta)
    carregar_transacoes()

    if tipo not in ("receita", "despesa"):
        log.error("CREATE falhou | motivo=tipo_invalido | tipo=%s", tipo)
        return 400, "Tipo inválido. Use 'receita' ou 'despesa'."
    if len(descricao.strip()) < 2:
        log.error("CREATE falhou | motivo=descricao_curta | descricao=%s", descricao)
        return 400, "Descrição deve ter pelo menos 2 caracteres."
    if not _validar_valor(valor):
        log.error("CREATE falhou | motivo=valor_invalido | valor=%s", valor)
        return 400, "Valor deve ser um número positivo."
    if categoria not in CATEGORIAS:
        log.error("CREATE falhou | motivo=categoria_invalida | categoria=%s", categoria)
        return 400, f"Categoria inválida. Opções: {', '.join(CATEGORIAS)}."
    if not id_conta:
        log.error("CREATE falhou | motivo=id_conta_ausente")
        return 400, "id_conta é obrigatório."

    id_transacao = gerar_id_transacao()

    transacao = {
        "id":           id_transacao,
        "tipo":         tipo,
        "descricao":    descricao.strip(),
        "valor":        float(valor),
        "categoria":    categoria,
        "id_conta":     id_conta,
        "id_orcamento": id_orcamento,
    }

    transacoes[id_transacao] = transacao
    guardar_transacoes()
    log.info("CREATE ok | id=%s | tipo=%s | valor=%.2f | categoria=%s", id_transacao, tipo, float(valor), categoria)
    return 201, transacao


# ── READ (individual) ─────────────────────────────────────────

def encontrar_transacao(id_transacao):
    log.info("READ encontrar_transacao | id=%s", id_transacao)
    carregar_transacoes()

    if id_transacao not in transacoes:
        log.error("READ encontrar_transacao | motivo=nao_encontrada | id=%s", id_transacao)
        return 404, f"Transação {id_transacao} não encontrada."

    log.info("READ encontrar_transacao ok | id=%s", id_transacao)
    return 200, transacoes[id_transacao]


# ── READ (lista) ──────────────────────────────────────────────

def listar_transacoes(id_conta=None, filtro="todas", categoria=None):
    log.info("READ listar_transacoes | id_conta=%s | filtro=%s | categoria=%s", id_conta, filtro, categoria)
    carregar_transacoes()

    if not transacoes:
        log.error("READ listar_transacoes | motivo=sem_registos")
        return 404, "Não existem transações registadas."

    resultado = {}
    for id_t, t in transacoes.items():
        if id_conta and t["id_conta"] != id_conta:
            continue
        if filtro == "receitas" and t["tipo"] != "receita":
            continue
        if filtro == "despesas" and t["tipo"] != "despesa":
            continue
        if filtro == "categoria" and t["categoria"] != categoria:
            continue
        resultado[id_t] = t

    if not resultado:
        log.error("READ listar_transacoes | motivo=sem_resultados | filtro=%s | categoria=%s", filtro, categoria)
        return 404, "Nenhuma transação encontrada com esse filtro."

    log.info("READ listar_transacoes ok | total=%d | filtro=%s", len(resultado), filtro)
    return 200, list(resultado.values())


# ── UPDATE ────────────────────────────────────────────────────

def editar_transacao(id_transacao, descricao=None, valor=None, categoria=None, id_orcamento=None):
    log.info("UPDATE transacao | id=%s | descricao=%s | valor=%s | categoria=%s", id_transacao, descricao, valor, categoria)
    carregar_transacoes()

    if id_transacao not in transacoes:
        log.error("UPDATE transacao | motivo=nao_encontrada | id=%s", id_transacao)
        return 404, f"Transação {id_transacao} não encontrada."

    if descricao is not None:
        if len(descricao.strip()) < 2:
            log.error("UPDATE transacao | motivo=descricao_curta | id=%s", id_transacao)
            return 400, "Descrição deve ter pelo menos 2 caracteres."
        transacoes[id_transacao]["descricao"] = descricao.strip()

    if valor is not None:
        if not _validar_valor(valor):
            log.error("UPDATE transacao | motivo=valor_invalido | id=%s | valor=%s", id_transacao, valor)
            return 400, "Valor deve ser um número positivo."
        transacoes[id_transacao]["valor"] = float(valor)

    if categoria is not None:
        if categoria not in CATEGORIAS:
            log.error("UPDATE transacao | motivo=categoria_invalida | id=%s | categoria=%s", id_transacao, categoria)
            return 400, f"Categoria inválida. Opções: {', '.join(CATEGORIAS)}."
        transacoes[id_transacao]["categoria"] = categoria

    if id_orcamento is not None:
        transacoes[id_transacao]["id_orcamento"] = id_orcamento

    guardar_transacoes()
    log.info("UPDATE transacao ok | id=%s", id_transacao)
    return 200, transacoes[id_transacao]


# ── DELETE ────────────────────────────────────────────────────

def apagar_transacao(id_transacao):
    log.info("DELETE transacao | id=%s", id_transacao)
    carregar_transacoes()

    if id_transacao not in transacoes:
        log.error("DELETE transacao | motivo=nao_encontrada | id=%s", id_transacao)
        return 404, f"Transação {id_transacao} não encontrada."

    del transacoes[id_transacao]
    guardar_transacoes()
    log.info("DELETE transacao ok | id=%s", id_transacao)
    return 200, f"Transação {id_transacao} removida com sucesso."


# ── HELPERS para o main ───────────────────────────────────────

def calcular_saldo(id_conta):
    log.info("HELPER calcular_saldo | id_conta=%s", id_conta)
    carregar_transacoes()

    total = 0.0
    for t in transacoes.values():
        if t["id_conta"] != id_conta:
            continue
        total += t["valor"] if t["tipo"] == "receita" else -t["valor"]

    log.info("HELPER calcular_saldo ok | id_conta=%s | saldo=%.2f€", id_conta, total)
    return 200, total

def totais(id_conta=None):
    log.info("HELPER totais | id_conta=%s", id_conta)
    carregar_transacoes()

    lista = [
        t for t in transacoes.values()
        if id_conta is None or t["id_conta"] == id_conta
    ]
    receitas = sum(t["valor"] for t in lista if t["tipo"] == "receita")
    despesas = sum(t["valor"] for t in lista if t["tipo"] == "despesa")

    log.info("HELPER totais ok | receitas=%.2f€ | despesas=%.2f€", receitas, despesas)
    return 200, receitas, despesas