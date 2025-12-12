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

# --- BARRA LATERAL (ARQUIVOS + ADICIONAR MATÉRIA) ---
st.sidebar.header("📂 Arquivos")
uploaded_file = st.sidebar.file_uploader("Carregar progresso (CSV)", type="csv")

if uploaded_file is not None:
    try:
        # Se carregou arquivo, lê ele
        df = pd.read_csv(uploaded_file)
        # Garante tipos
        df["PDF Fechado"] = df["PDF Fechado"].astype(bool)
        df["Revisões"] = df["Revisões"].fillna(0).astype(int)
        # Atualiza a memória se o arquivo for novo
        if not df.equals(st.session_state["df_memory"]):
            st.session_state["df_memory"] = df
    except:
        st.error("Erro no arquivo.")
        df = st.session_state["df_memory"]
else:
    # Se não tem arquivo, usa a memória atual
    df = st.session_state["df_memory"]

st.sidebar.markdown("---")
st.sidebar.header("➕ Adicionar Conteúdo")

# Menu de Adição
with st.sidebar.expander("Criar Novo Tópico/Matéria"):
    tipo_add = st.radio("O que adicionar?", ["Em Matéria Existente", "Nova Matéria Completa"])
    
    disciplina_input = ""
    if tipo_add == "Em Matéria Existente":
        disciplina_input = st.selectbox("Escolha a Matéria:", df["Disciplina"].unique())
    else:
        disciplina_input = st.text_input("Nome da Nova Matéria (ex: Direito Penal)")
    
    topico_input = st.text_input("Nome do Tópico (ex: Crimes contra a Vida)")
    
    if st.button("Adicionar ao Edital"):
        if disciplina_input and topico_input:
            novo_dado = pd.DataFrame([{
                "Disciplina": disciplina_input,
                "Tópico": topico_input,
                "PDF Fechado": False,
                "Revisões": 0
            }])
            # Adiciona ao DataFrame principal
            st.session_state["df_memory"] = pd.concat([st.session_state["df_memory"], novo_dado], ignore_index=True)
            st.success(f"✅ Adicionado: {topico_input}")
            st.rerun() # Recarrega para aparecer na tela
        else:
            st.warning("Preencha todos os campos!")

# Atualiza df com o que está na memória (incluindo adições recentes)
df = st.session_state["df_memory"]

# --- CABEÇALHO ---
st.title("🚀 Painel de Controle")

# --- KPIs ---
pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso_geral = (pdfs_concluidos / total_pdfs) * 100 if total_pdfs > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("PDFs Fechados", f"{pdfs_concluidos}/{total_pdfs}", border=True)
c2.metric("Progresso Global", f"{progresso_geral:.1f}%", border=True)
c3.metric("Total Revisões", f"{total_revisoes} 🔄", border=True)

# --- GRÁFICO ---
if not df.empty:
    st.subheader("🔭 Radar de Edital")
    fig = px.sunburst(
        df, path=['Disciplina', 'Tópico'], values=[1]*len(df),
        color='PDF Fechado', color_discrete_map={True: '#00CC96', False: '#EF553B'},
        title="Vermelho = Pendente | Verde = Concluído"
    )
    fig.update_layout(height=450, margin=dict(t=30, l=0, r=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- ÁREA DE EDIÇÃO ---
st.markdown("---")
st.subheader("📝 Atualizar Progresso")

filtro = st.selectbox("Filtrar Matéria:", ["TODAS"] + list(df["Disciplina"].unique()))

if filtro != "TODAS":
    df_show = df[df["Disciplina"] == filtro]
else:
    df_show = df

# Tabela Editável
edited_df = st.data_editor(
    df_show,
    column_config={
        "Disciplina": st.column_config.TextColumn(disabled=True),
        "Tópico": st.column_config.TextColumn(disabled=True),
        "PDF Fechado": st.column_config.CheckboxColumn("PDF OK?", width="small"),
        "Revisões": st.column_config.NumberColumn("Nº Rev.", step=1, min_value=0)
    },
    hide_index=True, use_container_width=True, num_rows="fixed"
)

# --- LÓGICA DE SALVAMENTO DE ESTADO ---
# Se o usuário editou a tabela, precisamos atualizar a memória principal
if not edited_df.equals(df_show):
    if filtro == "TODAS":
        st.session_state["df_memory"] = edited_df
    else:
        # Atualização cirúrgica (apenas nas linhas filtradas)
        # Primeiro, removemos as linhas antigas dessa matéria
        base_sem_filtro = st.session_state["df_memory"][st.session_state["df_memory"]["Disciplina"] != filtro]
        # Concatenamos com as linhas editadas
        st.session_state["df_memory"] = pd.concat([base_sem_filtro, edited_df], ignore_index=True)
    
    st.rerun() # Atualiza a tela instantaneamente

# --- BOTÃO DE DOWNLOAD (SALVAR) ---
st.markdown("###")
st.success("Não esqueça de baixar seu arquivo atualizado ao final do estudo!")

csv = st.session_state["df_memory"].to_csv(index=False).encode('utf-8')

st.download_button(
    label="💾 BAIXAR ARQUIVO ATUALIZADO (Salvar)",
    data=csv,
    file_name='meu_progresso_fiscal.csv',
    mime='text/csv',
    type="primary",
    use_container_width=True
)
