import streamlit as st
import requests
import PyPDF2
import json
import pandas as pd
st.title("Caza Talentos: Encontrar al Candidato Ideal")
prompt = """Quiero los siguientes datos del siguiente currículum vitae:
            Nombre, Ciudad, País, Fecha de Nacimiento (en formato: 'Número' de 'Mes' del 'Año'),
            Carrera, Número de Teléfono, Correo y
            Entidad Donde Estudió (por ej: Universidad de O'Higgins).
            Todo esto en formato JSON. No agregues más campos/claves de las que te pedí, sé exacto."""
uploaded_files = st.file_uploader("Sube uno o más PDFs", type=["pdf"], accept_multiple_files=True)
if st.button("Procesar"):
    if uploaded_files and prompt:
        all_dfs = []
        for pdf_file in uploaded_files:
            pdf_text = read_file(pdf_file)
            df = process_pdf(pdf_text, prompt)
            all_dfs.append(df)
        if len(all_dfs) > 0:
            final_df = pd.concat(all_dfs, ignore_index=True)
            st.dataframe(final_df)
    else:
        st.warning("Por favor sube al menos un archivo PDF.")