import streamlit as st
import sqlite3
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import time
from apimercadopago import gerar_link

# ---------------------------
# Funções de acesso ao banco
# ---------------------------

DB_PATH = "barbearia.db"


def connect_db():
    return sqlite3.connect(DB_PATH)


def get_agendamentos_from_db():
    """Busca todos os agendamentos do banco de dados com informações dos clientes e serviços"""
    conn = connect_db()
    query = '''
    SELECT 
        a.id,
        a.data,
        a.hora,
        a.status,
        a.cliente_id,
        c.nome as cliente_nome,
        a.servico_id,
        s.nome as servico_nome,
        s.duracao,
        s.preco
    FROM agendamentos a
    LEFT JOIN clientes c ON a.cliente_id = c.id
    LEFT JOIN servicos s ON a.servico_id = s.id
    ORDER BY a.data, a.hora
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_agendamento_by_id(agendamento_id):
    """Retorna um dict com os dados do agendamento (ou None)"""
    conn = connect_db()
    query = '''
    SELECT 
        a.id,
        a.data,
        a.hora,
        a.status,
        a.cliente_id,
        c.nome as cliente_nome,
        a.servico_id,
        s.nome as servico_nome,
        s.duracao,
        s.preco
    FROM agendamentos a
    LEFT JOIN clientes c ON a.cliente_id = c.id
    LEFT JOIN servicos s ON a.servico_id = s.id
    WHERE a.id = ?
    LIMIT 1
    '''
    try:
        df = pd.read_sql_query(query, conn, params=[agendamento_id])
    except Exception as e:
        conn.close()
        raise
    conn.close()
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_clientes_from_db():
    """Busca todos os clientes do banco de dados"""
    conn = connect_db()
    query = "SELECT id, nome, telefone FROM clientes ORDER BY nome"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_servicos_from_db():
    """Busca todos os serviços do banco de dados"""
    conn = connect_db()
    query = "SELECT id, nome, preco, duracao FROM servicos ORDER BY nome"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def inserir_agendamento(cliente_id, servico_id, data, hora, status='agendado'):
    """Insere um novo agendamento no banco de dados"""
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO agendamentos (cliente_id, servico_id, data, hora, status)
                     VALUES (?, ?, ?, ?, ?)''',
                  (cliente_id, servico_id, data, hora, status))
        conn.commit()
        agendamento_id = c.lastrowid
        conn.close()
        return True, agendamento_id
    except Exception as e:
        conn.close()
        return False, str(e)


def atualizar_agendamento(agendamento_id, cliente_id, servico_id, data, hora, status):
    """Atualiza os dados de um agendamento"""
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute('''UPDATE agendamentos 
                     SET cliente_id = ?, servico_id = ?, data = ?, hora = ?, status = ?
                     WHERE id = ?''',
                  (cliente_id, servico_id, data, hora, status, agendamento_id))
        conn.commit()
        conn.close()
        return True, "Agendamento atualizado com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


def atualizar_status_agendamento(agendamento_id, novo_status):
    """Atualiza o status de um agendamento"""
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("UPDATE agendamentos SET status = ? WHERE id = ?",
                  (novo_status, agendamento_id))
        conn.commit()
        conn.close()
        return True, "Status atualizado com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


def deletar_agendamento(agendamento_id):
    """(Opcional) Deleta um agendamento do banco"""
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM agendamentos WHERE id = ?", (agendamento_id,))
        conn.commit()
        conn.close()
        return True, "Agendamento deletado com sucesso!"
    except Exception as e:
        conn.close()
        return False, str(e)


# ---------------------------
# Regras de conflito / utilitários
# ---------------------------

