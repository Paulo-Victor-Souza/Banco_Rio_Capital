from datetime import datetime
from decimal import Decimal, InvalidOperation
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
import pyodbc
try:
    from fpdf import FPDF

    FPDF_DISPONIVEL = True
except ImportError:
    FPDF_DISPONIVEL = False

# ==========================================================
# BANCO RIO CAPITAL
# Aplicação académica com Tkinter e SQL Server
# ==========================================================

# CONFIGURAÇÃO DA BASE DE DADOS
SERVIDOR = "DESKTOP-SOUZA"
BASE_DADOS = "BANCO"
TABELA = "dbo.CONTA"

# ==========================================================
# ESTADO DA APLICAÇÃO
# ==========================================================

conta_atual = None
contas = []
movimentos = []
notificacoes = []


# ==========================================================
# LIGAÇÃO À BASE DE DADOS
# ==========================================================

def conectar():
    """Abre uma ligação ao SQL Server."""
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVIDOR};"
        f"DATABASE={BASE_DADOS};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;",
        timeout=10
    )


def carregar_contas():
    """Carrega as contas existentes na tabela SQL."""
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT ID, NOME, SALDO
                FROM dbo.CONTA
                ORDER BY ID
            """)
            return cursor.fetchall()

    except pyodbc.Error as erro:
        messagebox.showerror(
            "Erro de ligação SQL Server",
            f"Não foi possível carregar as contas.\n\n{erro}"
        )
        return []


def atualizar_dados_da_conta():
    """Volta a consultar no SQL Server os dados da conta selecionada."""
    global conta_atual

    if conta_atual is None:
        return False

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT ID, NOME, SALDO
                FROM dbo.CONTA
                WHERE ID = ?
            """, (conta_atual["id"],))
            linha = cursor.fetchone()

        if linha is None:
            messagebox.showerror(
                "Conta não encontrada",
                "A conta não existe na base de dados."
            )
            return False

        conta_atual = {
            "id": linha[0],
            "nome": linha[1],
            "saldo": Decimal(str(linha[2]))
        }

        carregar_cabecalho()
        atualizar_saldo()
        return True

    except pyodbc.Error as erro:
        messagebox.showerror(
            "Erro SQL",
            f"Não foi possível atualizar os dados.\n\n{erro}"
        )
        return False


# ==========================================================
# FORMATAÇÃO E ATUALIZAÇÃO DA INTERFACE
# ==========================================================

def formatar_euros(valor):
    """Formata um valor monetário com duas casas decimais."""
    return f"{Decimal(str(valor)):.2f} EUR"


def carregar_conta(event=None):
    """Atualiza a conta selecionada no seletor."""
    global conta_atual

    indice = seletor_contas.current()

    if indice < 0 or indice >= len(contas):
        return

    linha = contas[indice]
    conta_atual = {
        "id": linha[0],
        "nome": linha[1],
        "saldo": Decimal(str(linha[2]))
    }

    carregar_cabecalho()
    atualizar_saldo()


def carregar_cabecalho():
    """Apresenta o nome e o número da conta selecionada."""
    if conta_atual is None:
        return

    label_cliente.config(text=f"Olá, {conta_atual['nome']}")
    label_numero.config(text=f"Conta n.º {conta_atual['id']}")


def atualizar_saldo():
    """Atualiza o saldo apresentado na janela principal."""
    if conta_atual is not None:
        label_saldo.config(text=formatar_euros(conta_atual["saldo"]))


# ==========================================================
# CONSULTA DE SALDO E EXTRATO PDF (FPDF)
# ==========================================================

def consultar_saldo():
    if atualizar_dados_da_conta():
        messagebox.showinfo(
            "Saldo",
            f"Saldo disponível:\n\n"
            f"{formatar_euros(conta_atual['saldo'])}"
        )


