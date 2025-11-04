import streamlit as st
import time
import plotly.express as px
from src.carregamento_de_dados import carregar_top_produtos, carregar_ticket_medio_por_canal, carregar_produtos_e_margem, carregar_ticket_medio_por_loja
from src.inicializador_global import inicializar_dados
from src.organizacao_dos_dados import formatar_nome_loja

# Inicializa os dados globais necessários para a aplicação
inicializar_dados()

# Recupera metadados
df_stores = st.session_state['df_stores']
df_channels = st.session_state['df_channels']


# Configuração da página
st.set_page_config(layout="wide")

# Layout da página 1 - Vendas e Produtos
st.title("💰 Análise de Vendas, Produtos e Margens")


# --- FILTROS GLOBAIS ---
# FILTRO DE LOJA E DATA (Barra Lateral)
# Mapeia nome da loja para o ID
store_name_id_map = dict(zip(df_stores['name'], df_stores['id']))
# Filtros Únicos para esta página
with st.sidebar:
    st.header("Filtros Globais")
    
    store_options = df_stores['name'].unique()
    store_options_formatted = [formatar_nome_loja(name) for name in store_options]
    
    selected_store_name_formatted = st.selectbox(
        "Loja (Global):",
        options=store_options_formatted,
        index=0,
        key='global_store_filter' # Adicionando chave para cada loja para evitar avisos
    )
    
    # Usando o nome original (invertido) para buscar o ID correto na query SQL
    original_store_name = store_options[store_options_formatted.index(selected_store_name_formatted)]
    selected_store_id = store_name_id_map[original_store_name]
    
    # FILTRO DE DATA (SIDEBAR)
    date_range = st.date_input(
        "Período de Análise (Global):",
        value=(st.session_state['start_date'], st.session_state['end_date']),
        key='page1_date_range'
    )

    st.info("💡 Estes filtros afetam TODAS as análises nesta página.")

# --- FIM DOS FILTROS GLOBAIS --- #

# Determina as datas de início e fim para as queries
start_date = date_range[0]
end_date = date_range[1]

# --- DISPLAY DO CONTEXTO GLOBAL ---
# Mostra o contexto atual dos filtros aplicados
st.markdown("### 📊 Contexto Atual da Análise")

col_context_store, col_context_date = st.columns([1, 2])

with col_context_store:
    st.metric(label="Loja Selecionada", value=selected_store_name_formatted)

with col_context_date:
    data_inicio = date_range[0].strftime('%d/%m/%Y')
    data_fim = date_range[1].strftime('%d/%m/%Y')
    st.metric(label="Período de Análise", value=f"{data_inicio} até {data_fim}")

# Informação adicional sobre como o usuário tem controle sobre os dados analisados
with st.expander("💡 Caso queira alterar os filtros:", expanded=False):
    st.info("Para alterar a loja e o período de análise, use a barra lateral à esquerda.")

st.markdown("---")

# --- SESSÃO 1: TOP 10 PRODUTOS (DIAGNÓSTICO HIERÁRQUICO) --- 
# Análise do Top 10 Produtos por Canal e Horário

# Layout do gráfico de barras
st.header("🎯 Ranking de Produtos por Canal e Horário")
st.info("Responde: **Qual produto vende mais na quinta à noite no iFood?**")
# Seleção de filtros específicos para o gráfico
# Filtros: CANAL DE VENDAS, DIA DA SEMANA E HORÁRIO
with st.container():
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        selected_channel = st.selectbox("Canal de Vendas:", options=df_channels['name'].unique(), key='top_prod_channel')
    with col_b:
        selected_day = st.selectbox("Dia da Semana:", options=["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"], index=3, key='top_prod_day')
    with col_c:
        selected_hour_range = st.slider("Janela de Horário:", 0, 23, (19, 23), key='top_prod_hour')

    # Início da medição de latência
    start_time = time.time()

    # Carrega os dados otimizados para o gráfico dos Top Produtos
    df_top_prods = carregar_top_produtos(
        store_id=selected_store_id, 
        channel_name=selected_channel, 
        day_of_week=selected_day, 
        hour_min=selected_hour_range[0], 
        hour_max=selected_hour_range[1]
    )

    # Fim da medição de latência
    end_time = time.time()
    latency = end_time - start_time

