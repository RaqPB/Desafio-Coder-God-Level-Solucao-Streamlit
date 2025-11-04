import streamlit as st
import time # Para medir a latência
import pandas as pd
import plotly.express as px # Importação para melhoria do gráfico
from src.carregamento_de_dados import carregar_performance_temporal, carregar_performance_por_regiao
from src.inicializador_global import inicializar_dados
from src.organizacao_dos_dados import formatar_nome_loja

# Inicializa os dados globais necessários para a aplicação
inicializar_dados()

# Recupera metadados
df_stores = st.session_state.get('df_stores', pd.DataFrame())
if df_stores.empty:
    st.error("Dados de Lojas não carregados. Por favor, recarregue a página inicial.")
    st.stop()

# Configuração da página
st.set_page_config(layout="wide")

# Layout da página 2 - Operações e Logística
st.title("⏱️ Análise de Operações e Logística")

# Informação adicional sobre como o usuário tem controle sobre os dados analisados
with st.expander("💡 Caso queira altera o filtro:", expanded=False):
    st.info("Para alterar a loja use a barra lateral à esquerda.")

# --- FILTRO GLOBAL ---
# FILTRO DE LOJA (Barra Lateral)
# Mapeia nome da loja para o ID
store_name_id_map = dict(zip(df_stores['name'], df_stores['id']))
# Filtro Único para esta página
with st.sidebar:
    st.header("Filtros Globais")
    
    store_options = df_stores['name'].unique()
    store_options_formatted = [formatar_nome_loja(name) for name in store_options]
    
    selected_store_name_formatted = st.selectbox(
        "Loja para Análise:",
        options=store_options_formatted,
        index=0,
        key='global_store_filter_op' # Adicionando chave para cada loja para evitar avisos
    )
    
    # Usando o nome original (invertido) para buscar o ID correto na query SQL
    original_store_name = store_options[store_options_formatted.index(selected_store_name_formatted)]
    selected_store_id = store_name_id_map[original_store_name]
    
    st.info("💡 Este filtro afeta TODAS as análises nesta página.")

st.markdown("---")

# Layout Principal da Página
st.subheader(f"Dashboard de Entrega para a Loja: **{selected_store_name_formatted}**")

# Abas para separar as análises (Temporal e Geográfica)
tab1, tab2 = st.tabs(["Análise Temporal (Dia/Hora)", "Análise Geográfica (Bairros)"])

# Dicionário auxiliar para mapear o número do dia da semana (Postgres) para nome
DAY_MAP = {
    0: "Domingo", 1: "Segunda", 2: "Terça", 3: "Quarta", 
    4: "Quinta", 5: "Sexta", 6: "Sábado"
}