def gerar_extrato_pdf():
    """Gera um PDF diretamente com a biblioteca FPDF e abre-o automaticamente."""
    if conta_atual is None:
        messagebox.showwarning("Atenção", "Selecione uma conta primeiro.")
        return

    if not FPDF_DISPONIVEL:
        messagebox.showerror(
            "Biblioteca em falta",
            "A biblioteca 'fpdf2' não está instalada.\n\n"
            "Execute no terminal:\npip install fpdf2"
        )
        return

    ficheiro = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        initialfile=f"extrato_conta_{conta_atual['id']}.pdf"
    )

    if not ficheiro:
        return

    try:
        pdf = FPDF()
        pdf.add_page()

        # Cabeçalho
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(11, 31, 58)  # #0B1F3A
        pdf.cell(0, 10, "BANCO RIO CAPITAL", 0, 1, "C")

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, "Extrato Mensal de Movimentos (Sessão Atual)", 0, 1, "C")
        pdf.ln(10)

        # Informações da Conta
        pdf.set_fill_color(233, 238, 245)  # #E9EEF5
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(11, 31, 58)
        pdf.cell(190, 8, f" Titular: {conta_atual['nome']}     |     Conta N.o: {conta_atual['id']}", 0, 1, "L", True)
        pdf.cell(190, 8,
                 f" Saldo Atual: {formatar_euros(conta_atual['saldo'])}     |     Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 0, 1, "L", True)
        pdf.ln(10)

        # Tabela de Movimentos
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(11, 31, 58)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 8, " Historico de Movimentos", 0, 1, "L", True)

        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(50, 50, 50)

        if not movimentos:
            pdf.set_fill_color(249, 250, 251)
            pdf.cell(190, 8, " Ainda não existem movimentos registados nesta sessão.", 0, 1, "L", True)
        else:
            alternar = False
            for mov in reversed(movimentos):
                if alternar:
                    pdf.set_fill_color(249, 250, 251)
                else:
                    pdf.set_fill_color(255, 255, 255)

                texto_seguro = str(mov).replace("€", "EUR").encode("latin-1", "replace").decode("latin-1")
                pdf.cell(190, 8, f" {texto_seguro}", 0, 1, "L", True)
                alternar = not alternar

        # Rodapé do PDF
        pdf.set_y(-25)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(122, 134, 154)
        pdf.cell(0, 10, "Banco Rio Capital - Documento gerado para efeitos académicos e de simulação.", 0, 0, "C")

        pdf.output(ficheiro)

        # Abre o PDF automaticamente no leitor padrão do sistema
        try:
            webbrowser.open(os.path.abspath(ficheiro))
        except Exception:
            pass

        messagebox.showinfo(
            "Extrato Gerado",
            f"O PDF foi gerado e aberto com sucesso!"
        )

    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Não foi possível gerar o PDF:\n\n{e}"
        )


# ==========================================================
# DEPÓSITOS E LEVANTAMENTOS
# ==========================================================

def movimentar_saldo(tipo):
    """Executa um depósito ou levantamento no SQL Server."""
    if conta_atual is None:
        messagebox.showwarning(
            "Atenção",
            "Selecione uma conta primeiro."
        )
        return

    texto = entrada_valor.get().strip().replace(",", ".")

    try:
        valor = Decimal(texto)

        if not valor.is_finite() or valor <= 0:
            raise InvalidOperation

        valor = valor.quantize(Decimal("0.01"))

    except (InvalidOperation, ValueError):
        messagebox.showerror(
            "Valor inválido",
            "Introduza um valor monetário válido e superior a zero."
        )
        return

    if tipo == "LEVANTAMENTO":
        sql = """
            UPDATE dbo.CONTA
            SET SALDO = SALDO - ?
            WHERE ID = ? AND SALDO >= ?
        """
        parametros = (valor, conta_atual["id"], valor)
    else:
        sql = """
            UPDATE dbo.CONTA
            SET SALDO = SALDO + ?
            WHERE ID = ?
        """
        parametros = (valor, conta_atual["id"])

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(sql, parametros)

            if cursor.rowcount != 1:
                conexao.rollback()

                if tipo == "LEVANTAMENTO":
                    messagebox.showerror(
                        "Operação não realizada",
                        "Saldo insuficiente ou conta inexistente."
                    )
                else:
                    messagebox.showerror(
                        "Erro",
                        "Não foi possível atualizar a conta."
                    )
                return

            conexao.commit()

        entrada_valor.delete(0, tk.END)

        if not atualizar_dados_da_conta():
            return

        descricao = f"{tipo.title()}: {formatar_euros(valor)}"
        movimentos.append(descricao)
        notificacoes.append(f"{descricao} realizado com sucesso.")

        messagebox.showinfo(
            tipo.title(),
            f"{tipo.title()} realizado com sucesso."
        )

    except pyodbc.Error as erro:
        messagebox.showerror(
            "Erro na base de dados",
            f"A operação não foi concluída.\n\n{erro}"
        )


def levantar():
    movimentar_saldo("LEVANTAMENTO")


def depositar():
    movimentar_saldo("DEPÓSITO")


# ==========================================================
# TRANSFERÊNCIAS
# ==========================================================

