import streamlit as st
import time # Para medir a latência
import pandas as pd
import plotly.express as px # Usado para o gráfico de distribuição
from datetime import date
from src.carregamento_de_dados import carregar_dados_rfm_agregado
from src.inicializador_global import inicializar_dados

# Inicializa os dados globais necessários para a aplicação
inicializar_dados()

# Configuração da página
st.set_page_config(layout="wide")

# Layout da página 3 - Clientes e Fidelidade
st.title("👤 Análise de Clientes e Fidelidade")
st.subheader("Modelagem de Risco e Lealdade dos Clientes (RFM)")

# Explicação do Modelo RFM
with st.expander("❓ O que é o Modelo RFM?", expanded=False):
    st.markdown("""
    O Modelo RFM (Recência, Frequência, Valor Monetário) é uma ferramenta para avaliar a **Lealdade e o Risco de Perda** de cada cliente.
    
    Ele se baseia em três critérios de compra simples:
    
    * **Recência (R):** Há quantos dias o cliente fez a **última compra**? *(Quanto menor o número de dias, melhor!)*
    * **Frequência (F):** Quantas **compras ele fez** no total? *(Quanto mais compras, melhor!)*
    * **Valor Monetário (M):** Quanto ele **gastou** conosco até hoje? *(Usado para priorizar quem merece cupons mais valiosos).*
    
    Ao cruzar esses dados, conseguimos identificar nossos "Clientes em Risco" e enviar promoções ou lembretes no momento certo.
    """)
# A data de análise é sempre HOJE
TODAY_DATE = date.today()
# --- SESSÃO 1 RFM AGREGADA ---
# Início da medição de latência
start_time_rfm = time.time()

# Chamada da Função Otimizada (Resultado: 10.000 linhas, que é rápido de processar no Pandas)
df_rfm = carregar_dados_rfm_agregado(data_analise=TODAY_DATE)

end_time_rfm = time.time()
latency_rfm = end_time_rfm - start_time_rfm

# Fim da medição de latência
st.caption(f"Latência da Query RFM Agregada (Cache): {latency_rfm:.2f} segundos")
if df_rfm.empty:
    st.error("Não foi possível carregar os dados de RFM. Verifique a conexão com o banco.")
    st.stop()

st.markdown("---")

# --- FILTROS DE SEGMENTAÇÃO ---

# Determina os limites para os sliders
max_recency = int(df_rfm['recency_days'].max()) if not df_rfm.empty else 365
max_frequency = int(df_rfm['frequency'].max()) if not df_rfm.empty else 100

# Dados dinâmicos sobre os clientes
st.header("📊 Segmentação Dinâmica de Clientes")
st.info("💡 Use os filtros abaixo para definir seus próprios critérios de Recência (há quanto tempo sumiu) e Frequência (quanto comprou antes de sumir).")

# Filtros lado a lado
col_rec, col_freq = st.columns(2)

# Filtro de Recência
with col_rec:
    recency_threshold = st.slider(
        "Recência (Dias Sem Comprar):", 
        min_value=1, max_value=max_recency, value=30, step=7,
        help="Dias desde a última compra. Valores altos indicam maior risco."
    )
# Filtro de Frequência
with col_freq:
    frequency_threshold = st.slider(
        "Frequência (Mínimo de Compras):",
        min_value=1, max_value=max_frequency, value=3,
        help="Quantidade mínima de compras que o cliente fez antes de sumir."
    )

st.markdown("---")

# --- CLIENTES EM RISCO E RETENÇÃO ---
# Abas para separar as análises
tab1, tab2 = st.tabs(["Segmentação de Clientes (RFM Personalizado)", "Distribuição de Lealdade"])

