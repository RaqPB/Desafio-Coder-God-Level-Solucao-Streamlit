import streamlit as st
import pandas as pd
from datetime import date
from .carregamento_de_dados import carregar_metadados

#   INICIALIZAÇÃO DE VARIÁVEIS DE ESTADO
# Garante que a data de fim exista (default: hoje)
def inicializar_dados():
    if 'end_date' not in st.session_state:
        st.session_state['end_date'] = date.today()
    
    # Garante que a data de início exista (default: 6 meses atrás)
    if 'start_date' not in st.session_state:
        # Converte para datetime para fazer o cálculo e volta para date
        calculated_start_date = (pd.to_datetime(date.today()) - pd.DateOffset(months=6)).date()
        st.session_state['start_date'] = calculated_start_date

# BLOCO DE INICIALIZAÇÃO DE METADADOS
    if 'metadata_loaded' not in st.session_state:
        with st.spinner('Carregando dados estáticos e metadados...'):
            st.session_state['df_stores'], st.session_state['df_channels'] = carregar_metadados()
        st.session_state['metadata_loaded'] = True