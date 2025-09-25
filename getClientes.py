# import streamlit as st
# from streamlit import components
# import sqlite3
# from datetime import datetime, timedelta


# def excluir_cliente(cliente_id):
#     conn = sqlite3.connect("barbearia.db")
#     conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
#     conn.commit()
#     conn.close()


# def editar_cliente(cliente_id, nome, telefone, email):
#     conn = sqlite3.connect("barbearia.db")
#     conn.execute("""
#         UPDATE clientes
#         SET nome = ?, telefone = ?, email = ?
#         WHERE id = ?
#     """, (nome, telefone, email, cliente_id))
#     conn.commit()
#     conn.close()


# def bloquear_cliente(cliente_id, horas):
#     conn = sqlite3.connect("barbearia.db")
#     ate = datetime.now() + timedelta(hours=horas)
#     conn.execute("""
#         UPDATE clientes
#         SET bloqueado_ate = ?
#         WHERE id = ?
#     """, (ate.strftime("%Y-%m-%d %H:%M:%S"), cliente_id))
#     conn.commit()
#     conn.close()


# def desbloquear_cliente(cliente_id):
#     conn = sqlite3.connect("barbearia.db")
#     conn.execute(
#         "UPDATE clientes SET bloqueado_ate = NULL WHERE id = ?", (cliente_id,))
#     conn.commit()
#     conn.close()


# def obter_stats_cliente(cliente_id):
#     """Obter estatísticas do cliente do banco de dados"""
#     try:
#         conn = sqlite3.connect("barbearia.db")

#         # Total de agendamentos
#         cursor = conn.execute(
#             "SELECT COUNT(*) FROM agendamentos WHERE cliente_id = ?", (cliente_id,))
#         total_agendamentos = cursor.fetchone()[0]

#         # Último agendamento
#         cursor = conn.execute(
#             "SELECT MAX(data) FROM agendamentos WHERE cliente_id = ? AND status = 'concluido'", (cliente_id,))
#         ultimo = cursor.fetchone()[0]
#         ultimo_agendamento = ultimo if ultimo else "Nunca"

#         # Próximo agendamento
#         cursor = conn.execute(
#             "SELECT MIN(data) FROM agendamentos WHERE cliente_id = ? AND status = 'agendado' AND data >= date('now')", (cliente_id,))
#         proximo = cursor.fetchone()[0]
#         proximo_agendamento = datetime.strptime(
#             proximo, '%Y-%m-%d').strftime('%d/%m/%y') if proximo else "Não"

#         conn.close()

#         return {
#             'total': total_agendamentos,
#             'ultimo': ultimo_agendamento,
#             'proximo': proximo_agendamento
#         }
#     except:
#         return {'total': 0, 'ultimo': 'Nunca', 'proximo': 'Não'}


# def listar_clientes_st(clientes):

#     st.subheader("📋 Lista de Clientes")

#     if not clientes:
#         st.warning("Nenhum cliente encontrado.")
#         st.info("💡 Cadastre o primeiro cliente para começar!")
#         return

#     # CSS (string normal - sem f-string)
#     css = """
#     .clientes-container {
#         display: grid;
#         grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
#         gap: 20px;
#         margin: 20px 0;
#     }

#     .cliente-card {
#         border: 1px solid #e1e5e9;
#         border-radius: 12px;
#         background: white;
#         box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
#         overflow: hidden;
#         transition: all 0.3s ease;
#         position: relative;
#     }

#     .cliente-card:hover {
#         box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
#         transform: translateY(-2px);
#     }

#     .cliente-header {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 16px;
#         position: relative;
#     }

#     .cliente-avatar {
#         font-family: "Source Sans", sans-serif;
#         width: 60px;
#         height: 60px;
#         border-radius: 50%;
#         background: rgba(255, 255, 255, 0.2);
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-size: 24px;
#         margin-bottom: 10px;
#     }

#     .cliente-name {
#         font-family: "Source Sans", sans-serif;
#         font-size: 1.25em;
#         font-weight: bold;
#         margin: 0;
#     }

#     .cliente-status {
#         font-family: "Source Sans", sans-serif;
#         position: absolute;
#         top: 12px;
#         right: 12px;
#         background: rgba(255, 255, 255, 0.9);
#         color: #333;
#         padding: 4px 8px;
#         border-radius: 12px;
#         font-size: 0.75em;
#         font-weight: 500;
#     }

