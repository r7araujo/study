import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fiscal Tracker", layout="wide", page_icon="📊")

# --- FUNÇÃO: DADOS INICIAIS ---
def get_initial_data():
    limits = {
        "Contabilidade Geral": 32,
        "Direito Administrativo": 16,
        "Direito Civil": 15,
        "Direito Constitucional": 21,
        "Direito Tributário": 22,
        "RLM": 33,
        "Tecnologia da Informação": 17
    }
    rows = []
    for materia, max_num in limits.items():
        for i in range(max_num + 1):
            nome_topico = f"Aula {i:02d}"
            rows.append({
                "Disciplina": materia,
                "Tópico": nome_topico,
                "PDF Fechado": False,
                "Revisões": 0,
            })
    return pd.DataFrame(rows)

# --- MEMÓRIA ---
if "df_memory" not in st.session_state:
    st.session_state["df_memory"] = get_initial_data()

# ==============================================================================
# BARRA LATERAL (ARQUIVOS)
# ==============================================================================
st.sidebar.header("📂 Arquivos")
uploaded_file = st.sidebar.file_uploader("Carregar CSV Salvo", type="csv")

if uploaded_file is not None:
    try:
        df_temp = pd.read_csv(uploaded_file)
        df_temp["PDF Fechado"] = df_temp["PDF Fechado"].astype(bool)
        df_temp["Revisões"] = df_temp["Revisões"].fillna(0).astype(int)
        
        if not df_temp.equals(st.session_state["df_memory"]):
            st.session_state["df_memory"] = df_temp
            st.rerun()
    except:
        st.error("Arquivo inválido.")

st.sidebar.markdown("---")
if st.sidebar.button("⚠️ RESETAR BANCO DE DADOS", type="primary"):
    st.session_state["df_memory"] = get_initial_data()
    st.rerun()

df = st.session_state["df_memory"]

# ==============================================================================
# PAINEL PRINCIPAL
# ==============================================================================
st.title("⚖️ Painel de Controle - Auditor Fiscal")

# KPIs
pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Aulas Fechadas", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Total", f"{progresso:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes}", border=True)

# GRÁFICO GERAL (COMPARATIVO ENTRE MATÉRIAS)
st.markdown("---")
st.subheader("🏆 Comparativo de Revisões")
if not df.empty:
    df_geral = df.groupby("Disciplina")["Revisões"].sum().reset_index().sort_values("Revisões", ascending=False)
    fig_geral = px.bar(df_geral, x="Disciplina", y="Revisões", color="Disciplina", text="Revisões")
    fig_geral.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_geral, use_container_width=True)

# VISÃO DETALHADA POR DISCIPLINA
st.markdown("---")
st.subheader("🔎 Visão por Disciplina")

if not df.empty:
    lista_disciplinas = sorted(df["Disciplina"].unique())
    materia_foco = st.selectbox("Selecione a Disciplina:", lista_disciplinas)
    
    df_foco = df[df["Disciplina"] == materia_foco].copy()
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown(f"**🔭 Progresso: {materia_foco}**")
        concluido = df_foco["PDF Fechado"].sum()
        pendente = len(df_foco) - concluido
        fig_pizza = px.pie(
            values=[concluido, pendente], names=["Concluído", "Pendente"],
            hole=0.5, color_discrete_sequence=["#00CC96", "#EF553B"]
        )
        fig_pizza.update_traces(textinfo='percent+label')
        fig_pizza.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g2:
        st.markdown(f"**🔄 Revisões por Aula**")
        fig_rev = px.bar(
            df_foco, y="Tópico", x="Revisões", orientation='h', text_auto=True,
            color="Revisões", color_continuous_scale="Blues"
        )
        fig_rev.update_layout(
            yaxis_title=None, xaxis_title="Qtd Revisões", margin=dict(t=0, l=0, r=0, b=0),
            height=max(400, len(df_foco) * 25), yaxis={'autorange': "reversed"}
        )
        st.plotly_chart(fig_rev, use_container_width=True)

# ÁREA DE EDIÇÃO
st.markdown("---")
st.subheader(f"📝 Editar: {materia_foco}")
df_show = df[df["Disciplina"] == materia_foco].reset_index(drop=True)

with st.form("my_form"):
    edited_df = st.data_editor(
        df_show,
        column_config={
            "Disciplina": st.column_config.TextColumn(disabled=True),
            "Tópico": st.column_config.TextColumn("Aula", disabled=True),
            "PDF Fechado": st.column_config.CheckboxColumn("Concluído?", width="small"),
            "Revisões": st.column_config.NumberColumn("Nº Rev.", step=1, min_value=0)
        },
        hide_index=True, use_container_width=True, num_rows="fixed"
    )
    if st.form_submit_button("✅ Confirmar Alterações", type="primary"):
        df_full = st.session_state["df_memory"]
        df_others = df_full[df_full["Disciplina"] != materia_foco]
        st.session_state["df_memory"] = pd.concat([df_others, edited_df], ignore_index=True)
        st.rerun()

# DOWNLOAD
st.markdown("---")
csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')
st.download_button("💾 BAIXAR ARQUIVO (Salvar Progresso)", data=csv, file_name='progresso_auditor.csv', mime='text/csv', type="secondary", use_container_width=True)
