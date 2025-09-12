# boas_vindas.py
import streamlit as st

# ---------------------------
# Configuração da Página
# ---------------------------
st.set_page_config(page_title="Boas-Vindas - Barbearia do Daniel", 
                   page_icon="💈", layout="wide")

# ---------------------------
# Estilos CSS para cards e animações
# ---------------------------
st.markdown("""
<style>
body {
    background-color: #f0f2f6;
}
.card {
    background: linear-gradient(135deg, #ffe6e6, #fff0f5);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    cursor: pointer;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}
h1 {
    font-size: 50px;
    color: #ff4d4d;
    animation: fadeIn 2s ease-in-out;
}
@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}
</style>
""", unsafe_allow_html=True)
print("ola mundo")
# ---------------------------
# Conteúdo da Tela de Boas-Vindas
# ---------------------------
st.markdown('<h1>💈 Bem-vindo à Barbearia do Daniel</h1>', unsafe_allow_html=True)
st.write("Para melhor atendê-lo, gostaríamos de entender algumas coisas antes de agendar. 😊")

# Perguntas simples
cliente_novo = st.radio("👉 É a sua primeira vez conosco?", ["Sim, sou cliente novo", "Não, já sou cliente"], horizontal=True)

objetivo = st.selectbox("👉 O que você procura hoje?", [
    "Corte de cabelo",
    "Barba",
    "Pacote completo",
    "Somente uma visita rápida"
])

humor = st.slider("👉 Como está seu dia hoje?", 0, 10, 5)

st.markdown("<br>", unsafe_allow_html=True)

# Cards interativos
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✂️ Agendar Corte", key="corte"):
        st.session_state['objetivo'] = objetivo
        st.session_state['cliente_novo'] = cliente_novo
        st.session_state['humor'] = humor
        st.success("Redirecionando para o sistema principal...")
        st.stop()

with col2:
    if st.button("💳 Pagamentos / Relatórios", key="pagamentos"):
        st.session_state['objetivo'] = objetivo
        st.session_state['cliente_novo'] = cliente_novo
        st.session_state['humor'] = humor
        st.success("Redirecionando para o sistema principal...")
        st.stop()

with col3:
    if st.button("👥 Clientes / Serviços", key="clientes"):
        st.session_state['objetivo'] = objetivo
        st.session_state['cliente_novo'] = cliente_novo
        st.session_state['humor'] = humor
        st.success("Redirecionando para o sistema principal...")
        st.stop()

st.markdown("<br><br>", unsafe_allow_html=True)
st.info("✨ Clique em uma das opções acima para acessar o sistema principal da barbearia!")

# ---------------------------
# Dica para integração
# ---------------------------
st.write("💡 Obs: Após clicar em uma opção, execute `main.py` normalmente para abrir o sistema principal.")