#     .cliente-body {
#         font-family: "Source Sans", sans-serif;
#         padding: 16px;
#     }

#     .cliente-info {
#         font-family: "Source Sans", sans-serif;
#         display: flex;
#         flex-direction: column;
#         gap: 8px;
#         margin-bottom: 16px;
#     }

#     .info-item {
#         display: flex;
#         align-items: center;
#         gap: 8px;
#         font-size: 0.9em;
#         color: #666;
#     }

#     .info-icon {
#         width: 16px;
#         height: 16px;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#     }

#     .cliente-stats {
#         display: flex;
#         justify-content: space-between;
#         padding-top: 12px;
#         border-top: 1px solid #f0f0f0;
#         margin-top: 12px;
#     }

#     .stat-item {
#         text-align: center;
#         flex: 1;
#     }

#     .stat-number {
#         font-size: 1.1em;
#         font-weight: bold;
#         color: #333;
#         display: block;
#     }

#     .stat-label {
#         font-size: 0.75em;
#         color: #888;
#         margin-top: 2px;
#     }

#     .cliente-actions {
#         padding: 12px 16px;
#         background: #f8f9fa;
#         border-top: 1px solid #e9ecef;
#     }

#     .btn-action {
#         width: 100%;
#         padding: 8px 16px;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         border: none;
#         border-radius: 8px;
#         font-size: 0.9em;
#         font-weight: 500;
#         cursor: pointer;
#         transition: all 0.2s ease;
#     }

#     .btn-action:hover {
#         transform: translateY(-1px);
#         box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
#     }

#     @media (prefers-color-scheme: dark) {
#         .cliente-card {
#             background: #1e1e1e;
#             border-color: #333;
#             color: white;
#         }

#         .cliente-body { color: #e0e0e0; }
#         .info-item { color: #ccc; }
#         .cliente-actions {
#             background: #2d2d2d;
#             border-top-color: #444;
#         }

#         .stat-number {
#             font-size: 1.1em;
#             font-weight: bold;
#             color: white;
#             display: block;
#         }
#     }
#     """

#     # Começa o HTML
#     cards_html = '<!doctype html><html><head><meta charset="utf-8"><style>' + \
#         css + '</style></head><body>'
#     cards_html += '<div class="clientes-container">'

#     for cliente in clientes:
#         cliente_id = cliente[0]
#         nome = cliente[1] if len(cliente) > 1 else "Nome não informado"
#         telefone = cliente[2] if len(cliente) > 2 else "Não informado"
#         email = cliente[3] if len(cliente) > 3 else "Não informado"

#         stats = obter_stats_cliente(cliente_id)

#         avatar_letra = nome[0].upper() if nome else "?"
#         if stats['proximo'] == "Sim":
#             status = "🟢 Ativo"
#             status_color = "#22c55e"
#         elif stats['total'] > 0:
#             status = "🟡 Regular"
#             status_color = "#eab308"
#         else:
#             status = "🔵 Novo"
#             status_color = "#3b82f6"

#         if stats['ultimo'] != "Nunca":
#             try:
#                 ultimo_formatado = datetime.strptime(
#                     stats['ultimo'], '%Y-%m-%d').strftime('%d/%m/%y')
#             except:
#                 ultimo_formatado = stats['ultimo']
#         else:
#             ultimo_formatado = "Nunca"

#         # montar o card (uso f-strings somente em partes pequeninas)
#         card_html = (
#             '<div class="cliente-card">'
#             '<div class="cliente-header">'
#             f'<div class="cliente-avatar">{avatar_letra}</div>'
#             f'<h3 class="cliente-name">{nome}</h3>'
#             f'<div class="cliente-status" style="color: {status_color};">{status}</div>'
#             '</div>'
#             '<div class="cliente-body">'
#             '<div class="cliente-info">'
#             '<div class="info-item"><div class="info-icon">📞</div>' +
#             f'<span>{telefone}</span>' + '</div>'
#             '<div class="info-item"><div class="info-icon">✉️</div>' +
#             f'<span>{email}</span>' + '</div>'
#             '</div>'
#             '<div class="cliente-stats">'
#             '<div class="stat-item">' +
#             f'<span class="stat-number">{stats["total"]}</span>' +
#             '<div class="stat-label">Agendamentos</div></div>'
#             '<div class="stat-item">' +
#             f'<span class="stat-number">{ultimo_formatado}</span>' +
#             '<div class="stat-label">Último</div></div>'
#             '<div class="stat-item">' +
#             f'<span class="stat-number">{stats["proximo"] if stats["proximo"] != "Não" else "✗"}</span>' +
#             '<div class="stat-label">Próximo</div></div>'
#             '</div>'
#             '</div>'
#             '<div class="cliente-actions">'
#             "<button class='btn-action' onclick={st.baloons}>Ver Detalhes</button>"
#             '</div>'
#             '</div>'
#         )

