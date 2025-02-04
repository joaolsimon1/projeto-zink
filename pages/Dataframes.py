import streamlit as st



if 'df_abs' in st.session_state:
    st.markdown('As tabelas podem ser baixadas individualmente no ícone no canto superior direito de cada uma delas.')

tab1, tab2, tab3 = st.tabs(["Absorção", "Dessorção Corrigida", "Tabela Final"])

# Exibir tabelas se o processamento foi concluído
if 'df_abs' in st.session_state:
    with tab1:
        st.subheader("4 - Absorção")
        st.dataframe(st.session_state['df_abs'], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("6 - Dessorção Corrigida")
        st.dataframe(st.session_state['df_des'], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Tabela Final")
        st.dataframe(st.session_state['merged_data'], use_container_width=True, hide_index=True)