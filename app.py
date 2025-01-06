import streamlit as st

def main():
    # Título principal
    st.title("Mi Interfaz Dummy")

    # Descripción o texto introductorio
    st.write("¡Bienvenido/a! Este es un ejemplo sencillo de una interfaz en Streamlit.")

    # Barra lateral
    st.sidebar.title("Menú Lateral")
    texto_usuario = st.sidebar.text_input("Ingresa un texto:", "")
    
    # Botón para mostrar el texto ingresado
    if st.sidebar.button("Mostrar Texto"):
        st.write("Texto ingresado:", texto_usuario)

    # Sección extra (opcional)
    st.markdown("---")
    st.subheader("Sección Extra")
    st.write("Aquí puedes agregar más componentes, como tablas, gráficos, etc.")

if __name__ == "__main__":
    main()
