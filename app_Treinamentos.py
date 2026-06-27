import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CAMINHOS
# ==========================================
st.set_page_config(page_title="Dashboard de Treinamentos", layout="wide", initial_sidebar_state="expanded")

DIRETORIO = r"C:\Users\hamilton.pires\OneDrive - Grupo Mateus\hamilton\Consultoria\Lidiane\2026\app_Treinamentos"
ARQUIVO_BASE = os.path.join(DIRETORIO, 'BD_Treinamentos.xlsx')
ARQUIVO_SETORES = os.path.join(DIRETORIO, 'lista_setores.xlsx')

# Dicionários de tradução
MESES_PT = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

# ==========================================
# FUNÇÕES DE CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data
def carregar_dados():
    if os.path.exists(ARQUIVO_BASE):
        df = pd.read_excel(ARQUIVO_BASE)
        df['DATA'] = pd.to_datetime(df['DATA'])
        
        df['ANO'] = df['DATA'].dt.year
        df['MES_NUM'] = df['DATA'].dt.month
        
        # Limpeza para evitar filtros duplicados (remove espaços e padroniza caixa)
        df['TIPO DO PARTICIPANTE'] = df['TIPO DO PARTICIPANTE'].astype(str).str.strip().str.title()
        df['LOCAL'] = df['LOCAL'].astype(str).str.strip()
        df['Setor Participante'] = df['Setor Participante'].astype(str).str.strip()
        
        # Cria as colunas para o filtro de mês em PT
        df['MÊS_NOME'] = df['MES_NUM'].map(MESES_PT)
        df['MES_ANO_FILTRO'] = df['MÊS_NOME'] + "." + df['ANO'].astype(str).str[-2:]
        
        df['Ordem_Tempo'] = df['ANO'].astype(str) + df['MES_NUM'].astype(str).str.zfill(2)
        
        return df
    else:
        colunas = ['ID', 'ANO', 'DATA', 'NOME DO TREINAMENTO', 'LOCAL', 
                   'TIPO DO PARTICIPANTE', 'QTD PARTICIPANTES', 'Setor Participante']
        return pd.DataFrame(columns=colunas)

def carregar_setores():
    if os.path.exists(ARQUIVO_SETORES):
        df_setores = pd.read_excel(ARQUIVO_SETORES)
        return df_setores['Setor'].dropna().tolist()
    return ["SALA DE CGRSS", "ALA A", "ALA B", "ALA C", "OUTROS"] 

def salvar_registro(novo_registro):
    df_atual = carregar_dados()
    novo_id = 1 if df_atual.empty else df_atual['ID'].max() + 1
    novo_registro['ID'] = novo_id
    
    df_novo = pd.DataFrame([novo_registro])
    df_final = pd.concat([df_atual, df_novo], ignore_index=True)
    
    colunas_para_salvar = ['ID', 'ANO', 'DATA', 'NOME DO TREINAMENTO', 'LOCAL', 
                           'TIPO DO PARTICIPANTE', 'QTD PARTICIPANTES', 'Setor Participante']
    df_final[colunas_para_salvar].to_excel(ARQUIVO_BASE, index=False)
    st.cache_data.clear()

