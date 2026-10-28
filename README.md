# 🏦 Banco Rio Capital

> Aplicação desktop académica desenvolvida em **Python** com interface gráfica **Tkinter** e integração com base de dados relacional **SQL Server**.

## 📋 Sobre o Projeto
O **Banco Rio Capital** é uma simulação de sistema bancário que permite gerir contas de clientes, efetuar operações financeiras seguras (depósitos, levantamentos e transferências bancárias transacionais) e gerar extratos detalhados em **PDF**. O projeto foca-se em boas práticas de programação, precisão monetária (utilização de tipos decimais) e consistência de dados através de transações SQL.

---

## 📸 Capturas de Ecrã

### 1. Janela Principal
*Interface principal da aplicação, exibindo o saldo atualizado da conta selecionada, opções de navegação e botões de operações bancárias.*
<div align="center">
  <img src="image_d2feeb.png" alt="Janela Principal Banco Rio Capital" width="500px">
</div>

### 2. Consulta de Movimentos e Histórico
*Janela secundária que lista o histórico de transações e movimentos efetuados durante a sessão ativa.*
<div align="center">
  <img src="Captura de tela 2026-10-27 160854.png" alt="Consulta de Movimentos" width="500px">
</div>

---

## ✨ Funcionalidades Principais
* **Gestão de Contas:** Seletor dinâmico para alternar entre diferentes contas registadas na base de dados.
* **Operações de Caixa:** Realização de depósitos e levantamentos com validação de montantes e verificação de saldo em tempo real.
* **Transferências Bancárias Seguras:** Transferências entre contas executadas na mesma transação SQL (`ACID`), garantindo rollback automático em caso de falhas ou saldo insuficiente.
* **Extrato Mensal em PDF:** Geração direta de relatórios em formato PDF utilizando a biblioteca `fpdf2`, com abertura automática no leitor predefinido do sistema.
* **Módulos de Apoio:** Acesso rápido a links úteis de educação financeira e portais institucionais (como o Banco de Portugal e a CMVM).
* **Notificações e Movimentos:** Registo em memória de todas as operações realizadas na sessão.

---

## 🛠️ Tecnologias e Ferramentas Utilizadas
* **Linguagem:** Python 3.9+
* **Interface Gráfica:** Tkinter / ttk
* **Base de Dados:** Microsoft SQL Server
* **Conectividade SQL:** `pyodbc`
* **Manipulação Monetária:** Módulo `decimal` do Python (para evitar erros de arredondamento)
* **Geração de Documentos:** `fpdf2`

---

## ⚙️ Configuração e Instalação

### Pré-requisitos
1. Ter o **Python** instalado no computador.
2. Ter o **SQL Server** configurado com uma base de dados chamada `BANCO` e uma tabela `dbo.CONTA`.

### Passos para executar o projeto:

1. **Clonar o repositório:**
   ```bash
   git clone [https://github.com/o-seu-utilizador/banco-rio-capital.git](https://github.com/o-seu-utilizador/banco-rio-capital.git)
   cd banco-rio-capital