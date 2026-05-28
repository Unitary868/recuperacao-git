# app.py — réplica exata do main.py em Tkinter
# Fluxo: Auth → Header (Nome | ID | Saldo) → Tabs (Transações | Orçamentos | Pagamentos | Conta)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from logger import get_logger

from conta import (
    criar_conta, conta_existe, verificar_login,
    get_nome, get_id, get_dados, atualizar_pin, eliminar_conta,
)
from transacao import (
    adicionar_transacao, encontrar_transacao,
    editar_transacao, apagar_transacao, listar_transacoes,
    totais, calcular_saldo, CATEGORIAS,
)
from orcamento import (
    criar_orcamento, listar_orcamentos, consultar_orcamento,
    atualizar_orcamento, remover_orcamento, registar_gasto,
    CATEGORIAS_ORC, PERIODOS,
)
from pagamento import (
    criar_pagamento, listar_pagamentos, consultar_pagamento,
    atualizar_pagamento, remover_pagamento, METODOS_PAG,
)

log = get_logger("app")


# ══════════════════════════════════════════════════════════════
# CORES E FONTES
# ══════════════════════════════════════════════════════════════

C_DARK   = "#1a1a2e"
C_ACCENT = "#e94560"
C_BG     = "#f4f6f8"
C_FRAME  = "#ffffff"
C_TEXTO  = "#2d3436"
C_MUTED  = "#636e72"
C_OK     = "#00b894"
C_ERR    = "#d63031"
C_WARN   = "#fdcb6e"

BTN = {
    "add":    ("#27ae60", "#2ecc71"),
    "info":   ("#2980b9", "#3498db"),
    "edit":   ("#d35400", "#e67e22"),
    "del":    ("#c0392b", "#e74c3c"),
    "neu":    ("#636e72", "#7f8c8d"),
    "login":  ("#1a1a2e", "#2d3436"),
    "reg":    ("#6c5ce7", "#a29bfe"),
}

F_NORM  = ("Helvetica", 10)
F_BOLD  = ("Helvetica", 10, "bold")
F_HEAD  = ("Helvetica", 12, "bold")
F_BIG   = ("Helvetica", 16, "bold")
F_BTN   = ("Helvetica", 9,  "bold")
F_SMALL = ("Helvetica", 9)
F_TAB   = ("Helvetica", 9)


# ══════════════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════════════

def _estilos(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("TNotebook",           background=C_BG, borderwidth=0)
    s.configure("TNotebook.Tab",       font=F_BOLD, padding=[14, 7],
                                        background="#dfe6e9", foreground=C_MUTED)
    s.map("TNotebook.Tab",
          background=[("selected", C_FRAME)],
          foreground=[("selected", C_ACCENT)])
    s.configure("TFrame",              background=C_BG)
    s.configure("T.Treeview",          font=F_TAB, rowheight=24,
                                        background=C_FRAME, fieldbackground=C_FRAME,
                                        foreground=C_TEXTO)
    s.configure("T.Treeview.Heading",  font=("Helvetica", 9, "bold"),
                                        background="#dfe6e9", foreground=C_TEXTO, relief="flat")
    s.map("T.Treeview",                background=[("selected", "#2980b9")],
                                        foreground=[("selected", "white")])
    s.configure("TScrollbar",          background="#dfe6e9", troughcolor=C_BG,
                                        borderwidth=0, arrowsize=11)
    s.configure("TCombobox",           padding=3)


# ══════════════════════════════════════════════════════════════
# WIDGETS AUXILIARES
# ══════════════════════════════════════════════════════════════

def _btn(parent, txt, cmd, tipo, w=12, **kw):
    bg, ac = BTN[tipo]
    b = tk.Button(parent, text=txt, command=cmd, width=w,
                  bg=bg, fg="white", activebackground=ac, activeforeground="white",
                  font=F_BTN, relief="flat", cursor="hand2", pady=5, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=ac))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def _lf(parent, titulo, fill=tk.X, expand=False, padx=14, pady=(10,4)):
    lf = tk.LabelFrame(parent, text=f"  {titulo}  ", font=F_BOLD,
                       bg=C_FRAME, fg=C_TEXTO, relief="solid", bd=1)
    lf.pack(fill=fill, expand=expand, padx=padx, pady=pady)
    return lf

def _entry(parent, row, col, label, show=None, ro=False, w=22, bg=C_FRAME):
    tk.Label(parent, text=label, font=F_NORM, bg=bg, fg=C_TEXTO, anchor="e"
             ).grid(row=row, column=col*2,   sticky="e", padx=(10,5), pady=4)
    e = tk.Entry(parent, width=w, show=show or "", font=F_NORM,
                 state="readonly" if ro else "normal", relief="solid", bd=1, bg="white")
    e.grid(row=row, column=col*2+1, sticky="w", padx=(0,12), pady=4)
    return e

def _combo(parent, row, col, label, vals, w=20, bg=C_FRAME):
    tk.Label(parent, text=label, font=F_NORM, bg=bg, fg=C_TEXTO, anchor="e"
             ).grid(row=row, column=col*2,   sticky="e", padx=(10,5), pady=4)
    c = ttk.Combobox(parent, values=vals, width=w, state="readonly", font=F_NORM)
    c.grid(row=row, column=col*2+1, sticky="w", padx=(0,12), pady=4)
    return c

