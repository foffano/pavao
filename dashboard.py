import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Monitoramento Pavão",
    page_icon="🦚",
    layout="wide"
)

# --- CONSTANTES ---
DB_NAME = "monitoramento_pavao.db"

# --- FUNÇÕES ---
@st.cache_data(ttl=60) # Cache de 1 minuto para não sobrecarregar o banco
def load_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT * FROM historico_precos"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Conversão de tipos
        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
        df['preco_atual'] = pd.to_numeric(df['preco_atual'], errors='coerce')
        df['preco_original'] = pd.to_numeric(df['preco_original'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def main():
    st.title("🦚 Dashboard de Monitoramento - Pavão")
    st.markdown("Visualize o histórico de preços e disponibilidade dos produtos.")

    # Carregar dados
    df = load_data()

    if df.empty:
        st.warning("Nenhum dado encontrado no banco de dados.")
        return

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Categoria
    categorias = ["Todas"] + sorted(df['categoria'].unique().tolist())
    cat_filter = st.sidebar.selectbox("Categoria", categorias)
    
    # Filtro de Disponibilidade
    disp_options = ["Todos", "Disponível", "Indisponível"]
    disp_filter = st.sidebar.selectbox("Disponibilidade", disp_options)
    
    # Filtro de Promoção
    promo_options = ["Todos", "Em Promoção", "Preço Normal"]
    promo_filter = st.sidebar.selectbox("Status de Promoção", promo_options)

    # Aplicar Filtros
    df_filtered = df.copy()
    
    if cat_filter != "Todas":
        df_filtered = df_filtered[df_filtered['categoria'] == cat_filter]
        
    if disp_filter == "Disponível":
        df_filtered = df_filtered[df_filtered['disponivel'] == 1]
    elif disp_filter == "Indisponível":
        df_filtered = df_filtered[df_filtered['disponivel'] == 0]
        
    if promo_filter == "Em Promoção":
        df_filtered = df_filtered[df_filtered['em_promocao'] == 1]
    elif promo_filter == "Preço Normal":
        df_filtered = df_filtered[df_filtered['em_promocao'] == 0]

    # --- KPIs (TOPO) ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_produtos = df_filtered['sku'].nunique()
    total_registros = len(df_filtered)
    media_preco = df_filtered['preco_atual'].mean()
    qtd_promo = df_filtered[df_filtered['em_promocao'] == 1]['sku'].nunique()

    col1.metric("Produtos Únicos", total_produtos)
    col2.metric("Total de Registros", total_registros)
    col3.metric("Preço Médio", f"R$ {media_preco:.2f}")
    col4.metric("Em Promoção", qtd_promo)

    st.divider()

    # --- GRÁFICOS ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Distribuição de Preços")
        fig_hist = px.histogram(df_filtered, x="preco_atual", nbins=20, title="Histograma de Preços")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart2:
        st.subheader("Disponibilidade")
        disp_counts = df_filtered['disponivel'].value_counts().rename({1: 'Disponível', 0: 'Indisponível'})
        fig_pie = px.pie(values=disp_counts.values, names=disp_counts.index, title="Proporção de Disponibilidade")
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- EVOLUÇÃO TEMPORAL (LINHA) ---
    st.subheader("Evolução de Preços (Últimos Registros)")
    # Pegar os top 5 produtos mais frequentes no filtro para não poluir o gráfico
    top_products = df_filtered['produto_nome'].value_counts().head(5).index
    df_line = df_filtered[df_filtered['produto_nome'].isin(top_products)]
    
    if not df_line.empty:
        fig_line = px.line(df_line, x="data_coleta", y="preco_atual", color="produto_nome", title="Histórico de Preços (Top 5 Produtos)")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Sem dados suficientes para gráfico de linha.")

    # --- TABELA DE DADOS ---
    st.subheader("Dados Detalhados")
    st.dataframe(df_filtered.sort_values(by="data_coleta", ascending=False))

if __name__ == "__main__":
    main()
