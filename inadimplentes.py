import streamlit as st
import sqlite3
from datetime import datetime


def get_clientes():
    """Busca todos os clientes do banco de dados"""
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("SELECT id, nome, telefone FROM clientes ORDER BY nome")
    clientes = c.fetchall()
    conn.close()
    return clientes


def get_inadimplentes():
    """Busca todos os inadimplentes com informações dos clientes"""
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute('''
        SELECT i.id, c.nome, c.telefone, i.status, i.data_atualizacao
        FROM inadimplentes i
        JOIN clientes c ON i.cliente_id = c.id
        ORDER BY i.data_atualizacao DESC
    ''')
    inadimplentes = c.fetchall()
    conn.close()
    return inadimplentes


def formatar_data_br(data_str):
    """Converte data do formato YYYY-MM-DD para DD/MM/YYYY"""
    try:
        if data_str:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d')
            return data_obj.strftime('%d/%m/%Y')
        return data_str
    except:
        return data_str


def cadastrar_inadimplente(cliente_id, status):
    """Cadastra um novo inadimplente"""
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()

    c.execute("SELECT id FROM inadimplentes WHERE cliente_id = ?", (cliente_id,))
    existe = c.fetchone()

    if existe:
        c.execute('''
            UPDATE inadimplentes 
            SET status = ?, data_atualizacao = DATE('now') 
            WHERE cliente_id = ?
        ''', (status, cliente_id))
        conn.commit()
        conn.close()
        return "atualizado"
    else:
        c.execute('''
            INSERT INTO inadimplentes (cliente_id, status, data_atualizacao) 
            VALUES (?, ?, DATE('now'))
        ''', (cliente_id, status))
        conn.commit()
        conn.close()
        return "cadastrado"


def remover_inadimplente(inadimplente_id):
    """Remove um inadimplente do banco de dados"""
    conn = sqlite3.connect("barbearia.db")
    c = conn.cursor()
    c.execute("DELETE FROM inadimplentes WHERE id = ?", (inadimplente_id,))
    conn.commit()
    conn.close()