def _tree(frame, cols, widths):
    tv = ttk.Treeview(frame, columns=cols, show="headings",
                       height=10, style="T.Treeview", selectmode="browse")
    for c, w in zip(cols, widths):
        tv.heading(c, text=c)
        tv.column(c,  width=w, anchor="center")
    tv.tag_configure("par",   background="#f8f9fa")
    tv.tag_configure("impar", background=C_FRAME)
    tv.tag_configure("desp",  foreground="#c0392b")
    tv.tag_configure("rec",   foreground="#27ae60")
    tv.tag_configure("exc",   background="#ffe0e0", foreground="#c0392b")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    return tv

def _row(tv, vals, extra_tag=None):
    n = len(tv.get_children())
    tag = "par" if n % 2 == 0 else "impar"
    tags = (tag,) if not extra_tag else (tag, extra_tag)
    tv.insert("", tk.END, values=vals, tags=tags)

def _clr(tv):
    tv.delete(*tv.get_children())

def _set(e, v, ro=False):
    if ro: e.config(state="normal")
    e.delete(0, tk.END)
    e.insert(0, str(v) if v else "")
    if ro: e.config(state="readonly")

def _clear(*ws):
    for w in ws:
        if isinstance(w, ttk.Combobox): w.set("")
        elif w.cget("state") == "readonly":
            w.config(state="normal"); w.delete(0, tk.END); w.config(state="readonly")
        else: w.delete(0, tk.END)


# ══════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════

class LoginFrame(tk.Frame):
    """Replica auth() do terminal."""

    def __init__(self, root, on_login):
        super().__init__(root, bg=C_DARK)
        self.on_login = on_login
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=C_FRAME)
        card.place(relx=.5, rely=.5, anchor="center", width=380, height=480)

        tk.Frame(card, bg=C_ACCENT, height=6).pack(fill=tk.X)

        tk.Label(card, text="💰", font=("Helvetica", 38), bg=C_FRAME).pack(pady=(28,4))
        tk.Label(card, text="Gestão Financeira", font=F_BIG,  bg=C_FRAME, fg=C_DARK).pack()
        tk.Label(card, text="Inicie sessão para continuar", font=F_SMALL,
                 bg=C_FRAME, fg=C_MUTED).pack(pady=(3,18))

        ttk.Separator(card).pack(fill=tk.X, padx=28)

        frm = tk.Frame(card, bg=C_FRAME)
        frm.pack(padx=28, pady=16, fill=tk.X)

        tk.Label(frm, text="ID da Conta", font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X)
        self.e_id = tk.Entry(frm, font=F_NORM, relief="solid", bd=1)
        self.e_id.pack(fill=tk.X, pady=(3,12), ipady=5)

        tk.Label(frm, text="PIN", font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X)
        self.e_pin = tk.Entry(frm, font=F_NORM, relief="solid", bd=1, show="*")
        self.e_pin.pack(fill=tk.X, pady=(3,4), ipady=5)
        self.e_pin.bind("<Return>", lambda _: self._login())

        self.lbl_err = tk.Label(frm, text="", font=F_SMALL, bg=C_FRAME, fg=C_ERR)
        self.lbl_err.pack(fill=tk.X, pady=(0,4))

        frm_btn = tk.Frame(card, bg=C_FRAME)
        frm_btn.pack(padx=28, fill=tk.X)
        _btn(frm_btn, "Entrar",      self._login,    "login").pack(fill=tk.X, ipady=3, pady=(2,6))
        _btn(frm_btn, "Criar Conta", self._registar, "reg"  ).pack(fill=tk.X, ipady=3)

    # ── login ─────────────────────────────────────────────────
    def _login(self):
        uid = self.e_id.get().strip().upper()
        pin = self.e_pin.get().strip()
        if not uid or not pin:
            return self._err("Preencha o ID e o PIN.")
        log.info("AUTH login | id=%s", uid)
        code, obj = verificar_login(uid, pin)
        if code == 200:
            log.info("AUTH ok | id=%s | nome=%s", uid, obj["nome"])
            self.on_login(obj)
        else:
            log.error("AUTH falhou | id=%s | %s", uid, obj)
            self._err(str(obj))

    # ── criar conta (replica opcao "1" do auth()) ─────────────
    def _registar(self):
        win = tk.Toplevel(self)
        win.title("Criar Conta")
        win.geometry("320x300")
        win.resizable(False, False)
        win.configure(bg=C_FRAME)
        win.grab_set()

        tk.Label(win, text="Nova Conta", font=F_HEAD, bg=C_FRAME, fg=C_DARK).pack(pady=(20,4))
        tk.Label(win, text="Preencha os dados abaixo", font=F_SMALL,
                 bg=C_FRAME, fg=C_MUTED).pack(pady=(0,14))

        frm = tk.Frame(win, bg=C_FRAME)
        frm.pack(padx=28, fill=tk.X)

        entries = {}
        for lbl, key, kw in [("Nome completo", "nome", {}),
                               ("NIF (9 dígitos)", "nif",  {}),
                               ("PIN (4 dígitos)", "pin",  {"show": "*"})]:
            tk.Label(frm, text=lbl, font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X, pady=(6,0))
            e = tk.Entry(frm, font=F_NORM, relief="solid", bd=1, **kw)
            e.pack(fill=tk.X, ipady=4)
            entries[key] = e

        lbl_e = tk.Label(win, text="", font=F_SMALL, bg=C_FRAME, fg=C_ERR)
        lbl_e.pack(pady=4)

        def _submit():
            nome = entries["nome"].get().strip()
            if not nome:
                lbl_e.config(text="400: Nome obrigatório.")
                return
            code, obj = criar_conta(nome, entries["nif"].get(), entries["pin"].get())
            if code == 201:
                log.info("AUTH conta criada | id=%s", obj["id"])
                win.destroy()
                messagebox.showinfo("Conta criada",
                    f"Conta criada com sucesso!\n\nO seu ID é:\n\n{obj['id']}\n\nGuarde-o para fazer login.")
            else:
                log.error("AUTH criar conta | %s", obj)
                lbl_e.config(text=f"{code}: {obj}")

        _btn(win, "Criar Conta", _submit, "add", w=20).pack(padx=28, fill=tk.X, ipady=3, pady=8)

    def _err(self, msg):
        self.lbl_err.config(text=msg)
        self.after(4000, lambda: self.lbl_err.config(text=""))


