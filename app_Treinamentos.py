import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CONEXÃO
# ==========================================
st.set_page_config(page_title="Dashboard de Treinamentos", layout="wide", initial_sidebar_state="expanded")

# Dicionários de tradução
MESES_PT = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

# Conexão com o Google Sheets (Substituiu os caminhos locais do OS)
conn = st.connection("gsheets", type=GSheetsConnection)
URL_PLANILHA = "[https://docs.google.com/spreadsheets/d/12qx7Y7fM1rSq2Mtt79QwV5owtL8hj7A9CYMBaldhMzo/edit?gid=2052337637#gid=2052337637](https://docs.google.com/spreadsheets/d/12qx7Y7fM1rSq2Mtt79QwV5owtL8hj7A9CYMBaldhMzo/edit?gid=2052337637#gid=2052337637)"

# ==========================================
# FUNÇÕES DE CARREGAMENTO DE DADOS (NUVEM)
# ==========================================
@st.cache_data(ttl=5) # Cache curto para a nuvem atualizar rápido
def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Dados")
        
        if not df.empty:
            df['DATA'] = pd.to_datetime(df['DATA'])
            
            df['ANO'] = df['DATA'].dt.year
            df['MES_NUM'] = df['DATA'].dt.month
            
            # Limpeza para evitar filtros duplicados
            df['TIPO DO PARTICIPANTE'] = df['TIPO DO PARTICIPANTE'].astype(str).str.strip().str.title()
            df['LOCAL'] = df['LOCAL'].astype(str).str.strip()
            df['Setor Participante'] = df['Setor Participante'].astype(str).str.strip()
            
            # Cria as colunas para o filtro de mês em PT
            df['MÊS_NOME'] = df['MES_NUM'].map(MESES_PT)
            df['MES_ANO_FILTRO'] = df['MÊS_NOME'] + "." + df['ANO'].astype(str).str[-2:]
            
            df['Ordem_Tempo'] = df['ANO'].astype(str) + df['MES_NUM'].astype(str).str.zfill(2)
            
            return df
    except Exception:
        pass
    
    # Se der erro ou a planilha estiver vazia, cria a estrutura base
    colunas = ['ID', 'ANO', 'DATA', 'NOME DO TREINAMENTO', 'LOCAL', 
               'TIPO DO PARTICIPANTE', 'QTD PARTICIPANTES', 'Setor Participante']
    return pd.DataFrame(columns=colunas)

def carregar_setores():
    # Mantido estático conforme sua estrutura anterior para simplificar a transição
    return ["SALA DE CGRSS", "ALA A", "ALA B", "ALA C", "OUTROS"] 

def salvar_registro(novo_registro):
    # Nova lógica de salvamento: Sincroniza com o Google Sheets em vez do Excel
    df_atual = carregar_dados()
    novo_id = 1 if df_atual.empty or 'ID' not in df_atual.columns else df_atual['ID'].max() + 1
    novo_registro['ID'] = novo_id
    
    df_novo = pd.DataFrame([novo_registro])
    df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    
    colunas_para_salvar = ['ID', 'ANO', 'DATA', 'NOME DO TREINAMENTO', 'LOCAL', 
                           'TIPO DO PARTICIPANTE', 'QTD PARTICIPANTES', 'Setor Participante']
    
    conn.update(worksheet="Dados", data=df_final[colunas_para_salvar], spreadsheet=URL_PLANILHA)
    st.cache_data.clear()

def salvar_banco_completo(df_editado):
    # Função auxiliar para salvar edições completas feitas na tela de Gestão
    conn.update(worksheet="Dados", data=df_editado, spreadsheet=URL_PLANILHA)
    st.cache_data.clear()

# ==========================================
# FUNÇÃO DE ESTILIZAÇÃO DOS GRÁFICOS (Tema ViaFluxo mantido)
# ==========================================
def aplicar_estilo_grafico(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=12, color="#333"),
        title_font=dict(size=16, color="#1f77b4", family="Arial Black"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=False, title="", showline=False, zeroline=False, showticklabels=False)
    )
    return fig

# ==========================================
# MENU LATERAL DE NAVEGAÇÃO
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2936/2936690.png", width=60)
    st.title("Navegação")
    # Menu atualizado com a 3ª opção pedida no áudio
    menu = st.radio("", ["📊 Dashboard Analítico", "📝 Cadastro de Treinamento", "⚙️ Gestão de Dados"])
    st.markdown("---")

