import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
import scipy.stats as stats

# -----------------------------
# Conexão com o banco
# -----------------------------
def get_connection():
    return sqlite3.connect("pega_ai.db", check_same_thread=False)


# -----------------------------
# Página principal
# -----------------------------
def main():
    st.set_page_config(page_title="Dashboard de Análises – Pega Aí", layout="wide")
    st.title("📊 Dashboard de Análises – Pega Aí")
    st.markdown("Relatórios automáticos com base nos dados populados no protótipo.")

    conn = get_connection()

    # -----------------------------
    # KPIs gerais
    # -----------------------------
    st.header("🔢 Indicadores Gerais")

    col1, col2, col3, col4 = st.columns(4)

    total_ofertas = pd.read_sql("SELECT COUNT(*) AS total FROM ofertas", conn)["total"][0]
    total_pedidos = pd.read_sql("SELECT COUNT(*) AS total FROM pedidos", conn)["total"][0]
    total_retirados = pd.read_sql("SELECT COUNT(*) AS total FROM pedidos WHERE status='retirado'", conn)["total"][0]
    total_consumidores = pd.read_sql("SELECT COUNT(*) AS total FROM usuarios WHERE tipo='Consumidor'", conn)["total"][0]

    col1.metric("Ofertas cadastradas", total_ofertas)
    col2.metric("Pedidos criados", total_pedidos)
    col3.metric("Pedidos retirados", total_retirados)
    col4.metric("Consumidores", total_consumidores)

    st.markdown("---")

    # -----------------------------
    # Ticket médio (corrigido)
    # -----------------------------
    st.header("💳 Ticket Médio")

    df_ticket = pd.read_sql("""
        SELECT valor_total
        FROM pedidos
        WHERE status = 'retirado'
    """, conn)

    if len(df_ticket) > 0:
        ticket_medio = df_ticket["valor_total"].mean()
        ticket_min = df_ticket["valor_total"].min()
        ticket_max = df_ticket["valor_total"].max()
        ticket_std = df_ticket["valor_total"].std()

        st.metric("Ticket médio", f"R$ {ticket_medio:.2f}")
        st.markdown(f"- **Mínimo:** R$ {ticket_min:.2f}")
        st.markdown(f"- **Máximo:** R$ {ticket_max:.2f}")
        st.markdown(f"- **Desvio padrão:** {ticket_std:.2f}")
    else:
        st.info("Não há pedidos retirados suficientes para calcular o ticket médio.")

    st.markdown("---")

    # -----------------------------
    # Tabela de vendas por oferta (corrigida com SUM de pedidos)
    # -----------------------------
    st.header("📦 Desempenho das Ofertas")

    df_ofertas = pd.read_sql("""
        SELECT 
            o.id,
            o.titulo,
            o.categoria,
            o.preco_venda,
            o.preco_original,
            o.estoque_inicial,
            COALESCE(SUM(p.quantidade), 0) AS vendidos
        FROM ofertas o
        LEFT JOIN pedidos p ON p.oferta_id = o.id AND p.status='retirado'
        GROUP BY o.id
    """, conn)

    st.dataframe(df_ofertas)

    fig = px.scatter(
        df_ofertas,
        x="preco_venda",
        y="vendidos",
        color="categoria",
        size="vendidos",
        title="Preço vs. Quantidade Vendida"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # -----------------------------
    # Correlação preço x vendas
    # -----------------------------
    st.header("📈 Correlação: Preço vs Vendas")

    df_corr = df_ofertas.copy()

    if len(df_corr) > 2 and df_corr["vendidos"].std() > 0:
        corr_val = df_corr["preco_venda"].corr(df_corr["vendidos"])
        st.metric("Correlação (Pearson)", f"{corr_val:.3f}")

        if abs(corr_val) >= 0.5:
            st.success("Há correlação forte.")
        elif abs(corr_val) >= 0.3:
            st.warning("Correlação moderada.")
        else:
            st.info("Correlação fraca.")
    else:
        st.info("Não há dados suficientes para calcular correlação.")

    st.markdown("---")

    # -----------------------------
    # Teste estatístico por categoria (corrigido)
    # -----------------------------
    st.header("🧪 Teste Estatístico entre Categorias")

    df_teste = pd.read_sql("""
        SELECT 
            o.categoria,
            COALESCE(SUM(p.quantidade), 0) AS total_vendido
        FROM ofertas o
        LEFT JOIN pedidos p ON p.oferta_id = o.id AND p.status='retirado'
        GROUP BY o.categoria
        HAVING COUNT(DISTINCT o.id) >= 3
    """, conn)

    if len(df_teste["categoria"].unique()) >= 2:
        categorias = df_teste["categoria"].unique()

        # Criar lista de grupos para ANOVA
        grupos = []
        for cat in categorias:
            valores = pd.read_sql("""
                SELECT COALESCE(p.quantidade,0) as vendidos
                FROM ofertas o
                LEFT JOIN pedidos p ON p.oferta_id = o.id AND p.status='retirado'
                WHERE o.categoria = ?
            """, conn, params=[cat])
            grupos.append(valores["vendidos"])

        try:
            f_valor, p_valor = stats.f_oneway(*grupos)

            st.write("**ANOVA** entre categorias")
            st.write(f"F = {f_valor:.3f}, p = {p_valor:.4f}")

            if p_valor < 0.05:
                st.success("Há diferença estatisticamente significativa entre categorias.")
            else:
                st.info("Não há diferença significativa.")
        except:
            st.warning("Não foi possível realizar ANOVA. Verifique se há dados suficientes.")
    else:
        st.info("Não há categorias suficientes para realizar teste estatístico (precisa de 2+ categorias).")

    st.markdown("---")

    # -----------------------------
    # Evolução temporal das vendas
    # -----------------------------
    st.header("📅 Vendas ao Longo do Tempo")

    df_tempo = pd.read_sql("""
        SELECT DATE(criado_em) as data, SUM(quantidade) as vendidos
        FROM pedidos
        WHERE status='retirado'
        GROUP BY DATE(criado_em)
        ORDER BY DATE(criado_em)
    """, conn)

    if len(df_tempo) > 0:
        fig2 = px.line(df_tempo, x="data", y="vendidos", title="Vendas ao longo do tempo")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Ainda não há vendas retiradas para análise temporal.")

    conn.close()


if __name__ == "__main__":
    main()
