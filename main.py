import streamlit as st
import sqlite3
from datetime import datetime
from streamlit_autorefresh import st_autorefresh


# -------------------------------
# Configuração da Página
# -------------------------------
st.set_page_config(page_title="💈 Barbearia do Daniel", layout="wide")

# -------------------------------
# Banco de Dados SQLite
# -------------------------------


def init_db():
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()

    # Tabelas
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    telefone TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS servicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    preco REAL,
                    duracao INTEGER
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    servico_id INTEGER,
                    data TEXT,
                    hora TEXT,
                    status TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS pagamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    servico_id INTEGER,
                    valor REAL,
                    metodo TEXT,
                    data_pagamento TEXT
                )''')

    conn.commit()
    conn.close()

init_db()

# -------------------------------
# Funções de Banco
# -------------------------------
def cadastrar_cliente(nome, telefone):
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (nome, telefone))
    conn.commit()
    conn.close()

def listar_clientes():
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("SELECT * FROM clientes")
    clientes = c.fetchall()
    conn.close()
    return clientes

def cadastrar_servico(nome, preco, duracao):
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("INSERT INTO servicos (nome, preco, duracao) VALUES (?, ?, ?)", (nome, preco, duracao))
    conn.commit()
    conn.close()

def listar_servicos():
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("SELECT * FROM servicos")
    servicos = c.fetchall()
    conn.close()
    return servicos

# -------------------------------
# Menu de Navegação
# -------------------------------
menu = ["🏠 Dashboard", "👥 Clientes", "📅 Agendamentos", "✂️ Serviços", "💳 Pagamentos", "📊 Relatórios"]
escolha = st.sidebar.radio("Navegação", menu)

# -------------------------------
# Telas
# -------------------------------
if escolha == "🏠 Dashboard":
    st.title("💈 Barbearia do Daniel")
    st.subheader("Bem-vindo ao sistema da barbearia!")
    st.info("Use o menu lateral para navegar entre as telas.")
    imagens = [
        r"C:\Users\ricar\Documents\Streamlit_\imagem1.png",
        r"C:\Users\ricar\Documents\Streamlit_\imagem2.png",
        r"C:\Users\ricar\Documents\Streamlit_\imagem3.png"
    ]

    if "img_index" not in st.session_state:
        st.session_state.img_index = 0

    # Troque o key para algo único
    count = st_autorefresh(interval=3000, limit=None, key="carousel_autorefresh")

    st.session_state.img_index = count % len(imagens)

    st.image(imagens[st.session_state.img_index], width=1000)
    # -------------------------------
elif escolha == "👥 Clientes":
    st.title("👥 Gestão de Clientes")

    with st.form("novo_cliente"):
        nome = st.text_input("Nome do Cliente")
        telefone = st.text_input("Telefone")
        if st.form_submit_button("➕ Adicionar Cliente"):
            cadastrar_cliente(nome, telefone)
            st.success(f"Cliente {nome} cadastrado com sucesso!")

    st.subheader("📋 Lista de Clientes")
    clientes = listar_clientes()
    for c in clientes:
        st.write(f"**{c[1]}** - 📞 {c[2]}")

# -------------------------------
elif escolha == "✂️ Serviços":
    st.title("✂️ Serviços")

    with st.form("novo_servico"):
        nome = st.text_input("Nome do Serviço")
        preco = st.number_input("Preço (R$)", min_value=0.0, step=1.0)
        duracao = st.number_input("Duração (min)", min_value=10, step=5)
        if st.form_submit_button("➕ Adicionar Serviço"):
            cadastrar_servico(nome, preco, duracao)
            st.success(f"Serviço {nome} cadastrado!")

    st.subheader("📋 Lista de Serviços")
    servicos = listar_servicos()
    for s in servicos:
        st.write(f"**{s[1]}** - R$ {s[2]} - ⏳ {s[3]} min")

# -------------------------------
elif escolha == "📅 Agendamentos":
    st.title("📅 Agendamentos")
    st.info("Aqui você poderá cadastrar novos horários e ver os próximos agendamentos (a implementar).")

# -------------------------------
elif escolha == "💳 Pagamentos":
    st.title("💳 Pagamentos")
    st.info("Aqui você poderá registrar pagamentos e emitir QR Code Pix (a implementar).")

# -------------------------------
elif escolha == "📊 Relatórios":
    st.title("📊 Relatórios")
    st.info("Aqui serão exibidos gráficos de faturamento e serviços mais vendidos (a implementar).")
