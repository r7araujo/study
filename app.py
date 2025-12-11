import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA (OTIMIZADA PARA MOBILE) ---
st.set_page_config(page_title="Fiscal Tracker", layout="wide", page_icon="⚖️")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DADOS DO EDITAL (BASE DE DADOS INICIAL) ---
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
                "Status": "Não Iniciado",
                "Revisões": 0,
                "Acertos": 0,
                "Questões Totais": 0,
                "% Acerto": 0.0
            })
    return pd.DataFrame(rows)

# --- CARREGAR DADOS ---
st.title("📱 Fiscal Tracker - iPad Edition")

try:
    # Tenta ler a planilha. Se estiver vazia ou der erro, carrega o padrão
    df = conn.read(worksheet="Página1", ttl=0) # ttl=0 evita cache antigo
    if df.empty or "Disciplina" not in df.columns:
        df = get_initial_data()
except:
    df = get_initial_data()

# --- DASHBOARD RÁPIDO (TOPO) ---
st.caption("Visão Geral do Ciclo Básico")
col1, col2, col3 = st.columns(3)
total_topicos = len(df)
concluidos = len(df[df["Status"] == "Finalizado"])
em_andamento = len(df[df["Status"] == "Em Estudo"])

col1.metric("Progresso", f"{round((concluidos/total_topicos)*100)}%")
col2.metric("Finalizados", concluidos)
col3.metric("Estudando", em_andamento)

with st.expander("📊 Ver Gráfico de Evolução"):
    progresso_por_materia = df[df["Status"] == "Finalizado"].groupby("Disciplina").size()
    total_por_materia = df.groupby("Disciplina").size()
    evolucao = (progresso_por_materia / total_por_materia * 100).fillna(0).reset_index(name="Progresso")
    fig = px.bar(evolucao, x="Progresso", y="Disciplina", orientation='h', text_auto='.0f')
    fig.update_layout(xaxis_range=[0, 100], margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- ÁREA DE ESTUDO (TABELA EDITÁVEL) ---
st.markdown("---")
st.subheader("📝 Registro de Estudos")

# Filtro por matéria para não poluir a tela do iPad
materia_filtro = st.selectbox("Filtrar Disciplina:", ["TODAS"] + list(df["Disciplina"].unique()))

if materia_filtro != "TODAS":
    df_show = df[df["Disciplina"] == materia_filtro]
else:
    df_show = df

# A TABELA MÁGICA (Data Editor)
# Permite editar direto na tela como se fosse Excel
edited_df = st.data_editor(
    df_show,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Não Iniciado", "Em Estudo", "Resumo Feito", "Finalizado"],
            required=True,
            width="medium"
        ),
        "% Acerto": st.column_config.ProgressColumn(
            "Desempenho",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Revisões": st.column_config.NumberColumn("Rev.", min_value=0, step=1),
        "Acertos": st.column_config.NumberColumn("Acertos", min_value=0),
        "Questões Totais": st.column_config.NumberColumn("Q. Totais", min_value=0),
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    key="editor"
)

# --- BOTÃO DE SALVAR ---
# Lógica para recalcular % e salvar na nuvem
if st.button("💾 Salvar Alterações na Nuvem", type="primary", use_container_width=True):
    # Atualiza o dataframe original com as edições feitas na tela
    if materia_filtro != "TODAS":
        # Se estava filtrado, atualizamos apenas as linhas correspondentes
        df.update(edited_df)
        df_final = df.copy()
    else:
        df_final = edited_df.copy()
    
    # Recalcula a porcentagem de acertos
    df_final["% Acerto"] = df_final.apply(
        lambda x: (x["Acertos"] / x["Questões Totais"] * 100) if x["Questões Totais"] > 0 else 0, 
        axis=1
    )
    
    # Envia para o Google Sheets
    conn.update(worksheet="Página1", data=df_final)
    st.success("Sincronizado com sucesso! Pode fechar.")
    st.rerun()