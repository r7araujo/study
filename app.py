import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fiscal Tracker", layout="wide", page_icon="📊")

# --- FUNÇÃO: GERAR DADOS COM NUMERAÇÃO (00, 01, 02...) ---
def get_initial_data():
    # Configuração dos limites de cada matéria
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
            # Formata como "Aula 00", "Aula 01" (sempre 2 dígitos)
            nome_topico = f"Aula {i:02d}"
            rows.append({
                "Disciplina": materia,
                "Tópico": nome_topico,
                "PDF Fechado": False,
                "Revisões": 0,
            })
    return pd.DataFrame(rows)

# --- GERENCIAMENTO DE ESTADO ---
if "df_memory" not in st.session_state:
    st.session_state["df_memory"] = get_initial_data()

# --- BARRA LATERAL ---
st.sidebar.header("📂 Arquivos")
uploaded_file = st.sidebar.file_uploader("Carregar CSV", type="csv")

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
st.sidebar.info("Para adicionar matérias extras, edite o código ou use a versão anterior. Esta versão foca na numeração fixa.")

df = st.session_state["df_memory"]

# --- CABEÇALHO ---
st.title("📊 Painel Auditor Fiscal")

pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("PDFs Fechados", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Total", f"{progresso:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes}", border=True)

# --- ÁREA DE ANÁLISE (PIZZA + REVISÕES) ---
st.markdown("---")
st.subheader("🔎 Análise por Disciplina")

if not df.empty:
    lista_disciplinas = sorted(df["Disciplina"].unique())
    
    # 1. Seletor de Matéria
    materia_foco = st.selectbox("Selecione a Disciplina para ver o gráfico:", lista_disciplinas)
    
    # Filtra dados
    df_foco = df[df["Disciplina"] == materia_foco].copy()
    
    col_g1, col_g2 = st.columns(2)
    
    # --- GRÁFICO 1: PIZZA (DONUT) DE PROGRESSO ---
    with col_g1:
        st.markdown(f"**🔭 Progresso: {materia_foco}**")
        
        # Prepara dados para o gráfico de pizza
        concluido = df_foco["PDF Fechado"].sum()
        pendente = len(df_foco) - concluido
        dados_pizza = pd.DataFrame({
            "Status": ["Concluído", "Pendente"],
            "Quantidade": [concluido, pendente]
        })
        
        # Cria o gráfico Donut (Pizza com furo)
        fig_pizza = px.pie(
            dados_pizza, 
            values="Quantidade", 
            names="Status",
            hole=0.6, # Faz o furo no meio (Donut)
            color="Status",
            color_discrete_map={"Concluído": "#00CC96", "Pendente": "#EF553B"}
        )
        
        # Deixa bonitão
        fig_pizza.update_traces(textinfo='percent+label')
        fig_pizza.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
        
        # Coloca o número total no meio do buraco
        fig_pizza.add_annotation(text=f"{int((concluido/len(df_foco))*100)}%", x=0.5, y=0.5, font_size=20, showarrow=False)
        
        st.plotly_chart(fig_pizza, use_container_width=True)

    # --- GRÁFICO 2: BARRAS DE REVISÃO ---
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
        # Ajusta altura dinamicamente para caber todas as aulas sem espremer
        altura_dinamica = max(350, len(df_foco) * 25)
        
        fig_rev.update_layout(
            yaxis_title=None,
            xaxis_title="Qtd Revisões",
            margin=dict(t=0, l=0, r=0, b=0),
            height=altura_dinamica
        )
        # Inverte eixo Y para Aula 00 ficar em cima
        fig_rev['layout']['yaxis']['autorange'] = "reversed"
        
        st.plotly_chart(fig_rev, use_container_width=True)

# --- ÁREA DE EDIÇÃO (FORMULÁRIO) ---
st.markdown("---")
st.subheader("📝 Marcar Aulas")

# Usa a mesma seleção de cima ou permite mudar
filtro_tabela = st.selectbox("Filtrar Tabela:", ["IGUAL AO GRÁFICO", "TODAS"])

if filtro_tabela == "IGUAL AO GRÁFICO":
    df_show = df[df["Disciplina"] == materia_foco].reset_index(drop=True)
else:
    df_show = df.reset_index(drop=True)

with st.form("my_form"):
    edited_df = st.data_editor(
        df_show,
        column_config={
            "Disciplina": st.column_config.TextColumn(disabled=True),
            "Tópico": st.column_config.TextColumn(disabled=True),
            "PDF Fechado": st.column_config.CheckboxColumn("PDF OK?", width="small"),
            "Revisões": st.column_config.NumberColumn("Nº Rev.", step=1, min_value=0)
        },
        hide_index=True, 
        use_container_width=True, 
        num_rows="fixed"
    )
    
    submitted = st.form_submit_button("✅ Confirmar Alterações", type="primary")

    if submitted:
        if filtro_tabela == "TODAS":
            st.session_state["df_memory"] = edited_df
        else:
            # Atualiza apenas a matéria filtrada no dataframe principal
            df_full = st.session_state["df_memory"]
            df_others = df_full[df_full["Disciplina"] != materia_foco]
            st.session_state["df_memory"] = pd.concat([df_others, edited_df], ignore_index=True)
        st.rerun()

# --- DOWNLOAD ---
st.markdown("---")
csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')

st.download_button(
    label="💾 BAIXAR ARQUIVO (Salvar)",
    data=csv,
    file_name='progresso_auditor.csv',
    mime='text/csv',
    type="secondary",
    use_container_width=True
)