# ==========================================
# FUNÇÃO DE ESTILIZAÇÃO DOS GRÁFICOS (Tema ViaFluxo)
# ==========================================
def aplicar_estilo_grafico(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=12, color="#333"),
        title_font=dict(size=16, color="#1f77b4", family="Arial Black"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        # Remover as linhas de fundo do gráfico
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
    menu = st.radio("", ["📊 Dashboard Analítico", "📝 Cadastro de Treinamento"])
    st.markdown("---")

# ==========================================
# TELA DE DASHBOARD
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
        
        # Filtro de Mês no formato Jan.25, Fev.25...
        meses_disp = df_temp.sort_values('Ordem_Tempo')['MES_ANO_FILTRO'].unique().tolist()
        mes_selecionado = st.sidebar.multiselect("Mês/Ano", meses_disp, default=meses_disp)
        
        locais_disp = sorted(df['LOCAL'].dropna().unique().tolist())
        local_selecionado = st.sidebar.multiselect("Local", locais_disp, default=locais_disp)
        
        tipos_disp = sorted(df['TIPO DO PARTICIPANTE'].dropna().unique().tolist())
        tipo_selecionado = st.sidebar.multiselect("Tipo de Participante", tipos_disp, default=tipos_disp)
        
        # --- APLICAÇÃO DOS FILTROS ---
        df_filtrado = df[
            (df['ANO'].isin(ano_selecionado)) &
            (df['MES_ANO_FILTRO'].isin(mes_selecionado)) &
            (df['LOCAL'].isin(local_selecionado)) &
            (df['TIPO DO PARTICIPANTE'].isin(tipo_selecionado))
        ]
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()
            
        # --- PREPARAÇÃO DE DADOS ---
        total_participantes = df_filtrado['QTD PARTICIPANTES'].sum()
        qtd_meses = df_filtrado['MES_ANO_FILTRO'].nunique()
        media_participantes_mes = total_participantes / qtd_meses if qtd_meses > 0 else 0
        
        df_mes = df_filtrado.groupby(['ANO', 'MÊS_NOME', 'Ordem_Tempo', 'MES_ANO_FILTRO'])['QTD PARTICIPANTES'].sum().reset_index()
        df_mes = df_mes.sort_values('Ordem_Tempo')
        
        df_setor = df_filtrado.groupby('Setor Participante')['QTD PARTICIPANTES'].sum().reset_index()
        df_setor = df_setor.sort_values('QTD PARTICIPANTES', ascending=False).head(15)
        
        # Dados para comparação Ano vs Ano
        df_ano_mes = df_filtrado.groupby(['ANO', 'MES_NUM', 'MÊS_NOME'])['QTD PARTICIPANTES'].sum().reset_index()
        df_ano_mes = df_ano_mes.sort_values(['MES_NUM'])
        df_ano_mes['ANO'] = df_ano_mes['ANO'].astype(str)

        
        # --- LAYOUT DOS GRÁFICOS ---
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. Gráfico de Barras: Total por Mês/Ano (Com divisão de Ano)
            fig_bar_mes = go.Figure(data=[
                go.Bar(
                    x=[df_mes['ANO'], df_mes['MÊS_NOME']], # Multicategoria: Ano embaixo, Mês em cima
                    y=df_mes['QTD PARTICIPANTES'],
                    text=df_mes['QTD PARTICIPANTES'],
                    texttemplate='<b>%{text}</b>',
                    textposition='outside',
                    textfont=dict(size=14),
                    marker_color="#1f77b4"
                )
            ])
            fig_bar_mes.update_layout(
                title="TOTAL DE PARTICIPANTES POR MÊS",
                xaxis_tickfont=dict(weight='bold'), # Mês em negrito
                xaxis=dict(type='multicategory', title="") # Força a divisão visual dos anos
            )
            fig_bar_mes = aplicar_estilo_grafico(fig_bar_mes)
            st.plotly_chart(fig_bar_mes, use_container_width=True)
            
            # 2. Gráfico Comparativo: Ano vs Ano (Cores invertidas e negrito)
            fig_comp = px.bar(df_ano_mes, x='MÊS_NOME', y='QTD PARTICIPANTES', color='ANO', barmode='group',
                              title="COMPARATIVO: ANO VS ANO",
                              color_discrete_sequence=['#8fd4f7', '#1f77b4'])
            fig_comp.update_traces(texttemplate='<b>%{y}</b>', textposition='outside')
            fig_comp = aplicar_estilo_grafico(fig_comp)
            fig_comp.update_layout(
                legend_title_text='',
                xaxis_tickfont=dict(weight='bold')
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        with col2:
            # 3. Gráfico de Barras por Setor (Eixo em negrito)
            fig_bar_setor = px.bar(df_setor, x='Setor Participante', y='QTD PARTICIPANTES', 
                                   title="TOTAL POR SETOR PARTICIPANTE")
            fig_bar_setor.update_traces(texttemplate='<b>%{y}</b>', textposition='outside', textfont_size=14, marker_color="#ff7f0e")
            fig_bar_setor = aplicar_estilo_grafico(fig_bar_setor)
            fig_bar_setor.update_layout(
                xaxis_tickangle=-45,
                xaxis_tickfont=dict(weight='bold')
            ) 
            st.plotly_chart(fig_bar_setor, use_container_width=True)
            
            # 4. Gráfico com a Média (Com divisão de Ano)
            fig_media = go.Figure()
            # Linha principal
            fig_media.add_trace(go.Scatter(
                x=[df_mes['ANO'], df_mes['MÊS_NOME']], # Multicategoria
                y=df_mes['QTD PARTICIPANTES'], 
                mode='lines+markers+text', name='Qtd Mensal',
                text=df_mes['QTD PARTICIPANTES'],
                texttemplate='<b>%{text}</b>',
                textposition='top center',
                textfont=dict(size=14, color="#1f77b4"),
                line=dict(width=3, color="#1f77b4"),
                marker=dict(size=8)
            ))
            # Linha da média tracejada SEM rótulos
            fig_media.add_trace(go.Scatter(
                x=[df_mes['ANO'], df_mes['MÊS_NOME']], # Multicategoria
                y=[media_participantes_mes]*len(df_mes), 
                mode='lines', name='Média do Período',
                line=dict(dash='dash', color='#d62728', width=2),
                hoverinfo='skip'
            ))
            
            # Caixinha com a média no topo
            fig_media.add_annotation(
                text=f"Média do Período: <b>{media_participantes_mes:.1f}</b>",
                xref="paper", yref="paper",
                x=1.0, y=1.05,
                showarrow=False,
                font=dict(size=13, color="#d62728"),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="#d62728",
                borderwidth=1,
                borderpad=4
            )

            fig_media.update_layout(
                title="PARTICIPANTES VS MÉDIA DO PERÍODO", 
                showlegend=False,
                xaxis_tickfont=dict(weight='bold'), # Mês em negrito
                xaxis=dict(type='multicategory', title="") # Força a divisão visual dos anos
            )
            fig_media = aplicar_estilo_grafico(fig_media)
            st.plotly_chart(fig_media, use_container_width=True)

# ==========================================
# TELA DE CADASTRO
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
                        'DATA': data_treinamento,
                        'NOME DO TREINAMENTO': nome_treinamento.strip(),
                        'LOCAL': local,
                        'TIPO DO PARTICIPANTE': tipo_participante,
                        'QTD PARTICIPANTES': qtd_participantes,
                        'Setor Participante': setor_participante
                    }
                    salvar_registro(novo_registro)
                    st.success(f"✅ Treinamento **{nome_treinamento}** cadastrado com sucesso!")