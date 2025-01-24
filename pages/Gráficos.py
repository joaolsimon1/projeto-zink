import streamlit as st

# Exibir tabelas se o processamento foi concluído
if 'df_abs' in st.session_state:
    st.subheader("4 - Absorção")
    st.dataframe(st.session_state['df_abs'])

    st.subheader("6 - Dessorção Corrigida")
    st.dataframe(st.session_state['df_des'])

    st.subheader("Tabela Final")
    st.dataframe(st.session_state['merged_data'])