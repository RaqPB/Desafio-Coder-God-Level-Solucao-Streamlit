# Homepage.py
import streamlit as st
from src.inicializador_global import inicializar_dados

# Inicializa os dados globais necessários para a aplicação
inicializar_dados()

# Página Inicial da Aplicação
st.set_page_config(layout="wide")
st.title("🍽️ Bem-Vinda Maria à Plataforma Ingrediente Certo")

st.markdown("""
Essa plataforma foi construída para responder as perguntas mais urgentes 
do seu negócio de forma **rápida** e **personalizada**.

Aqui, você tem o poder de explorar seus dados operacionais, de vendas e de clientes 
sem precisar de um time técnico.
""")

st.subheader("🚀 Vamos Começar?")

st.markdown("""
Use o **Menu de Navegação** (na barra lateral) para explorar as principais áreas:

1. **Vendas e Produtos:** Descubra o que mais vende por canal e horário.
2. **Operações e Tempo:** Analise a logística e o tempo de entrega por dia.
3. **Clientes e Fidelidade:** Identifique clientes que precisam de atenção.
""")

#Separador da página
st.markdown("---")

# Botão para começar a explorar a plataforma
st.markdown("Você pode começar sua análise pela **barra lateral** ou no **botão abaixo**:")
if st.button("Começar Análise de Vendas e Produtos"):
    st.switch_page("pages/1_Vendas_e_Produtos.py")