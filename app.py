# app.py — Gestão Financeira | Tkinter
# Fluxo: Login → App Principal (Tabs: Minha Conta | Transações | Orçamentos | Pagamentos)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from logger import get_logger

from conta import (
    criar_conta, listar_contas, consultar_conta,
    atualizar_pin, eliminar_conta, verificar_login,
)
from transacao import (
    adicionar_transacao, listar_transacoes, encontrar_transacao,
    editar_transacao, apagar_transacao, calcular_saldo, totais,
)
from orcamento import (
    criar_orcamento, listar_orcamentos, consultar_orcamento,
    atualizar_orcamento, remover_orcamento, registar_gasto,
)
from pagamento import (
    criar_pagamento, listar_pagamentos, consultar_pagamento,
    atualizar_pagamento, remover_pagamento,
)

log = get_logger("app")


# ══════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════

CATEGORIAS_TRANSACAO = (
    "Alimentação", "Transporte", "Lazer", "Saúde",
    "Educação", "Habitação", "Vestuário", "Tecnologia",
    "Poupança", "Salário", "Freelance", "Outros",
)
CATEGORIAS_ORCAMENTO = (
    "Alimentação", "Transporte", "Lazer", "Saúde",
    "Educação", "Habitação", "Vestuário", "Tecnologia",
    "Poupança", "Outros",
)
PERIODOS    = ("diário", "semanal", "mensal", "anual")
METODOS_PAG = ("MB Way", "Transferência", "Multibanco", "Dinheiro", "Cartão")

# Cores
C_DARK    = "#1a1a2e"
C_ACCENT  = "#e94560"
C_BG      = "#f4f6f8"
C_FRAME   = "#ffffff"
C_TEXTO   = "#2d3436"
C_MUTED   = "#636e72"
C_SUCCESS = "#00b894"
C_ERROR   = "#d63031"
C_WARN    = "#fdcb6e"

BTN_CORES = {
    "criar":     ("#27ae60", "#2ecc71"),
    "consultar": ("#2980b9", "#3498db"),
    "atualizar": ("#d35400", "#e67e22"),
    "remover":   ("#c0392b", "#e74c3c"),
    "limpar":    ("#636e72", "#7f8c8d"),
    "login":     ("#1a1a2e", "#2d3436"),
    "registar":  ("#6c5ce7", "#a29bfe"),
}

F_NORMAL  = ("Helvetica", 10)
F_BOLD    = ("Helvetica", 10, "bold")
F_TITULO  = ("Helvetica", 12, "bold")
F_GRANDE  = ("Helvetica", 16, "bold")
F_BTN     = ("Helvetica", 9,  "bold")
F_SMALL   = ("Helvetica", 9)
F_TABELA  = ("Helvetica", 9)


# ══════════════════════════════════════════════════════════════
# ESTILOS
# ══════════════════════════════════════════════════════════════

def _aplicar_estilos(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("TNotebook",            background=C_BG, borderwidth=0)
    s.configure("TNotebook.Tab",        font=F_BOLD, padding=[16, 8],
                                         background="#dfe6e9", foreground=C_MUTED)
    s.map("TNotebook.Tab",
          background=[("selected", C_FRAME)],
          foreground=[("selected", C_ACCENT)])
    s.configure("TFrame",               background=C_BG)
    s.configure("Tabela.Treeview",      font=F_TABELA, rowheight=26,
                                         background=C_FRAME, fieldbackground=C_FRAME,
                                         foreground=C_TEXTO)
    s.configure("Tabela.Treeview.Heading",
                                         font=("Helvetica", 9, "bold"),
                                         background="#dfe6e9", foreground=C_TEXTO,
                                         relief="flat")
    s.map("Tabela.Treeview",            background=[("selected", "#2980b9")],
                                         foreground=[("selected", "white")])
    s.configure("TScrollbar",           background="#dfe6e9", troughcolor=C_BG,
                                         borderwidth=0, arrowsize=12)
    s.configure("TCombobox",            padding=4)


# ══════════════════════════════════════════════════════════════
# WIDGETS AUXILIARES
# ══════════════════════════════════════════════════════════════

def _btn(parent, texto, cmd, tipo, width=12):
    bg, active = BTN_CORES[tipo]
    b = tk.Button(parent, text=texto, command=cmd, width=width,
                  bg=bg, fg="white", activebackground=active, activeforeground="white",
                  font=F_BTN, relief="flat", cursor="hand2", pady=5)
    b.bind("<Enter>", lambda e: b.config(bg=active))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def _label_entry(frame, texto, row, col=0, show=None, readonly=False, width=24, bg=C_FRAME):
    tk.Label(frame, text=texto, font=F_NORMAL, bg=bg, fg=C_TEXTO, anchor="e"
             ).grid(row=row, column=col * 2, sticky="e", padx=(12, 6), pady=5)
    e = tk.Entry(frame, width=width, show=show or "",
                 state="readonly" if readonly else "normal",
                 relief="solid", bd=1, font=F_NORMAL, bg="white")
    e.grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 16), pady=5)
    return e