#         cards_html += card_html

#     cards_html += '</div></body></html>'

#     # calcula height dinâmico (ajuste conforme necessário)
#     height = min(1200, 250 + len(clientes) * 220)

#     # Informação do total
#     st.info(f"📊 Total de clientes: {len(clientes)}")

#     # Renderiza dentro do iframe do componente (CSS incluso)
#     components.v1.html(cards_html, height=height, scrolling=True)

import streamlit as st
import sqlite3
from datetime import datetime, timedelta


def excluir_cliente(cliente_id):
    conn = sqlite3.connect("barbearia.db")
    conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()


def editar_cliente(cliente_id, nome, telefone, email, obs):
    conn = sqlite3.connect("barbearia.db")
    conn.execute("""
        UPDATE clientes
        SET nome = ?, telefone = ?, email = ?, obs = ?
        WHERE id = ?
    """, (nome, telefone, email, obs, cliente_id))
    conn.commit()
    conn.close()


def bloquear_cliente(cliente_id, horas):
    conn = sqlite3.connect("barbearia.db")
    ate = datetime.now() + timedelta(hours=horas)
    conn.execute("""
        UPDATE clientes
        SET bloqueado_ate = ?
        WHERE id = ?
    """, (ate.strftime("%Y-%m-%d %H:%M:%S"), cliente_id))
    conn.commit()
    conn.close()