# SESSÃO 1: ANÁLISE TEMPORAL (Dias e Horas)
with tab1:
    st.markdown("#### Desempenho de Entrega por Horário e Dia da Semana")
    st.info("O **P90** é o tempo máximo que 90% dos seus pedidos levam. Use o filtro para comparar os dias e identificar os gargalos operacionais no **pico de vendas**.")
    
    # --- FILTRO DE DIA DA SEMANA ---
    selected_day = st.selectbox(
        "Dia da Semana para Análise:", 
        options=list(DAY_MAP.values()), 
        index=5,
        key='delivery_day_filter'
    )
    
    # Reverte o nome para o número SQL (0-6) para o filtro
    selected_day_num = [k for k, v in DAY_MAP.items() if v == selected_day][0]
    
    # Início da medição de latência
    start_time_t = time.time()

    # Carrega os dados (agora agregados por dia e hora)
    df_temporal_raw = carregar_performance_temporal(store_id=selected_store_id)
    
    # Fim da medição de latência
    end_time_t = time.time()
    latency_t = end_time_t - start_time_t

    # Gráfico Temporal (Filtrado pelo dia selecionado)
    if not df_temporal_raw.empty:
        # Filtra apenas o dia selecionado
        df_temporal = df_temporal_raw[df_temporal_raw['day_of_week_num'] == selected_day_num].copy()

        # Caso não haja dados para o dia selecionado
        if df_temporal.empty:
             st.info(f"Nenhuma entrega encontrada para a {selected_day} nesta loja.")
             st.caption(f"Latência da Query Temporal (Cache): {latency_t:.2f} segundos")
             st.stop()

        # Renomeando Colunas
        df_temporal = df_temporal.rename(columns={
            'hour_of_day': 'Hora do Dia',
            'avg_delivery_minutes': 'Tempo Médio (Min)',
            'p90_delivery_minutes': 'P90 Entrega (Min)'
        })

        # Plotly (Gráfico de Linha Dupla)
        fig_temporal = px.line(
            df_temporal,
            x='Hora do Dia',
            y=['Tempo Médio (Min)', 'P90 Entrega (Min)'],
            title=f"Tempo de Entrega por Hora na {selected_day} - Loja {selected_store_name_formatted}",
            color_discrete_map={
                "Tempo Médio (Min)": "blue",
                "P90 Entrega (Min)": "red" 
            },
            markers=True
        )
        
        # Configurações do Layout
        fig_temporal.update_layout(
            title_x=0.1, 
            yaxis_title="Tempo (Minutos)",
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
            xaxis_title_font_color="#000000", # Hora do Dia
            yaxis_title_font_color="#000000" # Tempo (Minutos)
        )
        # Exibe o gráfico
        st.plotly_chart(fig_temporal, use_container_width=True)


        # Aviso de Anomalia no P90 quando muito alto em determinado horário
        pico_p90 = df_temporal.loc[df_temporal['P90 Entrega (Min)'].idxmax()]
        st.error(
            f"⚠️ **PICO DE ESTRESSE OPERACIONAL:** Na {selected_day}, o nosso pior momento foi às **{pico_p90['Hora do Dia']}h**."
            f"\n\nNeste horário, o tempo de entrega sobe drasticamente, chegando a **{pico_p90['P90 Entrega (Min)']:.1f} minutos** para os 10% de pedidos mais lentos."
            f"\n\n👉 **Ação:** O gargalo está aqui. Revise a capacidade de produção ou a logística externa neste horário específico."
        )
    # Caso não haja dados para o filtro selecionado
    else:
        st.info("Nenhum dado temporal encontrado para esta loja.")
    
    # Exibe a latência da query
    st.caption(f"Latência da Query Temporal (Cache): {latency_t:.2f} segundos")

# SESSÃO 2: ANÁLISE GEOGRÁFICA (Regiões e Anomalias)
# Análise Geográfica por Bairro
# Usando a segunda aba
with tab2:
    st.markdown("#### Performance Média e P90 por Bairro")
    st.info("Compare a eficiência da entrega entre os bairros atendidos. P90 alto em bairros próximos pode indicar problemas de rota.")
    
    # Início da medição de latência
    start_time_g = time.time()
    
    # Carrega os dados otimizados para o gráfico geográfico
    df_geografica = carregar_performance_por_regiao(store_id=selected_store_id)
    
    # Fim da medição de latência
    end_time_g = time.time()
    latency_g = end_time_g - start_time_g

    # Visualização da Tabela de Bairros
    if not df_geografica.empty:
        # Renomeando Colunas
        df_geografica = df_geografica.rename(columns={
            'neighborhood': 'Bairro',
            'avg_delivery_minutes': 'Tempo Médio (Min)',
            'p90_delivery_minutes': 'P90 Entrega (Min)',
            'total_deliveries': 'Total Entregas'
        })
        
        # Tabela: Mostrar os bairros com o pior tempo (ordenado por P90)
        df_display = df_geografica.sort_values('P90 Entrega (Min)', ascending=False)
        
        st.markdown("##### Bairros com Maior Tempo de Entrega")
        st.dataframe(
            df_display.style.format({
                'Tempo Médio (Min)': "{:.1f}", 
                'P90 Entrega (Min)': "{:.1f}",
                'Total Entregas': "{:,.0f}"
            })
            # Aplica gradiente: Vermelho no P90 mais alto (indicando pior desempenho)
            .background_gradient(subset=['P90 Entrega (Min)'], cmap='Reds', high=0.5),
            hide_index=True)
        
        # Aviso de Anomalia no Bairro com Pior P90
        # Destaque o pior bairro
        pior_bairro = df_display.iloc[0]['Bairro']
        # Tempo P90 do pior bairro
        pior_p90 = df_display.iloc[0]['P90 Entrega (Min)']
        
        st.warning(
            f"🗺️ **FOCO DE ATENÇÃO:** O bairro **{pior_bairro}** é o nosso ponto mais fraco na logística."
            f"\n\nNesta região, **1 em cada 10 clientes** espera **{pior_p90:.1f} minutos** ou mais, indicando um risco alto de insatisfação."
            f"\n\n👉 **Ação:** Investigue rotas, trânsito ou a distância física para este bairro para otimizar a velocidade de entrega."
            )

    # Exibe a latência da query
    st.caption(f"Latência da Query Geográfica (Cache): {latency_g:.2f} segundos")