def _label_combo(frame, texto, row, values, col=0, width=22, bg=C_FRAME):
    tk.Label(frame, text=texto, font=F_NORMAL, bg=bg, fg=C_TEXTO, anchor="e"
             ).grid(row=row, column=col * 2, sticky="e", padx=(12, 6), pady=5)
    c = ttk.Combobox(frame, values=values, width=width, state="readonly", font=F_NORMAL)
    c.grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 16), pady=5)
    return c

def _treeview(frame, colunas, larguras=None):
    tree = ttk.Treeview(frame, columns=colunas, show="headings",
                         height=12, style="Tabela.Treeview", selectmode="browse")
    for i, col in enumerate(colunas):
        w = larguras[i] if larguras else 150
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    tree.tag_configure("par",   background="#f8f9fa")
    tree.tag_configure("impar", background=C_FRAME)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    return tree

def _inserir_linha(tree, valores):
    tag = "par" if len(tree.get_children()) % 2 == 0 else "impar"
    tree.insert("", tk.END, values=valores, tags=(tag,))

def _limpar_tree(tree):
    tree.delete(*tree.get_children())

def _set(entry, valor, readonly=False):
    if readonly:
        entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, str(valor) if valor else "")
    if readonly:
        entry.config(state="readonly")

def _clear(*widgets):
    for w in widgets:
        if isinstance(w, ttk.Combobox):
            w.set("")
        elif w.cget("state") == "readonly":
            w.config(state="normal"); w.delete(0, tk.END); w.config(state="readonly")
        else:
            w.delete(0, tk.END)

def _separador(parent):
    ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=16, pady=2)


# ══════════════════════════════════════════════════════════════
# CLASSE BASE — Tab
# ══════════════════════════════════════════════════════════════

class Tab:
    def __init__(self, notebook, titulo, conta, set_status):
        self.conta      = conta          # dict da conta autenticada
        self.set_status = set_status
        self.frame      = ttk.Frame(notebook)
        notebook.add(self.frame, text=f"  {titulo}  ")
        self._construir()

    def _construir(self):  raise NotImplementedError
    def _limpar(self):     raise NotImplementedError
    def _carregar(self):   raise NotImplementedError

    # ── Helpers de layout ─────────────────────────────────────
    def _lf(self, titulo):
        lf = tk.LabelFrame(self.frame, text=f"  {titulo}  ",
                           font=F_TITULO, bg=C_FRAME, fg=C_TEXTO,
                           relief="solid", bd=1, labelanchor="nw")
        lf.pack(fill=tk.X, padx=16, pady=(14, 4))
        return lf

    def _frame_btn(self):
        f = tk.Frame(self.frame, bg=C_BG)
        f.pack(pady=8)
        return f

    def _frame_tab(self):
        outer = tk.LabelFrame(self.frame, text="  Registos  ",
                              font=F_TITULO, bg=C_FRAME, fg=C_TEXTO,
                              relief="solid", bd=1, labelanchor="nw")
        outer.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))
        inner = tk.Frame(outer, bg=C_FRAME)
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        return inner

    # ── Helpers de feedback ───────────────────────────────────
    def ok(self, msg):
        log.info(msg)
        self.set_status(msg, "ok")

    def erro(self, msg):
        log.error(msg)
        self.set_status(str(msg), "erro")
        messagebox.showerror("Erro", str(msg))

    def aviso(self, msg):
        log.warning(msg)
        self.set_status(str(msg), "aviso")
        messagebox.showwarning("Aviso", str(msg))

    def confirmar(self, msg):
        return messagebox.askyesno("Confirmação", msg)

    def pedir(self, titulo, prompt, show=None):
        return simpledialog.askstring(titulo, prompt, show=show, parent=self.frame)


# ══════════════════════════════════════════════════════════════
# TAB — MINHA CONTA
# ══════════════════════════════════════════════════════════════

