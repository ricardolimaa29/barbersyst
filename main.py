import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import random
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from createCalendar import createCalendar

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
    c.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
              (nome, telefone))
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
    c.execute("INSERT INTO servicos (nome, preco, duracao) VALUES (?, ?, ?)",
              (nome, preco, duracao))
    conn.commit()
    conn.close()


def listar_servicos():
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("SELECT * FROM servicos")
    servicos = c.fetchall()
    conn.close()
    return servicos


def gerar_inserts_pagamentos(qtd=5):
    conn = sqlite3.connect("barbearia.db")
    clientes = pd.read_sql("SELECT id FROM clientes", conn)["id"].tolist()
    servicos = pd.read_sql("SELECT id, preco FROM servicos", conn)
    conn.close()

    inserts = []
    hoje = datetime.today()

    for _ in range(qtd):
        cliente_id = random.choice(clientes)
        servico = servicos.sample(1).iloc[0]
        servico_id = int(servico["id"])
        preco = float(servico["preco"])
        metodo = random.choice(["Pix", "Cartão", "Dinheiro"])

        # gera uma data de pagamento nos últimos 90 dias
        data_pag = hoje  # - timedelta(days=random.randint(0, 90))
        data_str = data_pag.strftime("%Y-%m-%d")

        inserts.append(
            f"INSERT INTO pagamentos (cliente_id, servico_id, valor, metodo, data_pagamento) "
            f"VALUES ({cliente_id}, {servico_id}, {preco}, '{metodo}', '{data_str}');"
        )

    return inserts


def executar_inserts_pagamentos(qtd=5):
    inserts = gerar_inserts_pagamentos(qtd)

    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    for sql in inserts:
        c.execute(sql)
    conn.commit()
    conn.close()

    print(f"✅ {qtd} pagamentos inseridos com sucesso!")


# -------------------------------
# Menu de Navegação
# -------------------------------
menu = ["🏠 Dashboard", "👥 Clientes", "📅 Agendamentos",
        "✂️ Serviços", "💳 Pagamentos", "📊 Relatórios"]
escolha = st.sidebar.radio("Navegação", menu)

# -------------------------------
# Telas
# -------------------------------
if escolha == "🏠 Dashboard":
    st.title("💈 Barbearia do Daniel")
    st.subheader("Bem-vindo ao sistema da barbearia!")
    st.info("Use o menu lateral para navegar entre as telas.")
    imagens = [
        "imagem1.png",
        "imagem2.png",
        "imagem3.png"
    ]

    if "img_index" not in st.session_state:
        st.session_state.img_index = 0

    # Troque o key para algo único
    count = st_autorefresh(interval=3000, limit=None,
                           key="carousel_autorefresh")

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
    # st.info("Aqui você poderá cadastrar novos horários e ver os próximos agendamentos (a implementar).")
    createCalendar()

# -------------------------------
elif escolha == "💳 Pagamentos":
    st.title("💳 Pagamentos")
    st.info(
        "Aqui você poderá registrar pagamentos e emitir QR Code Pix (a implementar).")