def verificar_conflito_horario(data, hora, duracao_minutos, agendamento_id=None):
    """Verifica se há conflito de horário em uma data específica.
       Retorna lista de conflitos (vazia quando não houver)."""
    conn = connect_db()

    inicio = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
    fim = inicio + timedelta(minutes=duracao_minutos)

    query = '''
    SELECT a.id, a.hora, s.duracao, c.nome as cliente_nome, s.nome as servico
    FROM agendamentos a
    JOIN clientes c ON a.cliente_id = c.id
    JOIN servicos s ON a.servico_id = s.id
    WHERE a.data = ? AND a.status NOT IN ('cancelado', 'concluido')
    '''
    params = [data]
    if agendamento_id:
        query += " AND a.id != ?"
        params.append(agendamento_id)

    # IMPORTANTE: ordem dos argumentos do read_sql_query -> (sql, con, params=params)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    conflitos = []
    for _, row in df.iterrows():
        existing_inicio = datetime.strptime(
            f"{data} {row['hora']}", "%Y-%m-%d %H:%M")
        existing_fim = existing_inicio + timedelta(minutes=row['duracao'])

        # sobreposição
        if not (fim <= existing_inicio or inicio >= existing_fim):
            conflitos.append({
                'id': row['id'],
                'cliente': row['cliente_nome'],
                'servico': row['servico'],
                'hora': row['hora'],
                'duracao': row['duracao']
            })

    return conflitos


def get_status_color(status):
    """Retorna a cor baseada no status do agendamento"""
    colors = {
        'agendado': {'bg': '#28a745', 'border': '#1e7e34'},
        'confirmado': {'bg': '#17a2b8', 'border': '#138496'},
        'em_andamento': {'bg': '#ffc107', 'border': '#e0a800'},
        'concluido': {'bg': '#6f42c1', 'border': '#59359a'},
        'cancelado': {'bg': '#dc3545', 'border': '#c82333'},
        'faltou': {'bg': '#6c757d', 'border': '#545b62'}
    }
    return colors.get(str(status).lower(), {'bg': '#28a745', 'border': '#1e7e34'})


