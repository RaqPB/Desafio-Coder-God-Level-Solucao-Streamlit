import streamlit as st
import psycopg2
import pandas as pd

# Função para inicializar a conexão com o docker
@st.cache_resource
def conexao_banco_de_dados():
    """Initializes and returns the database connection object."""
    try:
        return psycopg2.connect(
            host=st.secrets["connections"]["postgres"]["host"],
            database=st.secrets["connections"]["postgres"]["database"],
            user=st.secrets["connections"]["postgres"]["user"],
            password=st.secrets["connections"]["postgres"]["password"],
            port=st.secrets["connections"]["postgres"]["port"]
        )
    except Exception as e:
        st.error(f"Não foi possível conectar ao Postgres. Verifique o Docker e o Host. Error: {e}")
        st.stop()
        return None

#Carregamento de Metadados
@st.cache_data(ttl=60 * 60 * 24) # Cache longo para dados estáticos
def carregar_metadados():
    """Carrega dados estáticos (Lojas e Canais) e retorna dois DataFrames."""
    conn = conexao_banco_de_dados()
    if conn is None:
        # Retornanando a mesma quantidade de objetos que serão desempacotados (IMPORTANTE)!
        return pd.DataFrame(), pd.DataFrame() 
    
    try:
        # Carrega a lista de lojas
        df_stores = pd.read_sql("SELECT id, name FROM stores WHERE is_active = TRUE;", conn)
        # Carrega a lista de canais
        df_channels = pd.read_sql("SELECT id, name FROM channels;", conn)
        
        # Retorna os dois DataFrames para desempacotá-los
        return df_stores, df_channels
    except Exception as e:
        st.error(f"Erro ao carregar metadados (Lojas/Canais): {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 1. Top Produtos por Filtro (DOR: "Qual produto vende mais...?") ---
@st.cache_data(ttl=360) 
def carregar_top_produtos(store_id, channel_name, day_of_week, hour_min, hour_max):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()
    day_map = {"Segunda": 1, "Terça": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5, "Sábado": 6, "Domingo": 0}
    day_sql = day_map.get(day_of_week)

    query = f"""
    SELECT 
        p.name AS product_name, 
        SUM(ps.quantity) AS total_vendido
    FROM sales s
    JOIN product_sales ps ON ps.sale_id = s.id
    JOIN products p ON p.id = ps.product_id
    JOIN channels c ON c.id = s.channel_id
    WHERE s.sale_status_desc = 'COMPLETED'
      AND c.name = '{channel_name}'
      AND s.store_id = {store_id}
      AND EXTRACT(DOW FROM s.created_at) = {day_sql}
      AND EXTRACT(HOUR FROM s.created_at) BETWEEN {hour_min} AND {hour_max}
    GROUP BY p.name
    ORDER BY total_vendido DESC
    LIMIT 10;
    """
    return pd.read_sql(query, conn)

# --- 2. Ticket Médio por Canal e Loja (DOR: "Ticket médio está caindo...") ---
@st.cache_data(ttl=360)
def carregar_ticket_medio_por_canal(start_date, end_date):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()

    query = f"""
    SELECT 
        DATE_TRUNC('day', s.created_at) AS sale_date,
        c.name AS channel_name,
        AVG(s.total_amount) AS avg_ticket
    FROM sales s
    JOIN channels c ON c.id = s.channel_id
    WHERE s.sale_status_desc = 'COMPLETED'
      AND s.created_at BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1, 2
    ORDER BY 1;
    """
    return pd.read_sql(query, conn)

@st.cache_data(ttl=360)
def carregar_ticket_medio_por_loja(start_date, end_date):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()

    query = f"""
    SELECT 
        DATE_TRUNC('day', s.created_at) AS sale_date,
        st.name AS store_name,
        AVG(s.total_amount) AS avg_ticket
    FROM sales s
    JOIN stores st ON st.id = s.store_id
    WHERE s.sale_status_desc = 'COMPLETED'
      AND s.created_at BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 1, 2
    ORDER BY 1;
    """
    return pd.read_sql(query, conn)

# --- 3. Produtos e Margem (DOR: "Produtos com menor margem...") ---
@st.cache_data(ttl=360)
def carregar_produtos_e_margem(store_id):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()

    # Simplificação: Usamos a diferença entre preço total e custo base como proxy para margem, 
    # ou uma agregação que traga base_price e total_price.
    # SQL aqui é um pouco mais complexo devido ao JOIN de item_product_sales.
    query = f"""
    -- Traz o preço médio de venda e o custo/base price (proxy)
    SELECT 
        p.name AS product_name,
        AVG(ps.total_price / ps.quantity) AS avg_sale_price,
        AVG(ps.base_price) AS avg_base_price,
        SUM(ps.quantity) AS total_quantity_sold
    FROM product_sales ps
    JOIN sales s ON s.id = ps.sale_id
    JOIN products p ON p.id = ps.product_id
    WHERE s.store_id = {store_id} 
      AND s.sale_status_desc = 'COMPLETED'
    GROUP BY p.name
    HAVING SUM(ps.quantity) > 50 -- Filtra produtos pouco vendidos para relevância
    ;
    """
    df = pd.read_sql(query, conn)
    # Cálculo da Margem (Estimada) no Pandas, após carregar o resultado AGREGADO do SQL.
    df['estimated_margin'] = (df['avg_sale_price'] - df['avg_base_price']) / df['avg_sale_price']
    df['estimated_margin_percent'] = df['estimated_margin'] * 100
    return df.sort_values(by='estimated_margin_percent', ascending=True)

# --- 4. Performance Temporal de Entrega ---
@st.cache_data(ttl=360) 
def carregar_performance_temporal(store_id):
  conn = conexao_banco_de_dados()
  if conn is None: return pd.DataFrame()
  
  # EXTRACT(DOW) para agrupar por Dia da Semana (0=Domingo, 6=Sábado)
  query = f"""
  SELECT
    EXTRACT(DOW FROM s.created_at) AS day_of_week_num, -- Novo: Dia da Semana (0-6)
    EXTRACT(HOUR FROM s.created_at) AS hour_of_day,
    AVG(s.delivery_seconds / 60.0) AS avg_delivery_minutes,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY s.delivery_seconds / 60.0) AS p90_delivery_minutes
  FROM sales s
  WHERE s.store_id = {store_id}
   AND s.delivery_seconds IS NOT NULL -- Apenas vendas com entrega
   AND s.sale_status_desc = 'COMPLETED'
  GROUP BY 1, 2 -- Agrupamos por Dia E Hora
  ORDER BY 1, 2;
  """
  return pd.read_sql(query, conn)

# --- 5. Análise Geográfica de Entrega (DOR: "Tempo de entrega por região?") ---
@st.cache_data(ttl=360) 
def carregar_performance_por_regiao(store_id):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()

    query = f"""
    SELECT 
        da.neighborhood,
        COUNT(s.id) AS total_deliveries,
        AVG(s.delivery_seconds / 60.0) AS avg_delivery_minutes,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY s.delivery_seconds / 60.0) AS p90_delivery_minutes
    FROM sales s
    JOIN delivery_addresses da ON da.sale_id = s.id
    WHERE s.store_id = {store_id}
      AND s.delivery_seconds IS NOT NULL
      AND s.sale_status_desc = 'COMPLETED'
    GROUP BY da.neighborhood
    HAVING COUNT(s.id) >= 10 -- Garante que a amostra é relevante
    ORDER BY avg_delivery_minutes DESC;
    """
    return pd.read_sql(query, conn)

# --- 6. Modelo RFM Agregado ---
@st.cache_data(ttl=60 * 60) # Cache de 1 hora, pois os dados mudam lentamente
def carregar_dados_rfm_agregado(data_analise):
    conn = conexao_banco_de_dados()
    if conn is None: return pd.DataFrame()

    # CRUCIAL: A Data de Análise (hoje) é necessária para calcular a Recência (diferença)
    query = f"""
    WITH customer_summary AS (
        SELECT
            c.id AS customer_id,
            c.customer_name,
            MAX(s.created_at) AS last_sale_date,
            COUNT(s.id) AS frequency,
            SUM(s.total_amount) AS monetary
        FROM customers c
        JOIN sales s ON s.customer_id = c.id
        WHERE s.sale_status_desc = 'COMPLETED'
          AND c.id IS NOT NULL -- Apenas clientes identificados
        GROUP BY c.id, c.customer_name
    )
    SELECT
        customer_id,
        customer_name,
        frequency,
        monetary,
        -- Calcula a Recência em dias
        ('{data_analise}'::date - last_sale_date::date) AS recency_days
    FROM customer_summary
    WHERE frequency > 0
    ORDER BY recency_days ASC;
    """
    df = pd.read_sql(query, conn)
    return df