# ══════════════════════════════════════════════════════════════
# TAB — TRANSAÇÕES  (replica opcoes 1,2,3,4 do main())
# ══════════════════════════════════════════════════════════════

class TabTransacoes:
    """Replica: nova transação + extrato + editar + apagar."""

    def __init__(self, nb, id_conta, refresh_saldo, set_status):
        self.id_conta      = id_conta
        self.refresh_saldo = refresh_saldo
        self.set_status    = set_status
        self.frame         = ttk.Frame(nb)
        nb.add(self.frame, text="  Transações  ")
        self._build()

    def _build(self):
        self._build_form()
        self._build_extrato()

    # ── Formulário: nova transação (opcao 1) ──────────────────
    def _build_form(self):
        frm = _lf(self.frame, "Nova Transação")

        self.cb_tipo = _combo(frm, 0, 0, "Tipo",       ("receita", "despesa"), w=14)
        self.cb_cat  = _combo(frm, 0, 1, "Categoria",  list(CATEGORIAS), w=18)
        self.e_desc  = _entry(frm, 1, 0, "Descrição",  w=30)
        self.e_val   = _entry(frm, 1, 1, "Valor (€)",  w=12)
        self.e_orc   = _entry(frm, 2, 0, "ID Orçamento (opcional)", w=18)

        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(3, weight=1)

        _btn(frm, "Adicionar Transação", self._adicionar, "add", w=20
             ).grid(row=3, column=0, columnspan=4, pady=(6,10), padx=10, sticky="w")

    # ── Extrato (opcao 2) + Editar (3) + Apagar (4) ──────────
    def _build_extrato(self):
        outer = _lf(self.frame, "Extrato", fill=tk.BOTH, expand=True, pady=(0,12))

        # Filtros — replica "1-Todas 2-Receitas 3-Despesas 4-Por categoria"
        frm_f = tk.Frame(outer, bg=C_FRAME)
        frm_f.pack(fill=tk.X, padx=8, pady=(6,4))

        tk.Label(frm_f, text="Filtro:", font=F_BOLD, bg=C_FRAME).pack(side=tk.LEFT, padx=(4,8))
        self.filtro_var = tk.StringVar(value="todas")

        self.cb_cat_filtro = ttk.Combobox(frm_f, values=list(CATEGORIAS),
                                           width=16, state="disabled", font=F_NORM)
        self.cb_cat_filtro.pack(side=tk.RIGHT, padx=6)
        tk.Label(frm_f, text="Categoria:", font=F_NORM, bg=C_FRAME).pack(side=tk.RIGHT)

        for txt, val in [("Todas","todas"),("Receitas","receitas"),
                          ("Despesas","despesas"),("Por Categoria","categoria")]:
            rb = tk.Radiobutton(frm_f, text=txt, variable=self.filtro_var,
                                value=val, font=F_NORM, bg=C_FRAME,
                                activebackground=C_FRAME, command=self._on_filtro)
            rb.pack(side=tk.LEFT, padx=4)

        ttk.Separator(outer).pack(fill=tk.X, padx=8, pady=4)

        # Tabela
        frm_tv = tk.Frame(outer, bg=C_FRAME)
        frm_tv.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,4))
        self.tv = _tree(frm_tv,
            ("ID", "Tipo", "Descrição", "Valor", "Categoria"),
            [120, 90, 240, 90, 140])

        # Rodapé: totais + botões
        frm_foot = tk.Frame(outer, bg=C_FRAME)
        frm_foot.pack(fill=tk.X, padx=8, pady=(2,8))

        self.lbl_rec  = tk.Label(frm_foot, text="Receitas: +0.00€", font=F_BOLD,
                                  bg=C_FRAME, fg=C_OK)
        self.lbl_desp = tk.Label(frm_foot, text="Despesas: -0.00€", font=F_BOLD,
                                  bg=C_FRAME, fg=C_ERR)
        self.lbl_rec.pack(side=tk.LEFT, padx=(4,16))
        self.lbl_desp.pack(side=tk.LEFT)

        _btn(frm_foot, "Editar",    self._editar, "edit", w=10).pack(side=tk.RIGHT, padx=4)
        _btn(frm_foot, "Apagar",    self._apagar, "del",  w=10).pack(side=tk.RIGHT, padx=4)
        _btn(frm_foot, "↻ Atualizar", self._carregar, "neu", w=12).pack(side=tk.RIGHT, padx=4)

        self._carregar()

    # ── Opcao 1: adicionar ────────────────────────────────────
    def _adicionar(self):
        tipo  = self.cb_tipo.get()
        desc  = self.e_desc.get().strip()
        val   = self.e_val.get().strip().replace(",",".")
        cat   = self.cb_cat.get()
        id_orc = self.e_orc.get().strip().upper() or None

        if not tipo:   return self._status("Escolha o tipo.", "aviso")
        if not desc:   return self._status("400: Descrição obrigatória.", "erro")
        if not cat:    return self._status("Escolha a categoria.", "aviso")
        try:
            fval = float(val)
            if fval <= 0: raise ValueError
        except ValueError:
            return self._status("400: Valor inválido. Use: 12.50 ou 100.", "erro")

        log.info("TRANSACAO adicionar | tipo=%s | desc=%s | val=%s", tipo, desc, fval)
        code, obj = adicionar_transacao(tipo, desc, fval, cat, self.id_conta, id_orc)
        if code != 201:
            return self._status(f"{code}: {obj}", "erro")

        # Replica: se despesa, procura orçamento por categoria se não foi dado ID
        if tipo == "despesa":
            orc_alvo = id_orc
            if not orc_alvo:
                code_l, lista = listar_orcamentos()
                if code_l == 200:
                    for oid, o in lista.items():
                        if o["categoria"] == cat:
                            orc_alvo = oid
                            break
            if orc_alvo:
                code_o, msg_o = registar_gasto(orc_alvo, fval)
                log.info("ORCAMENTO gasto registado | %s: %s", code_o, msg_o)
                if "AVISO" in str(msg_o):
                    messagebox.showwarning("Orçamento excedido", str(msg_o))

        self._status(f"201: Transação criada! {obj['id']}", "ok")
        _clear(self.cb_tipo, self.e_desc, self.e_val, self.cb_cat, self.e_orc)
        self._carregar()
        self.refresh_saldo()

    # ── Opcao 2: extrato / listar ─────────────────────────────
    def _carregar(self):
        filtro = self.filtro_var.get()
        cat = self.cb_cat_filtro.get() if filtro == "categoria" else None
        code, obj = listar_transacoes(self.id_conta, filtro, cat)
        _clr(self.tv)
        if code == 200:
            for t in obj:
                sg  = "+" if t["tipo"] == "receita" else "-"
                tag = "rec" if t["tipo"] == "receita" else "desp"
                self.tv.insert("", tk.END, tags=(tag,), values=(
                    t["id"], t["tipo"], t["descricao"],
                    f"{sg}{t['valor']:.2f}€", t["categoria"],
                ))
        code_t, rec, desp = totais(self.id_conta)
        if code_t == 200:
            self.lbl_rec.config( text=f"Receitas:  +{rec:.2f}€")
            self.lbl_desp.config(text=f"Despesas:  -{desp:.2f}€")

    def _on_filtro(self):
        ativo = self.filtro_var.get() == "categoria"
        self.cb_cat_filtro.config(state="readonly" if ativo else "disabled")
        self._carregar()

    # ── Opcao 3: editar ───────────────────────────────────────
    def _editar(self):
        sel = self.tv.focus()
        if not sel: return self._status("Selecione uma transação.", "aviso")
        id_t = self.tv.item(sel, "values")[0]

        code, obj = encontrar_transacao(id_t)
        if code != 200: return self._status(f"{code}: {obj}", "erro")

        # Dialog de edição — replica "Nova descrição (enter para manter): ..."
        win = tk.Toplevel(self.frame)
        win.title(f"Editar Transação {id_t}")
        win.geometry("360x300")
        win.resizable(False, False)
        win.configure(bg=C_FRAME)
        win.grab_set()

        tk.Label(win, text=f"Editar  {id_t}", font=F_HEAD, bg=C_FRAME, fg=C_DARK).pack(pady=(16,4))
        tk.Label(win, text=f"{obj['tipo']}  |  {obj['descricao']}  |  {obj['valor']:.2f}€",
                 font=F_SMALL, bg=C_FRAME, fg=C_MUTED).pack(pady=(0,12))

        frm = tk.Frame(win, bg=C_FRAME)
        frm.pack(padx=24, fill=tk.X)

        tk.Label(frm, text="Descrição", font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X)
        e_desc = tk.Entry(frm, font=F_NORM, relief="solid", bd=1)
        e_desc.pack(fill=tk.X, ipady=4, pady=(2,10))
        _set(e_desc, obj["descricao"])

        tk.Label(frm, text="Valor (€)", font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X)
        e_val = tk.Entry(frm, font=F_NORM, relief="solid", bd=1)
        e_val.pack(fill=tk.X, ipady=4, pady=(2,10))
        _set(e_val, obj["valor"])

        tk.Label(frm, text="Categoria", font=F_BOLD, bg=C_FRAME, anchor="w").pack(fill=tk.X)
        cb_cat = ttk.Combobox(frm, values=list(CATEGORIAS), font=F_NORM, state="readonly")
        cb_cat.pack(fill=tk.X, pady=(2,4))
        cb_cat.set(obj["categoria"])

        lbl_e = tk.Label(win, text="", font=F_SMALL, bg=C_FRAME, fg=C_ERR)
        lbl_e.pack(pady=4)

        def _guardar():
            nova_d = e_desc.get().strip() or None
            raw_v  = e_val.get().strip().replace(",",".")
            try:
                novo_v = float(raw_v) if raw_v else None
                if novo_v is not None and novo_v <= 0: raise ValueError
            except ValueError:
                lbl_e.config(text="400: Valor inválido.")
                return
            nova_c = cb_cat.get() or None
            code2, obj2 = editar_transacao(id_t, nova_d, novo_v, nova_c)
            if code2 == 200:
                log.info("TRANSACAO editada | id=%s", id_t)
                win.destroy()
                self._status(f"200: Transação {id_t} atualizada.", "ok")
                self._carregar()
                self.refresh_saldo()
            else:
                lbl_e.config(text=f"{code2}: {obj2}")

        _btn(win, "Guardar", _guardar, "edit", w=18).pack(padx=24, fill=tk.X, ipady=3, pady=4)

    # ── Opcao 4: apagar ───────────────────────────────────────
    def _apagar(self):
        sel = self.tv.focus()
        if not sel: return self._status("Selecione uma transação.", "aviso")
        vals = self.tv.item(sel, "values")
        id_t = vals[0]

        if not messagebox.askyesno("Confirmar apagar",
            f"Apagar transação {id_t}?\n{vals[2]}  |  {vals[3]}"):
            self._status("Cancelado.", "aviso")
            return

        code, msg = apagar_transacao(id_t)
        if code == 200:
            log.info("TRANSACAO apagada | id=%s", id_t)
            self._status(f"200: {msg}", "ok")
            self._carregar()
            self.refresh_saldo()
        else:
            self._status(f"{code}: {msg}", "erro")

    def _status(self, msg, tipo="ok"):
        log.info(msg) if tipo == "ok" else log.error(msg)
        self.set_status(msg, tipo)