def convert_to_calendar_events(df_agendamentos):
    """Converte os agendamentos do banco para o formato do calendário"""
    events = []
    for _, row in df_agendamentos.iterrows():
        data_str = row['data']
        hora_str = row['hora']
        try:
            start_datetime = datetime.strptime(
                f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")
            duracao = int(row['duracao']) if pd.notna(row['duracao']) else 60
            end_datetime = start_datetime + timedelta(minutes=duracao)
            colors = get_status_color(row['status'])
            cliente = row['cliente_nome'] if pd.notna(
                row['cliente_nome']) else "Cliente não encontrado"
            servico = row['servico_nome'] if pd.notna(
                row['servico_nome']) else "Serviço não encontrado"
            preco = row['preco'] if pd.notna(row['preco']) else 0
            title = f"{servico} - {cliente} (R$ {preco:.2f})"

            event = {
                "id": str(row['id']),
                "title": title,
                "start": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "backgroundColor": colors['bg'],
                "borderColor": colors['border'],
                "extendedProps": {
                    "agendamento_id": int(row['id']),
                    "cliente": cliente,
                    "servico": servico,
                    "status": row['status'],
                    "preco": preco,
                    "duracao": duracao
                }
            }
            events.append(event)
        except Exception as e:
            st.error(
                f"Erro ao processar agendamento ID {row.get('id', '??')}: {str(e)}")
            continue
    return events


# ---------------------------
# UI: calendário + ações
# ---------------------------

def createCalendar():

    # Novo agendamento (toggle)
    if st.button("➕ Novo Agendamento", type="secondary"):
        st.session_state['mostrar_form_agendamento'] = not st.session_state.get(
            'mostrar_form_agendamento', False)

    # Form novo agendamento
    if st.session_state.get('mostrar_form_agendamento', False):
        st.markdown("---")
        st.markdown("### 📝 Cadastrar Novo Agendamento")
        try:
            df_clientes = get_clientes_from_db()
            df_servicos = get_servicos_from_db()

            if df_clientes.empty:
                st.error(
                    "❌ Nenhum cliente cadastrado! Cadastre clientes primeiro.")
            elif df_servicos.empty:
                st.error(
                    "❌ Nenhum serviço cadastrado! Cadastre serviços primeiro.")
            else:
                with st.form("form_novo_agendamento"):
                    col1, col2 = st.columns(2)
                    with col1:
                        opcoes_clientes = [
                            f"{row['nome']} - {row['telefone']}" for _, row in df_clientes.iterrows()]
                        cliente_selecionado = st.selectbox(
                            "👤 Cliente:",
                            options=range(len(opcoes_clientes)),
                            format_func=lambda x: opcoes_clientes[x],
                            help="Selecione o cliente para o agendamento"
                        )
                        data_agendamento = st.date_input(
                            "📅 Data:",
                            value=datetime.now().date(),
                            min_value=datetime.now().date(),
                            help="Selecione a data do agendamento"
                        )
                    with col2:
                        opcoes_servicos = [
                            f"{row['nome']} - R$ {row['preco']:.2f} ({row['duracao']}min)" for _, row in df_servicos.iterrows()]
                        servico_selecionado = st.selectbox(
                            "💇 Serviço:",
                            options=range(len(opcoes_servicos)),
                            format_func=lambda x: opcoes_servicos[x],
                            help="Selecione o serviço a ser realizado"
                        )
                        hora_agendamento = st.time_input(
                            "⏰ Horário:",
                            value=datetime.now().replace(minute=0, second=0, microsecond=0).time(),
                            help="Selecione o horário do agendamento"
                        )
                    status_agendamento = st.selectbox(
                        "📊 Status:", options=['agendado', 'confirmado'], index=0)

                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                    with col_btn1:
                        submitted = st.form_submit_button(
                            "✅ Salvar", type="secondary")
                    with col_btn2:
                        cancelled = st.form_submit_button("❌ Cancelar")

                    if cancelled:
                        st.session_state['mostrar_form_agendamento'] = False
                        st.rerun()

                    if submitted:
                        cliente_id = int(
                            df_clientes.iloc[cliente_selecionado]['id'])
                        servico_id = int(
                            df_servicos.iloc[servico_selecionado]['id'])
                        duracao = int(
                            df_servicos.iloc[servico_selecionado]['duracao'])
                        data_str = data_agendamento.strftime("%Y-%m-%d")
                        hora_str = hora_agendamento.strftime("%H:%M")

                        conflitos = verificar_conflito_horario(
                            data_str, hora_str, duracao)
                        if conflitos:
                            st.error(
                                "⚠️ Conflito de horário detectado! Não foi possível agendar.")
                            for conflito in conflitos:
                                st.warning(
                                    f"• {conflito['cliente']} - {conflito['servico']} às {conflito['hora']}")
                        else:
                            sucesso, resultado = inserir_agendamento(
                                cliente_id, servico_id, data_str, hora_str, status_agendamento)
                            if sucesso:
                                st.success(
                                    f"✅ Agendamento criado com sucesso! ID: {resultado}")
                                st.session_state['mostrar_form_agendamento'] = False
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ Erro ao criar agendamento: {resultado}")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")

    # Buscar dados para o calendário
    try:
        df_agendamentos = get_agendamentos_from_db()
        if df_agendamentos.empty:
            st.warning("⚠️ Nenhum agendamento encontrado no banco de dados.")
            st.info(
                "💡 Cadastre alguns clientes, serviços e agendamentos para visualizar no calendário.")
            return

        calendar_events = convert_to_calendar_events(df_agendamentos)

        # Estatísticas rápidas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Agendamentos", len(df_agendamentos))
        with col2:
            hoje_str = datetime.now().strftime("%Y-%m-%d")
            st.metric("Hoje", len(
                df_agendamentos[df_agendamentos['data'] == hoje_str]))
        with col3:
            st.metric("Concluídos", len(
                df_agendamentos[df_agendamentos['status'] == 'concluido']))
        with col4:
            receita_total = df_agendamentos[df_agendamentos['status']
                                            == 'concluido']['preco'].sum()
            st.metric("Receita Concluída", f"R$ {receita_total:.2f}")

    except Exception as e:
        st.error(f"❌ Erro ao conectar com o banco de dados: {str(e)}")
        return

    # Configurações do calendário
    calendar_options = {
        "editable": True,
        "selectable": True,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "slotMinTime": "08:00:00",
        "slotMaxTime": "23:00:00",
        "initialView": "timeGridWeek",
        "locale": "pt",
        "height": 600,
        "slotDuration": "00:30:00",
        "businessHours": {
            "daysOfWeek": [1, 2, 3, 4, 5, 6],  # Segunda a Sábado
            "startTime": "08:00",
            "endTime": "23:00"
        }
    }

    custom_css = """
        .fc-event-past { opacity: 0.6; }
        .fc-event-time { font-weight: bold; }
        .fc-event-title { font-weight: 500; font-size: 11px; }
        .fc-toolbar-title { font-size: 1.5rem; color: #2c3e50; }
        .fc-daygrid-event { font-size: 12px; }
        .fc-timegrid-event { font-size: 11px; }
    """

    resultado_calendario = calendar(
        events=calendar_events,
        options=calendar_options,
        custom_css=custom_css,
        key='calendario_barbearia_db',
    )

    # Interações do calendário
    if resultado_calendario:
        # clique em data
        if resultado_calendario.get('dateClick'):
            data_clicada = resultado_calendario['dateClick']['dateStr']
            st.success(f"📅 Data selecionada: {data_clicada}")
            if st.button("➕ Novo Agendamento nesta data"):
                st.session_state['nova_data_agendamento'] = data_clicada
                st.info(
                    "💡 Funcionalidade de novo agendamento nessa data (usando formulário) aberta.")
                # opcional: abrir o form e preencher data automaticamente
                st.session_state['mostrar_form_agendamento'] = True

        # clique em evento
        if resultado_calendario.get('eventClick'):
            evento = resultado_calendario['eventClick']['event']
            props = evento.get('extendedProps', {})
            agendamento_id = props.get('agendamento_id')

            st.markdown("---")
            st.markdown("### 🔍 Detalhes do Agendamento")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**👤 Cliente:** {props.get('cliente', 'N/A')}")
                st.write(f"**💇 Serviço:** {props.get('servico', 'N/A')}")
                st.write(f"**💰 Preço:** R$ {props.get('preco', 0):.2f}")
            with col2:
                st.write(
                    f"**📅 Data/Hora:** {evento['start'][:10]} às {evento['start'][11:16]}")
                st.write(f"**⏱️ Duração:** {props.get('duracao', 0)} min")
                st.write(
                    f"**📊 Status:** {str(props.get('status', 'N/A')).title()}")

            # Carrega dados completos do agendamento (para edição precisa de IDs)
            ag = None
            try:
                ag = get_agendamento_by_id(agendamento_id)
            except Exception as e:
                st.error(f"Erro ao buscar agendamento: {str(e)}")

            col_btn1, col_btn2, col_btn3 = st.columns(3)

            # Editar
            with col_btn1:
                if st.button("✏️ Editar", key=f"editar_{agendamento_id}"):
                    st.session_state['editar_agendamento_id'] = agendamento_id

            # Concluir
            with col_btn2:
                if st.button("✅ Concluir", key=f"concluir_{agendamento_id}"):
                    sucesso, msg = atualizar_status_agendamento(
                        agendamento_id, "concluido")
                    if sucesso:
                        st.success("✅ Agendamento concluído!")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {msg}")

            # Cancelar
            with col_btn3:
                if st.button("❌ Cancelar", key=f"cancelar_{agendamento_id}"):
                    sucesso, msg = atualizar_status_agendamento(
                        agendamento_id, "cancelado")
                    if sucesso:
                        st.warning("🚫 Agendamento cancelado!")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {msg}")

            # Formulário de edição (aparece quando session_state indica)
            if st.session_state.get('editar_agendamento_id') == agendamento_id and ag is not None:
                st.markdown("---")
                st.markdown("### ✏️ Editar Agendamento")

                try:
                    df_clientes = get_clientes_from_db()
                    df_servicos = get_servicos_from_db()

                    # encontra índices iniciais por id
                    try:
                        cliente_idx = int(
                            df_clientes.index[df_clientes['id'] == ag['cliente_id']].tolist()[0])
                    except Exception:
                        cliente_idx = 0
                    try:
                        servico_idx = int(
                            df_servicos.index[df_servicos['id'] == ag['servico_id']].tolist()[0])
                    except Exception:
                        servico_idx = 0

                    with st.form(f"form_editar_{agendamento_id}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            cliente_idx_new = st.selectbox("👤 Cliente:", options=range(len(df_clientes)),
                                                           format_func=lambda x: f"{df_clientes.iloc[x]['nome']} - {df_clientes.iloc[x]['telefone']}",
                                                           index=cliente_idx)
                            data_edit = st.date_input(
                                "📅 Data:", value=datetime.strptime(ag['data'], "%Y-%m-%d").date())
                        with col2:
                            servico_idx_new = st.selectbox("💇 Serviço:", options=range(len(df_servicos)),
                                                           format_func=lambda x: f"{df_servicos.iloc[x]['nome']} - R$ {df_servicos.iloc[x]['preco']:.2f} ({df_servicos.iloc[x]['duracao']}min)",
                                                           index=servico_idx)
                            hora_edit = st.time_input(
                                "⏰ Horário:", value=datetime.strptime(ag['hora'], "%H:%M").time())
                        status_options = [
                            'agendado', 'confirmado', 'concluido', 'cancelado', 'faltou']
                        try:
                            status_index = status_options.index(
                                ag.get('status', 'agendado'))
                        except ValueError:
                            status_index = 0
                        status_edit = st.selectbox(
                            "📊 Status:", options=status_options, index=status_index)

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            salvar = st.form_submit_button("💾 Salvar")
                        with col_btn2:
                            fechar = st.form_submit_button("❌ Fechar")

                        if fechar:
                            st.session_state['editar_agendamento_id'] = None
                            st.rerun()

                        if salvar:
                            cliente_id_new = int(
                                df_clientes.iloc[cliente_idx_new]['id'])
                            servico_id_new = int(
                                df_servicos.iloc[servico_idx_new]['id'])
                            duracao_new = int(
                                df_servicos.iloc[servico_idx_new]['duracao'])
                            data_str_new = data_edit.strftime("%Y-%m-%d")
                            hora_str_new = hora_edit.strftime("%H:%M")

                            # verificar conflitos, excluindo o próprio agendamento
                            conflitos = verificar_conflito_horario(
                                data_str_new, hora_str_new, duracao_new, agendamento_id=agendamento_id)
                            if conflitos:
                                st.error(
                                    "⚠️ Conflito de horário detectado! Não foi possível salvar.")
                                for conflito in conflitos:
                                    st.warning(
                                        f"• {conflito['cliente']} - {conflito['servico']} às {conflito['hora']}")
                            else:
                                sucesso, msg = atualizar_agendamento(
                                    agendamento_id,
                                    cliente_id_new,
                                    servico_id_new,
                                    data_str_new,
                                    hora_str_new,
                                    status_edit
                                )
                                if sucesso:
                                    st.success("✅ Agendamento atualizado!")
                                    st.session_state['editar_agendamento_id'] = None
                                    time.sleep(0.8)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {msg}")

                except Exception as e:
                    st.error(
                        f"Erro ao carregar clientes/serviços para edição: {str(e)}")

    # Legenda de status
    st.markdown("---")
    st.markdown("### 🏷️ Legenda de Status")
    status_colors = {
        'Agendado': '#28a745',
        'Confirmado': '#17a2b8',
        'Em Andamento': '#ffc107',
        'Concluído': '#6f42c1',
        'Cancelado': '#dc3545',
        'Faltou': '#6c757d'
    }
    cols = st.columns(len(status_colors))
    for i, (status, color) in enumerate(status_colors.items()):
        with cols[i]:
            st.markdown(f"""
            <div style='background-color: {color}; color: white; padding: 5px; border-radius: 3px; text-align: center; font-size: 12px;'>
                <strong>{status}</strong>
            </div><br>
            """, unsafe_allow_html=True)

    # if st.checkbox("Formato de Tabela"):

    def criar_item_mercadopago(row):
        items = [
            {
                "id": str(row['id']),  # ID do agendamento
                "title": row['servico_nome'],  # Nome do serviço
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(row['preco'])  # Preço do serviço
            }
        ]
        url_real = gerar_link(items)
        # Retorna o link em formato markdown
        return url_real

    # df_agendamentos['link'] = df_agendamentos['preco'].apply(
    #     lambda preco: f"https://seusite.com/detalhes?preco={preco}"
    # )

    df_agendamentos['link'] = df_agendamentos.apply(
        criar_item_mercadopago, axis=1)

    df_agendamentos['data'] = pd.to_datetime(
        df_agendamentos['data']).dt.strftime('%d/%m/%Y')

    st.dataframe(
        df_agendamentos,
        column_config={
            "link": st.column_config.LinkColumn("Link de Pagamento")
        }
    )


if __name__ == "__main__":
    createCalendar()
