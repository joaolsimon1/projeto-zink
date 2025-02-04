import streamlit as st
import pandas as pd
import plotly.express as px
from function import process_excel

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="App Zink",  # Título da página
    page_icon="⚛️"  # Ícone da página (opcional)
)

# Título da aplicação
st.title("Processamento de Dados")

# Sidebar para upload de arquivo
with st.sidebar:
    st.header("Envio de Arquivo")
    uploaded_file = st.file_uploader("Envie o arquivo Excel ou CSV", type=['xlsx', 'csv', 'txt'])

# Verifica se há um arquivo carregado ou se os dados já estão no session_state
if uploaded_file:
    # Se um novo arquivo foi carregado, processa os dados
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=";", header=None)
        elif uploaded_file.name.endswith('.txt'):
            df = pd.read_csv(uploaded_file, sep="\t", header=None)  # Usar \t para separador de tabulação

        # Armazena o arquivo carregado no session_state
        st.session_state['uploaded_file'] = uploaded_file
        st.session_state['df'] = df

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")

    with st.sidebar:
        if st.button("Iniciar Processamento"):
            # Processa os dados e armazena no session_state
            df_abs, df_des, merged_data = process_excel(df)
            st.session_state['df_abs'] = df_abs
            st.session_state['df_des'] = df_des
            st.session_state['merged_data'] = merged_data
            st.success("Processamento concluído!")

elif 'df_abs' in st.session_state:
    # Se os dados já estão no session_state, exibe uma mensagem informativa
    st.info("Dados já carregados e processados.")

else:
    # Se nenhum arquivo foi carregado e não há dados no session_state, exibe uma mensagem
    st.info("Envie um arquivo padronizado pela barra lateral para começar.")

# Se os dados processados estão no session_state, exibe as opções e gráficos
if 'df_abs' in st.session_state and 'df_des' in st.session_state:
    container = st.container()
    all = st.checkbox("Selecionar todos os ciclos")

    if all:
        selected_options = container.multiselect(
            "Selecione um ou mais ciclos:",
            st.session_state['df_abs']['NUMERO_CICLO'].unique(),
            st.session_state['df_abs']['NUMERO_CICLO'].unique()
        )
    else:
        selected_options = container.multiselect(
            "Selecione um ou mais ciclos:",
            st.session_state['df_abs']['NUMERO_CICLO'].unique()
        )

    if selected_options:
        col1, col2 = st.columns(2)

        with col1:
            df1_filtrado = st.session_state['df_abs']
            df1_filtrado = df1_filtrado[df1_filtrado['NUMERO_CICLO'].isin(selected_options)]
            resultados = []
            df1_filtrado = df1_filtrado.set_index('DATAHORA')
            for i in range(int(df1_filtrado['NUMERO_CICLO'].max()) + 1):
                aux1 = df1_filtrado.loc[df1_filtrado['NUMERO_CICLO'] == i]
                aux1 = aux1['AcumuladoABS'].resample('T').mean().reset_index()
                aux1.columns = ['DATAHORA', 'AcumuladoABS']
                aux1 = aux1.loc[pd.notna(aux1['AcumuladoABS'])].reset_index(drop=True)
                aux1['Tempo'] = aux1.index
                aux1['NUMERO_CICLO'] = i
                resultados.append(aux1)
            df_todos_ciclos = pd.concat(resultados).reset_index(drop=True)

            df_pivot = df_todos_ciclos.pivot(index='Tempo', columns='NUMERO_CICLO', values='AcumuladoABS')
            df_pivot.columns = [f"Acum ABS C{n}" for n in df_pivot.columns]
            df_pivot = df_pivot.reset_index().rename(columns={'Tempo': 'Tempo'})
            df_pivot = df_pivot.round(3)
            df_pivot = df_pivot.applymap(lambda x: str(x).replace('.', ',') if isinstance(x, (int, float)) else x)

            fig = px.line(
                df_todos_ciclos,
                x='Tempo',
                y='AcumuladoABS',
                color='NUMERO_CICLO',
                title='Absorção'
            )
            fig.update_layout(xaxis_title="Tempo (Minutos)", yaxis_title="CO₂ absorvido acumulado (mg)", title_x=0.5, legend_title_text="Ciclos")
            st.plotly_chart(fig, use_container_width=True)
            st.write("Dataframe utilizado no gráfico de Absorção:")
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)

            st.download_button(
                label="Baixar dados de Absorção como .txt",
                data=df_todos_ciclos.to_csv(index=False, sep="\t"),
                file_name='dados_absorcao.txt',
                mime='text/plain'
            )

        with col2:
            df2_filtrado = st.session_state['df_des']
            df2_filtrado = df2_filtrado[df2_filtrado['NUMERO_CICLO'].isin(selected_options)]
            resultados = []
            df2_filtrado = df2_filtrado.set_index('DATAHORA')
            for i in range(int(df2_filtrado['NUMERO_CICLO'].max()) + 1):
                aux2 = df2_filtrado.loc[df2_filtrado['NUMERO_CICLO'] == i]
                aux2 = aux2['AcumuladoDES'].resample('T').mean().reset_index()
                aux2.columns = ['DATAHORA', 'AcumuladoDES']
                aux2 = aux2.loc[pd.notna(aux2['AcumuladoDES'])].reset_index(drop=True)
                aux2['Tempo'] = aux2.index
                aux2['NUMERO_CICLO'] = i
                resultados.append(aux2)
            df_todos_ciclos2 = pd.concat(resultados).reset_index(drop=True)

            df_pivot2 = df_todos_ciclos2.pivot(index='Tempo', columns='NUMERO_CICLO', values='AcumuladoDES')
            df_pivot2.columns = [f"Acum DES C{n}" for n in df_pivot2.columns]
            df_pivot2 = df_pivot2.reset_index().rename(columns={'Tempo': 'Tempo'})
            df_pivot2 = df_pivot2.round(3)
            df_pivot2 = df_pivot2.applymap(lambda x: str(x).replace('.', ',') if isinstance(x, (int, float)) else x)

            fig2 = px.line(
                df_todos_ciclos2,
                x='Tempo',
                y='AcumuladoDES',
                color='NUMERO_CICLO',
                title='Dessorção'
            )
            fig2.update_layout(xaxis_title="Tempo (Minutos)", yaxis_title="CO₂ dessorvido acumulado (mg)", title_x=0.5, legend_title_text="Ciclos")
            st.plotly_chart(fig2, use_container_width=True)
            st.write("Dataframe utilizado no gráfico de Dessorção:")
            st.dataframe(df_pivot2, use_container_width=True, hide_index=True)

            st.download_button(
                label="Baixar dados de Dessorção como .txt",
                data=df_todos_ciclos2.to_csv(index=False, sep="\t"),
                file_name='dados_dessorcao.txt',
                mime='text/plain'
            )