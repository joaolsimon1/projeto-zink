import streamlit as st
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt


if 'resultado' not in st.session_state:
    st.session_state['resultado'] = None


# Função para processar o arquivo Excel
def process_excel(df):
    df.columns = ['DATAHORA', 'MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']
    
    df['DATAHORA'] = pd.to_datetime(df['DATAHORA'])
    # Converter as colunas 1:4 para float
    df[['MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV','ETAPA_ATUAL', 'NUMERO_CICLO']] = df[['MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']].apply(pd.to_numeric, errors='coerce')


    # Fator de Correção
    df_etapa_1 = df[df['ETAPA_ATUAL'] == 1]
    df_etapa_1 = df_etapa_1[(df_etapa_1['BT_PV'] > 39.7) & (df_etapa_1['BT_PV'] < 40.2)]
    df_etapa_1 = df_etapa_1.sort_values(by=['NUMERO_CICLO', 'DATAHORA'])
    df_etapa_1 = df_etapa_1.groupby('NUMERO_CICLO').tail(150)
    
    media = df_etapa_1.groupby('NUMERO_CICLO').agg(
        media_c3=('MFC05_PV', 'mean'),
        media_c2=('MFC02_PV', 'mean')
    ).reset_index()

    media['erro_p'] = (media['media_c3'] - media['media_c2']) / media['media_c3'] * 100
    media['fator'] = (-media['erro_p'] / 100) + 1

    df = df.merge(media[['NUMERO_CICLO', 'erro_p', 'fator']], on='NUMERO_CICLO', how='left')

    # Absorção
    df_abs = df[df['ETAPA_ATUAL'] == 4]
    df_abs['MFC05_corrigido'] = df_abs['MFC05_PV'] * df_abs['fator']
    df_abs['DiffABS'] = df_abs['MFC02_PV'] - df_abs['MFC05_corrigido']
    df_abs['Diff_corrigidaABS'] = df_abs['DiffABS'] * 5 / 60
    df_abs.loc[df_abs['PC02_PV'] <= 3.485, 'Diff_corrigidaABS'] = 0
    df_abs['AcumuladoABS'] = df_abs.groupby('NUMERO_CICLO')['Diff_corrigidaABS'].cumsum()
    df_abs['MaxAcumuladoABS'] = df_abs.groupby('NUMERO_CICLO')['AcumuladoABS'].transform('max')

    # Dessorção
    df_des = df[df['ETAPA_ATUAL'] == 6]
    df_des['DiffDES'] = df_des['MFC02_PV'] - df_des['MFC05_PV']
    df_des['Diff_corrigidaDES'] = df_des['DiffDES'] * 5 / 60
    df_des['AcumuladoDES'] = df_des.groupby('NUMERO_CICLO')['Diff_corrigidaDES'].cumsum()
    df_des['MinAcumuladoDES'] = df_des.groupby('NUMERO_CICLO')['AcumuladoDES'].transform('min')

    # Resultado Final
    des_aggregated = df_des.groupby('NUMERO_CICLO').agg(
        MinAcumuladoDES=('AcumuladoDES', 'min')
    ).reset_index()

    abs_aggregated = df_abs.groupby('NUMERO_CICLO').agg(
        MaxAcumuladoABS=('AcumuladoABS', 'max')
    ).reset_index()

    merged_data = pd.merge(des_aggregated, abs_aggregated, on='NUMERO_CICLO')

    # Retornar os resultados
    return df_abs, df_des, merged_data


# Configuração da interface do Streamlit
st.title("Processamento de Dados")

# Sidebar para seleção e upload de arquivo
with st.sidebar:
    st.header("Navegação")
    selected_tab = st.radio("Escolha uma opção:", ["Gráficos", "Tabelas"])
    uploaded_file = st.file_uploader("Envie o arquivo Excel ou CSV", type=['xlsx', 'csv'])

    

if uploaded_file:

    if uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file,  sep=";", header=None)

    df_abs, df_des, merged_data = process_excel(df)

    st.session_state['resultado'] = merged_data
    
    if selected_tab == "Gráficos":
        st.subheader("Visualização de Gráficos")
        
        # Exemplo de gráfico
        fig, ax = plt.subplots()
        ax.plot(df_abs['NUMERO_CICLO'], df_abs['MaxAcumuladoABS'], label='Max Acumulado ABS')
        ax.set_xlabel("Número do Ciclo")
        ax.set_ylabel("Máximo Acumulado ABS")
        ax.set_title("Máximo Acumulado ABS por Ciclo")
        ax.legend()
        st.pyplot(fig)

    elif selected_tab == "Tabelas":
        tab1, tab2, tab3 = st.tabs(["Absorção", "Dessorção Corrigida", "Tabela Final"])
        
        with tab1:
            st.subheader("4 - Absorção")
            st.dataframe(df_abs)
        with tab2:
            st.subheader("6 - Dessorção Corrigida")
            st.dataframe(df_des)
        with tab3:
            st.subheader("Tabela Final")
            st.dataframe(merged_data)

else:
    st.info("Envie um arquivo Excel pela barra lateral para começar.")
    
if st.session_state['resultado'] != None:   
    # Botão de download na sidebar
    with st.sidebar:
        with pd.ExcelWriter('Resultados_Industriais.xlsx') as writer:
            df_abs.to_excel(writer, sheet_name='4_Absorção', index=False)
            df_des.to_excel(writer, sheet_name='6_Dessorção Corrigida', index=False)
            merged_data.to_excel(writer, sheet_name='Tabela Final', index=False)

        with open('Resultados_Industriais.xlsx', 'rb') as file:
            st.download_button(
                label="Baixar Resultados",
                data=file,
                file_name=f'Resultados_Industriais_{dt.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