def transferir():
    """Transfere dinheiro entre duas contas na mesma transação SQL."""
    if conta_atual is None:
        messagebox.showwarning(
            "Atenção",
            "Selecione uma conta primeiro."
        )
        return

    destinos = [
        linha for linha in contas
        if linha[0] != conta_atual["id"]
    ]

    if not destinos:
        messagebox.showwarning(
            "Transferências",
            "Não existem outras contas para receber a transferência."
        )
        return

    janela_transf = tk.Toplevel(janela)
    janela_transf.title("Transferir dinheiro")
    janela_transf.geometry("420x260")
    janela_transf.configure(bg="#E9EEF5")
    janela_transf.transient(janela)
    janela_transf.grab_set()

    tk.Label(
        janela_transf,
        text="Conta destinatária",
        bg="#E9EEF5"
    ).pack(pady=(20, 5))

    seletor_destino = ttk.Combobox(
        janela_transf,
        state="readonly",
        width=38,
        values=[
            f"Conta ID {linha[0]} - {linha[1]}"
            for linha in destinos
        ]
    )
    seletor_destino.pack()
    seletor_destino.current(0)

    tk.Label(
        janela_transf,
        text="Valor a transferir (€)",
        bg="#E9EEF5"
    ).pack(pady=(15, 5))

    entrada_transf = tk.Entry(
        janela_transf,
        justify="center",
        font=("Arial", 12)
    )
    entrada_transf.pack()
    entrada_transf.focus_set()

    def confirmar_transferencia():
        try:
            valor = Decimal(
                entrada_transf.get().strip().replace(",", ".")
            )

            if not valor.is_finite() or valor <= 0:
                raise InvalidOperation

            valor = valor.quantize(Decimal("0.01"))

        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Valor inválido",
                "Introduza um valor superior a zero.",
                parent=janela_transf
            )
            return

        indice_destino = seletor_destino.current()
        if indice_destino < 0 or indice_destino >= len(destinos):
            messagebox.showerror(
                "Destino inválido",
                "Selecione uma conta destinatária válida.",
                parent=janela_transf
            )
            return

        destino = destinos[indice_destino]
        id_origem = conta_atual["id"]
        id_destino = destino[0]

        try:
            with conectar() as conexao:
                cursor = conexao.cursor()

                cursor.execute("""
                    UPDATE dbo.CONTA
                    SET SALDO = SALDO - ?
                    WHERE ID = ? AND SALDO >= ?
                """, (valor, id_origem, valor))

                if cursor.rowcount != 1:
                    conexao.rollback()
                    messagebox.showerror(
                        "Transferência não realizada",
                        "Saldo insuficiente ou conta de origem inexistente.",
                        parent=janela_transf
                    )
                    return

                cursor.execute("""
                    UPDATE dbo.CONTA
                    SET SALDO = SALDO + ?
                    WHERE ID = ?
                """, (valor, id_destino))

                if cursor.rowcount != 1:
                    conexao.rollback()
                    messagebox.showerror(
                        "Transferência não realizada",
                        "A conta destinatária não foi encontrada.",
                        parent=janela_transf
                    )
                    return

                conexao.commit()

            if not atualizar_dados_da_conta():
                messagebox.showwarning(
                    "Atenção",
                    "A transferência foi concluída, mas não foi possível "
                    "atualizar o saldo apresentado.",
                    parent=janela_transf
                )
                janela_transf.destroy()
                return

            descricao = (
                f"Transferência para conta {id_destino}: "
                f"{formatar_euros(valor)}"
            )
            movimentos.append(descricao)
            notificacoes.append(
                f"{descricao} realizada com sucesso."
            )

            janela_transf.destroy()

            messagebox.showinfo(
                "Transferência concluída",
                f"Valor: {formatar_euros(valor)}\n"
                f"Conta destinatária: {id_destino}"
            )

        except pyodbc.Error as erro:
            messagebox.showerror(
                "Erro na base de dados",
                f"A transferência não foi concluída.\n\n{erro}",
                parent=janela_transf
            )

    tk.Button(
        janela_transf,
        text="CONFIRMAR TRANSFERÊNCIA",
        command=confirmar_transferencia,
        bg="#176B87",
        fg="white",
        font=("Arial", 10, "bold"),
        bd=0,
        padx=12,
        pady=10
    ).pack(pady=20)


# ==========================================================
# MOVIMENTOS E NOTIFICAÇÕES
# ==========================================================