class TabMinhaConta(Tab):
    def _construir(self):
        # ── Info ──────────────────────────────────────────────
        frm_info = self._lf("Informações da Conta")
        frm_info.configure(bg=C_FRAME)

        dados = [
            ("ID",   self.conta["id"]),
            ("Nome", self.conta["nome"]),
            ("NIF",  self.conta["nif"]),
        ]
        for i, (label, valor) in enumerate(dados):
            tk.Label(frm_info, text=f"{label}:", font=F_BOLD,
                     bg=C_FRAME, fg=C_MUTED).grid(row=i, column=0, sticky="e", padx=(20,8), pady=6)
            tk.Label(frm_info, text=valor, font=F_NORMAL,
                     bg=C_FRAME, fg=C_TEXTO).grid(row=i, column=1, sticky="w", padx=(0,20))

        # ── Saldo ─────────────────────────────────────────────
        _, saldo = calcular_saldo(self.conta["id"])
        _, rec, desp = totais(self.conta["id"])
        cor_saldo = C_SUCCESS if saldo >= 0 else C_ERROR

        frm_saldo = self._lf("Resumo Financeiro")
        frm_saldo.configure(bg=C_FRAME)

        self.lbl_saldo    = tk.Label(frm_saldo, text=f"{saldo:.2f}€",   font=("Helvetica", 22, "bold"), bg=C_FRAME, fg=cor_saldo)
        self.lbl_receitas = tk.Label(frm_saldo, text=f"▲ {rec:.2f}€",  font=F_BOLD, bg=C_FRAME, fg=C_SUCCESS)
        self.lbl_despesas = tk.Label(frm_saldo, text=f"▼ {desp:.2f}€", font=F_BOLD, bg=C_FRAME, fg=C_ERROR)

        tk.Label(frm_saldo, text="Saldo atual:", font=F_BOLD, bg=C_FRAME, fg=C_MUTED
                 ).grid(row=0, column=0, sticky="e", padx=(20, 8), pady=8)
        self.lbl_saldo.grid(row=0, column=1, sticky="w")

        tk.Label(frm_saldo, text="Receitas:", font=F_BOLD, bg=C_FRAME, fg=C_MUTED
                 ).grid(row=1, column=0, sticky="e", padx=(20, 8), pady=4)
        self.lbl_receitas.grid(row=1, column=1, sticky="w")

        tk.Label(frm_saldo, text="Despesas:", font=F_BOLD, bg=C_FRAME, fg=C_MUTED
                 ).grid(row=2, column=0, sticky="e", padx=(20, 8), pady=4)
        self.lbl_despesas.grid(row=2, column=1, sticky="w")

        tk.Button(frm_saldo, text="↻  Atualizar", font=F_BTN, command=self._atualizar_saldo,
                  bg="#dfe6e9", fg=C_TEXTO, relief="flat", cursor="hand2", padx=8
                  ).grid(row=3, column=0, columnspan=2, pady=(10, 6))

        # ── Ações ─────────────────────────────────────────────
        frm_acoes = self._lf("Ações")
        frm_acoes.configure(bg=C_FRAME)

        f = tk.Frame(frm_acoes, bg=C_FRAME)
        f.pack(padx=10, pady=10)
        _btn(f, "Alterar PIN",      self._alterar_pin,   "atualizar", width=16).pack(side=tk.LEFT, padx=6)
        _btn(f, "Eliminar Conta",   self._eliminar,      "remover",   width=16).pack(side=tk.LEFT, padx=6)

    def _atualizar_saldo(self):
        _, saldo    = calcular_saldo(self.conta["id"])
        _, rec, desp = totais(self.conta["id"])
        cor = C_SUCCESS if saldo >= 0 else C_ERROR
        self.lbl_saldo.config(text=f"{saldo:.2f}€", fg=cor)
        self.lbl_receitas.config(text=f"▲ {rec:.2f}€")
        self.lbl_despesas.config(text=f"▼ {desp:.2f}€")
        self.ok("Saldo atualizado.")

    def _alterar_pin(self):
        p_atual = self.pedir("Alterar PIN", "PIN atual:", show="*")
        if p_atual is None: return
        p_novo  = self.pedir("Alterar PIN", "Novo PIN (4 dígitos):", show="*")
        if p_novo is None: return
        code, obj = atualizar_pin(self.conta["id"], p_atual, p_novo)
        if code == 200:
            self.conta["pin"] = p_novo
            self.ok("PIN atualizado com sucesso.")
        else:
            self.erro(obj)

    def _eliminar(self):
        pin = self.pedir("Eliminar Conta", "Insira o seu PIN para confirmar:", show="*")
        if pin is None: return
        if not self.confirmar("Esta ação é irreversível.\nTem a certeza que pretende eliminar a sua conta?"):
            return
        code, obj = eliminar_conta(self.conta["id"], pin)
        if code == 200:
            self.ok(f"Conta eliminada → {self.conta['id']}")
            messagebox.showinfo("Conta eliminada", "A sua conta foi eliminada. A aplicação vai fechar.")
            self.frame.winfo_toplevel().destroy()
        else:
            self.erro(obj)

    def _limpar(self): pass
    def _carregar(self): pass


