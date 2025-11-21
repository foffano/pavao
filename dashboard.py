import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Monitoramento Another Place",
    page_icon="🛍️",
    layout="wide"
)

# --- CONSTANTES ---
DB_NAME = "monitoramento_anotherplace.db"

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

# --- FUNÇÕES DE ANÁLISE ---
def calculate_price_changes(df):
    """Calcula variações de preço entre coletas para cada SKU"""
    if df.empty:
        return pd.DataFrame()
    
    # Ordenar por SKU e data
    df_sorted = df.sort_values(['sku', 'data_coleta'])
    
    # Para cada SKU, calcular a diferença entre primeira e última coleta
    price_changes = []
    for sku in df_sorted['sku'].unique():
        sku_data = df_sorted[df_sorted['sku'] == sku]
        if len(sku_data) < 2:
            continue
            
        first_record = sku_data.iloc[0]
        last_record = sku_data.iloc[-1]
        
        price_diff = last_record['preco_atual'] - first_record['preco_atual']
        price_pct = (price_diff / first_record['preco_atual'] * 100) if first_record['preco_atual'] > 0 else 0
        
        price_changes.append({
            'sku': sku,
            'produto_nome': last_record['produto_nome'],
            'categoria': last_record['categoria'],
            'preco_inicial': first_record['preco_atual'],
            'preco_final': last_record['preco_atual'],
            'variacao_absoluta': price_diff,
            'variacao_percentual': price_pct,
            'data_inicial': first_record['data_coleta'],
            'data_final': last_record['data_coleta']
        })
    
    return pd.DataFrame(price_changes)

def get_top_price_drops(df, n=10):
    """Retorna os N produtos com maior queda de preço"""
    changes = calculate_price_changes(df)
    if changes.empty:
        return pd.DataFrame()
    return changes.nsmallest(n, 'variacao_percentual')

def get_top_price_increases(df, n=10):
    """Retorna os N produtos com maior aumento de preço"""
    changes = calculate_price_changes(df)
    if changes.empty:
        return pd.DataFrame()
    return changes.nlargest(n, 'variacao_percentual')

def get_availability_changes(df):
    """Identifica produtos que mudaram status de disponibilidade"""
    if df.empty:
        return pd.DataFrame()
    
    df_sorted = df.sort_values(['sku', 'data_coleta'])
    availability_changes = []
    
    for sku in df_sorted['sku'].unique():
        sku_data = df_sorted[df_sorted['sku'] == sku]
        if len(sku_data) < 2:
            continue
            
        first_record = sku_data.iloc[0]
        last_record = sku_data.iloc[-1]
        
        if first_record['disponivel'] != last_record['disponivel']:
            availability_changes.append({
                'sku': sku,
                'produto_nome': last_record['produto_nome'],
                'status_anterior': 'Disponível' if first_record['disponivel'] == 1 else 'Indisponível',
                'status_atual': 'Disponível' if last_record['disponivel'] == 1 else 'Indisponível',
                'data_mudanca': last_record['data_coleta']
            })
    
    return pd.DataFrame(availability_changes)

def calculate_promotion_metrics(df_latest):
    """Calcula métricas agregadas sobre promoções"""
    if df_latest.empty:
        return {}
    
    total_products = len(df_latest)
    promo_products = len(df_latest[df_latest['em_promocao'] == 1])
    promo_percentage = (promo_products / total_products * 100) if total_products > 0 else 0
    
    # Calcular desconto médio
    promo_df = df_latest[df_latest['em_promocao'] == 1].copy()
    if not promo_df.empty:
        promo_df['desconto_pct'] = ((promo_df['preco_original'] - promo_df['preco_atual']) / promo_df['preco_original'] * 100)
        avg_discount = promo_df['desconto_pct'].mean()
    else:
        avg_discount = 0
    
    # Categoria com mais promoções
    if not promo_df.empty:
        top_promo_category = promo_df['categoria'].value_counts().index[0]
        top_promo_count = promo_df['categoria'].value_counts().iloc[0]
    else:
        top_promo_category = "N/A"
        top_promo_count = 0
    
    return {
        'total_products': total_products,
        'promo_products': promo_products,
        'promo_percentage': promo_percentage,
        'avg_discount': avg_discount,
        'top_promo_category': top_promo_category,
        'top_promo_count': top_promo_count
    }

