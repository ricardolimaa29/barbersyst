# # from datetime import datetime, timedelta
# # import streamlit as st
# # import sqlite3
# # import pandas as pd

# # # ---------- Configuração da Página ----------
# # st.set_page_config(
# #     page_title="Sistema de Feedbacks - Barbearia",
# #     page_icon="⭐",
# #     layout="wide"
# # )

# # # ---------- Conexão ----------


# # def get_connection():
# #     return sqlite3.connect("barbearia.db", check_same_thread=False)


# # def get_feedbacks():
# #     """Retorna todos os feedbacks"""
# #     conn = get_connection()
# #     try:
# #         df = pd.read_sql("""
# #             SELECT
# #                 f.id_feedback,
# #                 f.id_agendamento,
# #                 f.id_cliente,
# #                 c.nome as nome_cliente,
# #                 f.nota,
# #                 f.comentario,
# #                 f.data_feedback
# #             FROM feedbacks f
# #             LEFT JOIN clientes c ON f.id_cliente = c.id
# #             ORDER BY f.data_feedback DESC
# #         """, conn)
# #         return df
# #     except:
# #         # Se não houver tabela de clientes, retorna sem JOIN
# #         df = pd.read_sql(
# #             "SELECT * FROM feedbacks ORDER BY data_feedback DESC", conn)
# #         return df
# #     finally:
# #         conn.close()


# # def get_feedback_stats():
# #     """Retorna estatísticas dos feedbacks"""
# #     conn = get_connection()
# #     try:
# #         stats = pd.read_sql("""
# #             SELECT
# #                 COUNT(*) as total_feedbacks,
# #                 AVG(nota) as nota_media,
# #                 COUNT(CASE WHEN nota >= 4 THEN 1 END) as feedbacks_positivos,
# #                 COUNT(CASE WHEN nota <= 2 THEN 1 END) as feedbacks_negativos
# #             FROM feedbacks
# #         """, conn)

# #         notas_dist = pd.read_sql("""
# #             SELECT nota, COUNT(*) as quantidade
# #             FROM feedbacks
# #             GROUP BY nota
# #             ORDER BY nota
# #         """, conn)

# #         return stats, notas_dist
# #     except:
# #         return pd.DataFrame(), pd.DataFrame()
# #     finally:
# #         conn.close()


# # def update_feedback(id_feedback, nota, comentario):
# #     """Atualiza um feedback existente"""
# #     conn = get_connection()
# #     c = conn.cursor()
# #     try:
# #         c.execute("""
# #             UPDATE feedbacks
# #             SET nota = ?, comentario = ?
# #             WHERE id_feedback = ?
# #         """, (nota, comentario, id_feedback))
# #         conn.commit()
# #         return True
# #     except sqlite3.Error as e:
# #         st.error(f"Erro ao atualizar feedback: {e}")
# #         return False
# #     finally:
# #         conn.close()


# # def delete_feedback(id_feedback):
# #     """Exclui um feedback"""
# #     conn = get_connection()
# #     c = conn.cursor()
# #     try:
# #         c.execute("DELETE FROM feedbacks WHERE id_feedback = ?", (id_feedback,))
# #         conn.commit()
# #         return True
# #     except sqlite3.Error as e:
# #         st.error(f"Erro ao excluir feedback: {e}")
# #         return False
# #     finally:
# #         conn.close()

# # # ---------- Funções Auxiliares ----------


# # def get_emoji_nota(nota):
# #     """Retorna emoji baseado na nota"""
# #     emojis = {1: "😞", 2: "😐", 3: "🙂", 4: "😊", 5: "🤩"}
# #     return emojis.get(nota, "⭐")


# # def format_date(date_str):
# #     """Formata data para exibição"""
# #     try:
# #         dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
# #         return dt.strftime("%d/%m/%Y às %H:%M")
# #     except:
# #         return date_str

# # # ---------- Interface Principal ----------


# # def get_feedbacks_interface():

# #     st.title("⭐ Sistema de Gestão de Feedbacks")

# #     # Get all data once
# #     df_all = get_feedbacks()

# #     # Filtros na página principal
# #     if not df_all.empty:
# #         col1, col2 = st.columns([2, 2])