# Análise de Clientes em Risco
# Visualização dos dados da análise do risco de perda de clientes
with tab1:
    df_clientes_selecionados = df_rfm[
        (df_rfm['recency_days'] > recency_threshold) & 
        (df_rfm['frequency'] >= frequency_threshold)
    ].sort_values('monetary', ascending=False)
    
    # Renomeando colunas
    df_clientes_selecionados_display = df_clientes_selecionados[['customer_name', 'recency_days', 'frequency', 'monetary']].head(50).rename(columns={
        'customer_name': 'Nome do Cliente',
        'recency_days': 'Recência (Dias)',
        'frequency': 'Frequência (Total)',
        'monetary': 'Gasto Total (R$)'
    })
    # Título e descrição
    st.markdown("#### Lista de Alvo Gerada pelos Filtros")
    st.info(f"Critérios Atuais: Sumiram há mais de **{recency_threshold} dias** E compraram **{frequency_threshold} ou mais vezes** antes.")
    
    # Total de clientes de acordo com os filtros
    st.metric(
        label=f"Total de Clientes que não compram a {recency_threshold} dias e compraram {frequency_threshold}+ vezes",
        value=f"{len(df_clientes_selecionados):,}".replace(",", ".")
    )
    
    # Visualização da tabela de clientes de acordo com os filtros
    st.markdown("##### Detalhe dos Clientes (Priorizar quem gastou mais)")
    st.dataframe(
        df_clientes_selecionados_display.style.format({
            "Gasto Total (R$)": "R$ {:,.2f}",
            "Recência (Dias)": "{:,.0f} dias",
            "Frequência (Total)": "{:,.0f}x"
        })
        # Destaque em Amarelo/Vermelho para Recência ALTA (clientes sumidos há muito tempo)
        .background_gradient(subset=['Recência (Dias)'], cmap='YlOrRd', low=0.1, high=0.8),
        hide_index=True
    )
    
    st.warning(
        f"**OBSERVAÇÃO:** Esta lista de {len(df_clientes_selecionados)} clientes são seus alvos prioritários. Quanto mais vermelho o campo 'Recência', mais urgente é a reativação."
    )

# --- SESSÃO 2 DISTRIBUIÇÃO DE FREQUÊNCIA ---
# Análise da Distribuição de Frequência
# Visualização do gráfico de distribuição da frequência de compra
with tab2:
    st.markdown("#### Distribuição da Frequência de Compra")
    st.info("Mostra como sua base de clientes se distribui em termos de lealdade.")
    
    # Criando grupos de frequência
    bins = [0, 3, 10, df_rfm['frequency'].max() + 1]
    labels = ['1-3x (Novos/Ocasionais)', '4-10x (Leais)', '10+x (Melhores/VIP)']
    df_rfm['frequency_group'] = pd.cut(df_rfm['frequency'], bins=bins, labels=labels, right=False)
    
    df_frequency_count = df_rfm['frequency_group'].value_counts().reset_index()
    df_frequency_count.columns = ['Quantidade de Vezes (Frequência)', 'Total de Clientes']
    
    # Plotly
    fig_freq = px.bar(
        df_frequency_count, 
        x='Quantidade de Vezes (Frequência)', # Usar novo nome
        y='Total de Clientes',
        title="Base de Clientes por Lealdade",
        color='Quantidade de Vezes (Frequência)', # Cores diferentes para cada barra
        color_discrete_sequence=px.colors.qualitative.Pastel # Paleta de cores suaves
    )
    # Customizando o layout do gráfico
    fig_freq.update_layout(
        title_x=0.1,
        # Definindo a fonte do layout
            font=dict(
                family="Arial, sans-serif",
            ),
            # Definindo a cor da legenda
            legend=dict(
                title_font_color="#000000", 
                font_color="#000000"
            ),
            # Definindo a cor dos rótulos dos eixos
            xaxis_title_font_color="#000000", # Quantidade de Vezes (Frequência)
            yaxis_title_font_color="#000000" # Total de Clientes
            )
    # Exibindo o gráfico
    st.plotly_chart(fig_freq, use_container_width=True)
    
    st.success(
        "**INSIGHT (Sócio/Marketing):** O maior grupo deve ser o de 'Novos/Ocasionais'. O foco estratégico deve ser criar programas de fidelidade para mover esses clientes para os segmentos 'Leais' e 'Melhores/VIP'."
    )