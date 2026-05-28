import random
from datetime import datetime
import string

# ── PEDIR INPUT (para main) ───────────────────────────────────
def pedir_num(msg, mn=None, mx=None, dec=True):
    """pedir_num do teu sistema original (simplificado)"""
    while True:
        try:
            v = (float if dec else int)(input(msg).strip().replace(",", "."))
            if (mn is None or v >= mn) and (mx is None or v <= mx):
                return v
            print(f"400: Valor deve estar entre {mn} e {mx}.")
        except ValueError:
            print("400: Número inválido.")

# ── GERAÇÃO DE IDs ────────────────────────────────────────────
def gerar_id_conta():
    return f"C{random.randint(1, 999):03d}"

def gerar_id_transacao():
    return f"T{random.randint(1, 999):03d}"

def gerar_id_orcamento():
    return f"O{random.randint(1, 999):03d}"

def gerar_id_pagamento():
    return f"P{random.randint(1, 999):03d}"

# ── VALIDAÇÕES (para módulos) ─────────────────────────────────
def validar_data(data_str):
    if not data_str: return False
    try:
        datetime.strptime(data_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_nif(nif):
    return isinstance(nif, str) and nif.isdigit() and len(nif) == 9

def validar_pin(pin):
    return isinstance(pin, str) and pin.isdigit() and len(pin) == 4

def validar_float_positivo(valor):
    try:
        v = float(valor)
        return v > 0
    except (TypeError, ValueError):
        return False

def gerar_token(uid):
    l = "".join(random.choices(string.ascii_uppercase, k=3))
    n = "".join(random.choices(string.digits, k=3))
    return f"USR-{uid}-{l}{n}"