# #         with col1:
# #             periodo = st.selectbox(
# #                 "📅 Período",
# #                 ["Todos", "Últimos 7 dias", "Último mês", "Últimos 3 meses"]
# #             )

# #         with col2:
# #             st.write("")  # Spacing
# #             if st.button("🔄 Atualizar", type="secondary"):
# #                 st.rerun()
# #     else:
# #         periodo = "Todos"

# #     # Aplicar filtros
# #     df_filtered = df_all.copy()
# #     if not df_filtered.empty:

# #         if periodo != "Todos":
# #             hoje = datetime.now()
# #             if periodo == "Últimos 7 dias":
# #                 data_limite = hoje - timedelta(days=7)
# #             elif periodo == "Último mês":
# #                 data_limite = hoje - timedelta(days=30)
# #             elif periodo == "Últimos 3 meses":
# #                 data_limite = hoje - timedelta(days=90)

# #             df_filtered['data_feedback'] = pd.to_datetime(
# #                 df_filtered['data_feedback'])
# #             df_filtered = df_filtered[df_filtered['data_feedback']
# #                                       >= data_limite]

# #     st.divider()

# #     # Tabs principais
# #     tab1 = st.tabs(
# #         ["📋 Feedbacks"])[0]

# #     with tab1:
# #         st.subheader("📋 Lista de Feedbacks")

# #         if not df_filtered.empty:
# #             st.write(f"**{len(df_filtered)} feedbacks encontrados**")
# #             st.write("")

# #             # Lista de feedbacks mais clean
# #             for _, row in df_filtered.iterrows():
# #                 with st.container():
# #                     col1, col2, col3 = st.columns([5, 1, 1])

# #                     with col1:
# #                         cliente_nome = row.get(
# #                             'nome_cliente', f"Cliente #{row['id_cliente']}")
# #                         st.write(
# #                             f"**{get_emoji_nota(row['nota'])} {cliente_nome}**")
# #                         st.caption(
# #                             f"📅 {format_date(str(row['data_feedback']))} | 📝 Agendamento #{row['id_agendamento']}")
# #                         if row['comentario']:
# #                             st.write(f"💬 *{row['comentario']}*")

# #                     with col2:
# #                         st.metric("Nota", f"{row['nota']}/5")

# #                     with col3:
# #                         st.write("")
# #                         col_edit, col_del = st.columns(2)
# #                         with col_edit:
# #                             if st.button("✏️", key=f"edit_{row['id_feedback']}", help="Editar", use_container_width=True):
# #                                 st.session_state["edit_id"] = row['id_feedback']
# #                         with col_del:
# #                             if st.button("🗑️", key=f"del_{row['id_feedback']}", help="Excluir", use_container_width=True):
# #                                 st.session_state["delete_id"] = row['id_feedback']

# #                 st.divider()

# #             # Dialogs de edição e exclusão
# #             handle_edit_dialog(df_filtered)
# #             handle_delete_dialog()
# #         else:
# #             st.info("📝 Nenhum feedback encontrado com os filtros aplicados.")


# # def handle_edit_dialog(df_filtered):
# #     """Gerencia o dialog de edição"""
# #     if "edit_id" in st.session_state:
# #         edit_id = st.session_state["edit_id"]
# #         feedback_row = df_filtered[df_filtered["id_feedback"]
# #                                    == edit_id].iloc[0]

# #         @st.dialog("✏️ Editar Feedback")
# #         def edit_dialog():
# #             st.write(f"**Editando Feedback #{edit_id}**")

# #             new_nota = st.slider(
# #                 "Nova Nota",
# #                 1, 5,
# #                 int(feedback_row["nota"])
# #             )

# #             new_comentario = st.text_area(
# #                 "Novo Comentário",
# #                 value=feedback_row["comentario"] or "",
# #                 height=100
# #             )

# #             col1, col2 = st.columns(2)
# #             with col1:
# #                 if st.button("💾 Salvar alterações", type="primary"):
# #                     if update_feedback(edit_id, new_nota, new_comentario):
# #                         st.success("✅ Feedback atualizado com sucesso!")
# #                         del st.session_state["edit_id"]
# #                         st.rerun()

# #             with col2:
# #                 if st.button("❌ Cancelar"):
# #                     del st.session_state["edit_id"]
# #                     st.rerun()

