import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fiscal Tracker", layout="wide", page_icon="📊")

# --- FUNÇÃO: GERAR DADOS COM NUMERAÇÃO CORRETA ---
def get_initial_data():
    # Limites exatos solicitados
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
        # Gera de 0 até o número limite (inclusive)
        for i in range(max_num + 1):
            # Formata como "Aula 00", "Aula 01"...
            nome_topico = f"Aula {i:02d}"
            rows.append({
                "Disciplina": materia,
                "Tópico": nome_topico,
                "PDF Fechado": False,
                "Revisões": 0,
            })
    return pd.DataFrame(rows)

# --- GERENCIAMENTO DE ESTADO ---
# Se não existir dados na memória, carrega o inicial
if "df_memory" not in st.session_state:
    st.session_state["df_memory"] = get_initial_data()

# --- BARRA LATERAL ---
st.sidebar.header("📂 Gerenciamento")

# 1. Carregar Arquivo
uploaded_file = st.sidebar.file_uploader("Carregar Progresso Salvo (CSV)", type="csv")
if uploaded_file is not None:
    try:
        df_temp = pd.read_csv(uploaded_file)
        df_temp["PDF Fechado"] = df_temp["PDF Fechado"].astype(bool)
        df_temp["Revisões"] = df_temp["Revisões"].fillna(0).astype(int)
        
        # Verifica se o arquivo carregado é diferente da memória atual
        if not df_temp.equals(st.session_state["df_memory"]):
            st.session_state["df_memory"] = df_temp
            st.rerun()
    except:
        st.error("Arquivo inválido.")

st.sidebar.markdown("---")

# 2. BOTÃO DE EMERGÊNCIA (RESET)
# Use isso se estiver aparecendo os nomes antigos dos tópicos
if st.sidebar.button("⚠️ RESETAR BANCO DE DADOS", help="Apaga tudo e recria com as Aulas 00-XX", type="primary"):
    st.session_state["df_memory"] = get_initial_data()
    st.rerun()

df = st.session_state["df_memory"]

# --- CABEÇALHO ---
st.title("📊 Painel Auditor Fiscal")

pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Aulas Fechadas", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Total", f"{progresso:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes}", border=True)

# --- ÁREA DE ANÁLISE (PIZZA + BARRAS) ---
st.markdown("---")
st.subheader("🔎 Análise por Disciplina")

if not df.empty:
    lista_disciplinas = sorted(df["Disciplina"].unique())
    
    # Seletor de Matéria
    materia_foco = st.selectbox("Selecione a Disciplina:", lista_disciplinas)
    
    # Filtra dados apenas dessa matéria
    df_foco = df[df["Disciplina"] == materia_foco].copy()
    
    col_g1, col_g2 = st.columns(2)
    
    # --- GRÁFICO 1: PIZZA (DONUT) DE PROGRESSO ---
    with col_g1:
        st.markdown(f"**🔭 Progresso: {materia_foco}**")
        
        concluido = df_foco["PDF Fechado"].sum()
        pendente = len(df_foco) - concluido
        
        # Dados para o gráfico
        dados_pizza = pd.DataFrame({
            "Status": ["Concluído", "Pendente"],
            "Quantidade": [concluido, pendente]
        })
        
        # Gráfico Donut
        fig_pizza = px.pie(
            dados_pizza, 
            values="Quantidade", 
            names="Status",
            hole=0.5, # Faz o furo no meio
            color="Status",
            color_discrete_map={"Concluído": "#00CC96", "Pendente": "#EF553B"}
        )
        
        # Visual clean
        fig_pizza.update_traces(textinfo='percent+label', textfont_size=14)
        fig_pizza.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
        
        st.plotly_chart(fig_pizza, use_container_width=True)

    # --- GRÁFICO 2: BARRAS DE REVISÃO (AULA 00 a XX) ---
    with col_g2:
        st.markdown(f"**🔄 Revisões por Aula**")
        
        fig_rev = px.bar(
            df_foco,
            y="Tópico", # Aula 00, Aula 01...
            x="Revisões",
            orientation='h',
            text_auto=True,
            color="Revisões",
            color_continuous_scale="Blues"
        )
        
        # Altura dinâmica para caber todas as aulas (evita espremer)
        altura_dinamica = max(400, len(df_foco) * 25)
        
        fig_rev.update_layout(
            yaxis_title=None,
            xaxis_title="Qtd Revisões",
            margin=dict(t=0, l=0, r=0, b=0),
            height=altura_dinamica
        )
        # Inverte o eixo Y para Aula 00 ficar no topo
        fig_rev['layout']['yaxis']['autorange'] = "reversed"
        
        st.plotly_chart(fig_rev, use_container_width=True)

# --- ÁREA DE EDIÇÃO (FORMULÁRIO) ---
st.markdown("---")
st.subheader(f"📝 Marcar Aulas: {materia_foco}")

# Mostra apenas a matéria selecionada no gráfico
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
        hide_index=True, 
        use_container_width=True, 
        num_rows="fixed"
    )
    
    submitted = st.form_submit_button("✅ Confirmar Alterações", type="primary")

    if submitted:
        # Atualiza o banco de dados principal com as alterações feitas na matéria filtrada
        df_full = st.session_state["df_memory"]
        
        # Remove as linhas antigas dessa matéria
        df_others = df_full[df_full["Disciplina"] != materia_foco]
        
        # Adiciona as linhas novas editadas
        st.session_state["df_memory"] = pd.concat([df_others, edited_df], ignore_index=True)
        st.rerun()

# --- DOWNLOAD ---
st.markdown("---")
# Gera o CSV para salvar
csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')

st.download_button(
    label="💾 BAIXAR ARQUIVO (Salvar Progresso)",
    data=csv,
    file_name='progresso_auditor_aulas.csv',
    mime='text/csv',
    type="secondary",
    use_container_width=True
)
