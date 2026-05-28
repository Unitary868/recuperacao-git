import json
import os
from utils import gerar_id_conta, gerar_token
from logger import get_logger

log = get_logger("contas")

contas = {}

FICHEIRO_CONTAS = "contas.json"

# Atributos da entidade Conta:
#   id      → identificador único
#   nome    → nome do utilizador
#   nif     → número de identificação fiscal
#   pin     → código de autenticação
#   token   → identificador de sessão


# ── Persistência ──────────────────────────────────────────────

def guardar_contas():
    with open(FICHEIRO_CONTAS, "w", encoding="utf-8") as ficheiro:
        json.dump(contas, ficheiro, indent=4, ensure_ascii=False)
    log.debug("Contas guardadas em disco.")

def carregar_contas():
    global contas
    if os.path.exists(FICHEIRO_CONTAS):
        with open(FICHEIRO_CONTAS, "r", encoding="utf-8") as ficheiro:
            contas = json.load(ficheiro)
        log.debug("Contas carregadas do ficheiro (%d registo(s)).", len(contas))
    else:
        contas = {}
        log.debug("Ficheiro de contas não encontrado — a iniciar vazio.")


# ── Helpers internos ──────────────────────────────────────────

def _validar_nif(nif):
    return nif.isdigit() and len(nif) == 9

def _validar_pin(pin):
    return pin.isdigit() and len(pin) == 4

def _gerar_id_unico():
    novo = gerar_id_conta()
    while novo in contas:
        novo = gerar_id_conta()
    return novo


# ── CREATE ────────────────────────────────────────────────────

def criar_conta(nome, nif, pin):
    log.info("CREATE conta | nome=%s | nif=%s", nome, nif)
    carregar_contas()

    if len(nome.strip()) < 2:
        log.error("CREATE falhou | motivo=nome_curto | nome=%s", nome)
        return 400, "Nome deve ter pelo menos 2 caracteres."
    if not _validar_nif(nif):
        log.error("CREATE falhou | motivo=nif_invalido | nif=%s", nif)
        return 400, "NIF inválido. Deve ter 9 dígitos."
    if not _validar_pin(pin):
        log.error("CREATE falhou | motivo=pin_invalido")
        return 400, "PIN inválido. Deve ter 4 dígitos."

    for conta in contas.values():
        if conta["nif"] == nif:
            log.error("CREATE falhou | motivo=nif_duplicado | nif=%s", nif)
            return 409, "Já existe uma conta com este NIF."

    id_conta = _gerar_id_unico()

    conta = {
        "id":    id_conta,
        "nome":  nome.strip(),
        "nif":   nif,
        "pin":   pin,
        "token": gerar_token(id_conta),
    }

    contas[id_conta] = conta
    guardar_contas()
    log.info("CREATE ok | id=%s | nome=%s", id_conta, nome.strip())
    return 201, conta


# ── READ (listar todas) ───────────────────────────────────────

def listar_contas():
    log.info("READ listar_contas")
    carregar_contas()

    if not contas:
        log.error("READ listar_contas | motivo=sem_registos")
        return 404, "Não existem contas registadas."

    log.info("READ listar_contas ok | total=%d", len(contas))
    return 200, contas


# ── READ (consultar individual) ───────────────────────────────

def consultar_conta(id_conta):
    log.info("READ consultar_conta | id=%s", id_conta)
    carregar_contas()

    if id_conta not in contas:
        log.error("READ consultar_conta | motivo=nao_encontrada | id=%s", id_conta)
        return 404, "Conta não encontrada."

    log.info("READ consultar_conta ok | id=%s", id_conta)
    return 200, contas[id_conta]


# ── UPDATE PIN ────────────────────────────────────────────────

def atualizar_pin(id_conta, pin_atual, pin_novo):
    log.info("UPDATE pin | id=%s", id_conta)
    carregar_contas()

    if id_conta not in contas:
        log.error("UPDATE pin | motivo=nao_encontrada | id=%s", id_conta)
        return 404, "Conta não encontrada."
    if contas[id_conta]["pin"] != pin_atual:
        log.error("UPDATE pin | motivo=pin_incorreto | id=%s", id_conta)
        return 401, "PIN atual incorreto."
    if not _validar_pin(pin_novo):
        log.error("UPDATE pin | motivo=pin_novo_invalido | id=%s", id_conta)
        return 400, "Novo PIN inválido. Deve ter 4 dígitos."

    contas[id_conta]["pin"] = pin_novo
    guardar_contas()
    log.info("UPDATE pin ok | id=%s", id_conta)
    return 200, contas[id_conta]


# ── DELETE ────────────────────────────────────────────────────

def eliminar_conta(id_conta, pin):
    log.info("DELETE conta | id=%s", id_conta)
    carregar_contas()

    if id_conta not in contas:
        log.error("DELETE conta | motivo=nao_encontrada | id=%s", id_conta)
        return 404, "Conta não encontrada."
    if contas[id_conta]["pin"] != pin:
        log.error("DELETE conta | motivo=pin_incorreto | id=%s", id_conta)
        return 401, "PIN incorreto."

    del contas[id_conta]
    guardar_contas()
    log.info("DELETE conta ok | id=%s", id_conta)
    return 200, id_conta


# ── AUTH ──────────────────────────────────────────────────────

def verificar_login(id_conta, pin):
    log.info("AUTH login | id=%s", id_conta)
    carregar_contas()

    if id_conta not in contas:
        log.error("AUTH login | motivo=nao_encontrada | id=%s", id_conta)
        return 404, "Conta não encontrada."
    if contas[id_conta]["pin"] != pin:
        log.error("AUTH login | motivo=pin_incorreto | id=%s", id_conta)
        return 401, "PIN incorreto."

    log.info("AUTH login ok | id=%s", id_conta)
    return 200, contas[id_conta]


# ── HELPERS para o main ───────────────────────────────────────

def _resolver_id(id_conta=None):
    carregar_contas()
    if not contas:
        return None
    return id_conta if id_conta in contas else next(iter(contas))

def get_nome(id_conta=None):
    carregar_contas()
    uid = _resolver_id(id_conta)
    if uid is None:
        log.error("get_nome | motivo=sem_contas")
        return 404, "Nenhuma conta encontrada."
    return 200, contas[uid]["nome"]

def get_id(id_conta=None):
    uid = _resolver_id(id_conta)
    if uid is None:
        log.error("get_id | motivo=sem_contas")
        return 404, "Nenhuma conta encontrada."
    return 200, uid

def get_dados(id_conta=None):
    carregar_contas()
    uid = _resolver_id(id_conta)
    if uid is None:
        log.error("get_dados | motivo=sem_contas")
        return 404, "Nenhuma conta encontrada."
    return 200, contas[uid]

def conta_existe():
    carregar_contas()
    existe = bool(contas)
    log.debug("conta_existe | resultado=%s", existe)
    return existe