def desbloquear_cliente(cliente_id):
    conn = sqlite3.connect("barbearia.db")
    conn.execute(
        "UPDATE clientes SET bloqueado_ate = NULL WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()


def obter_stats_cliente(cliente_id):
    """Obter estatísticas do cliente do banco de dados"""
    try:
        conn = sqlite3.connect("barbearia.db")

        # Total de agendamentos
        cursor = conn.execute(
            "SELECT COUNT(*) FROM agendamentos WHERE cliente_id = ?", (cliente_id,))
        total_agendamentos = cursor.fetchone()[0]

        # Último agendamento
        cursor = conn.execute(
            "SELECT MAX(data) FROM agendamentos WHERE cliente_id = ? AND status = 'concluido'", (cliente_id,))
        ultimo = cursor.fetchone()[0]
        ultimo_agendamento = ultimo if ultimo else "Nunca"

        # Próximo agendamento
        cursor = conn.execute(
            "SELECT MIN(data) FROM agendamentos WHERE cliente_id = ? AND status = 'agendado' AND data >= date('now')", (cliente_id,))
        proximo = cursor.fetchone()[0]
        proximo_agendamento = datetime.strptime(
            proximo, '%Y-%m-%d').strftime('%d/%m/%y') if proximo else "Não"

        conn.close()

        return {
            'total': total_agendamentos,
            'ultimo': ultimo_agendamento,
            'proximo': proximo_agendamento
        }
    except:
        return {'total': 0, 'ultimo': 'Nunca', 'proximo': 'Não'}


def verificar_cliente_bloqueado(cliente_id):
    """Verifica se o cliente está bloqueado"""
    try:
        conn = sqlite3.connect("barbearia.db")
        cursor = conn.execute(
            "SELECT bloqueado_ate FROM clientes WHERE id = ?", (cliente_id,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado and resultado[0]:
            bloqueado_ate = datetime.strptime(
                resultado[0], "%Y-%m-%d %H:%M:%S")
            return bloqueado_ate > datetime.now(), bloqueado_ate
        return False, None
    except:
        return False, None


def modal_editar_cliente(cliente_id, nome_atual, telefone_atual, email_atual, obs_atual):
    """Modal para editar cliente usando dialog do Streamlit"""

    @st.dialog("Editar Cliente")
    def edit_dialog():
        st.write(f"**Cliente ID:** {cliente_id}")

        novo_nome = st.text_input(
            "Nome:", value=nome_atual, key=f"edit_nome_{cliente_id}")
        novo_telefone = st.text_input(
            "Telefone:", value=telefone_atual, key=f"edit_tel_{cliente_id}")
        novo_email = st.text_input(
            "Email:", value=email_atual, key=f"edit_email_{cliente_id}")
        novo_obs = st.text_area(
            "Observações:", value=obs_atual, key=f"edit_obs_{cliente_id}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Salvar", type="primary", use_container_width=True):
                if novo_nome.strip():
                    editar_cliente(cliente_id, novo_nome,
                                   novo_telefone, novo_email, novo_obs)
                    st.success("Cliente editado com sucesso!")
                    st.rerun()
                else:
                    st.error("Nome é obrigatório!")

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()

    return edit_dialog


def modal_bloquear_cliente(cliente_id, nome_cliente):
    """Modal para bloquear cliente"""

    @st.dialog("Bloquear Cliente")
    def block_dialog():
        st.write(f"**Bloquear cliente:** {nome_cliente}")
        st.warning(
            "⚠️ O cliente não poderá fazer novos agendamentos durante o período de bloqueio.")

        horas_opcoes = {
            "1 hora": 1,
            "2 horas": 2,
            "6 horas": 6,
            "12 horas": 12,
            "24 horas": 24,
            "48 horas": 48
        }

        periodo_selecionado = st.selectbox(
            "Selecione o período de bloqueio:",
            options=list(horas_opcoes.keys()),
            index=5  # Default: 48 horas
        )

        horas = horas_opcoes[periodo_selecionado]
        data_desbloqueio = datetime.now() + timedelta(hours=horas)

        st.info(
            f"📅 Cliente será desbloqueado em: **{data_desbloqueio.strftime('%d/%m/%Y às %H:%M')}**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚫 Confirmar Bloqueio", type="primary", use_container_width=True):
                bloquear_cliente(cliente_id, horas)
                st.success(f"Cliente bloqueado por {periodo_selecionado}!")
                st.rerun()

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()

    return block_dialog


def modal_confirmar_exclusao(cliente_id, nome_cliente):
    """Modal para confirmar exclusão de cliente"""

    @st.dialog("Confirmar Exclusão")
    def delete_dialog():
        st.error(f"⚠️ **ATENÇÃO: Esta ação não pode ser desfeita!**")
        st.write(
            f"Tem certeza que deseja excluir o cliente **{nome_cliente}**?")
        st.write("Todos os dados relacionados serão perdidos permanentemente.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True):
                excluir_cliente(cliente_id)
                st.success("Cliente excluído com sucesso!")
                st.rerun()

        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()

    return delete_dialog


def listar_clientes_st(clientes):
    """Lista clientes usando componentes nativos do Streamlit"""

    st.subheader("📋 Lista de Clientes")

    if not clientes:
        st.warning("Nenhum cliente encontrado.")
        st.info("💡 Cadastre o primeiro cliente para começar!")
        return

    # Informação do total
    st.info(f"📊 Total de clientes: **{len(clientes)}**")

    # CSS personalizado para cards menores
    st.markdown("""
    <style>
    .stContainer > div {
        padding: 0.5rem !important;
    }
    
    .status-badge {
        padding: 0.15rem 0.4rem;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 500;
        text-align: center;
        display: inline-block;
    }
    
    .status-ativo { background: #dcfce7; color: #166534; }
    .status-bloqueado { background: #fef2f2; color: #dc2626; }
    .status-regular { background: #fef3c7; color: #92400e; }
    .status-novo { background: #dbeafe; color: #1e40af; }
    
    .compact-info {
        font-size: 1.35rem;
        margin: 0.2rem 0;
    }
    
    .compact-metric {
        font-size: 1rem;
        text-align: center;
        line-height: 1.2;
    }
    
    .metric-number {
        font-size: 1.3rem;
        font-weight: bold;
        display: block;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Organizar em colunas (3 clientes por linha para cards menores)
    cols_per_row = 3

    for i in range(0, len(clientes), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, cliente in enumerate(clientes[i:i+cols_per_row]):
            with cols[j]:
                cliente_id = cliente[0]
                nome = cliente[1] if len(cliente) > 1 else "Nome não informado"
                telefone = cliente[2] if len(cliente) > 2 else "Não informado"
                email = cliente[3] if len(cliente) > 3 else "Não informado"
                obs = cliente[5] if len(cliente) > 5 else "-"

                # Verificar se está bloqueado
                esta_bloqueado, bloqueado_ate = verificar_cliente_bloqueado(
                    cliente_id)

                # Obter estatísticas
                stats = obter_stats_cliente(cliente_id)

                # Container do card
                with st.container(border=True):
                    # Cabeçalho com nome e status
                    col_nome, col_status = st.columns([3, 1])

                    with col_nome:
                        st.markdown(f"#### {nome}")

                    with col_status:
                        if esta_bloqueado:
                            st.markdown('<div class="status-badge status-bloqueado">🚫 Bloqueado</div>',
                                        unsafe_allow_html=True)
                        elif stats['proximo'] != "Não":
                            st.markdown('<div class="status-badge status-ativo">🟢 Ativo</div>',
                                        unsafe_allow_html=True)
                        elif stats['total'] > 0:
                            st.markdown('<div class="status-badge status-regular">🟡 Regular</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="status-badge status-novo">🔵 Novo</div>',
                                        unsafe_allow_html=True)

                    # Informações de contato compactas
                    st.markdown(
                        f'<div class="compact-info">📞 {telefone}</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="compact-info">✉️ {email}</div><br>', unsafe_allow_html=True)

                    # Informação de bloqueio se aplicável
                    if esta_bloqueado:
                        st.markdown(f'<div style="color: #dc2626; font-size: 0.95rem;">🚫 Até: {bloqueado_ate.strftime("%d/%m %H:%M")}</div><br>',
                                    unsafe_allow_html=True)

                    # Estatísticas compactas
                    col_stats1, col_stats2, col_stats3 = st.columns(3)

                    with col_stats1:
                        st.markdown(f'<div class="compact-metric"><span class="metric-number">{stats["total"]}</span><div class="metric-label">Agend</div></div>',
                                    unsafe_allow_html=True)

                    with col_stats2:
                        ultimo_formatado = "—"
                        if stats['ultimo'] != "Nunca":
                            try:
                                ultimo_formatado = datetime.strptime(
                                    stats['ultimo'], '%Y-%m-%d').strftime('%d/%m')
                            except:
                                ultimo_formatado = "—"
                        st.markdown(f'<div class="compact-metric"><span class="metric-number">{ultimo_formatado}</span><div class="metric-label">Último</div></div>',
                                    unsafe_allow_html=True)

                    with col_stats3:
                        proximo_texto = "—"
                        if stats['proximo'] != "Não":
                            proximo_texto = stats['proximo']
                        st.markdown(f'<div class="compact-metric"><span class="metric-number">{proximo_texto}</span><div class="metric-label">Próximo</div></div>',
                                    unsafe_allow_html=True)

                    st.markdown("---")

                    # Botões de ação compactos
                    col_btn1, col_btn2, col_btn4 = st.columns(3)

                    with col_btn1:
                        if st.button("✏️", help="Editar", key=f"edit_{cliente_id}", use_container_width=True):
                            edit_dialog = modal_editar_cliente(
                                cliente_id, nome, telefone, email, obs)
                            edit_dialog()

                    with col_btn2:
                        if esta_bloqueado:
                            if st.button("🔓", help="Desbloquear", key=f"unblock_{cliente_id}",
                                         use_container_width=True):
                                desbloquear_cliente(cliente_id)
                                st.success("Desbloqueado!")
                                st.rerun()
                        else:
                            if st.button("🚫", help="Bloquear", key=f"block_{cliente_id}",
                                         use_container_width=True):
                                block_dialog = modal_bloquear_cliente(
                                    cliente_id, nome)
                                block_dialog()

                    # with col_btn3:
                    #     if st.button("📊", help="Detalhes", key=f"details_{cliente_id}", use_container_width=True):
                    #         st.info(
                    #             f"{obs if obs else 'Sem observações.'}")

                    with col_btn4:
                        if st.button("🗑️", help="Excluir", key=f"delete_{cliente_id}",
                                     use_container_width=True):
                            delete_dialog = modal_confirmar_exclusao(
                                cliente_id, nome)
                            delete_dialog()

                    if st.button("📊 Ver Observações", key=f"details_{cliente_id}", use_container_width=True):
                        st.info(f"{obs if obs else 'Sem observações.'}")


# Função principal para testar (opcional)
def main():
    st.set_page_config(
        page_title="Sistema de Clientes - Barbearia",
        page_icon="💇‍♂️",
        layout="wide"
    )

    st.title("💇‍♂️ Sistema de Clientes - Barbearia")


if __name__ == "__main__":
    main()