# -------------------------------
elif escolha == "📊 Relatórios":
    st.title("📊 Relatórios")

    tab1, tab2 = st.tabs(["📅 Semanais", "📆 Mensais"])

    with tab1:
        opcoes_semanais = [
            "Faturamento da semana por Serviço",
            "Formas de pagamento mais usadas",
            "Atendimentos por barbeiro"
        ]

        escolha_sem = st.radio("Escolha um relatório:", opcoes_semanais)

        # Opção para o usuário escolher início e fim da semana
        dias_semana = ["Segunda", "Terça", "Quarta",
                       "Quinta", "Sexta", "Sábado", "Domingo"]
        col1, col2 = st.columns(2)
        with col1:
            inicio_semana = st.selectbox(
                "Dia inicial da semana:", dias_semana, index=0)  # padrão: Segunda
        with col2:
            fim_semana = st.selectbox(
                "Dia final da semana:", dias_semana, index=5)  # padrão: Sábado

            # Mapear nomes para número (segunda=0, domingo=6)
        mapa_dias = {d: i for i, d in enumerate(dias_semana)}
        inicio_idx = mapa_dias[inicio_semana]
        fim_idx = mapa_dias[fim_semana]

        hoje = datetime.today()

        # Encontrar a data de início da semana
        delta_inicio = (hoje.weekday() - inicio_idx) % 7
        data_inicio = hoje - timedelta(days=delta_inicio)
        # Encontrar a data de fim da semana
        delta_fim = (fim_idx - hoje.weekday()) % 7
        data_fim = hoje + timedelta(days=delta_fim)

        st.info(
            f"Semana atual considerada: **{data_inicio.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}**")

        if escolha_sem == "Faturamento da semana por Serviço":
            st.subheader("📈 Faturamento da semana por Serviço")
            # Buscar dados no banco
            conn = sqlite3.connect("barbearia.db")
            query = """
                SELECT s.nome as servico, SUM(p.valor) as total
                FROM pagamentos p
                JOIN servicos s ON p.servico_id = s.id
                WHERE date(p.data_pagamento) BETWEEN date(?) AND date(?)
                GROUP BY s.nome
                ORDER BY total DESC
            """
            df = pd.read_sql(query, conn, params=(
                data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
            conn.close()

            if df.empty:
                st.warning("Nenhum pagamento encontrado nesta semana.")
            else:
                # st.write("### 📋 Faturamento diário")
                # st.dataframe(df)

                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X("total:Q", title="Faturamento (R$)"),
                    y=alt.Y("servico:N", sort="-x", title="Serviço"),
                    tooltip=["servico", "total"]
                ).properties(height=400)

                st.altair_chart(chart, use_container_width=True)

        elif escolha_sem == "Formas de pagamento mais usadas":
            st.subheader("Formas de pagamento mais usadas")

            conn = sqlite3.connect("barbearia.db")
            query = """
                SELECT COUNT(metodo) qtd, metodo
                FROM pagamentos p
                JOIN servicos s ON p.servico_id = s.id
                WHERE date(p.data_pagamento) BETWEEN date(?) AND date(?)
                GROUP BY metodo
                ORDER BY qtd DESC
            """

            try:
                df = pd.read_sql(query, conn, params=(
                    data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
                conn.close()

                if not df.empty:
                    # Métricas gerais
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_pagamentos = df['qtd'].sum()
                        st.metric("Total de Pagamentos",
                                  f"{total_pagamentos:,}")

                    with col2:
                        metodo_principal = df.iloc[0]['metodo']
                        qtd_principal = df.iloc[0]['qtd']
                        st.metric("Método Mais Usado", metodo_principal)

                    with col3:
                        percentual_principal = (
                            qtd_principal / total_pagamentos) * 100
                        st.metric("% do Principal",
                                  f"{percentual_principal:.1f}%")

                    # Criar donut chart usando go
                    fig = go.Figure(data=[go.Pie(
                        labels=df['metodo'],
                        values=df['qtd'],
                        hole=0.4
                    )])

                    fig.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>' +
                        'Quantidade: %{value:,}<br>' +
                        'Percentual: %{percent}<br>' +
                        '<extra></extra>'
                    )

                    fig.update_layout(
                        title="Distribuição das Formas de Pagamento",
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        ),
                        font=dict(size=12)
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Checkbox para dados detalhados
                    if st.checkbox("Mostrar dados detalhados", key="checkbox_pagamentos"):
                        # Adicionar coluna de percentual
                        df_detalhado = df.copy()
                        df_detalhado['percentual'] = (
                            df_detalhado['qtd'] / df_detalhado['qtd'].sum() * 100).round(1)
                        df_detalhado['percentual_str'] = df_detalhado['percentual'].astype(
                            str) + '%'

                        # Renomear colunas para melhor apresentação
                        df_detalhado = df_detalhado.rename(columns={
                            'metodo': 'Método de Pagamento',
                            'qtd': 'Quantidade',
                            'percentual_str': 'Percentual'
                        })

                        # Adicionar linha de total
                        total_row = pd.DataFrame({
                            'Método de Pagamento': ['TOTAL'],
                            'Quantidade': [df_detalhado['Quantidade'].sum()],
                            'Percentual': ['100.0%']
                        })

                        df_final = pd.concat([df_detalhado[['Método de Pagamento', 'Quantidade', 'Percentual']],
                                              total_row], ignore_index=True)

                        st.dataframe(
                            df_final,
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.info("Nenhum dado encontrado para o período selecionado.")

            except Exception as e:
                st.error(f"Erro ao executar consulta: {e}")
                if 'conn' in locals():
                    conn.close()

    with tab2:
        opcoes_mensais = [
            "Faturamento Geral",
            "Ticket médio mensal",
            "Top clientes do mês"
        ]
        escolha_men = st.radio("Escolha um relatório:", opcoes_mensais)
        ano_atual = datetime.now().year
        anos = list(range(2020, ano_atual + 1))  # De 2020 até ano atual

        col1, col2 = st.columns(2)

        with col1:
            ano = st.selectbox(
                "Ano",
                anos,
                index=anos.index(
                    ano_atual) if ano_atual in anos else len(anos)-1
            )

        with col2:
            meses_opcoes = ['Todos'] + ['Janeiro', 'Fevereiro', 'Março', 'Abril',
                                        'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            mes_selecionado = st.selectbox("Mês", meses_opcoes)

        if escolha_men == "Faturamento Geral":

            conn = sqlite3.connect("barbearia.db")

            if mes_selecionado == 'Todos':
                query = """
                    SELECT 
                        strftime('%m', p.data_pagamento) as mes,
                        s.nome as servico,
                        SUM(p.valor) as valor_total,
                        COUNT(p.id) as quantidade
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    WHERE strftime('%Y', p.data_pagamento) = ?
                    GROUP BY strftime('%m', p.data_pagamento), s.nome
                    ORDER BY mes, servico
                """
                params = (str(ano),)
            else:
                # Converter nome do mês para número
                meses_num = {
                    'Janeiro': '01', 'Fevereiro': '02', 'Março': '03', 'Abril': '04',
                    'Maio': '05', 'Junho': '06', 'Julho': '07', 'Agosto': '08',
                    'Setembro': '09', 'Outubro': '10', 'Novembro': '11', 'Dezembro': '12'
                }
                mes_num = meses_num[mes_selecionado]

                query = """
                    SELECT 
                        strftime('%m', p.data_pagamento) as mes,
                        s.nome as servico,
                        SUM(p.valor) as valor_total,
                        COUNT(p.id) as quantidade
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    WHERE strftime('%Y', p.data_pagamento) = ? 
                    AND strftime('%m', p.data_pagamento) = ?
                    GROUP BY strftime('%m', p.data_pagamento), s.nome
                    ORDER BY mes, servico
                """
                params = (str(ano), mes_num)

            df = pd.read_sql(query, conn, params=params)
            conn.close()

            if not df.empty:
                # Converter mês para nome
                meses = {
                    '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
                    '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
                    '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
                }

                df['mes_nome'] = df['mes'].map(meses)
                df['mes_num'] = df['mes'].astype(int)

                # Ordenar por número do mês
                df = df.sort_values('mes_num')

                # Mostrar métricas gerais
                periodo_titulo = f"{ano}" if mes_selecionado == 'Todos' else f"{mes_selecionado}/{ano}"
                st.subheader(f"Faturamento {periodo_titulo}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    total_faturamento = df['valor_total'].sum()
                    st.metric("Faturamento Total",
                              f"R$ {total_faturamento:,.2f}")

                with col2:
                    total_servicos = df['quantidade'].sum()
                    st.metric("Total de Serviços", f"{total_servicos:,}")

                with col3:
                    ticket_medio = total_faturamento / total_servicos if total_servicos > 0 else 0
                    st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")

                fig = px.bar(
                    df,
                    x='mes_nome',
                    y='valor_total',
                    color='servico',
                    title=f'Faturamento por Serviço - {periodo_titulo}',
                    labels={
                        'valor_total': 'Faturamento (R$)',
                        'mes_nome': 'Mês',
                        'servico': 'Serviço'
                    }
                )

                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Faturamento (R$)",
                    barmode='stack',  # Barras empilhadas
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                # Formatar valores no hover
                fig.update_traces(
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                    'Mês: %{x}<br>' +
                    'Valor: R$ %{y:,.2f}<br>' +
                    '<extra></extra>'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Tabela de dados detalhados
                if st.checkbox("Mostrar dados detalhados"):
                    # Pivot table para melhor visualização
                    pivot_df = df.pivot_table(
                        values='valor_total',
                        index='mes_nome',
                        columns='servico',
                        fill_value=0,
                        aggfunc='sum'
                    )

                    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

                    # Reordenar o DataFrame pela ordem dos meses
                    pivot_df = pivot_df.reindex(ordem_meses).dropna(how='all')

                    # Adicionar total por mês
                    pivot_df['Total'] = pivot_df.sum(axis=1)

                    # Adicionar total por serviço
                    total_row = pivot_df.sum()
                    total_row.name = 'Total'
                    pivot_df = pd.concat([pivot_df, total_row.to_frame().T])

                    st.dataframe(
                        pivot_df.style.format("R$ {:.2f}"),
                        use_container_width=True
                    )

                # Gráfico adicional: Distribuição por serviço (Donut)
                st.subheader("Distribuição por Serviço")

                servico_total = df.groupby(
                    'servico')['valor_total'].sum().reset_index()

                fig_donut = go.Figure(data=[go.Pie(
                    labels=servico_total['servico'],
                    values=servico_total['valor_total'],
                    hole=0.4
                )])

                fig_donut.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>' +
                    'Valor: R$ %{value:,.2f}<br>' +
                    'Percentual: %{percent}<br>' +
                    '<extra></extra>'
                )

                fig_donut.update_layout(
                    title=f"Distribuição do Faturamento por Serviço - {periodo_titulo}",
                    showlegend=True
                )

                st.plotly_chart(fig_donut, use_container_width=True)

            else:
                periodo_msg = f"o ano {ano}" if mes_selecionado == 'Todos' else f"{mes_selecionado}/{ano}"
                st.info(f"Nenhum dado encontrado para {periodo_msg}")

        elif escolha_men == "Ticket médio mensal":
            st.subheader("Ticket Médio Mensal")

            comparar_ano = st.checkbox(
                "Comparar com ano anterior", key="checkbox_comparar_ano")

            conn = sqlite3.connect("barbearia.db")

            # Query para ticket médio mensal
            if mes_selecionado == 'Todos':
                query = """
                    SELECT 
                        strftime('%m', p.data_pagamento) as mes,
                        COUNT(p.id) as quantidade_servicos,
                        SUM(p.valor) as faturamento_total,
                        ROUND(SUM(p.valor) / COUNT(p.id), 2) as ticket_medio
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    WHERE strftime('%Y', p.data_pagamento) = ?
                    GROUP BY strftime('%m', p.data_pagamento)
                    ORDER BY mes
                """
                params_atual = (str(ano),)
                params_anterior = (
                    str(ano - 1),) if comparar_ano and ano > 2020 else None
            else:
                # Converter nome do mês para número
                meses_num = {
                    'Janeiro': '01', 'Fevereiro': '02', 'Março': '03', 'Abril': '04',
                    'Maio': '05', 'Junho': '06', 'Julho': '07', 'Agosto': '08',
                    'Setembro': '09', 'Outubro': '10', 'Novembro': '11', 'Dezembro': '12'
                }
                mes_num = meses_num[mes_selecionado]

                query = """
                    SELECT 
                        strftime('%m', p.data_pagamento) as mes,
                        COUNT(p.id) as quantidade_servicos,
                        SUM(p.valor) as faturamento_total,
                        ROUND(SUM(p.valor) / COUNT(p.id), 2) as ticket_medio
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    WHERE strftime('%Y', p.data_pagamento) = ? 
                    AND strftime('%m', p.data_pagamento) = ?
                    GROUP BY strftime('%m', p.data_pagamento)
                    ORDER BY mes
                """
                params_atual = (str(ano), mes_num)
                params_anterior = (
                    str(ano - 1), mes_num) if comparar_ano and ano > 2020 else None

            try:
                # Dados do ano selecionado
                df_atual = pd.read_sql(query, conn, params=params_atual)

                # Se comparar com ano anterior
                df_anterior = pd.DataFrame()
                if comparar_ano and ano > 2020 and params_anterior:
                    df_anterior = pd.read_sql(
                        query, conn, params=params_anterior)

                conn.close()

                if not df_atual.empty:
                    # Converter mês para nome com ordem preservada
                    meses_ordenados = [
                        ('01', 'Janeiro'), ('02', 'Fevereiro'), ('03',
                                                                 'Março'), ('04', 'Abril'),
                        ('05', 'Maio'), ('06', 'Junho'), ('07',
                                                          'Julho'), ('08', 'Agosto'),
                        ('09', 'Setembro'), ('10', 'Outubro'), ('11',
                                                                'Novembro'), ('12', 'Dezembro')
                    ]

                    meses_dict = dict(meses_ordenados)
                    df_atual['mes_nome'] = df_atual['mes'].map(meses_dict)
                    df_atual['mes_num'] = df_atual['mes'].astype(int)
                    df_atual['ano'] = ano

                    # Criar categoria ordenada
                    df_atual['mes_nome'] = pd.Categorical(
                        df_atual['mes_nome'],
                        categories=[nome for _, nome in meses_ordenados],
                        ordered=True
                    )

                    # Processar dados do ano anterior se existir
                    if not df_anterior.empty and comparar_ano:
                        df_anterior['mes_nome'] = df_anterior['mes'].map(
                            meses_dict)
                        df_anterior['mes_num'] = df_anterior['mes'].astype(int)
                        df_anterior['ano'] = ano - 1
                        df_anterior['mes_nome'] = pd.Categorical(
                            df_anterior['mes_nome'],
                            categories=[nome for _, nome in meses_ordenados],
                            ordered=True
                        )

                    # Métricas gerais do ano atual
                    col1, col2, col3, col4 = st.columns(4)

                    periodo_titulo = f"{ano}" if mes_selecionado == 'Todos' else f"{mes_selecionado}/{ano}"

                    with col1:
                        ticket_medio_anual = df_atual['faturamento_total'].sum(
                        ) / df_atual['quantidade_servicos'].sum()
                        st.metric(f"Ticket Médio {periodo_titulo}",
                                  f"R$ {ticket_medio_anual:.2f}")

                    with col2:
                        melhor_mes = df_atual.loc[df_atual['ticket_medio'].idxmax(
                        )]
                        label_melhor = "Melhor Mês" if mes_selecionado == 'Todos' else "Mês Selecionado"
                        st.metric(label_melhor, f"{melhor_mes['mes_nome']}")

                    with col3:
                        label_ticket = "Ticket do Melhor Mês" if mes_selecionado == 'Todos' else "Ticket do Mês"
                        st.metric(label_ticket,
                                  f"R$ {melhor_mes['ticket_medio']:.2f}")

                    with col4:
                        if len(df_atual) > 1:
                            variacao = (
                                (df_atual['ticket_medio'].iloc[-1] - df_atual['ticket_medio'].iloc[0]) / df_atual['ticket_medio'].iloc[0]) * 100
                            st.metric("Variação no Período",
                                      f"{variacao:+.1f}%")
                        else:
                            st.metric("Variação no Período", "N/A")

                    # Gráfico de linha para ticket médio mensal
                    st.subheader("Evolução do Ticket Médio")

                    fig = go.Figure()

                    # Linha do ano atual
                    fig.add_trace(go.Scatter(
                        x=df_atual['mes_nome'],
                        y=df_atual['ticket_medio'],
                        mode='lines+markers',
                        name=f'{ano}',
                        line=dict(width=3, color='#1f77b4'),
                        marker=dict(size=8),
                        hovertemplate='<b>%{x} %{fullData.name}</b><br>' +
                        'Ticket Médio: R$ %{y:.2f}<br>' +
                        '<extra></extra>'
                    ))

                    # Linha do ano anterior (se selecionado)
                    if not df_anterior.empty and comparar_ano:
                        fig.add_trace(go.Scatter(
                            x=df_anterior['mes_nome'],
                            y=df_anterior['ticket_medio'],
                            mode='lines+markers',
                            name=f'{ano-1}',
                            line=dict(width=2, color='#ff7f0e', dash='dash'),
                            marker=dict(size=6),
                            hovertemplate='<b>%{x} %{fullData.name}</b><br>' +
                            'Ticket Médio: R$ %{y:.2f}<br>' +
                            '<extra></extra>'
                        ))

                    titulo_grafico = f"Ticket Médio - {periodo_titulo}"
                    if comparar_ano and not df_anterior.empty:
                        titulo_grafico += f" vs {ano-1}"

                    fig.update_layout(
                        title=titulo_grafico,
                        xaxis_title="Mês",
                        yaxis_title="Ticket Médio (R$)",
                        hovermode='x unified',
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Gráfico de barras para quantidade de serviços
                    st.subheader("Quantidade de Serviços por Mês")

                    fig_bar = go.Figure()

                    fig_bar.add_trace(go.Bar(
                        x=df_atual['mes_nome'],
                        y=df_atual['quantidade_servicos'],
                        name=f'Serviços {ano}',
                        marker_color='#2E8B57',
                        hovertemplate='<b>%{x}</b><br>' +
                        'Quantidade: %{y}<br>' +
                        '<extra></extra>'
                    ))

                    if not df_anterior.empty and comparar_ano:
                        fig_bar.add_trace(go.Bar(
                            x=df_anterior['mes_nome'],
                            y=df_anterior['quantidade_servicos'],
                            name=f'Serviços {ano-1}',
                            marker_color='#87CEEB',
                            opacity=0.7,
                            hovertemplate='<b>%{x}</b><br>' +
                            'Quantidade: %{y}<br>' +
                            '<extra></extra>'
                        ))

                    fig_bar.update_layout(
                        title="Quantidade de Serviços por Mês",
                        xaxis_title="Mês",
                        yaxis_title="Quantidade de Serviços",
                        barmode='group'
                    )

                    st.plotly_chart(fig_bar, use_container_width=True)

                    # Tabela comparativa
                    if st.checkbox("Mostrar dados detalhados", key="checkbox_ticket_medio"):
                        if not df_anterior.empty and comparar_ano:
                            # Merge dos dados para comparação
                            df_comparacao = df_atual[[
                                'mes_nome', 'ticket_medio', 'quantidade_servicos', 'faturamento_total']].copy()
                            df_comparacao.columns = [
                                'Mês', f'Ticket Médio {ano}', f'Qtd Serviços {ano}', f'Faturamento {ano}']

                            df_ant_temp = df_anterior[[
                                'mes_nome', 'ticket_medio', 'quantidade_servicos', 'faturamento_total']].copy()
                            df_ant_temp.columns = [
                                'Mês', f'Ticket Médio {ano-1}', f'Qtd Serviços {ano-1}', f'Faturamento {ano-1}']

                            df_final = df_comparacao.merge(
                                df_ant_temp, on='Mês', how='outer').fillna(0)

                            # Calcular variações
                            df_final[f'Var. Ticket (%)'] = (
                                (df_final[f'Ticket Médio {ano}'] - df_final[f'Ticket Médio {ano-1}']) / df_final[f'Ticket Médio {ano-1}'] * 100).round(1)
                            df_final[f'Var. Qtd (%)'] = (
                                (df_final[f'Qtd Serviços {ano}'] - df_final[f'Qtd Serviços {ano-1}']) / df_final[f'Qtd Serviços {ano-1}'] * 100).round(1)

                            # Substituir infinito por 0
                            df_final = df_final.replace(
                                [float('inf'), -float('inf')], 0)

                        else:
                            # Apenas dados do ano atual
                            df_final = df_atual[[
                                'mes_nome', 'ticket_medio', 'quantidade_servicos', 'faturamento_total']].copy()
                            df_final.columns = [
                                'Mês', 'Ticket Médio', 'Qtd Serviços', 'Faturamento Total']

                        # Formatar valores monetários
                        def format_currency(val):
                            if pd.isna(val) or val == 0:
                                return "R$ 0,00"
                            return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                        # Aplicar formatação
                        for col in df_final.columns:
                            if 'Ticket Médio' in col or 'Faturamento' in col:
                                df_final[col] = df_final[col].apply(
                                    format_currency)
                            elif 'Qtd' in col:
                                df_final[col] = df_final[col].astype(int)
                            elif 'Var.' in col and '%' in col:
                                df_final[col] = df_final[col].astype(str) + '%'

                        st.dataframe(
                            df_final, use_container_width=True, hide_index=True)

                else:
                    periodo_msg = f"o ano {ano}" if mes_selecionado == 'Todos' else f"{mes_selecionado}/{ano}"
                    st.info(f"Nenhum dado encontrado para {periodo_msg}")

            except Exception as e:
                st.error(f"Erro ao executar consulta: {e}")
                if 'conn' in locals():
                    conn.close()

        elif escolha_men == "Top clientes do mês":
            st.subheader("Top clientes do mês")

            # Query para top clientes
            conn = sqlite3.connect("barbearia.db")

            if mes_selecionado == 'Todos':
                query = """
                    SELECT 
                        c.nome,
                        COUNT(p.id) as total_servicos,
                        SUM(p.valor) as total_gasto,
                        ROUND(SUM(p.valor) / COUNT(p.id), 2) as ticket_medio
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE strftime('%Y', p.data_pagamento) = ?
                    GROUP BY c.id, c.nome
                    ORDER BY total_gasto DESC
                    LIMIT 10
                """
                params = (str(ano),)
            else:
                # Converter nome do mês para número
                meses_num = {
                    'Janeiro': '01', 'Fevereiro': '02', 'Março': '03', 'Abril': '04',
                    'Maio': '05', 'Junho': '06', 'Julho': '07', 'Agosto': '08',
                    'Setembro': '09', 'Outubro': '10', 'Novembro': '11', 'Dezembro': '12'
                }
                mes_num = meses_num[mes_selecionado]

                query = """
                    SELECT 
                        c.nome,
                        COUNT(p.id) as total_servicos,
                        SUM(p.valor) as total_gasto,
                        ROUND(SUM(p.valor) / COUNT(p.id), 2) as ticket_medio
                    FROM pagamentos p
                    JOIN servicos s ON p.servico_id = s.id
                    JOIN clientes c ON p.cliente_id = c.id
                    WHERE strftime('%Y', p.data_pagamento) = ? 
                    AND strftime('%m', p.data_pagamento) = ?
                    GROUP BY c.id, c.nome
                    ORDER BY total_gasto DESC
                    LIMIT 10
                """
                params = (str(ano), mes_num)

            periodo_titulo = f"{ano}" if mes_selecionado == 'Todos' else f"{mes_selecionado}/{ano}"
            st.info(f"Período selecionado: **{periodo_titulo}**")

            try:
                df = pd.read_sql(query, conn, params=params)
                conn.close()

                if not df.empty:
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        melhor_cliente = df.iloc[0]
                        st.metric("Melhor Cliente", melhor_cliente['nome'])

                    with col2:
                        st.metric("Total Gasto",
                                  f"R$ {melhor_cliente['total_gasto']:,.2f}")

                    with col3:
                        st.metric("Ticket Médio",
                                  f"R$ {melhor_cliente['ticket_medio']:,.2f}")

                    # Gráfico de barras
                    fig = go.Figure(data=[go.Bar(
                        x=df['nome'],
                        y=df['total_gasto'],
                        marker_color='#1f77b4',
                        hovertemplate='<b>%{x}</b><br>' +
                        'Total Gasto: R$ %{y:,.2f}<br>' +
                        '<extra></extra>'
                    )])

                    fig.update_layout(
                        title=f"Top 10 Clientes por Faturamento - {periodo_titulo}",
                        xaxis_title="Cliente",
                        yaxis_title="Total Gasto (R$)",
                        xaxis_tickangle=-45
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Tabela detalhada
                    if st.checkbox("Mostrar dados detalhados", key="checkbox_top_clientes"):
                        df_formatado = df.copy()
                        df_formatado['total_gasto'] = df_formatado['total_gasto'].apply(
                            lambda x: f"R$ {x:,.2f}".replace(
                                ',', 'X').replace('.', ',').replace('X', '.')
                        )
                        df_formatado['ticket_medio'] = df_formatado['ticket_medio'].apply(
                            lambda x: f"R$ {x:,.2f}".replace(
                                ',', 'X').replace('.', ',').replace('X', '.')
                        )
                        df_formatado.columns = [
                            'Cliente', 'Total Serviços', 'Total Gasto', 'Ticket Médio']

                        st.dataframe(
                            df_formatado, use_container_width=True, hide_index=True)
                else:
                    st.info(
                        f"Nenhum cliente encontrado para {periodo_titulo}.")

            except Exception as e:
                st.error(f"Erro ao executar consulta: {e}")
                if 'conn' in locals():
                    conn.close()