# #         edit_dialog()


# # def handle_delete_dialog():
# #     """Gerencia o dialog de exclusão"""
# #     if "delete_id" in st.session_state:
# #         delete_id = st.session_state["delete_id"]

# #         @st.dialog("🗑️ Confirmar Exclusão")
# #         def delete_dialog():
# #             st.warning(
# #                 f"⚠️ Tem certeza que deseja excluir o feedback #{delete_id}?")
# #             st.write("Esta ação não pode ser desfeita.")

# #             col1, col2 = st.columns(2)
# #             with col1:
# #                 if st.button("🗑️ Sim, excluir", type="primary"):
# #                     if delete_feedback(delete_id):
# #                         st.success("✅ Feedback excluído com sucesso!")
# #                         del st.session_state["delete_id"]
# #                         st.rerun()

# #             with col2:
# #                 if st.button("❌ Cancelar"):
# #                     del st.session_state["delete_id"]
# #                     st.rerun()

# #         delete_dialog()


# # if __name__ == "__main__":
# #     get_feedbacks_interface()


# from datetime import datetime, timedelta
# import streamlit as st
# import sqlite3
# import pandas as pd

# # ---------- Configuração da Página ----------
# st.set_page_config(
#     page_title="Sistema de Feedbacks - Barbearia",
#     page_icon="⭐",
#     layout="wide"
# )

# # ---------- Conexão ----------


# def get_connection():
#     return sqlite3.connect("barbearia.db", check_same_thread=False)


# def get_feedbacks():
#     """Retorna todos os feedbacks"""
#     conn = get_connection()
#     try:
#         df = pd.read_sql("""
#             SELECT
#                 f.id_feedback,
#                 f.id_agendamento,
#                 f.id_cliente,
#                 c.nome as nome_cliente,
#                 f.nota,
#                 f.comentario,
#                 f.data_feedback
#             FROM feedbacks f
#             LEFT JOIN clientes c ON f.id_cliente = c.id
#             ORDER BY f.data_feedback DESC
#         """, conn)
#         return df
#     except:
#         # Se não houver tabela de clientes, retorna sem JOIN
#         df = pd.read_sql(
#             "SELECT * FROM feedbacks ORDER BY data_feedback DESC", conn)
#         return df
#     finally:
#         conn.close()


# def get_feedback_stats():
#     """Retorna estatísticas dos feedbacks"""
#     conn = get_connection()
#     try:
#         stats = pd.read_sql("""
#             SELECT
#                 COUNT(*) as total_feedbacks,
#                 AVG(nota) as nota_media,
#                 COUNT(CASE WHEN nota >= 4 THEN 1 END) as feedbacks_positivos,
#                 COUNT(CASE WHEN nota <= 2 THEN 1 END) as feedbacks_negativos
#             FROM feedbacks
#         """, conn)

#         notas_dist = pd.read_sql("""
#             SELECT nota, COUNT(*) as quantidade
#             FROM feedbacks
#             GROUP BY nota
#             ORDER BY nota
#         """, conn)

#         return stats, notas_dist
#     except:
#         return pd.DataFrame(), pd.DataFrame()
#     finally:
#         conn.close()


# def update_feedback(id_feedback, nota, comentario):
#     """Atualiza um feedback existente"""
#     conn = get_connection()
#     c = conn.cursor()
#     try:
#         c.execute("""
#             UPDATE feedbacks
#             SET nota = ?, comentario = ?
#             WHERE id_feedback = ?
#         """, (nota, comentario, id_feedback))
#         conn.commit()
#         return True
#     except sqlite3.Error as e:
#         st.error(f"Erro ao atualizar feedback: {e}")
#         return False
#     finally:
#         conn.close()


# def delete_feedback(id_feedback):
#     """Exclui um feedback"""
#     conn = get_connection()
#     c = conn.cursor()
#     try:
#         c.execute("DELETE FROM feedbacks WHERE id_feedback = ?", (id_feedback,))
#         conn.commit()
#         return True
#     except sqlite3.Error as e:
#         st.error(f"Erro ao excluir feedback: {e}")
#         return False
#     finally:
#         conn.close()

# # ---------- Funções Auxiliares ----------