# ==========================================
# TELA 1: DASHBOARD (Mantido 100% como o seu original)
# ==========================================
if menu == "📊 Dashboard Analítico":
    st.title("📊 Dashboard de Treinamentos")
    st.markdown("Acompanhamento e indicadores de desenvolvimento.")
    
    df = carregar_dados()
    
    if df.empty:
        st.info("Nenhum dado cadastrado na base ainda.")
    else:
        st.sidebar.subheader("🎯 Filtros")
        
        anos_disp = sorted(df['ANO'].dropna().unique().tolist())
        ano_selecionado = st.sidebar.multiselect("Ano", anos_disp, default=anos_disp)
        
        df_temp = df[df['ANO'].isin(ano_selecionado)] if ano_selecionado else df
        
        meses_disp = df_temp.sort_values('Ordem_Tempo')['MES_ANO_FILTRO'].unique().tolist()
        mes_selecionado = st.sidebar.multiselect("Mês/Ano", meses_disp, default=meses_disp)
        
        locais_disp = sorted(df['LOCAL'].dropna().unique().tolist())
        local_selecionado = st.sidebar.multiselect("Local", locais_disp, default=locais_disp)
        
        tipos_disp = sorted(df['TIPO DO PARTICIPANTE'].dropna().unique().tolist())
        tipo_selecionado = st.sidebar.multiselect("Tipo de Participante", tipos_disp, default=tipos_disp)
        
        df_filtrado = df[
            (df['ANO'].isin(ano_selecionado)) &
            (df['MES_ANO_FILTRO'].isin(mes_selecionado)) &
            (df['LOCAL'].isin(local_selecionado)) &
            (df['TIPO DO PARTICIPANTE'].isin(tipo_selecionado))
        ]
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()
            
        total_participantes = df_filtrado['QTD PARTICIPANTES'].sum()
        qtd_meses = df_filtrado['MES_ANO_FILTRO'].nunique()
        media_participantes_mes = total_participantes / qtd_meses if qtd_meses > 0 else 0
        
        df_mes = df_filtrado.groupby(['ANO', 'MÊS_NOME', 'Ordem_Tempo', 'MES_ANO_FILTRO'])['QTD PARTICIPANTES'].sum().reset_index()
        df_mes = df_mes.sort_values('Ordem_Tempo')
        
        df_setor = df_filtrado.groupby('Setor Participante')['QTD PARTICIPANTES'].sum().reset_index()
        df_setor = df_setor.sort_values('QTD PARTICIPANTES', ascending=False).head(15)
        
        df_ano_mes = df_filtrado.groupby(['ANO', 'MES_NUM', 'MÊS_NOME'])['QTD PARTICIPANTES'].sum().reset_index()
        df_ano_mes = df_ano_mes.sort_values(['MES_NUM'])
        df_ano_mes['ANO'] = df_ano_mes['ANO'].astype(str)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar_mes = go.Figure(data=[
                go.Bar(
                    x=[df_mes['ANO'], df_mes['MÊS_NOME']],
                    y=df_mes['QTD PARTICIPANTES'],
                    text=df_mes['QTD PARTICIPANTES'],
                    texttemplate='<b>%{text}</b>',
                    textposition='outside',
                    textfont=dict(size=14),
                    marker_color="#1f77b4"
                )
            ])
            fig_bar_mes.update_layout(title="TOTAL DE PARTICIPANTES POR MÊS", xaxis_tickfont=dict(weight='bold'), xaxis=dict(type='multicategory', title=""))
            st.plotly_chart(aplicar_estilo_grafico(fig_bar_mes), use_container_width=True)
            
            fig_comp = px.bar(df_ano_mes, x='MÊS_NOME', y='QTD PARTICIPANTES', color='ANO', barmode='group', title="COMPARATIVO: ANO VS ANO", color_discrete_sequence=['#8fd4f7', '#1f77b4'])
            fig_comp.update_traces(texttemplate='<b>%{y}</b>', textposition='outside')
            fig_comp.update_layout(legend_title_text='', xaxis_tickfont=dict(weight='bold'))
            st.plotly_chart(aplicar_estilo_grafico(fig_comp), use_container_width=True)

        with col2:
            fig_bar_setor = px.bar(df_setor, x='Setor Participante', y='QTD PARTICIPANTES', title="TOTAL POR SETOR PARTICIPANTE")
            fig_bar_setor.update_traces(texttemplate='<b>%{y}</b>', textposition='outside', textfont_size=14, marker_color="#ff7f0e")
            fig_bar_setor.update_layout(xaxis_tickangle=-45, xaxis_tickfont=dict(weight='bold'))
            st.plotly_chart(aplicar_estilo_grafico(fig_bar_setor), use_container_width=True)
            
            fig_media = go.Figure()
            fig_media.add_trace(go.Scatter(x=[df_mes['ANO'], df_mes['MÊS_NOME']], y=df_mes['QTD PARTICIPANTES'], mode='lines+markers+text', name='Qtd Mensal', text=df_mes['QTD PARTICIPANTES'], texttemplate='<b>%{text}</b>', textposition='top center', textfont=dict(size=14, color="#1f77b4"), line=dict(width=3, color="#1f77b4"), marker=dict(size=8)))
            fig_media.add_trace(go.Scatter(x=[df_mes['ANO'], df_mes['MÊS_NOME']], y=[media_participantes_mes]*len(df_mes), mode='lines', name='Média do Período', line=dict(dash='dash', color='#d62728', width=2), hoverinfo='skip'))
            fig_media.add_annotation(text=f"Média do Período: <b>{media_participantes_mes:.1f}</b>", xref="paper", yref="paper", x=1.0, y=1.05, showarrow=False, font=dict(size=13, color="#d62728"), bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="#d62728", borderwidth=1, borderpad=4)
            fig_media.update_layout(title="PARTICIPANTES VS MÉDIA DO PERÍODO", showlegend=False, xaxis_tickfont=dict(weight='bold'), xaxis=dict(type='multicategory', title=""))
            st.plotly_chart(aplicar_estilo_grafico(fig_media), use_container_width=True)

