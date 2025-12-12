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
    disciplinas_atuais = sorted(st.session_state["df_memory"]["Disciplina"].unique())
    
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

# --- ÁREA DE GRÁFICOS POR DISCIPLINA (NOVA LÓGICA) ---
st.markdown("---")
st.subheader("📊 Análise Detalhada por Disciplina")

if not df.empty:
    lista_disciplinas = sorted(df["Disciplina"].unique())
    # O usuário escolhe UMA disciplina para focar os gráficos
    materia_foco = st.selectbox("Selecione a Disciplina para visualizar os gráficos:", lista_disciplinas)
    
    # Filtra os dados apenas dessa disciplina
    df_foco = df[df["Disciplina"] == materia_foco].copy()
    
    # Cria duas colunas para os gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown(f"**🔭 Situação dos Tópicos: {materia_foco}**")
        # Gráfico de barras horizontais: Tópico vs Status
        # Usamos trick do Plotly: x=1 para todas as barras terem mesmo tamanho, cor define status
        fig_prog = px.bar(
            df_foco, 
            y="Tópico", 
            x=[1]*len(df_foco), 
            color="PDF Fechado",
            orientation='h',
            color_discrete_map={True: '#00CC96', False: '#EF553B'}, # Verde e Vermelho
            text="PDF Fechado", # Mostra True/False (ou podemos customizar)
            category_orders={"Tópico": sorted(df_foco["Tópico"].tolist())} # Ordena alfabeticamente ou manter ordem
        )
        # Limpeza visual do gráfico
        fig_prog.update_traces(texttemplate="%{y}", textposition="inside", insidetextanchor="start")
        fig_prog.update_yaxes(visible=False, showticklabels=False) # Esconde eixo Y pois o texto já está na barra
        fig_prog.update_xaxes(visible=False)
        fig_prog.update_layout(
            showlegend=True, 
            legend_title="PDF Finalizado?",
            margin=dict(t=0, l=0, r=0, b=0), 
            height=max(400, len(df_foco) * 25) # Altura dinâmica baseada no número de tópicos
        )
        st.plotly_chart(fig_prog, use_container_width=True)
        st.caption("Verde = Concluído | Vermelho = Pendente")

    with col_g2:
        st.markdown(f"**🔄 Quantidade de Revisões por Assunto**")
        # Gráfico de barras: Quantas revisões em CADA tópico
        fig_rev = px.bar(
            df_foco,
            y="Tópico",
            x="Revisões",
            orientation='h',
            text_auto=True,
            color="Revisões",
            color_continuous_scale="Blues"
        )
        fig_rev.update_layout(
            yaxis_title=None,
            xaxis_title="Nº de Revisões",
            margin=dict(t=0, l=0, r=0, b=0),
            height=max(400, len(df_foco) * 25) # Mesma altura dinâmica
        )
        st.plotly_chart(fig_rev, use_container_width=True)

# --- ÁREA DE EDIÇÃO ---
st.markdown("---")
st.subheader("📝 Atualizar e Estudar")

filtro = st.selectbox("Filtrar Tabela para Edição:", ["TODAS"] + lista_disciplinas)

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