# Visualização do gráfico de barras
with st.expander("Clique para expandir o gráfico", expanded=False):
    if not df_top_prods.empty:

        # Renomeando as colunas para melhor legibilidade        
        df_top_prods = df_top_prods.rename(columns={
            'product_name': 'Produtos',
            'total_vendido': 'Quantidade Vendida'
        })

        # Plotly Bar Chart com melhorias de legibilidade        
        fig = px.bar(
            df_top_prods.sort_values(by='Quantidade Vendida', ascending=False),
            x='Produtos', 
            y='Quantidade Vendida', 
            title=f"Top 10 Vendas - Modo: {selected_channel} ({selected_day} - {selected_hour_range[0]}h/{selected_hour_range[1]}h)",
            color='Produtos',
            color_discrete_sequence=px.colors.qualitative.T10 # Paleta de cores consistente
        )
        
        # --- OTIMIZAÇÃO DE LEGIBILIDADE E FONTES ---
        fig.update_layout(
            # Ajuste da ordenação
            xaxis={'categoryorder':'total descending'},
            height=500, 
            title_x=0.2, # Centraliza o título 
            xaxis_tickangle=-45,
            
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
            xaxis_title_font_color="#000000", # Produtos
            yaxis_title_font_color="#000000" # Quantidade Vendida
        )
        # Exibindo o gráfico
        st.plotly_chart(fig, use_container_width=True) 
    # Caso não haja dados para os filtros selecionados
    else:
        st.info("Nenhuma venda encontrada para os filtros selecionados.")
    
    # Exibe a latência da query
    st.caption(f"Latência da Query (Cache): {latency:.2f} segundos")
    if latency > 0.5:
        st.warning("A latência está alta. Verifique o PostgreSQL ou a complexidade do JOIN.")
    else:
        st.success("Query executada rapidamente. Otimização SQL está funcionando.")

# Separador da página
st.markdown("---")

# --- SESSÃO 2: TICKET MÉDIO (DIAGNÓSTICO HIERÁRQUICO) ---
# Análise do Ticket Médio por Canal e Loja
# Layout da análise do Ticket Médio
st.header("📉 Análise Temporal do Ticket Médio")
st.info("Responde: **Meu ticket médio está caindo. É por canal ou por loja?**")

# Layout com abas para separar as análises
with st.expander("Clique para expandir a análise diagnóstica", expanded=False):
    # 2.1. DIAGNÓSTICO MACRO (É POR CANAL?)
    # Layout do diagnóstico sobre o canal
    st.subheader("1. Evolução Diária do Ticket Médio por Canal")
    st.caption("Foco: Identificar a causa-raiz. Qual canal (iFood, Rappi, etc.) está puxando a média para baixo?")
    
    # Início da medição de latência
    start_time = time.time()

    # Carrega dados agregados por data E canal (A partir da loja selecionada e para o período selecionado)
    df_ticket_canal = carregar_ticket_medio_por_canal(start_date=start_date, end_date=end_date)

    # Fim da medição de latência
    end_time = time.time()
    latency = end_time - start_time

    # Visualização do gráfico de linhas
    if not df_ticket_canal.empty:
        # Renomeando Colunas
        df_ticket_canal = df_ticket_canal.rename(columns={
            'sale_date': 'Data',
            'channel_name': 'Canal',
            'avg_ticket': 'Ticket Médio (R$)'
        })
        
        # Plotly (Gráfico de Linha, fácil de isolar e comparar)
        fig_ticket = px.line(
            df_ticket_canal, 
            x='Data', 
            y='Ticket Médio (R$)', 
            color='Canal', 
            title="Ticket Médio Diário por Canal (Visão Macro)",
            markers=True, # Adiciona marcadores para melhor visualização dos pontos
            color_discrete_sequence=px.colors.qualitative.Bold # Paleta de cores forte para melhor distinção
        )
        
        # Formatação
        fig_ticket.update_layout(
            title_x=0.1, 
            yaxis_title="Ticket Médio (R$)", 
            hovermode="x unified",

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
            xaxis_title_font_color="#000000", # Produtos
            yaxis_title_font_color="#000000" # Quantidade Vendida
            )
        
        # Exibição do gráfico
        st.plotly_chart(fig_ticket, use_container_width=True)

        # Exibe a latência da query
        st.caption(f"Latência da Query (Cache): {latency:.2f} segundos")
        if latency > 0.5:
            st.warning("A latência está alta. Verifique o PostgreSQL ou a complexidade do JOIN.")
        else:
            st.success("Query executada rapidamente. Otimização SQL está funcionando.")
        
        st.markdown("---")
        
        # 2.2: DIAGNÓSTICO MICRO (É POR LOJA?)
        # Diagrama do diagnóstico sobre a loja
        # Layout do diagnóstico sobre a loja
        st.subheader("2. Ranking das Lojas por Ticket Médio")
        st.markdown("**OBS**: Esse ranking reflete o período total selecionado no filtro global.")
        st.caption("Foco: Uma vez identificado o canal (no gráfico acima), veja qual loja está com o pior desempenho no período.")
        
        # Início da medição de latência
        start_time = time.time()
        # Carregando os dados de ticket médio por loja (para o período selecionado)
        df_loja_ranking_raw = carregar_ticket_medio_por_loja(start_date=start_date, end_date=end_date)

        # Fim da medição de latência
        end_time = time.time()
        latency_t = end_time - start_time
        
        # Cálculo da Média Agregada por Loja no Pandas (usando a coluna original 'store_name')
        df_loja_ranking = df_loja_ranking_raw.groupby('store_name')['avg_ticket'].mean().reset_index()
        df_loja_ranking = df_loja_ranking.rename(columns={
            'store_name': 'Loja', 
            'avg_ticket': 'Ticket Médio Período (R$)'
        })
        
        st.caption(
            "***Dica:** No gráfico acima, clique na legenda do **Canal** que você suspeita para isolá-lo. Depois, veja o ranking abaixo:*"
        )
        
        # Mostra a tabela ordenada do pior para o melhor ticket médio
        st.dataframe(
            df_loja_ranking.sort_values(by='Ticket Médio Período (R$)', ascending=True)
                           .style.format({'Ticket Médio Período (R$)': "R$ {:.2f}"})
                           # Utiliza o background_gradient para destacar as lojas com pior ticket médio
                           .background_gradient(
                       subset=['Ticket Médio Período (R$)'], 
                       cmap='Reds_r', # Nota: o '_r' (reverse) inverte o mapa de cores,
                                      # fazendo com que o vermelho forte seja para o valor mais baixo (pior)
                       low=0.2, high=0.9 # Ajuste low/high para controle visual da intensidade do destaque.
                   ),
            hide_index=True
        )

        st.markdown(
            "**Observação:** As primeiras lojas (cor mais escura) no ranking têm o Ticket Médio mais baixo. Elas precisam de atenção imediata na precificação ou promoção.")
    # Caso não haja dados para os filtros selecionados
    else:
        st.info("Nenhum dado de Ticket Médio encontrado para o período.")

    # Exibe a latência da query
    st.caption(f"Latência da Query (Cache): {latency:.2f} segundos")
    if latency > 0.5:
        st.warning("A latência está alta. Verifique o PostgreSQL ou a complexidade do JOIN.")
    else:
        st.success("Query executada rapidamente. Otimização SQL está funcionando.")

