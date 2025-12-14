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
            rows.append({
                "Disciplina": materia,
                "Tópico": f"Aula {i:02d}",
                "PDF Fechado": False,
                "Revisões": 0,
            })
    return pd.DataFrame(rows)

# --- INICIALIZAÇÃO SEGURA DA MEMÓRIA ---
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
        
        # --- CORREÇÃO DE BUG: FORÇAR BOOLEANOS ---
        # Isso corrige o erro onde o gráfico não atualiza porque leu "True" como texto
        bool_map = {'True': True, 'False': False, 'TRUE': True, 'FALSE': False, True: True, False: False}
        if df_temp["PDF Fechado"].dtype == 'object':
            df_temp["PDF Fechado"] = df_temp["PDF Fechado"].map(bool_map).fillna(False)
        else:
            df_temp["PDF Fechado"] = df_temp["PDF Fechado"].astype(bool)
            
        df_temp["Revisões"] = df_temp["Revisões"].fillna(0).astype(int)
        
        # Atualiza a memória apenas se o arquivo for novo
        if not df_temp.equals(st.session_state["df_memory"]):
            st.session_state["df_memory"] = df_temp
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")

st.sidebar.markdown("---")
# Botão de Pânico: Se tudo der errado, isso limpa a memória
if st.sidebar.button("⚠️ RESETAR BANCO DE DADOS", type="primary"):
    st.session_state["df_memory"] = get_initial_data()
    st.rerun()

# Carrega da memória
df = st.session_state["df_memory"]

# ==============================================================================
# PAINEL PRINCIPAL
# ==============================================================================
st.title("⚖️ Painel de Controle - Auditor Fiscal")

# --- KPIs (INDICADORES) ---
pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Aulas Fechadas", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Total", f"{progresso:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes}", border=True)

# --- GRÁFICO GERAL (BARRAS NO TOPO) ---
st.markdown("---")
st.subheader("🏆 Comparativo de Revisões")
if not df.empty:
    df_geral = df.groupby("Disciplina")["Revisões"].sum().reset_index().sort_values("Revisões", ascending=False)
    fig_geral = px.bar(df_geral, x="Disciplina", y="Revisões", color="Disciplina", text="Revisões")
    fig_geral.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_geral, use_container_width=True)

# --- ÁREA DETALHADA POR MATÉRIA ---
st.markdown("---")
st.subheader("🔎 Visão Detalhada")

if not df.empty:
    lista_disciplinas = sorted(df["Disciplina"].unique())
    # O index=4 tenta selecionar Direito Tributário/Const se estiver na lista para facilitar
    materia_foco = st.selectbox("Selecione a Disciplina:", lista_disciplinas)
    
    # Filtra os dados (Cria uma cópia limpa para os gráficos)
    df_foco = df[df["Disciplina"] == materia_foco].copy()
    
    col_g1, col_g2 = st.columns(2)
    
    # Gráfico Pizza
    with col_g1:
        st.markdown(f"**🔭 Progresso: {materia_foco}**")
        concluido = int(df_foco["PDF Fechado"].sum()) # Força conversão para número
        pendente = len(df_foco) - concluido
        
        fig_pizza = px.pie(
            values=[concluido, pendente], names=["Concluído", "Pendente"],
            hole=0.5, color_discrete_sequence=["#00CC96", "#EF553B"]
        )
        fig_pizza.update_traces(textinfo='percent+label')
        fig_pizza.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
        # Adiciona o número % no meio
        pct = int((concluido / len(df_foco)) * 100) if len(df_foco) > 0 else 0
        fig_pizza.add_annotation(text=f"{pct}%", x=0.5, y=0.5, font_size=20, showarrow=False)
        st.plotly_chart(fig_pizza, use_container_width=True)

    # Gráfico Barras (Aulas)
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

# --- ÁREA DE EDIÇÃO ---
st.markdown("---")
st.subheader(f"📝 Editar: {materia_foco}")

# Prepara tabela para edição
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
        hide_index=True, use_container_width=True, num_rows="fixed",
        key=f"editor_{materia_foco}" # Chave única para evitar conflito de cache
    )
    
    # O BOTÃO DE CONFIRMAÇÃO
    if st.form_submit_button("✅ Confirmar Alterações", type="primary"):
        # Lógica de atualização segura
        df_full = st.session_state["df_memory"]
        
        # Remove as linhas antigas dessa matéria
        df_others = df_full[df_full["Disciplina"] != materia_foco]
        
        # Junta o resto com a versão editada
        st.session_state["df_memory"] = pd.concat([df_others, edited_df], ignore_index=True)
        st.rerun()

# --- DOWNLOAD ---
st.markdown("---")
csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')
st.download_button(
    label="💾 BAIXAR ARQUIVO (Salvar Progresso)", 
    data=csv, 
    file_name='progresso_auditor.csv', 
    mime='text/csv', 
    type="secondary", 
    use_container_width=True
)