# def get_emoji_nota(nota):
#     """Retorna emoji baseado na nota"""
#     emojis = {1: "😞", 2: "😐", 3: "🙂", 4: "😊", 5: "🤩"}
#     return emojis.get(nota, "⭐")


# def format_date(date_str):
#     """Formata data para exibição"""
#     try:
#         dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
#         return dt.strftime("%d/%m/%Y às %H:%M")
#     except:
#         return date_str

# # ---------- Interface Principal ----------


# def get_feedbacks_interface():

#     st.title("⭐ Sistema de Gestão de Feedbacks")

#     # Get all data once
#     df_all = get_feedbacks()

#     # Filtros na página principal
#     if not df_all.empty:
#         col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

#         with col1:
#             periodo = st.selectbox(
#                 "📅 Período",
#                 ["Todos", "Últimos 7 dias", "Último mês", "Últimos 3 meses"]
#             )

#         with col2:
#             # Meses em português
#             meses_pt = {
#                 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
#                 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
#                 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
#             }
#             opcoes_mes = ["Todos os meses"]
#             hoje = datetime.now()

#             for mes in range(1, 13):
#                 opcoes_mes.append(f"{meses_pt[mes]}")

#             mes_selecionado = st.selectbox(
#                 "📅 Mês específico",
#                 opcoes_mes
#             )

#         with col3:
#             # Últimos 5 anos
#             opcoes_ano = ["Todos os anos"]
#             for ano in range(hoje.year, hoje.year - 6, -1):
#                 opcoes_ano.append(str(ano))

#             ano_selecionado = st.selectbox(
#                 "📅 Ano específico",
#                 opcoes_ano
#             )

#         with col4:
#             st.write("")  # Spacing
#             if st.button("🔄 Atualizar", type="secondary"):
#                 st.rerun()
#     else:
#         periodo = "Todos"
#         mes_selecionado = "Todos os meses"
#         ano_selecionado = "Todos os anos"

#     # Aplicar filtros
#     df_filtered = df_all.copy()
#     if not df_filtered.empty and len(df_filtered) > 0:
#         df_filtered['data_feedback'] = pd.to_datetime(
#             df_filtered['data_feedback'])

#         # Filtro por período
#         if periodo != "Todos":
#             hoje = datetime.now()

#             if periodo == "Últimos 7 dias":
#                 data_limite = hoje - timedelta(days=7)
#                 df_filtered = df_filtered[df_filtered['data_feedback']
#                                           >= data_limite]
#             elif periodo == "Último mês":
#                 data_limite = hoje - timedelta(days=30)
#                 df_filtered = df_filtered[df_filtered['data_feedback']
#                                           >= data_limite]
#             elif periodo == "Últimos 3 meses":
#                 data_limite = hoje - timedelta(days=90)
#                 df_filtered = df_filtered[df_filtered['data_feedback']
#                                           >= data_limite]

#         # Filtro por mês específico
#         if mes_selecionado != "Todos os meses":
#             # Extrair mês e ano do texto selecionado (ex: "Janeiro 2024")
#             try:
#                 meses_pt = {
#                     "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
#                     "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
#                     "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
#                 }
#                 partes = mes_selecionado.split()
#                 mes_nome = partes[0]
#                 ano_mes = int(partes[1])
#                 mes_num = meses_pt[mes_nome]

#                 df_filtered = df_filtered[
#                     (df_filtered['data_feedback'].dt.month == mes_num) &
#                     (df_filtered['data_feedback'].dt.year == ano_mes)
#                 ]
#             except:
#                 pass  # Em caso de erro, não aplica filtro de mês

#         # Filtro por ano específico
#         if ano_selecionado != "Todos os anos":
#             try:
#                 ano_num = int(ano_selecionado)
#                 df_filtered = df_filtered[df_filtered['data_feedback'].dt.year == ano_num]
#             except:
#                 pass  # Em caso de erro, não aplica filtro de ano

#     st.divider()

#     # Corrigido: usando apenas uma aba
#     tab1 = st.tabs(["📋 Feedbacks"])[0]

#     with tab1:
#         st.subheader("📋 Lista de Feedbacks")

#         if not df_filtered.empty:
#             st.write(f"**{len(df_filtered)} feedbacks encontrados**")
#             st.write("")