# ══════════════════════════════════════════════════════════════
# TAB — ORÇAMENTOS  (replica submenu_orcamento())
# ══════════════════════════════════════════════════════════════

class TabOrcamentos:
    def __init__(self, nb, set_status):
        self.set_status = set_status
        self.frame      = ttk.Frame(nb)
        nb.add(self.frame, text="  Orçamentos  ")
        self._build()

    def _build(self):
        frm = _lf(self.frame, "Orçamento")
        self.e_id      = _entry(frm, 0, 0, "ID",          ro=True, w=16)
        self.cb_cat    = _combo(frm, 0, 1, "Categoria",   list(CATEGORIAS_ORC), w=18)
        self.e_lim     = _entry(frm, 1, 0, "Limite (€)",  w=16)
        self.cb_per    = _combo(frm, 1, 1, "Período",     list(PERIODOS), w=14)

        frm_btn = tk.Frame(self.frame, bg=C_BG)
        frm_btn.pack(pady=6)
        for txt, cmd, t in [("Criar",     self._criar,     "add"),
                              ("Atualizar", self._atualizar, "edit"),
                              ("Remover",   self._remover,   "del"),
                              ("Limpar",    self._limpar,    "neu")]:
            _btn(frm_btn, txt, cmd, t).pack(side=tk.LEFT, padx=5)

        outer = _lf(self.frame, "Lista de Orçamentos", fill=tk.BOTH, expand=True, pady=(0,12))
        frm_tv = tk.Frame(outer, bg=C_FRAME)
        frm_tv.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.tv = _tree(frm_tv,
            ("ID", "Categoria", "Período", "Limite", "Gasto", "Restante"),
            [110, 160, 100, 100, 100, 110])
        self.tv.bind("<<TreeviewSelect>>", self._selecionar)

        self._carregar()

    def _criar(self):
        cat = self.cb_cat.get(); lim = self.e_lim.get().replace(",","."); per = self.cb_per.get()
        if not cat or not per: return self._st("Escolha categoria e período.", "aviso")
        try:
            fv = float(lim)
            if fv <= 0: raise ValueError
        except ValueError:
            return self._st("400: Limite inválido.", "erro")
        code, obj = criar_orcamento(cat, fv, per)
        if code == 201:
            log.info("ORCAMENTO criado | id=%s", obj["id"])
            self._st(f"201: Orçamento criado! {obj['id']}", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _atualizar(self):
        uid = self.e_id.get()
        if not uid: return self._st("Selecione um orçamento.", "aviso")
        lim_raw = self.e_lim.get().strip().replace(",",".")
        try:
            novo_l = float(lim_raw) if lim_raw else None
            if novo_l is not None and novo_l <= 0: raise ValueError
        except ValueError:
            return self._st("400: Limite inválido.", "erro")
        nova_c = self.cb_cat.get() or None
        novo_p = self.cb_per.get() or None
        code, obj = atualizar_orcamento(uid, novo_l, nova_c, novo_p)
        if code == 200:
            log.info("ORCAMENTO atualizado | id=%s", uid)
            self._st(f"200: Orçamento {uid} atualizado.", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _remover(self):
        uid = self.e_id.get()
        if not uid: return self._st("Selecione um orçamento.", "aviso")
        if not messagebox.askyesno("Confirmar", f"Remover orçamento {uid}?"):
            return self._st("Cancelado.", "aviso")
        code, obj = remover_orcamento(uid)
        if code == 200:
            log.info("ORCAMENTO removido | id=%s", uid)
            self._st(f"200: Orçamento {uid} removido.", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _carregar(self):
        _clr(self.tv)
        code, obj = listar_orcamentos()
        if code == 200:
            for oid, d in obj.items():
                rest = d["limite"] - d["gasto_atual"]
                tag = "exc" if rest < 0 else ("par" if len(self.tv.get_children()) % 2 == 0 else "impar")
                self.tv.insert("", tk.END, tags=(tag,), values=(
                    oid, d["categoria"], d["periodo"],
                    f"{d['limite']:.2f}€", f"{d['gasto_atual']:.2f}€", f"{rest:.2f}€",
                ))

    def _limpar(self):
        _clear(self.e_id, self.cb_cat, self.e_lim, self.cb_per)

    def _selecionar(self, _):
        sel = self.tv.focus()
        if not sel: return
        v = self.tv.item(sel, "values")
        _set(self.e_id, v[0], ro=True)
        self.cb_cat.set(v[1]); self.cb_per.set(v[2])
        _set(self.e_lim, v[3].replace("€",""))

    def _st(self, msg, t="ok"):
        log.info(msg) if t == "ok" else log.error(msg)
        self.set_status(msg, t)


# ══════════════════════════════════════════════════════════════
# TAB — PAGAMENTOS  (replica submenu_pagamento())
# ══════════════════════════════════════════════════════════════

class TabPagamentos:
    def __init__(self, nb, set_status):
        self.set_status = set_status
        self.frame      = ttk.Frame(nb)
        nb.add(self.frame, text="  Pagamentos  ")
        self._build()

    def _build(self):
        frm = _lf(self.frame, "Pagamento")
        self.e_id    = _entry(frm, 0, 0, "ID",               ro=True, w=16)
        self.e_desc  = _entry(frm, 0, 1, "Descrição",        w=22)
        self.e_val   = _entry(frm, 1, 0, "Valor (€)",        w=14)
        self.e_data  = _entry(frm, 1, 1, "Data (YYYY-MM-DD)",w=16)
        self.cb_met  = _combo(frm, 2, 0, "Método",           list(METODOS_PAG), w=16)
        self.e_id_t  = _entry(frm, 2, 1, "ID Transação (opc.)", w=16)
        _set(self.e_data, datetime.now().strftime("%Y-%m-%d"))

        frm_btn = tk.Frame(self.frame, bg=C_BG)
        frm_btn.pack(pady=6)
        for txt, cmd, t in [("Criar",     self._criar,     "add"),
                              ("Atualizar", self._atualizar, "edit"),
                              ("Remover",   self._remover,   "del"),
                              ("Limpar",    self._limpar,    "neu")]:
            _btn(frm_btn, txt, cmd, t).pack(side=tk.LEFT, padx=5)

        outer = _lf(self.frame, "Lista de Pagamentos", fill=tk.BOTH, expand=True, pady=(0,12))
        frm_tv = tk.Frame(outer, bg=C_FRAME)
        frm_tv.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.tv = _tree(frm_tv,
            ("ID", "Descrição", "Valor", "Data", "Método", "ID Transação"),
            [110, 200, 90, 110, 120, 120])
        self.tv.bind("<<TreeviewSelect>>", self._selecionar)

        self._carregar()

    def _criar(self):
        desc = self.e_desc.get().strip()
        if not desc: return self._st("400: Descrição obrigatória.", "erro")
        try:
            fv = float(self.e_val.get().replace(",","."))
            if fv <= 0: raise ValueError
        except ValueError:
            return self._st("400: Valor inválido.", "erro")
        metodo = self.cb_met.get()
        if not metodo: return self._st("Escolha o método.", "aviso")
        id_t = self.e_id_t.get().strip().upper() or None
        code, obj = criar_pagamento(desc, fv, self.e_data.get(), metodo, id_t)
        if code == 201:
            log.info("PAGAMENTO criado | id=%s", obj["id"])
            self._st(f"201: Pagamento criado! {obj['id']}", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _atualizar(self):
        uid = self.e_id.get()
        if not uid: return self._st("Selecione um pagamento.", "aviso")
        raw_v = self.e_val.get().strip().replace(",",".")
        try:
            novo_v = float(raw_v) if raw_v else None
            if novo_v is not None and novo_v <= 0: raise ValueError
        except ValueError:
            return self._st("400: Valor inválido.", "erro")
        nova_d  = self.e_desc.get().strip() or None
        nova_dt = self.e_data.get().strip()  or None
        novo_m  = self.cb_met.get()          or None
        id_t    = self.e_id_t.get().strip().upper() or None
        code, obj = atualizar_pagamento(uid, nova_d, novo_v, nova_dt, novo_m, id_t)
        if code == 200:
            log.info("PAGAMENTO atualizado | id=%s", uid)
            self._st(f"200: Pagamento {uid} atualizado.", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _remover(self):
        uid = self.e_id.get()
        if not uid: return self._st("Selecione um pagamento.", "aviso")
        if not messagebox.askyesno("Confirmar", f"Remover pagamento {uid}?"):
            return self._st("Cancelado.", "aviso")
        code, obj = remover_pagamento(uid)
        if code == 200:
            log.info("PAGAMENTO removido | id=%s", uid)
            self._st(f"200: Pagamento {uid} removido.", "ok")
            self._limpar(); self._carregar()
        else:
            self._st(f"{code}: {obj}", "erro")

    def _carregar(self):
        _clr(self.tv)
        code, obj = listar_pagamentos()
        if code == 200:
            for pid, p in obj.items():
                _row(self.tv, (pid, p["descricao"], f"{p['valor']:.2f}€",
                               p["data"], p["metodo"], p["id_transacao"] or "—"))

    def _limpar(self):
        _clear(self.e_id, self.e_desc, self.e_val, self.cb_met, self.e_id_t)
        _set(self.e_data, datetime.now().strftime("%Y-%m-%d"))

    def _selecionar(self, _):
        sel = self.tv.focus()
        if not sel: return
        v = self.tv.item(sel, "values")
        _set(self.e_id, v[0], ro=True); _set(self.e_desc, v[1])
        _set(self.e_val, v[2].replace("€","")); _set(self.e_data, v[3])
        self.cb_met.set(v[4])
        _set(self.e_id_t, "" if v[5] == "—" else v[5])

    def _st(self, msg, t="ok"):
        log.info(msg) if t == "ok" else log.error(msg)
        self.set_status(msg, t)


# ══════════════════════════════════════════════════════════════
# TAB — CONTA  (replica submenu_conta())
# ══════════════════════════════════════════════════════════════

class TabConta:
    def __init__(self, nb, conta, on_logout, refresh_saldo, set_status):
        self.conta         = conta
        self.on_logout     = on_logout
        self.refresh_saldo = refresh_saldo
        self.set_status    = set_status
        self.frame         = ttk.Frame(nb)
        nb.add(self.frame, text="  Conta  ")
        self._build()

    def _build(self):
        # Opcao 1: Ver dados
        frm_d = _lf(self.frame, "Dados da Conta")
        for i, (lbl, val) in enumerate([
            ("ID",    self.conta["id"]),
            ("Nome",  self.conta["nome"]),
            ("NIF",   self.conta["nif"]),
            ("Token", self.conta["token"]),
        ]):
            tk.Label(frm_d, text=f"{lbl}:", font=F_BOLD, bg=C_FRAME,
                     fg=C_MUTED).grid(row=i, column=0, sticky="e", padx=(20,8), pady=5)
            tk.Label(frm_d, text=val, font=F_NORM, bg=C_FRAME,
                     fg=C_TEXTO, anchor="w").grid(row=i, column=1, sticky="w")

        # Saldo
        frm_s = _lf(self.frame, "Saldo")
        _, saldo = calcular_saldo(self.conta["id"])
        _, rec, desp = totais(self.conta["id"])
        cor = C_OK if saldo >= 0 else C_ERR
        self.lbl_saldo = tk.Label(frm_s, text=f"{saldo:.2f}€",
                                   font=("Helvetica", 24, "bold"), bg=C_FRAME, fg=cor)
        self.lbl_saldo.grid(row=0, column=1, sticky="w", padx=(0,20))
        tk.Label(frm_s, text="Saldo:",    font=F_BOLD, bg=C_FRAME, fg=C_MUTED).grid(row=0, column=0, sticky="e", padx=(20,8), pady=6)
        tk.Label(frm_s, text="Receitas:", font=F_BOLD, bg=C_FRAME, fg=C_MUTED).grid(row=1, column=0, sticky="e", padx=(20,8))
        tk.Label(frm_s, text="Despesas:", font=F_BOLD, bg=C_FRAME, fg=C_MUTED).grid(row=2, column=0, sticky="e", padx=(20,8), pady=4)
        self.lbl_rec  = tk.Label(frm_s, text=f"+{rec:.2f}€",  font=F_BOLD, bg=C_FRAME, fg=C_OK)
        self.lbl_desp = tk.Label(frm_s, text=f"-{desp:.2f}€", font=F_BOLD, bg=C_FRAME, fg=C_ERR)
        self.lbl_rec.grid( row=1, column=1, sticky="w")
        self.lbl_desp.grid(row=2, column=1, sticky="w")

        # Opcoes 2 e 3
        frm_btn = _lf(self.frame, "Ações")
        f = tk.Frame(frm_btn, bg=C_FRAME)
        f.pack(padx=10, pady=10)
        _btn(f, "↻ Atualizar Saldo", self._atualizar_saldo, "info",  w=18).pack(side=tk.LEFT, padx=6)
        _btn(f, "Alterar PIN",        self._alterar_pin,    "edit",  w=14).pack(side=tk.LEFT, padx=6)
        _btn(f, "Eliminar Conta",     self._eliminar,       "del",   w=14).pack(side=tk.LEFT, padx=6)

    # Opcao 2: atualizar PIN
    def _alterar_pin(self):
        p_atual = simpledialog.askstring("Alterar PIN", "PIN atual:", show="*", parent=self.frame)
        if p_atual is None: return
        p_novo = simpledialog.askstring("Alterar PIN", "Novo PIN (4 dígitos):", show="*", parent=self.frame)
        if p_novo is None: return
        code, obj = atualizar_pin(self.conta["id"], p_atual, p_novo)
        if code == 200:
            self.conta["pin"] = p_novo
            log.info("CONTA PIN atualizado | id=%s", self.conta["id"])
            self.set_status("200: PIN atualizado!", "ok")
        else:
            log.error("CONTA PIN falhou | %s", obj)
            self.set_status(f"{code}: {obj}", "erro")
            messagebox.showerror("Erro", str(obj))

    # Opcao 3: eliminar conta
    def _eliminar(self):
        pin = simpledialog.askstring("Eliminar Conta", "PIN para confirmar:", show="*", parent=self.frame)
        if pin is None: return
        if not messagebox.askyesno("Tens a certeza?", "Esta ação é irreversível.\nEliminar conta?"):
            self.set_status("Cancelado.", "aviso"); return
        code, obj = eliminar_conta(self.conta["id"], pin)
        if code == 200:
            log.info("CONTA eliminada | id=%s", self.conta["id"])
            messagebox.showinfo("Conta eliminada", "Conta eliminada. A sair...")
            self.on_logout()
        else:
            log.error("CONTA eliminar falhou | %s", obj)
            self.set_status(f"{code}: {obj}", "erro")
            messagebox.showerror("Erro", str(obj))

    def _atualizar_saldo(self):
        _, saldo    = calcular_saldo(self.conta["id"])
        _, rec, desp = totais(self.conta["id"])
        cor = C_OK if saldo >= 0 else C_ERR
        self.lbl_saldo.config(text=f"{saldo:.2f}€", fg=cor)
        self.lbl_rec.config( text=f"+{rec:.2f}€")
        self.lbl_desp.config(text=f"-{desp:.2f}€")
        self.set_status("Saldo atualizado.", "ok")
        self.refresh_saldo()


# ══════════════════════════════════════════════════════════════
# MAIN FRAME (após login)
# ══════════════════════════════════════════════════════════════

class MainFrame(tk.Frame):
    """Replica o loop principal de main(): mostra Nome | ID | Saldo no topo."""

    def __init__(self, root, conta, on_logout):
        super().__init__(root, bg=C_BG)
        self.conta     = conta
        self.on_logout = on_logout
        self._build()

    def _build(self):
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    # Header: "Nome | ID: C001 | Saldo: xx.xx€"  (replica print do main())
    def _build_header(self):
        hdr = tk.Frame(self, bg=C_DARK, height=54)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        _, saldo = calcular_saldo(self.conta["id"])
        cor_s    = C_OK if saldo >= 0 else C_ERR

        self.lbl_user = tk.Label(hdr, font=("Helvetica", 12, "bold"),
                                  bg=C_DARK, fg="white")
        self.lbl_user.pack(side=tk.LEFT, padx=20, pady=14)

        self.lbl_saldo = tk.Label(hdr, font=F_BOLD, bg=C_DARK, fg=cor_s)
        self.lbl_saldo.pack(side=tk.LEFT, padx=0)

        self._refresh_header_labels(saldo)

        def _logout():
            if messagebox.askyesno("Sair", "Tem a certeza que pretende sair?"):
                log.info("AUTH logout | id=%s", self.conta["id"])
                self.on_logout()

        tk.Button(hdr, text="⎋  Sair", command=_logout,
                  bg=C_ACCENT, fg="white", relief="flat",
                  font=F_BTN, cursor="hand2", padx=12, pady=5
                  ).pack(side=tk.RIGHT, padx=16, pady=10)

        self.lbl_hora = tk.Label(hdr, bg=C_DARK, fg=C_MUTED, font=F_SMALL)
        self.lbl_hora.pack(side=tk.RIGHT, padx=12)
        self._tick()

    def _refresh_header_labels(self, saldo=None):
        if saldo is None:
            _, saldo = calcular_saldo(self.conta["id"])
        cor = C_OK if saldo >= 0 else C_ERR
        self.lbl_user.config(text=f"💰  {self.conta['nome']}  |  ID: {self.conta['id']}")
        self.lbl_saldo.config(text=f"|  Saldo: {saldo:.2f}€", fg=cor)

    def _tick(self):
        self.lbl_hora.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        self.after(1000, self._tick)

    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        ss = self._set_status
        rs = self._refresh_header_labels

        TabTransacoes(nb, self.conta["id"], rs, ss)
        TabOrcamentos(nb, ss)
        TabPagamentos(nb, ss)
        TabConta(nb, self.conta, self.on_logout, rs, ss)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg="#2d3436", height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self._st_icon = tk.Label(bar, text="●", bg="#2d3436", fg=C_OK, font=("Helvetica", 11))
        self._st_icon.pack(side=tk.LEFT, padx=(12,4))

        self._st_var = tk.StringVar(value="Pronto.")
        tk.Label(bar, textvariable=self._st_var, bg="#2d3436",
                 fg="#dfe6e9", font=F_SMALL, anchor="w").pack(side=tk.LEFT)

        tk.Label(bar, text="Gestão Financeira  v1.0",
                 bg="#2d3436", fg=C_MUTED, font=("Helvetica", 8)
                 ).pack(side=tk.RIGHT, padx=12)

    def _set_status(self, msg, tipo="ok"):
        cores = {"ok": C_OK, "erro": C_ERR, "aviso": C_WARN}
        self._st_icon.config(fg=cores.get(tipo, C_OK))
        self._st_var.set(f"  {msg}")


# ══════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gestão Financeira")
        self.root.geometry("1080x700")
        self.root.minsize(880, 580)
        self.root.configure(bg=C_DARK)
        _estilos(self.root)
        self._frame = None
        self._ir_login()
        log.info("APP iniciada")
        self.root.mainloop()

    def _ir_login(self):
        if self._frame: self._frame.destroy()
        f = LoginFrame(self.root, on_login=self._ir_app)
        f.pack(fill=tk.BOTH, expand=True)
        self._frame = f

    def _ir_app(self, conta):
        if self._frame: self._frame.destroy()
        f = MainFrame(self.root, conta, on_logout=self._ir_login)
        f.pack(fill=tk.BOTH, expand=True)
        self._frame = f


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App()