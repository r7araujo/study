import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fiscal Command", layout="wide", page_icon="🚀")

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DADOS ---
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

# Carregamento seguro
try:
    df = conn.read(worksheet="Página1", ttl=0)
    if df.empty or "PDF Fechado" not in df.columns:
        df = get_initial_data()
except:
    df = get_initial_data()

# Tipagem
df["PDF Fechado"] = df["PDF Fechado"].astype(bool)
df["Revisões"] = df["Revisões"].fillna(0).astype(int)

# --- VISUAL DO DASHBOARD ---
st.title("🚀 Painel de Controle - Auditor Fiscal")

# KPIs (Agora usando st.container nativo para não bugar no modo escuro)
pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Revisões"].sum()
progresso_geral = (pdfs_concluidos / total_pdfs) * 100

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric("PDFs Fechados", f"{pdfs_concluidos}/{total_pdfs}")
with col2:
    with st.container(border=True):
        st.metric("Progresso Global", f"{progresso_geral:.1f}%")
with col3:
    with st.container(border=True):
        st.metric("Total Revisões", f"{total_revisoes} 🔄")

# GRÁFICO SUNBURST
st.subheader("🔭 Radar de Edital")
df["Cor"] = df["PDF Fechado"].map({True: 1, False: 0})
fig = px.sunburst(
    df, path=['Disciplina', 'Tópico'], values=[1]*len(df),
    color='PDF Fechado', color_discrete_map={True: '#00CC96', False: '#EF553B'},
    title="Vermelho = Pendente | Verde = Concluído"
)
fig.update_layout(height=500, margin=dict(t=30, l=0, r=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- ÁREA DE EDIÇÃO ---
st.markdown("---")
st.subheader("📝 Atualizar Progresso")
filtro = st.selectbox("Filtrar Matéria:", ["TODAS"] + list(df["Disciplina"].unique()))

if filtro != "TODAS":
    df_show = df[df["Disciplina"] == filtro]
else:
    df_show = df

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

# --- SALVAR ---
if st.button("💾 GRAVAR NA NUVEM", type="primary", use_container_width=True):
    if filtro != "TODAS":
        df.update(edited_df)
        df_final = df.copy()
    else:
        df_final = edited_df.copy()
    conn.update(worksheet="Página1", data=df_final)
    st.toast("Sucesso! Banco de dados atualizado.", icon="✅")
    st.rerun()
