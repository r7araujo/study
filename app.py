import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fiscal Command", layout="wide", page_icon="🚀")

# --- FUNÇÃO: DADOS INICIAIS ---
def get_initial_data():
    structure = {
        "Direito Tributário": ["Sistema Tributário Nacional", "Competência Tributária", "Limitações ao Poder de Tributar", "Impostos em Espécie", "Obrigação Tributária", "Crédito Tributário", "Suspensão/Extinção/Exclusão", "Administração Tributária"],
        "Direito Constitucional": ["Direitos Fundamentais", "Nacionalidade/Políticos", "Org. do Estado", "Adm. Pública (37-41)", "Poder Legislativo", "Poder Executivo", "Poder Judiciário", "Funções Essenciais"],
        "Direito Administrativo": ["Regime Jurídico Adm.", "Org. Administrativa", "Atos Administrativos", "Poderes", "Lei 8.112/90", "Licitações (14.133)", "Serviços Públicos", "Resp. Civil do Estado"],
        "RLM": ["Lógica Proposicional", "Tautologia/Contradição", "Equivalências", "Argumentação", "Conjuntos", "Combinatória", "Probabilidade", "Mat. Financeira"],
        "Direito Civil": ["LINDB", "Pessoas", "Domicílio", "Bens", "Fatos Jurídicos", "Prescrição/Decadência", "Obrigações", "Contratos"],
        "Contabilidade Geral": ["Conceitos/Patrimônio", "Escrituração", "DRE", "Balanço Patrimonial", "CPC 00", "Estoque (CPC 16)", "Imobilizado (CPC 27)", "Depreciação"],
        "TI": ["Dados/Info/Conhecimento", "Banco de Dados Relacional", "SQL", "Big Data", "Segurança da Info", "Governança (ITIL/COBIT)", "Ciclo de Software", "Python/R Análise"]
    }
    rows = []
    for materia, topicos in structure.items():
        for topico in topicos:
            rows.append({
                "Disciplina": materia,
                "Tópico": topico,
                "PDF Fechado": False,
                "Revisões": 0,
            })
    return pd.DataFrame(rows)

# --- GERENCIAMENTO DE ESTADO ---
if "df_memory" not in st.session_state:
    st.session_state["df_memory"] = get_initial_data()

# --- BARRA LATERAL ---
st.sidebar.header("📂 Arquivos")
uploaded_file = st.sidebar.file_uploader("Carregar CSV Antigo", type="csv")

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
st.sidebar.header("➕ Adicionar Conteúdo")

with st.sidebar.expander("Novo Tópico ou Matéria"):
    tipo_add = st.radio("Tipo:", ["Tópico em Matéria Existente", "Nova Matéria Completa"])
    disciplinas_atuais = st.session_state["df_memory"]["Disciplina"].unique()
    
    disciplina_input = ""
    if tipo_add == "Tópico em Matéria Existente":
        disciplina_input = st.selectbox("Selecione:", disciplinas_atuais)
    else:
        disciplina_input = st.text_input("Nome da Nova Matéria")
    
    topico_input = st.text_input("Nome do Tópico")
    
    if st.button("Adicionar"):
        if disciplina_input and topico_input:
            novo_dado = pd.DataFrame([{
                "Disciplina": disciplina_input,
                "Tópico": topico_input,
                "PDF Fechado": False,
                "Revisões": 0
            }])
            st.session_state["df_memory"] = pd.concat([st.session_state["df_memory"], novo_dado], ignore_index=True)
            st.success(f"Adicionado: {topico_input}")
            st.rerun()

df = st.session_state["df_memory"]

# --- CABEÇALHO ---
st.title("🚀 Painel de Controle - Auditor Fiscal")

pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("PDFs Fechados", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Total", f"{progresso:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes}", border=True)

# --- ÁREA DE GRÁFICOS (ALTERADA) ---
st.markdown("---")
if not df.empty:
    col_graph1, col_graph2 = st.columns(2)
    
    # Gráfico 1: Cobertura (O que já fechei?)
    with col_graph1:
        st.subheader("🔭 Cobertura (PDFs)")
        fig1 = px.sunburst(
            df, path=['Disciplina', 'Tópico'], values=[1]*len(df),
            color='PDF Fechado', color_discrete_map={True: '#00CC96', False: '#EF553B'},
        )
        fig1.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=350)
        st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Análise de Revisões (NOVO)
    with col_graph2:
        st.subheader("🔄 Volume de Revisões")
        # Agrupa somando as revisões por disciplina
        rev_por_materia = df.groupby("Disciplina")["Revisões"].sum().reset_index()
        
        fig2 = px.bar(
            rev_por_materia, 
            x="Disciplina", 
            y="Revisões", 
            color="Disciplina",
            text_auto=True, # Mostra o número em cima da barra
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig2.update_layout(showlegend=False, margin=dict(t=10, l=10, r=10, b=10), height=350)
        st.plotly_chart(fig2, use_container_width=True)

# --- ÁREA DE EDIÇÃO (FORMULÁRIO) ---
st.markdown("---")
st.subheader("📝 Atualizar Progresso")

filtro = st.selectbox("Filtrar Matéria:", ["TODAS"] + list(df["Disciplina"].unique()))

if filtro != "TODAS":
    df_show = df[df["Disciplina"] == filtro].reset_index(drop=True)
else:
    df_show = df.reset_index(drop=True)

with st.form("my_form"):
    edited_df = st.data_editor(
        df_show,
        column_config={
            "Disciplina": st.column_config.TextColumn(disabled=True),
            "Tópico": st.column_config.TextColumn(disabled=True),
            "PDF Fechado": st.column_config.CheckboxColumn("PDF OK?", width="small"),
            "Revisões": st.column_config.NumberColumn(
                "Nº Rev.", 
                step=1, 
                min_value=0, 
            )
        },
        hide_index=True, 
        use_container_width=True, 
        num_rows="fixed"
    )
    
    submitted = st.form_submit_button("✅ Confirmar Alterações", type="primary")

    if submitted:
        if filtro == "TODAS":
            st.session_state["df_memory"] = edited_df
        else:
            df_full = st.session_state["df_memory"]
            df_others = df_full[df_full["Disciplina"] != filtro]
            st.session_state["df_memory"] = pd.concat([df_others, edited_df], ignore_index=True)
        st.rerun()

# --- DOWNLOAD ---
st.markdown("---")
csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')

st.download_button(
    label="💾 BAIXAR ARQUIVO PARA SALVAR",
    data=csv,
    file_name='meu_progresso_fiscal.csv',
    mime='text/csv',
    type="secondary",
    use_container_width=True
)