def consultar_movimentos():
    abrir_lista(
        "Movimentos",
        "📋 MOVIMENTOS",
        movimentos,
        "Ainda não existem movimentos nesta sessão."
    )


def mostrar_notificacoes():
    abrir_lista(
        "Notificações",
        "🔔 NOTIFICAÇÕES",
        notificacoes,
        "Não existem notificações nesta sessão."
    )


def abrir_lista(titulo_janela, titulo, dados, vazio):
    """Abre uma janela com uma lista de movimentos ou notificações."""
    top = tk.Toplevel(janela)
    top.title(titulo_janela)
    top.geometry("520x450")
    top.configure(bg="#E9EEF5")

    tk.Label(
        top,
        text=titulo,
        font=("Arial", 20, "bold"),
        bg="#0B1F3A",
        fg="white"
    ).pack(fill="x", ipady=18)

    lista = tk.Listbox(
        top,
        font=("Arial", 11),
        bg="white",
        fg="#0B1F3A",
        width=55,
        height=17
    )
    lista.pack(fill="both", expand=True, padx=15, pady=15)

    if not dados:
        lista.insert(tk.END, vazio)
    else:
        for item in reversed(dados):
            lista.insert(tk.END, item)


# ==========================================================
# INVESTIMENTOS E EDUCAÇÃO FINANCEIRA
# ==========================================================

def abrir_link(url):
    webbrowser.open(url)


def abrir_investimentos():
    abrir_janela_links(
        "Investimentos",
        [
            ("AÇÕES", "https://www.todoscontam.pt/"),
            ("ETFs", "https://www.todoscontam.pt/"),
            ("OBRIGAÇÕES", "https://www.todoscontam.pt/"),
            ("DEPÓSITOS A PRAZO", "https://www.todoscontam.pt/")
        ]
    )


def abrir_educacao():
    abrir_janela_links(
        "Educação Financeira",
        [
            ("GUIA DE EDUCAÇÃO FINANCEIRA",
             "https://www.todoscontam.pt/"),
            ("BANCO DE PORTUGAL",
             "https://www.bportugal.pt/"),
            ("CMVM",
             "https://www.cmvm.pt/")
        ]
    )


def abrir_janela_links(titulo, links):
    """Abre uma janela com ligações a recursos financeiros."""
    top = tk.Toplevel(janela)
    top.title(titulo)
    top.geometry("500x400")
    top.configure(bg="#E9EEF5")

    tk.Label(
        top,
        text=titulo.upper(),
        font=("Arial", 20, "bold"),
        bg="#0B1F3A",
        fg="white"
    ).pack(fill="x", ipady=18)

    for nome, url in links:
        tk.Button(
            top,
            text=nome,
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#0B1F3A",
            width=35,
            height=2,
            command=lambda u=url: abrir_link(u)
        ).pack(pady=8)


# ==========================================================
# SAIR DA APLICAÇÃO
# ==========================================================

def sair():
    if messagebox.askyesno(
            "Sair",
            "Deseja sair do Banco Rio Capital?"
    ):
        janela.destroy()


# ==========================================================
# CONSTRUÇÃO DA INTERFACE
# ==========================================================

def criar_botao(texto, cor, comando):
    """Cria um botão padronizado na janela principal."""
    tk.Button(
        janela,
        text=texto,
        font=("Arial", 10, "bold"),
        bg=cor,
        fg="white",
        activebackground="#245276",
        width=34,
        height=2,
        bd=0,
        cursor="hand2",
        command=comando
    ).pack(pady=4)