st.markdown("---")

# --- SESSÃO 3: MARGEM E PRECIFICAÇÃO (TABELA OTIMIZADA) ---
# Análise de Produtos com Baixa Margem
# Layout da análise de margem
st.header("💸 Produtos de Baixa Margem")
st.info("Responde: **Quais produtos têm menor margem e devo repensar o preço?**")
st.markdown(f"Análise focada na Loja: **{selected_store_name_formatted}**")
st.caption("Para mudar a loja, utilize o filtro global na barra lateral.")

# Exibição da tabela de produtos com baixa margem
with st.expander("Clique para ver o ranking de margem", expanded=False):
    # Início da medição de latência
    start_time = time.time()
    
    # Carrega os dados otimizados de margem por produto
    df_margin = carregar_produtos_e_margem(store_id=selected_store_id)

    # Fim da medição de latência
    end_time = time.time()
    latency = end_time - start_time
    
    if not df_margin.empty:
        # Renomeação e Filtragem das Colunas
        df_margin = df_margin.rename(columns={
            'product_name': 'Produto',
            'estimated_margin_percent': 'Margem Estimada (%)',
            'total_quantity_sold': 'Qtd. Vendida'
        })
        df_display = df_margin[['Produto', 'Margem Estimada (%)', 'Qtd. Vendida']]
        
        # Formatação 
        st.markdown(f"##### Produtos com Menor Margem Estimada na Loja {selected_store_name_formatted}")
        # Tabela com destaque para margens baixas
        st.dataframe(
            df_display.style.format({
                'Margem Estimada (%)': "{:.2f}%", 
                'Qtd. Vendida': "{:,.0f}"        
            })
            .background_gradient(subset=['Margem Estimada (%)'], cmap='Reds_r', vmin=-10.0, vmax=20.0), # Destaque em vermelho para margens baixas
            hide_index=True
        )
        
        st.markdown(
            "**Insight Acionável:** Verifique os produtos destacados em **vermelho mais forte** (margem < 20%). Aqueles com **margem negativa** e **alto volume de vendas** indicam prejuízo e precisam de ação imediata na precificação ou custo."
        )
    else:
        st.info("Nenhum dado de Margem encontrado para esta loja.")

    # Exibe a latência da query
    st.caption(f"Latência da Query (Cache): {latency:.2f} segundos")
    if latency > 0.5:
        st.warning("A latência está alta. Verifique o PostgreSQL ou a complexidade do JOIN.")
    else:
        st.success("Query executada rapidamente. Otimização SQL está funcionando.")