#             # Lista de feedbacks mais clean
#             for _, row in df_filtered.iterrows():
#                 with st.container():
#                     col1, col2, col3 = st.columns([5, 1, 1])

#                     with col1:
#                         cliente_nome = row.get(
#                             'nome_cliente', f"Cliente #{row['id_cliente']}")
#                         st.write(
#                             f"**{get_emoji_nota(row['nota'])} {cliente_nome}**")
#                         st.caption(
#                             f"📅 {format_date(str(row['data_feedback']))} | 📝 Agendamento #{row['id_agendamento']}")
#                         if row['comentario']:
#                             st.write(f"💬 *{row['comentario']}*")

#                     with col2:
#                         st.metric("Nota", f"{row['nota']}/5")

#                     with col3:
#                         st.write("")
#                         col_edit, col_del = st.columns(2)
#                         with col_edit:
#                             if st.button("✏️", key=f"edit_{row['id_feedback']}", help="Editar", use_container_width=True):
#                                 st.session_state["edit_id"] = row['id_feedback']
#                         with col_del:
#                             if st.button("🗑️", key=f"del_{row['id_feedback']}", help="Excluir", use_container_width=True):
#                                 st.session_state["delete_id"] = row['id_feedback']

#                 st.divider()

#             # Dialogs de edição e exclusão
#             handle_edit_dialog(df_filtered)
#             handle_delete_dialog()
#         else:
#             st.info("📝 Nenhum feedback encontrado com os filtros aplicados.")


# def handle_edit_dialog(df_filtered):
#     """Gerencia o dialog de edição"""
#     if "edit_id" in st.session_state:
#         edit_id = st.session_state["edit_id"]
#         feedback_row = df_filtered[df_filtered["id_feedback"]
#                                    == edit_id].iloc[0]

#         @st.dialog("✏️ Editar Feedback")
#         def edit_dialog():
#             st.write(f"**Editando Feedback #{edit_id}**")

#             new_nota = st.slider(
#                 "Nova Nota",
#                 1, 5,
#                 int(feedback_row["nota"])
#             )

#             new_comentario = st.text_area(
#                 "Novo Comentário",
#                 value=feedback_row["comentario"] or "",
#                 height=100
#             )

#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("💾 Salvar alterações", type="primary"):
#                     if update_feedback(edit_id, new_nota, new_comentario):
#                         st.success("✅ Feedback atualizado com sucesso!")
#                         del st.session_state["edit_id"]
#                         st.rerun()

#             with col2:
#                 if st.button("❌ Cancelar"):
#                     del st.session_state["edit_id"]
#                     st.rerun()

#         edit_dialog()


# def handle_delete_dialog():
#     """Gerencia o dialog de exclusão"""
#     if "delete_id" in st.session_state:
#         delete_id = st.session_state["delete_id"]

#         @st.dialog("🗑️ Confirmar Exclusão")
#         def delete_dialog():
#             st.warning(
#                 f"⚠️ Tem certeza que deseja excluir o feedback #{delete_id}?")
#             st.write("Esta ação não pode ser desfeita.")

#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("🗑️ Sim, excluir", type="primary"):
#                     if delete_feedback(delete_id):
#                         st.success("✅ Feedback excluído com sucesso!")
#                         del st.session_state["delete_id"]
#                         st.rerun()

#             with col2:
#                 if st.button("❌ Cancelar"):
#                     del st.session_state["delete_id"]
#                     st.rerun()

#         delete_dialog()


# if __name__ == "__main__":
#     get_feedbacks_interface()


from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import pandas as pd

# ---------- Configuração da Página ----------
st.set_page_config(
    page_title="Sistema de Feedbacks - Barbearia",
    page_icon="⭐",
    layout="wide"
)

# ---------- Conexão ----------


def get_connection():
    return sqlite3.connect("barbearia.db", check_same_thread=False)


def get_feedbacks():
    """Retorna todos os feedbacks"""
    conn = get_connection()
    try:
        df = pd.read_sql("""
            SELECT 
                f.id_feedback,
                f.id_agendamento,
                f.id_cliente,
                c.nome as nome_cliente,
                f.nota,
                f.comentario,
                f.data_feedback
            FROM feedbacks f
            LEFT JOIN clientes c ON f.id_cliente = c.id
            ORDER BY f.data_feedback DESC
        """, conn)
        return df
    except:
        # Se não houver tabela de clientes, retorna sem JOIN
        df = pd.read_sql(
            "SELECT * FROM feedbacks ORDER BY data_feedback DESC", conn)
        return df
    finally:
        conn.close()