def pagina_inadimplentes():
    """Função principal da página de inadimplentes com tabs"""
    st.title("⚠️ Gestão de Inadimplentes")
    st.markdown("---")

    # Criar tabs
    tab1, tab2 = st.tabs(
        ["📋 Listar Inadimplentes", "➕ Cadastrar Inadimplente"])

    # TAB 1: LISTAR INADIMPLENTES
    with tab1:
        st.header("Lista de Inadimplentes")

        inadimplentes = get_inadimplentes()

        if not inadimplentes:
            st.info("📄 Nenhum inadimplente cadastrado.")
            return

        # Filtros
        col1, col2 = st.columns([2, 3])
        with col1:
            filtro_status = st.selectbox(
                "🔍 Filtrar por Status:",
                ["Todos", "Apenas Inadimplentes", "Apenas Regularizados"],
                key="filtro_inadimplentes"
            )

        # Aplicar filtro
        inadimplentes_filtrados = inadimplentes
        if filtro_status == "Apenas Inadimplentes":
            inadimplentes_filtrados = [i for i in inadimplentes if i[3] == 1]
        elif filtro_status == "Apenas Regularizados":
            inadimplentes_filtrados = [i for i in inadimplentes if i[3] == 0]

        if inadimplentes_filtrados:
            # Estatísticas
            total_inadimplentes = len(
                [i for i in inadimplentes_filtrados if i[3] == 1])
            total_regularizados = len(
                [i for i in inadimplentes_filtrados if i[3] == 0])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total de Registros", len(inadimplentes_filtrados))
            with col2:
                st.metric("🔴 Inadimplentes", total_inadimplentes)
            with col3:
                st.metric("🟢 Regularizados", total_regularizados)

            st.markdown("---")

            # Lista de inadimplentes
            for inadimplente in inadimplentes_filtrados:
                id_inadimplente, nome, telefone, status_bool, data_atualizacao = inadimplente
                status_texto = "🔴 Inadimplente" if status_bool else "🟢 Regularizado"
                data_formatada = formatar_data_br(data_atualizacao)

                # Container para cada registro
                with st.container():
                    # Borda colorida baseada no status
                    border_color = "#ff4b4b" if status_bool else "#00ff00"

                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"**👤 {nome}**")
                        st.write(f"📞 {telefone}")

                    with col2:
                        st.write(f"**Status:** {status_texto}")
                        st.write(f"📅 **Atualizado:** {data_formatada}")

                    with col3:
                        if st.button("🗑️ Remover", key=f"remove_{id_inadimplente}", type="secondary"):
                            remover_inadimplente(id_inadimplente)
                            st.success(f"✅ Cliente {nome} removido da lista!")
                            st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("🔍 Nenhum registro encontrado com os filtros aplicados.")

    # TAB 2: CADASTRAR INADIMPLENTE
    with tab2:
        st.header("Cadastro de Inadimplente")

        clientes = get_clientes()

        if not clientes:
            st.warning(
                "⚠️ Nenhum cliente cadastrado. Cadastre clientes primeiro.")
            st.info(
                "💡 **Dica:** Vá até a seção 'Clientes' para cadastrar novos clientes.")
            return

        # Formulário de cadastro
        with st.form("form_inadimplente", clear_on_submit=True):
            st.subheader("📝 Dados do Inadimplente")

            # Seleção de cliente
            opcoes_clientes = [
                f"{cliente[1]} - {cliente[2]}" for cliente in clientes]
            cliente_selecionado = st.selectbox(
                "👤 Selecione o Cliente:",
                opcoes_clientes,
                help="Escolha o cliente que será marcado como inadimplente",
                index=None,
                placeholder="Selecione um cliente..."
            )

            # Status
            col1, col2 = st.columns(2)
            with col1:
                status = st.radio(
                    "📊 Status:",
                    ["🔴 Inadimplente", "🟢 Regularizado"],
                    help="Marque como 'Inadimplente' para clientes em débito ou 'Regularizado' para quem quitou"
                )

            with col2:
                st.info("""
                **ℹ️ Informações:**
                - **Inadimplente**: Cliente com pendências financeiras
                - **Regularizado**: Cliente que quitou todas as dívidas
                - A data será automaticamente registrada como hoje
                """)

            # Botão de submit
            submitted = st.form_submit_button(
                "💾 Salvar Registro", type="secondary", use_container_width=True)

            if submitted:
                if not cliente_selecionado:
                    st.error("❌ Por favor, selecione um cliente!")
                else:
                    # Converter status para boolean
                    status_bool = True if "Inadimplente" in status else False

                    # Pegar o ID do cliente selecionado
                    indice_cliente = opcoes_clientes.index(cliente_selecionado)
                    cliente_id = clientes[indice_cliente][0]
                    cliente_nome = clientes[indice_cliente][1]

                    # Cadastrar/Atualizar
                    resultado = cadastrar_inadimplente(cliente_id, status_bool)

                    if resultado == "cadastrado":
                        st.success(
                            f"✅ **Cliente {cliente_nome}** foi cadastrado como **{status.replace('🔴 ', '').replace('🟢 ', '').lower()}**!")
                        st.balloons()
                    elif resultado == "atualizado":
                        st.success(
                            f"✅ **Status do cliente {cliente_nome}** foi atualizado para **{status.replace('🔴 ', '').replace('🟢 ', '').lower()}**!")
                        st.balloons()

                    # Mostrar informações adicionais
                    data_hoje = datetime.now().strftime('%d/%m/%Y')
                    st.info(f"📅 **Data de registro:** {data_hoje}")

                    # Recarregar a página após 2 segundos
                    import time
                    time.sleep(2)
                    st.rerun()