# ==========================================
# TELA 2: CADASTRO (Mantido 100% como o seu original)
# ==========================================
elif menu == "📝 Cadastro de Treinamento":
    st.title("📝 Painel de Cadastro")
    st.markdown("Preencha as informações abaixo para registrar um novo treinamento no sistema.")
    
    with st.container(border=True):
        st.subheader("Informações do Treinamento")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form(key="form_cadastro", clear_on_submit=True):
            nome_treinamento = st.text_input("Nome do Treinamento", placeholder="Ex: Boas práticas de segregação de resíduos...")
            
            st.markdown("---")
            st.markdown("##### Detalhes da Execução")
            col_a, col_b = st.columns(2)
            with col_a:
                data_treinamento = st.date_input("Data do Treinamento", format="DD/MM/YYYY")
                tipo_participante = st.selectbox("Tipo do Participante", 
                                                 ["Colaborador Interno", "Colaborador Externo", 
                                                  "Paciente/Acompanhante", "Extra Hospitalar"])
                qtd_participantes = st.number_input("Nº Participantes", min_value=1, step=1)
                
            with col_b:
                local = st.selectbox("Local de Realização", ["Hospital da Cidade", "Anexo", "Extra Hospitalar"])
                lista_de_setores = carregar_setores()
                setor_participante = st.selectbox("Setor Participante", lista_de_setores)
                
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="💾 Salvar Treinamento", use_container_width=True)
            
            if submit_button:
                if not nome_treinamento:
                    st.error("⚠️ O campo 'Nome do Treinamento' é obrigatório!")
                else:
                    novo_registro = {
                        'ANO': data_treinamento.year,
                        'DATA': pd.to_datetime(data_treinamento),
                        'NOME DO TREINAMENTO': nome_treinamento.strip(),
                        'LOCAL': local,
                        'TIPO DO PARTICIPANTE': tipo_participante,
                        'QTD PARTICIPANTES': qtd_participantes,
                        'Setor Participante': setor_participante
                    }
                    salvar_registro(novo_registro)
                    st.success(f"✅ Treinamento **{nome_treinamento}** cadastrado com sucesso na Nuvem!")

# ==========================================
# TELA 3: GESTÃO DE DADOS (Nova tela solicitada no áudio)
# ==========================================
elif menu == "⚙️ Gestão de Dados":
    st.title("⚙️ Gestão de Dados")
    st.markdown("Nesta tela, você pode visualizar todos os registros, **editar** informações clicando nas células ou **excluir** linhas selecionando-as no lado esquerdo.")
    
    df_raw = carregar_dados()
    
    if df_raw.empty:
        st.info("O banco de dados está vazio no momento.")
    else:
        # Puxa as colunas base para exibir na tabela de edição
        colunas_base = ['ID', 'ANO', 'DATA', 'NOME DO TREINAMENTO', 'LOCAL', 'TIPO DO PARTICIPANTE', 'QTD PARTICIPANTES', 'Setor Participante']
        df_base = df_raw[colunas_base].copy()
        
        # Editor interativo do Streamlit
        df_editado = st.data_editor(
            df_base,
            use_container_width=True,
            num_rows="dynamic", # Permite adicionar e deletar linhas
            hide_index=True,
            column_config={
                "DATA": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "ID": st.column_config.NumberColumn("ID", disabled=True)
            }
        )
        
        st.markdown("---")
        
        # Botão para enviar as alterações (edições/exclusões) para o Google Sheets
        if st.button("💾 Salvar Alterações na Nuvem", type="primary"):
            with st.spinner("Sincronizando com o Google Sheets..."):
                salvar_banco_completo(df_editado)
            st.success("✅ Banco de dados atualizado com sucesso!")