def get_feedback_stats():
    """Retorna estatísticas dos feedbacks"""
    conn = get_connection()
    try:
        stats = pd.read_sql("""
            SELECT 
                COUNT(*) as total_feedbacks,
                AVG(nota) as nota_media,
                COUNT(CASE WHEN nota >= 4 THEN 1 END) as feedbacks_positivos,
                COUNT(CASE WHEN nota <= 2 THEN 1 END) as feedbacks_negativos
            FROM feedbacks
        """, conn)

        notas_dist = pd.read_sql("""
            SELECT nota, COUNT(*) as quantidade
            FROM feedbacks
            GROUP BY nota
            ORDER BY nota
        """, conn)

        return stats, notas_dist
    except:
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()


def update_feedback(id_feedback, nota, comentario):
    """Atualiza um feedback existente"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            UPDATE feedbacks
            SET nota = ?, comentario = ?
            WHERE id_feedback = ?
        """, (nota, comentario, id_feedback))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar feedback: {e}")
        return False
    finally:
        conn.close()


def delete_feedback(id_feedback):
    """Exclui um feedback"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM feedbacks WHERE id_feedback = ?", (id_feedback,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao excluir feedback: {e}")
        return False
    finally:
        conn.close()

# ---------- Funções Auxiliares ----------


def get_emoji_nota(nota):
    """Retorna emoji baseado na nota"""
    emojis = {1: "😞", 2: "😐", 3: "🙂", 4: "😊", 5: "🤩"}
    return emojis.get(nota, "⭐")


def format_date(date_str):
    """Formata data para exibição"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y às %H:%M")
    except:
        return date_str

# ---------- Interface Principal ----------