# ══════════════════════════════════════════════════════════════
# TAB — TRANSAÇÕES
# ══════════════════════════════════════════════════════════════

class TabTransacoes(Tab):
    def _construir(self):
        frm = self._lf("Formulário — Transação")
        self.e_id        = _label_entry(frm, "ID",            0, col=0, readonly=True)
        self.cb_tipo     = _label_combo(frm, "Tipo",          1, col=0, values=("receita", "despesa"))
        self.e_descricao = _label_entry(frm, "Descrição",     2, col=0)
        self.e_valor     = _label_entry(frm, "Valor (€)",     3, col=0)
        self.cb_cat      = _label_combo(frm, "Categoria",     0, col=1, values=CATEGORIAS_TRANSACAO)
        self.e_id_orc    = _label_entry(frm, "ID Orçamento",  1, col=1)

        # ID Conta — preenchido e bloqueado com a conta autenticada
        tk.Label(frm, text="ID Conta", font=F_NORMAL, bg=C_FRAME, fg=C_MUTED, anchor="e"
                 ).grid(row=2, column=2, sticky="e", padx=(12, 6), pady=5)
        self.e_id_conta = tk.Entry(frm, width=24, font=F_NORMAL, state="readonly",
                                   relief="solid", bd=1, bg="#f0f0f0")
        self.e_id_conta.grid(row=2, column=3, sticky="w", padx=(0, 16), pady=5)
        _set(self.e_id_conta, self.conta["id"], readonly=True)

        frm_btn = self._frame_btn()
        for txt, cmd, tipo in [
            ("Adicionar", self._adicionar, "criar"),
            ("Consultar", self._consultar, "consultar"),
            ("Editar",    self._editar,    "atualizar"),
            ("Apagar",    self._apagar,    "remover"),
            ("Limpar",    self._limpar,    "limpar"),
        ]:
            _btn(frm_btn, txt, cmd, tipo).pack(side=tk.LEFT, padx=5)

        frm_tab = self._frame_tab()
        self.tabela = _treeview(frm_tab,
            ("ID", "Tipo", "Descrição", "Valor", "Categoria"),
            [130, 90, 220, 100, 150])
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar)
        self._carregar()

    def _adicionar(self):
        tipo  = self.cb_tipo.get()
        valor = self.e_valor.get()
        id_orc = self.e_id_orc.get() or None

        code, obj = adicionar_transacao(
            tipo, self.e_descricao.get(), valor,
            self.cb_cat.get(), self.conta["id"], id_orc,
        )
        if code != 201:
            return self.erro(obj)

        # Registar gasto no orçamento se for despesa
        if tipo == "despesa" and id_orc:
            code_o, msg_o = registar_gasto(id_orc, valor)
            if code_o == 200:
                if "AVISO" in str(msg_o):
                    self.aviso(msg_o)
                else:
                    self.ok(f"Transação adicionada → {obj['id']}  |  {msg_o}")
            else:
                self.ok(f"Transação adicionada → {obj['id']} (orçamento não atualizado: {msg_o})")
        else:
            self.ok(f"Transação adicionada → {obj['id']}")

        self._limpar(); self._carregar()

    def _consultar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione uma transação.")
        code, obj = encontrar_transacao(uid)
        if code == 200:
            self.ok(f"Transação consultada → {uid}")
            messagebox.showinfo("Transação",
                f"ID: {obj['id']}\nTipo: {obj['tipo']}\n"
                f"Descrição: {obj['descricao']}\nValor: {obj['valor']:.2f}€\n"
                f"Categoria: {obj['categoria']}\nID Orçamento: {obj['id_orcamento'] or '—'}")
        else:
            self.erro(obj)

    def _editar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione uma transação.")
        code, obj = editar_transacao(
            uid,
            descricao=self.e_descricao.get() or None,
            valor=self.e_valor.get() or None,
            categoria=self.cb_cat.get() or None,
            id_orcamento=self.e_id_orc.get() or None,
        )
        if code == 200:
            self.ok(f"Transação atualizada → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _apagar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione uma transação.")
        if not self.confirmar("Tem a certeza que pretende apagar esta transação?"):
            return
        code, obj = apagar_transacao(uid)
        if code == 200:
            self.ok(f"Transação apagada → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _carregar(self):
        _limpar_tree(self.tabela)
        code, obj = listar_transacoes(id_conta=self.conta["id"])
        if code == 200:
            for t in obj:
                _inserir_linha(self.tabela, (
                    t["id"], t["tipo"], t["descricao"],
                    f"{t['valor']:.2f}€", t["categoria"],
                ))

    def _limpar(self):
        _clear(self.e_id, self.cb_tipo, self.e_descricao,
               self.e_valor, self.cb_cat, self.e_id_orc)

    def _selecionar(self, _):
        sel = self.tabela.focus()
        if not sel: return
        v = self.tabela.item(sel, "values")
        _set(self.e_id, v[0], readonly=True)
        self.cb_tipo.set(v[1])
        _set(self.e_descricao, v[2])
        _set(self.e_valor, v[3].replace("€", ""))
        self.cb_cat.set(v[4])


# ══════════════════════════════════════════════════════════════
# TAB — ORÇAMENTOS
# ══════════════════════════════════════════════════════════════

class TabOrcamentos(Tab):
    def _construir(self):
        frm = self._lf("Formulário — Orçamento")
        self.e_id      = _label_entry(frm, "ID",         0, col=0, readonly=True)
        self.cb_cat    = _label_combo(frm, "Categoria",  1, col=0, values=CATEGORIAS_ORCAMENTO)
        self.e_limite  = _label_entry(frm, "Limite (€)", 2, col=0)
        self.cb_period = _label_combo(frm, "Período",    3, col=0, values=PERIODOS)

        frm_btn = self._frame_btn()
        for txt, cmd, tipo in [
            ("Criar",     self._criar,     "criar"),
            ("Consultar", self._consultar, "consultar"),
            ("Atualizar", self._atualizar, "atualizar"),
            ("Remover",   self._remover,   "remover"),
            ("Limpar",    self._limpar,    "limpar"),
        ]:
            _btn(frm_btn, txt, cmd, tipo).pack(side=tk.LEFT, padx=5)

        frm_tab = self._frame_tab()
        self.tabela = _treeview(frm_tab,
            ("ID", "Categoria", "Limite", "Período", "Gasto Atual", "Restante"),
            [120, 160, 100, 100, 110, 110])
        self.tabela.tag_configure("excedido", background="#ffe0e0", foreground="#c0392b")
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar)
        self._carregar()

    def _criar(self):
        code, obj = criar_orcamento(self.cb_cat.get(), self.e_limite.get(), self.cb_period.get())
        if code == 201:
            self.ok(f"Orçamento criado → {obj['id']}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _consultar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um orçamento.")
        code, obj = consultar_orcamento(uid)
        if code == 200:
            restante = obj["limite"] - obj["gasto_atual"]
            self.ok(f"Orçamento consultado → {uid}")
            messagebox.showinfo("Orçamento",
                f"ID: {obj['id']}\nCategoria: {obj['categoria']}\n"
                f"Limite: {obj['limite']:.2f}€\nPeríodo: {obj['periodo']}\n"
                f"Gasto atual: {obj['gasto_atual']:.2f}€\nRestante: {restante:.2f}€")
        else:
            self.erro(obj)

    def _atualizar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um orçamento.")
        code, obj = atualizar_orcamento(
            uid,
            limite=self.e_limite.get() or None,
            categoria=self.cb_cat.get() or None,
            periodo=self.cb_period.get() or None,
        )
        if code == 200:
            self.ok(f"Orçamento atualizado → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _remover(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um orçamento.")
        if not self.confirmar("Tem a certeza que pretende remover este orçamento?"):
            return
        code, obj = remover_orcamento(uid)
        if code == 200:
            self.ok(f"Orçamento removido → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _carregar(self):
        _limpar_tree(self.tabela)
        code, obj = listar_orcamentos()
        if code == 200:
            for oid, d in obj.items():
                restante = d["limite"] - d["gasto_atual"]
                excedido = restante < 0
                tag = "excedido" if excedido else ("par" if len(self.tabela.get_children()) % 2 == 0 else "impar")
                self.tabela.insert("", tk.END, tags=(tag,), values=(
                    oid, d["categoria"],
                    f"{d['limite']:.2f}€", d["periodo"],
                    f"{d['gasto_atual']:.2f}€",
                    f"{restante:.2f}€",
                ))

    def _limpar(self):
        _clear(self.e_id, self.cb_cat, self.e_limite, self.cb_period)

    def _selecionar(self, _):
        sel = self.tabela.focus()
        if not sel: return
        v = self.tabela.item(sel, "values")
        _set(self.e_id, v[0], readonly=True)
        self.cb_cat.set(v[1])
        _set(self.e_limite, v[2].replace("€", ""))
        self.cb_period.set(v[3])


# ══════════════════════════════════════════════════════════════
# TAB — PAGAMENTOS
# ══════════════════════════════════════════════════════════════

class TabPagamentos(Tab):
    def _construir(self):
        frm = self._lf("Formulário — Pagamento")
        self.e_id        = _label_entry(frm, "ID",               0, col=0, readonly=True)
        self.e_descricao = _label_entry(frm, "Descrição",        1, col=0)
        self.e_valor     = _label_entry(frm, "Valor (€)",        2, col=0)
        self.e_data      = _label_entry(frm, "Data (YYYY-MM-DD)", 3, col=0)
        self.cb_metodo   = _label_combo(frm, "Método",           0, col=1, values=METODOS_PAG)
        self.e_id_trans  = _label_entry(frm, "ID Transação",     1, col=1)

        # Sugestão de data de hoje
        _set(self.e_data, datetime.now().strftime("%Y-%m-%d"))

        frm_btn = self._frame_btn()
        for txt, cmd, tipo in [
            ("Criar",     self._criar,     "criar"),
            ("Consultar", self._consultar, "consultar"),
            ("Atualizar", self._atualizar, "atualizar"),
            ("Remover",   self._remover,   "remover"),
            ("Limpar",    self._limpar,    "limpar"),
        ]:
            _btn(frm_btn, txt, cmd, tipo).pack(side=tk.LEFT, padx=5)

        frm_tab = self._frame_tab()
        self.tabela = _treeview(frm_tab,
            ("ID", "Descrição", "Valor", "Data", "Método", "ID Transação"),
            [120, 200, 90, 110, 120, 130])
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar)
        self._carregar()

    def _criar(self):
        code, obj = criar_pagamento(
            self.e_descricao.get(), self.e_valor.get(),
            self.e_data.get(), self.cb_metodo.get(),
            self.e_id_trans.get() or None,
        )
        if code == 201:
            self.ok(f"Pagamento criado → {obj['id']}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _consultar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um pagamento.")
        code, obj = consultar_pagamento(uid)
        if code == 200:
            self.ok(f"Pagamento consultado → {uid}")
            messagebox.showinfo("Pagamento",
                f"ID: {obj['id']}\nDescrição: {obj['descricao']}\n"
                f"Valor: {obj['valor']:.2f}€\nData: {obj['data']}\n"
                f"Método: {obj['metodo']}\nID Transação: {obj['id_transacao'] or '—'}")
        else:
            self.erro(obj)

    def _atualizar(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um pagamento.")
        code, obj = atualizar_pagamento(
            uid,
            descricao=self.e_descricao.get() or None,
            valor=self.e_valor.get() or None,
            data=self.e_data.get() or None,
            metodo=self.cb_metodo.get() or None,
            id_transacao=self.e_id_trans.get() or None,
        )
        if code == 200:
            self.ok(f"Pagamento atualizado → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _remover(self):
        uid = self.e_id.get()
        if not uid: return self.aviso("Selecione um pagamento.")
        if not self.confirmar("Tem a certeza que pretende remover este pagamento?"):
            return
        code, obj = remover_pagamento(uid)
        if code == 200:
            self.ok(f"Pagamento removido → {uid}")
            self._limpar(); self._carregar()
        else:
            self.erro(obj)

    def _carregar(self):
        _limpar_tree(self.tabela)
        code, obj = listar_pagamentos()
        if code == 200:
            for pid, d in obj.items():
                _inserir_linha(self.tabela, (
                    pid, d["descricao"], f"{d['valor']:.2f}€",
                    d["data"], d["metodo"], d["id_transacao"] or "—",
                ))

    def _limpar(self):
        _clear(self.e_id, self.e_descricao, self.e_valor,
               self.e_data, self.cb_metodo, self.e_id_trans)
        _set(self.e_data, datetime.now().strftime("%Y-%m-%d"))

    def _selecionar(self, _):
        sel = self.tabela.focus()
        if not sel: return
        v = self.tabela.item(sel, "values")
        _set(self.e_id, v[0], readonly=True)
        _set(self.e_descricao, v[1])
        _set(self.e_valor, v[2].replace("€", ""))
        _set(self.e_data, v[3])
        self.cb_metodo.set(v[4])
        _set(self.e_id_trans, "" if v[5] == "—" else v[5])


# ══════════════════════════════════════════════════════════════
# FRAME DE LOGIN
# ══════════════════════════════════════════════════════════════

class LoginFrame(tk.Frame):
    def __init__(self, root, on_login):
        super().__init__(root, bg=C_DARK)
        self.on_login = on_login
        self._construir()

    def _construir(self):
        # Card central
        card = tk.Frame(self, bg=C_FRAME, relief="flat", bd=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=460)

        # Topo colorido do card
        top = tk.Frame(card, bg=C_ACCENT, height=8)
        top.pack(fill=tk.X)

        # Ícone e título
        tk.Label(card, text="💰", font=("Helvetica", 36), bg=C_FRAME
                 ).pack(pady=(30, 4))
        tk.Label(card, text="Gestão Financeira", font=F_GRANDE,
                 bg=C_FRAME, fg=C_DARK).pack()
        tk.Label(card, text="Inicie sessão para continuar", font=F_SMALL,
                 bg=C_FRAME, fg=C_MUTED).pack(pady=(4, 24))

        ttk.Separator(card).pack(fill=tk.X, padx=30)

        # Campos
        frm = tk.Frame(card, bg=C_FRAME)
        frm.pack(padx=30, pady=20, fill=tk.X)

        tk.Label(frm, text="ID da Conta", font=F_BOLD, bg=C_FRAME, fg=C_TEXTO,
                 anchor="w").pack(fill=tk.X)
        self.e_id = tk.Entry(frm, font=F_NORMAL, relief="solid", bd=1, width=30)
        self.e_id.pack(fill=tk.X, pady=(4, 14), ipady=6)

        tk.Label(frm, text="PIN", font=F_BOLD, bg=C_FRAME, fg=C_TEXTO,
                 anchor="w").pack(fill=tk.X)
        self.e_pin = tk.Entry(frm, font=F_NORMAL, relief="solid", bd=1,
                              show="*", width=30)
        self.e_pin.pack(fill=tk.X, pady=(4, 4), ipady=6)
        self.e_pin.bind("<Return>", lambda e: self._login())

        # Mensagem de erro inline
        self.lbl_erro = tk.Label(frm, text="", font=F_SMALL, bg=C_FRAME, fg=C_ERROR)
        self.lbl_erro.pack(fill=tk.X)

        # Botões
        frm_btn = tk.Frame(card, bg=C_FRAME)
        frm_btn.pack(padx=30, fill=tk.X)
        _btn(frm_btn, "Entrar",         self._login,    "login",    width=16).pack(fill=tk.X, ipady=4, pady=(4, 6))
        _btn(frm_btn, "Criar Conta",    self._registar, "registar", width=16).pack(fill=tk.X, ipady=4)

    def _login(self):
        uid = self.e_id.get().strip()
        pin = self.e_pin.get().strip()

        if not uid or not pin:
            self._mostrar_erro("Preencha o ID e o PIN.")
            return

        log.info("AUTH tentativa de login | id=%s", uid)
        code, obj = verificar_login(uid, pin)

        if code == 200:
            log.info("AUTH login bem-sucedido | id=%s | nome=%s", uid, obj["nome"])
            self.on_login(obj)
        else:
            log.error("AUTH login falhado | id=%s | motivo=%s", uid, obj)
            self._mostrar_erro(str(obj))

    def _registar(self):
        # Janela de registo
        win = tk.Toplevel(self)
        win.title("Criar Conta")
        win.geometry("340x320")
        win.resizable(False, False)
        win.configure(bg=C_FRAME)
        win.grab_set()

        tk.Label(win, text="Nova Conta", font=F_TITULO, bg=C_FRAME, fg=C_DARK
                 ).pack(pady=(20, 4))
        tk.Label(win, text="Preencha os dados abaixo", font=F_SMALL, bg=C_FRAME, fg=C_MUTED
                 ).pack(pady=(0, 16))

        frm = tk.Frame(win, bg=C_FRAME)
        frm.pack(padx=30, fill=tk.X)

        for label, attr, kw in [
            ("Nome",            "r_nome", {}),
            ("NIF (9 dígitos)", "r_nif",  {}),
            ("PIN (4 dígitos)", "r_pin",  {"show": "*"}),
        ]:
            tk.Label(frm, text=label, font=F_BOLD, bg=C_FRAME, fg=C_TEXTO,
                     anchor="w").pack(fill=tk.X, pady=(6, 0))
            e = tk.Entry(frm, font=F_NORMAL, relief="solid", bd=1, **kw)
            e.pack(fill=tk.X, ipady=5)
            setattr(self, attr, e)

        lbl_r_erro = tk.Label(win, text="", font=F_SMALL, bg=C_FRAME, fg=C_ERROR)
        lbl_r_erro.pack(pady=4)

        def _submeter():
            code, obj = criar_conta(self.r_nome.get(), self.r_nif.get(), self.r_pin.get())
            if code == 201:
                log.info("AUTH nova conta criada | id=%s | nome=%s", obj["id"], obj["nome"])
                win.destroy()
                messagebox.showinfo("Conta criada",
                    f"Conta criada com sucesso!\n\nO seu ID é:\n{obj['id']}\n\nGuarde-o para fazer login.")
            else:
                log.error("AUTH criar conta falhado | motivo=%s", obj)
                lbl_r_erro.config(text=str(obj))

        _btn(tk.Frame(win, bg=C_FRAME).pack(fill=tk.X, padx=30) or win,
             "Criar Conta", _submeter, "criar", width=20
             ).pack(fill=tk.X, padx=30, ipady=4, pady=4)

    def _mostrar_erro(self, msg):
        self.lbl_erro.config(text=msg)
        self.after(4000, lambda: self.lbl_erro.config(text=""))


# ══════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ══════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gestão Financeira")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=C_DARK)
        _aplicar_estilos(self.root)

        self._frame_atual = None
        self._mostrar_login()
        log.info("APP iniciada")
        self.root.mainloop()

    # ── Navegação login ↔ app ─────────────────────────────────
    def _mostrar_login(self):
        if self._frame_atual:
            self._frame_atual.destroy()
        lf = LoginFrame(self.root, on_login=self._abrir_app)
        lf.pack(fill=tk.BOTH, expand=True)
        self._frame_atual = lf

    def _abrir_app(self, conta):
        if self._frame_atual:
            self._frame_atual.destroy()
        mf = MainFrame(self.root, conta, on_logout=self._mostrar_login)
        mf.pack(fill=tk.BOTH, expand=True)
        self._frame_atual = mf


# ══════════════════════════════════════════════════════════════
# FRAME PRINCIPAL (após login)
# ══════════════════════════════════════════════════════════════

class MainFrame(tk.Frame):
    def __init__(self, root, conta, on_logout):
        super().__init__(root, bg=C_BG)
        self.conta     = conta
        self.on_logout = on_logout
        self._construir()

    def _construir(self):
        self._construir_header()
        self._construir_notebook()
        self._construir_statusbar()

    def _construir_header(self):
        hdr = tk.Frame(self, bg=C_DARK, height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="💰  Gestão Financeira",
                 bg=C_DARK, fg="white", font=("Helvetica", 14, "bold")
                 ).pack(side=tk.LEFT, padx=20, pady=14)

        # Logout
        def _logout():
            if messagebox.askyesno("Logout", "Tem a certeza que pretende sair?"):
                log.info("AUTH logout | id=%s", self.conta["id"])
                self.on_logout()

        tk.Button(hdr, text="⎋  Sair", command=_logout,
                  bg=C_ACCENT, fg="white", relief="flat",
                  font=F_BTN, cursor="hand2", padx=12, pady=6
                  ).pack(side=tk.RIGHT, padx=16, pady=10)

        # Utilizador
        tk.Label(hdr, text=f"👤  {self.conta['nome']}",
                 bg=C_DARK, fg="#a0aec0", font=F_SMALL
                 ).pack(side=tk.RIGHT, padx=4)

        # Relógio
        self.lbl_hora = tk.Label(hdr, text="", bg=C_DARK, fg="#636e72", font=F_SMALL)
        self.lbl_hora.pack(side=tk.RIGHT, padx=16)
        self._tick()

    def _tick(self):
        self.lbl_hora.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        self.after(1000, self._tick)

    def _construir_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)
        ss = self._set_status
        TabMinhaConta(nb,  "Minha Conta",  self.conta, ss)
        TabTransacoes(nb,  "Transações",   self.conta, ss)
        TabOrcamentos(nb,  "Orçamentos",   self.conta, ss)
        TabPagamentos(nb,  "Pagamentos",   self.conta, ss)

    def _construir_statusbar(self):
        bar = tk.Frame(self, bg="#2d3436", height=30)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self._status_icon = tk.Label(bar, text="●", bg="#2d3436", fg=C_SUCCESS,
                                     font=("Helvetica", 11))
        self._status_icon.pack(side=tk.LEFT, padx=(12, 4), pady=5)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(bar, textvariable=self._status_var, bg="#2d3436",
                 fg="#dfe6e9", font=F_SMALL, anchor="w"
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(bar, text="Gestão Financeira  v1.0",
                 bg="#2d3436", fg="#636e72", font=("Helvetica", 8)
                 ).pack(side=tk.RIGHT, padx=12)

    def _set_status(self, msg, tipo="ok"):
        cores = {"ok": C_SUCCESS, "erro": C_ERROR, "aviso": C_WARN}
        self._status_icon.config(fg=cores.get(tipo, C_SUCCESS))
        self._status_var.set(f"  {msg}")


# ══════════════════════════════════════════════════════════════
# ENTRADA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    App()