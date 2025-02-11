import streamlit as st
import pandas as pd
import datetime as dt
import io

@st.cache_data
def process_excel(df):
    df.columns = ['DATAHORA', 'MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']
    df['DATAHORA'] = pd.to_datetime(df['DATAHORA'])
    df[['MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']] = (df[['MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']]
    .replace(',', '.', regex=True)  # Substitui vírgulas por pontos
)
    cols_to_convert = ['MFC02_PV', 'MFC05_PV', 'PC02_PV', 'BT_PV', 'ETAPA_ATUAL', 'NUMERO_CICLO']
    df[cols_to_convert] = df[cols_to_convert].astype(float, errors='ignore')

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
    media['fator'] = 1 - (media['erro_p'] / 100)

    df = df.merge(media[['NUMERO_CICLO', 'erro_p', 'fator']], on='NUMERO_CICLO', how='left')

    # Absorção
    df_abs = df[df['ETAPA_ATUAL'] == 4].copy()
    df_abs['MFC05_corrigido'] = df_abs['MFC05_PV'] * df_abs['fator']
    df_abs['DiffABS'] = df_abs['MFC02_PV'] - df_abs['MFC05_corrigido']
    df_abs['Diff_corrigidaABS'] = (df_abs['DiffABS'] * 5 / 60).where(df_abs['PC02_PV'] > 3.485, 0)
    df_abs['AcumuladoABS'] = df_abs.groupby('NUMERO_CICLO')['Diff_corrigidaABS'].cumsum()
    df_abs['MaxAcumuladoABS'] = df_abs.groupby('NUMERO_CICLO')['AcumuladoABS'].transform('max')
    

    # Dessorção
    df_des = df[df['ETAPA_ATUAL'] == 6].copy()
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
    merged_data.loc[merged_data['MaxAcumuladoABS'].isnull(), 'MaxAcumuladoABS'] = 1

    return df_abs, df_des, merged_data