def get_feedbacks_interface():

    st.title("⭐ Sistema de Gestão de Feedbacks")

    # Get all data once
    df_all = get_feedbacks()

    # Filtros na página principal
    if not df_all.empty:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            periodo = st.selectbox(
                "📅 Período",
                ["Todos", "Últimos 7 dias", "Último mês", "Últimos 3 meses"]
            )

        with col2:
            # Meses em português
            meses_pt = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            opcoes_mes = ["Todos os meses"]
            hoje = datetime.now()

            for mes in range(1, 13):
                opcoes_mes.append(f"{meses_pt[mes]}")

            mes_selecionado = st.selectbox(
                "📅 Mês específico",
                opcoes_mes
            )

        with col3:
            # Últimos 5 anos
            opcoes_ano = ["Todos os anos"]
            for ano in range(hoje.year, hoje.year - 6, -1):
                opcoes_ano.append(str(ano))

            ano_selecionado = st.selectbox(
                "📅 Ano específico",
                opcoes_ano
            )

        with col4:
            st.write("")  # Spacing
            if st.button("🔄 Atualizar", type="secondary"):
                st.rerun()
    else:
        periodo = "Todos"
        mes_selecionado = "Todos os meses"
        ano_selecionado = "Todos os anos"

    # Aplicar filtros
    df_filtered = df_all.copy()
    if not df_filtered.empty and len(df_filtered) > 0:
        df_filtered['data_feedback'] = pd.to_datetime(
            df_filtered['data_feedback'])

        # Filtro por período
        if periodo != "Todos":
            hoje = datetime.now()

            if periodo == "Últimos 7 dias":
                data_limite = hoje - timedelta(days=7)
                df_filtered = df_filtered[df_filtered['data_feedback']
                                          >= data_limite]
            elif periodo == "Último mês":
                data_limite = hoje - timedelta(days=30)
                df_filtered = df_filtered[df_filtered['data_feedback']
                                          >= data_limite]
            elif periodo == "Últimos 3 meses":
                data_limite = hoje - timedelta(days=90)
                df_filtered = df_filtered[df_filtered['data_feedback']
                                          >= data_limite]

        # Filtro por mês específico
        if mes_selecionado != "Todos os meses":
            try:
                meses_pt = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                mes_num = meses_pt[mes_selecionado]

                # Se um ano específico foi selecionado, usar esse ano
                if ano_selecionado != "Todos os anos":
                    ano_filtro = int(ano_selecionado)
                    df_filtered = df_filtered[
                        (df_filtered['data_feedback'].dt.month == mes_num) &
                        (df_filtered['data_feedback'].dt.year == ano_filtro)
                    ]
                else:
                    # Se não, filtrar apenas pelo mês
                    df_filtered = df_filtered[df_filtered['data_feedback'].dt.month == mes_num]
            except:
                pass  # Em caso de erro, não aplica filtro de mês

        # Filtro por ano específico (quando não há filtro de mês)
        elif ano_selecionado != "Todos os anos":
            try:
                ano_num = int(ano_selecionado)
                df_filtered = df_filtered[df_filtered['data_feedback'].dt.year == ano_num]
            except:
                pass  # Em caso de erro, não aplica filtro de ano

    st.divider()

    # Corrigido: usando apenas uma aba
    tab1 = st.tabs(["📋 Feedbacks"])[0]

    with tab1:
        st.subheader("📋 Lista de Feedbacks")

        if not df_filtered.empty:
            st.write(f"**{len(df_filtered)} feedbacks encontrados**")
            st.write("")

            # Lista de feedbacks mais clean
            for _, row in df_filtered.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([5, 1, 1])

                    with col1:
                        cliente_nome = row.get(
                            'nome_cliente', f"Cliente #{row['id_cliente']}")
                        st.write(
                            f"**{get_emoji_nota(row['nota'])} {cliente_nome}**")
                        st.caption(
                            f"📅 {format_date(str(row['data_feedback']))} | 📝 Agendamento #{row['id_agendamento']}")
                        if row['comentario']:
                            st.write(f"💬 *{row['comentario']}*")

                    with col2:
                        st.metric("Nota", f"{row['nota']}/5")

                    with col3:
                        st.write("")
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=f"edit_{row['id_feedback']}", help="Editar", use_container_width=True):
                                st.session_state["edit_id"] = row['id_feedback']
                        with col_del:
                            if st.button("🗑️", key=f"del_{row['id_feedback']}", help="Excluir", use_container_width=True):
                                st.session_state["delete_id"] = row['id_feedback']

                st.divider()

            # Dialogs de edição e exclusão
            handle_edit_dialog(df_filtered)
            handle_delete_dialog()
        else:
            st.info("📝 Nenhum feedback encontrado com os filtros aplicados.")


def handle_edit_dialog(df_filtered):
    """Gerencia o dialog de edição"""
    if "edit_id" in st.session_state:
        edit_id = st.session_state["edit_id"]
        feedback_row = df_filtered[df_filtered["id_feedback"]
                                   == edit_id].iloc[0]

        @st.dialog("✏️ Editar Feedback")
        def edit_dialog():
            st.write(f"**Editando Feedback #{edit_id}**")

            new_nota = st.slider(
                "Nova Nota",
                1, 5,
                int(feedback_row["nota"])
            )

            new_comentario = st.text_area(
                "Novo Comentário",
                value=feedback_row["comentario"] or "",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar alterações", type="primary"):
                    if update_feedback(edit_id, new_nota, new_comentario):
                        st.success("✅ Feedback atualizado com sucesso!")
                        del st.session_state["edit_id"]
                        st.rerun()

            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state["edit_id"]
                    st.rerun()

        edit_dialog()


def handle_delete_dialog():
    """Gerencia o dialog de exclusão"""
    if "delete_id" in st.session_state:
        delete_id = st.session_state["delete_id"]

        @st.dialog("🗑️ Confirmar Exclusão")
        def delete_dialog():
            st.warning(
                f"⚠️ Tem certeza que deseja excluir o feedback #{delete_id}?")
            st.write("Esta ação não pode ser desfeita.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Sim, excluir", type="primary"):
                    if delete_feedback(delete_id):
                        st.success("✅ Feedback excluído com sucesso!")
                        del st.session_state["delete_id"]
                        st.rerun()

            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state["delete_id"]
                    st.rerun()

        delete_dialog()


if __name__ == "__main__":
    get_feedbacks_interface()