def construir_interface():
    """Cria e organiza os componentes da janela principal."""
    global janela
    global label_cliente, label_numero, label_saldo
    global seletor_contas, entrada_valor

    janela = tk.Tk()
    janela.title("Banco Rio Capital")
    janela.geometry("700x850")
    janela.resizable(False, False)
    janela.configure(bg="#E9EEF5")

    # Cabeçalho
    cabecalho = tk.Frame(janela, bg="#0B1F3A", height=125)
    cabecalho.pack(fill="x")
    cabecalho.pack_propagate(False)

    tk.Label(
        cabecalho,
        text="RC",
        font=("Arial", 20, "bold"),
        bg="#D4AF37",
        fg="#0B1F3A",
        width=4,
        height=2
    ).pack(side="left", padx=20, pady=20)

    tk.Label(
        cabecalho,
        text="BANCO RIO CAPITAL",
        font=("Arial", 21, "bold"),
        bg="#0B1F3A",
        fg="white"
    ).pack(side="left", padx=5)

    label_cliente = tk.Label(
        cabecalho,
        text="A carregar cliente...",
        font=("Arial", 10, "bold"),
        bg="#0B1F3A",
        fg="white"
    )
    label_cliente.place(relx=0.97, y=25, anchor="ne")

    label_numero = tk.Label(
        cabecalho,
        text="",
        font=("Arial", 9),
        bg="#0B1F3A",
        fg="#9FB3C8"
    )
    label_numero.place(relx=0.97, y=48, anchor="ne")

    tk.Button(
        cabecalho,
        text="🔔",
        font=("Arial", 14),
        bg="#0B1F3A",
        fg="white",
        bd=0,
        command=mostrar_notificacoes
    ).place(relx=0.77, y=35, anchor="center")

    # Seletor de contas
    tk.Label(
        janela,
        text="Selecionar conta",
        font=("Arial", 10, "bold"),
        bg="#E9EEF5",
        fg="#0B1F3A"
    ).pack(pady=(15, 3))

    seletor_contas = ttk.Combobox(
        janela,
        state="readonly",
        width=48
    )
    seletor_contas.pack()

    # Cartão de saldo
    frame_saldo = tk.Frame(
        janela,
        bg="white",
        width=540,
        height=130,
        highlightbackground="#D4AF37",
        highlightthickness=2
    )
    frame_saldo.pack(pady=18)
    frame_saldo.pack_propagate(False)

    tk.Label(
        frame_saldo,
        text="SALDO DISPONÍVEL",
        font=("Arial", 12, "bold"),
        bg="white",
        fg="#6B7280"
    ).pack(pady=(18, 3))

    label_saldo = tk.Label(
        frame_saldo,
        text="—",
        font=("Arial", 30, "bold"),
        bg="white",
        fg="#0B1F3A"
    )
    label_saldo.pack()

    # Campo de valor
    entrada_valor = tk.Entry(
        janela,
        font=("Arial", 14),
        justify="center",
        width=24
    )
    entrada_valor.pack(pady=5)

    tk.Label(
        janela,
        text="Valor para depósito ou levantamento",
        font=("Arial", 9),
        bg="#E9EEF5",
        fg="#777777"
    ).pack(pady=(0, 8))

    # Operações bancárias
    criar_botao("💳  CONSULTAR SALDO", "#0B1F3A", consultar_saldo)
    criar_botao("📄  EXTRATO MENSAL (PDF)", "#176B87", gerar_extrato_pdf)
    criar_botao("↓  LEVANTAR DINHEIRO", "#176B87", levantar)
    criar_botao("↑  DEPOSITAR DINHEIRO", "#176B87", depositar)
    criar_botao("💸  TRANSFERIR DINHEIRO", "#176B87", transferir)
    criar_botao("☰  CONSULTAR MOVIMENTOS", "#176B87", consultar_movimentos)

    # Recursos extra
    frame_extra = tk.Frame(janela, bg="#E9EEF5")
    frame_extra.pack(pady=8)

    tk.Button(
        frame_extra,
        text="📈 INVESTIMENTOS",
        font=("Arial", 9, "bold"),
        bg="#D4AF37",
        fg="#0B1F3A",
        width=19,
        height=2,
        command=abrir_investimentos
    ).grid(row=0, column=0, padx=5)

    tk.Button(
        frame_extra,
        text="📚 EDUCAÇÃO",
        font=("Arial", 9, "bold"),
        bg="#D4AF37",
        fg="#0B1F3A",
        width=19,
        height=2,
        command=abrir_educacao
    ).grid(row=0, column=1, padx=5)

    tk.Button(
        janela,
        text="✕  SAIR",
        font=("Arial", 10, "bold"),
        bg="#B42318",
        fg="white",
        width=34,
        height=2,
        command=sair
    ).pack(pady=7)

    tk.Label(
        janela,
        text="Banco Rio Capital • Simulação académica",
        font=("Arial", 8),
        bg="#E9EEF5",
        fg="#7A869A"
    ).pack(pady=3)

    seletor_contas.bind("<<ComboboxSelected>>", carregar_conta)


# ==========================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==========================================================

def main():
    global contas

    construir_interface()
    contas = carregar_contas()

    if contas:
        seletor_contas["values"] = [
            f"Conta ID {linha[0]} - {linha[1]}"
            for linha in contas
        ]
        seletor_contas.current(0)
        carregar_conta()
    else:
        label_cliente.config(text="Sem conta disponível")
        label_numero.config(text="")
        label_saldo.config(text="—")

    janela.mainloop()


if __name__ == "__main__":
    main()