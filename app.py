import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DE DESIGN ---
st.set_page_config(page_title="Fiscal Command Center", layout="wide", page_icon="🚀")

# Ajuste CSS para remover cara de "documento" e deixar mais "app"
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    [data-testid="stHeader"] {background-color: rgba(0,0,0,0);}
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DADOS INICIAIS ---
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
                "PDF Fechado": False,  # Checkbox simples
                "Total Revisões": 0,   # Contador simples
            })
    return pd.DataFrame(rows)

# --- CARREGAMENTO ---
try:
    df = conn.read(worksheet="Página1", ttl=0)
    # Verifica se tem as colunas novas, senão reseta
    if df.empty or "PDF Fechado" not in df.columns:
        df = get_initial_data()
except:
    df = get_initial_data()

# Garantir tipos corretos
df["PDF Fechado"] = df["PDF Fechado"].astype(bool)
df["Total Revisões"] = df["Total Revisões"].fillna(0).astype(int)

# --- CABEÇALHO ---
st.title("🚀 Painel de Controle - Auditor Fiscal")
st.markdown("---")

# --- BLOCO 1: KPI CARDS (VISUAL DE DASHBOARD) ---
pdfs_concluidos = df["PDF Fechado"].sum()
total_pdfs = len(df)
total_revisoes = df["Total Revisões"].sum()
progresso_geral = (pdfs_concluidos / total_pdfs) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("PDFs Fechados", f"{pdfs_concluidos}/{total_pdfs}", border=True)
col2.metric("Progresso Edital", f"{progresso_geral:.1f}%", border=True)
col3.metric("Total Revisões Acumuladas", f"{total_revisoes} 🔄", border=True)

# Cálculo da matéria mais forte
materia_forte = df[df["PDF Fechado"]==True]["Disciplina"].mode()
materia_forte_nome = materia_forte[0] if not materia_forte.empty else "Nenhuma"
col4.metric("Foco Principal Atual", materia_forte_nome, border=True)

# --- BLOCO 2: VISUALIZAÇÃO GRÁFICA (SUNBURST) ---
# Este gráfico foge totalmente do padrão Notion
st.subheader("🔭 Radar de Cobertura do Edital")

# Criando coluna de cor baseada no status
df["Cor"] = df["PDF Fechado"].map({True: 1, False: 0})

fig = px.sunburst(
    df, 
    path=['Disciplina', 'Tópico'], 
    values=[1]*len(df), # Tamanho igual para todos
    color='PDF Fechado',
    color_discrete_map={True: '#00CC96', False: '#EF553B'}, # Verde e Vermelho
    title="Mapa de Calor (Vermelho = Pendente | Verde = Fechado)"
)
fig.update_layout(height=500, margin=dict(t=30, l=0, r=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- BLOCO 3: INPUT DE DADOS (SIMPLIFICADO) ---
st.markdown("---")
st.subheader("🎛️ Console de Atualização")

# Filtro
lista_materias = ["TODAS AS MATÉRIAS"] + list(df["Disciplina"].unique())
filtro = st.selectbox("Selecione o Bloco de Estudo:", lista_materias)

if filtro != "TODAS AS MATÉRIAS":
    df_show = df[df["Disciplina"] == filtro]
else:
    df_show = df

# TABELA DE COMANDO
edited_df = st.data_editor(
    df_show,
    column_config={
        "Disciplina": st.column_config.TextColumn("Matéria", disabled=True),
        "Tópico": st.column_config.TextColumn("Assunto", disabled=True),
        "PDF Fechado": st.column_config.CheckboxColumn(
            "PDF Finalizado?",
            help="Marque se você já matou a teoria desse PDF",
            default=False
        ),
        "Total Revisões": st.column_config.NumberColumn(
            "Nº Revisões",
            help="Quantas vezes você já voltou neste assunto?",
            min_value=0,
            step=1,
            format="%d 🔄"
        )
    },
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    key="editor_dashboard"
)

# --- SALVAR ---
st.markdown("###")
col_save, _ = st.columns([1, 4])
if col_save.button("💾 GRAVAR DADOS NA NUVEM", type="primary", use_container_width=True):
    if filtro != "TODAS AS MATÉRIAS":
        df.update(edited_df)
        df_final = df.copy()
    else:
        df_final = edited_df.copy()
    
    conn.update(worksheet="Página1", data=df_final)
    st.toast("✅ Banco de dados atualizado com sucesso!", icon="💾")
    st.rerun()