def export_to_csv(df):
    """Exporta dados para CSV e retorna o conteúdo"""
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.title("🛍️ Dashboard de Monitoramento - Another Place")
    st.markdown("Visualize o histórico de preços e disponibilidade dos produtos.")

    # Carregar dados
    df = load_data()

    if df.empty:
        st.warning("Nenhum dado encontrado no banco de dados.")
        return

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Período
    if not df.empty:
        min_date = df['data_coleta'].min().date()
        max_date = df['data_coleta'].max().date()
        
        date_range = st.sidebar.date_input(
            "Período de Análise",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Aplicar filtro de data
        if isinstance(date_range, tuple) and len(date_range) == 2:
            df = df[(df['data_coleta'].dt.date >= date_range[0]) & (df['data_coleta'].dt.date <= date_range[1])]
    
    # Filtro de Categoria
    categorias = ["Todas"] + sorted(df['categoria'].unique().tolist())
    cat_filter = st.sidebar.selectbox("Categoria", categorias)
    
    # Filtro de Disponibilidade
    disp_options = ["Todos", "Disponível", "Indisponível"]
    disp_filter = st.sidebar.selectbox("Disponibilidade", disp_options)
    
    # Filtro de Promoção
    promo_options = ["Todos", "Em Promoção", "Preço Normal"]
    promo_filter = st.sidebar.selectbox("Status de Promoção", promo_options)
    
    st.sidebar.divider()
    
    # Exportação de Dados
    st.sidebar.header("📥 Exportar Dados")
    if st.sidebar.button("Baixar CSV Filtrado", use_container_width=True):
        csv_data = export_to_csv(df)
        st.sidebar.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"monitoramento_pavao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )


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

    # --- PREPARAÇÃO DOS DADOS (SKU ÚNICO) ---
    # Para análises de distribuição e KPIs, queremos apenas o registro mais recente de cada SKU
    df_latest = df_filtered.sort_values(by="data_coleta", ascending=False).drop_duplicates(subset="sku", keep="first")

    # --- KPIs (TOPO) ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_produtos = df_latest['sku'].nunique()
    total_registros = len(df_filtered) # Mantém o total de registros histórico
    media_preco = df_latest['preco_atual'].mean()
    qtd_promo = df_latest[df_latest['em_promocao'] == 1]['sku'].nunique()
    
    # Métricas de promoção
    promo_metrics = calculate_promotion_metrics(df_latest)
    
    col1.metric("Produtos Únicos", total_produtos)
    col2.metric("Total de Registros", total_registros)
    col3.metric("Preço Médio", f"R$ {media_preco:.2f}")
    col4.metric("Em Promoção", qtd_promo)
    col5.metric("% em Promoção", f"{promo_metrics.get('promo_percentage', 0):.1f}%")
    col6.metric("Desconto Médio", f"{promo_metrics.get('avg_discount', 0):.1f}%")

    st.divider()
    
    # --- ANÁLISE DE TENDÊNCIAS ---
    st.header("📊 Análise de Tendências")
    
    col_trend1, col_trend2 = st.columns(2)
    
    with col_trend1:
        st.subheader("🔻 Maiores Quedas de Preço")
        top_drops = get_top_price_drops(df_filtered, n=5)
        if not top_drops.empty:
            for idx, row in top_drops.iterrows():
                with st.expander(f"{row['produto_nome'][:50]}... ({row['variacao_percentual']:.1f}%)"):
                    st.write(f"**Categoria:** {row['categoria']}")
                    st.write(f"**SKU:** {row['sku']}")
                    st.write(f"**Preço Inicial:** R$ {row['preco_inicial']:.2f}")
                    st.write(f"**Preço Final:** R$ {row['preco_final']:.2f}")
                    st.write(f"**Variação:** {row['variacao_percentual']:.1f}% (R$ {row['variacao_absoluta']:.2f})")
        else:
            st.info("Dados insuficientes para análise de tendências (necessário múltiplas coletas)")
    
    with col_trend2:
        st.subheader("🔺 Maiores Aumentos de Preço")
        top_increases = get_top_price_increases(df_filtered, n=5)
        if not top_increases.empty:
            for idx, row in top_increases.iterrows():
                with st.expander(f"{row['produto_nome'][:50]}... (+{row['variacao_percentual']:.1f}%)"):
                    st.write(f"**Categoria:** {row['categoria']}")
                    st.write(f"**SKU:** {row['sku']}")
                    st.write(f"**Preço Inicial:** R$ {row['preco_inicial']:.2f}")
                    st.write(f"**Preço Final:** R$ {row['preco_final']:.2f}")
                    st.write(f"**Variação:** +{row['variacao_percentual']:.1f}% (R$ +{row['variacao_absoluta']:.2f})")
        else:
            st.info("Dados insuficientes para análise de tendências (necessário múltiplas coletas)")
    
    st.divider()
    
    # --- SISTEMA DE ALERTAS ---
    st.header("🚨 Alertas e Mudanças Importantes")
    
    # Mudanças de disponibilidade
    availability_changes = get_availability_changes(df_filtered)
    if not availability_changes.empty:
        st.subheader("📦 Mudanças de Disponibilidade")
        st.dataframe(
            availability_changes[['produto_nome', 'sku', 'status_anterior', 'status_atual', 'data_mudanca']],
            use_container_width=True,
            hide_index=True
        )
    
    # Produtos com variação significativa (>10% ou <-10%)
    all_changes = calculate_price_changes(df_filtered)
    if not all_changes.empty:
        significant_changes = all_changes[
            (all_changes['variacao_percentual'] > 10) | (all_changes['variacao_percentual'] < -10)
        ].copy()
        
        if not significant_changes.empty:
            st.subheader("💰 Variações Significativas de Preço (>10%)")
            significant_changes['variacao_formatada'] = significant_changes['variacao_percentual'].apply(
                lambda x: f"{x:+.1f}%"
            )
            st.dataframe(
                significant_changes[['produto_nome', 'categoria', 'preco_inicial', 'preco_final', 'variacao_formatada']],
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    
    # --- GRÁFICOS ---
    st.header("📈 Visualizações")
    
    col_chart1, col_chart2, col_chart3 = st.columns(3)

    with col_chart1:
        st.subheader("Distribuição de Preços")
        fig_hist = px.histogram(
            df_latest, 
            x="preco_atual", 
            nbins=20, 
            title="Histograma de Preços (Última Coleta)",
            labels={"preco_atual": "Preço (R$)", "count": "Quantidade"}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart2:
        st.subheader("Disponibilidade")
        disp_counts = df_latest['disponivel'].value_counts().rename({1: 'Disponível', 0: 'Indisponível'})
        fig_pie = px.pie(
            values=disp_counts.values, 
            names=disp_counts.index, 
            title="Proporção de Disponibilidade",
            color_discrete_sequence=['#2ecc71', '#e74c3c']
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart3:
        st.subheader("Promoções por Categoria")
        promo_by_cat = df_latest[df_latest['em_promocao'] == 1].groupby('categoria').size().reset_index(name='count')
        if not promo_by_cat.empty:
            fig_bar = px.bar(
                promo_by_cat.nlargest(10, 'count'),
                x='count',
                y='categoria',
                orientation='h',
                title="Top 10 Categorias em Promoção",
                labels={"count": "Quantidade", "categoria": "Categoria"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum produto em promoção no momento")

    # --- EVOLUÇÃO TEMPORAL (LINHA) ---
    st.subheader("📉 Evolução de Preços ao Longo do Tempo")
    
    # Pegar os top 5 produtos mais frequentes no filtro para não poluir o gráfico
    top_products = df_filtered['produto_nome'].value_counts().head(5).index
    df_line = df_filtered[df_filtered['produto_nome'].isin(top_products)]
    
    if not df_line.empty and len(df_line) > 1:
        fig_line = px.line(
            df_line, 
            x="data_coleta", 
            y="preco_atual", 
            color="produto_nome", 
            title="Histórico de Preços (Top 5 Produtos)",
            labels={"data_coleta": "Data", "preco_atual": "Preço (R$)", "produto_nome": "Produto"},
            markers=True
        )
        fig_line.update_layout(
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Dados insuficientes para gráfico de evolução temporal (necessário múltiplas coletas)")

    st.divider()

    # --- TABELA DE DADOS ---
    st.subheader("📋 Dados Detalhados")
    
    # Opções de visualização
    col_table1, col_table2 = st.columns([3, 1])
    with col_table1:
        view_option = st.radio(
            "Visualizar:",
            ["Última Coleta (SKU Único)", "Histórico Completo"],
            horizontal=True
        )
    with col_table2:
        num_rows = st.number_input("Linhas a exibir:", min_value=10, max_value=1000, value=50, step=10)
    
    # Selecionar dados baseado na opção
    if view_option == "Última Coleta (SKU Único)":
        display_df = df_latest.copy()
    else:
        display_df = df_filtered.copy()
    
    # Formatar colunas para melhor visualização
    display_df = display_df.sort_values(by="data_coleta", ascending=False).head(num_rows)
    
    # Selecionar colunas relevantes
    columns_to_show = [
        'data_coleta', 'produto_nome', 'sku', 'categoria', 
        'preco_atual', 'preco_original', 'em_promocao', 'disponivel'
    ]
    
    display_df_formatted = display_df[columns_to_show].copy()
    display_df_formatted['em_promocao'] = display_df_formatted['em_promocao'].map({1: '✅', 0: '❌'})
    display_df_formatted['disponivel'] = display_df_formatted['disponivel'].map({1: '✅', 0: '❌'})
    
    st.dataframe(
        display_df_formatted,
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_coleta": st.column_config.DatetimeColumn("Data Coleta", format="DD/MM/YYYY HH:mm"),
            "produto_nome": st.column_config.TextColumn("Produto", width="large"),
            "sku": st.column_config.TextColumn("SKU", width="small"),
            "categoria": st.column_config.TextColumn("Categoria", width="medium"),
            "preco_atual": st.column_config.NumberColumn("Preço Atual", format="R$ %.2f"),
            "preco_original": st.column_config.NumberColumn("Preço Original", format="R$ %.2f"),
            "em_promocao": st.column_config.TextColumn("Promoção", width="small"),
            "disponivel": st.column_config.TextColumn("Disponível", width="small")
        }
    )
    
    # Estatísticas rápidas da tabela
    st.caption(f"Exibindo {len(display_df_formatted)} de {len(display_df)} registros filtrados")

if __name__ == "__main__":
    main()
