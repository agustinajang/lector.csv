import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# config inicial de la pagina
st.set_page_config(page_title="Lector CSV", layout="wide")
st.title("Lector de archivos CSV de osciloscopio", anchor=False)

## cargar datos en la barra lateral
uploaded_file = st.sidebar.file_uploader("Sube o arrastra tu archivo CSV", type=['csv'])

if uploaded_file is not None:
    try:
        ## codigo robusto
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df = df.apply(pd.to_numeric, errors='coerce')
        df = df.dropna().reset_index(drop=True)

        if df.empty:
            st.error("Error: El archivo está vacío o no contiene datos numéricos válidos.")
            st.stop()

        col_x = df.columns[0]
        col_canales = df.columns[1:]

        # logica de memoria para detectar archivo nuevo y ajustar la escala inicial
        if "archivo_actual" not in st.session_state or st.session_state.archivo_actual != uploaded_file.name:
            st.session_state.archivo_actual = uploaded_file.name
            st.session_state.inicial_x_min = float(df[col_x].min())
            st.session_state.inicial_x_max = float(df[col_x].max())

        ## barra lateral
        st.sidebar.markdown("---")
        st.sidebar.header("Panel de Control")
        
        modo_xy = st.sidebar.checkbox("Activar MODO XY (Lissajous)")

        # logica condicional de titulos y herramientas acordes al modo elegido
        if modo_xy:
            st.sidebar.subheader("Títulos y ajustes")
            titulo_grafico = st.sidebar.text_input("Título del gráfico", value="Figura de Lissajous")
            show_grid = st.sidebar.checkbox("Mostrar grilla", value=True)
            escala_x_mult = 1.0
            log_x = False
            log_y = False
        else:
            st.sidebar.subheader("Títulos y ejes globales")
            titulo_grafico = st.sidebar.text_input("Título del gráfico", value="Gráfica temporal (YT)")
            titulo_eje_x = st.sidebar.text_input("Título del eje X", value=str(col_x))
            unidad_x = st.sidebar.text_input("Unidad del eje X (Ej: s, ms, µs)", value="s")
            titulo_eje_y = st.sidebar.text_input("Título del eje Y", value="Voltaje (V)")
            
            show_grid = st.sidebar.checkbox("Mostrar grilla", value=True)
            log_x = st.sidebar.checkbox("Escala X logarítmica")
            log_y = st.sidebar.checkbox("Escala Y logarítmica")
            
            escala_x_mult = st.sidebar.number_input(
                "Multiplicador eje X (Ej: 1000000 para pasar a µs)", 
                value=1.0, format="%.1e"
            )

            # los valores por defecto se adaptan al tamaño real del CSV automáticamente
            st.sidebar.markdown("**Límites de pantalla (Eje X)**")
            col1, col2 = st.sidebar.columns(2)
            x_min = col1.number_input("Límite izquierdo", value=st.session_state.inicial_x_min)
            x_max = col2.number_input("Límite derecho", value=st.session_state.inicial_x_max)

        st.sidebar.subheader("Ajustes por canal")
        ajustes_canales = {}
        
        colores_default = ["#FF0000", "#0000FF", "#00FF00", "#FF9900", "#9900FF", "#00FFFF"]
        
        for i, canal in enumerate(col_canales):
            with st.sidebar.expander(f"Ajustes de {canal}"):
                color_inicial = colores_default[i % len(colores_default)]
                
                if not modo_xy:
                    color = st.color_picker(f"Color de {canal}", value=color_inicial, key=f"c_{canal}")
                else:
                    color = color_inicial
                
                escala = st.number_input(f"Amplitud {canal}", value=1.0, key=f"esc_{canal}")
                offset = st.number_input(f"Desplazamiento Y {canal}", value=0.0, step=0.5, key=f"off_{canal}")
                
                if not modo_xy:
                    marcar = st.checkbox(f"Marcar máx/mín {canal}", key=f"m_{canal}")
                else:
                    marcar = False
                
                ajustes_canales[canal] = {'color': color, 'escala': escala, 'offset': offset, 'marcar': marcar}

        ## grafica en la pantalla principal
        fig = go.Figure()

        if modo_xy:
            if len(col_canales) < 2:
                st.warning("Se requieren al menos 2 canales de datos para el modo XY.")
            else:
                col1, col2 = st.columns(2)
                canal_x_xy = col1.selectbox("Eje X (Canal)", col_canales, index=0)
                canal_y_xy = col2.selectbox("Eje Y (Canal)", col_canales, index=1)
                
                data_x = (df[canal_x_xy] * ajustes_canales[canal_x_xy]['escala']) + ajustes_canales[canal_x_xy]['offset']
                data_y = (df[canal_y_xy] * ajustes_canales[canal_y_xy]['escala']) + ajustes_canales[canal_y_xy]['offset']
                
                fig.add_trace(go.Scatter(x=data_x, y=data_y, mode='lines', name='X-Y'))
                
                fig.update_layout(
                    xaxis_title=f"{canal_x_xy}", 
                    yaxis_title=f"{canal_y_xy}",
                    xaxis_showgrid=show_grid,
                    yaxis_showgrid=show_grid
                )

        else:
            x_data = df[col_x] * escala_x_mult
            
            for canal in col_canales:
                ajuste = ajustes_canales[canal]
                y_data = (df[canal] * ajuste['escala']) + ajuste['offset']
                
                fig.add_trace(go.Scatter(
                    x=x_data, y=y_data, mode='lines', 
                    name=canal, line=dict(color=ajuste['color'])
                ))
                
                if ajuste['marcar']:
                    idx_max = y_data.idxmax()
                    idx_min = y_data.idxmin()
                    fig.add_trace(go.Scatter(
                        x=[x_data[idx_max]], y=[y_data[idx_max]], 
                        mode='markers', marker=dict(size=12, symbol='triangle-up', color='green'), 
                        name=f'Máx {canal}'
                    ))
                    fig.add_trace(go.Scatter(
                        x=[x_data[idx_min]], y=[y_data[idx_min]], 
                        mode='markers', marker=dict(size=12, symbol='triangle-down', color='red'), 
                        name=f'Mín {canal}'
                    ))

            texto_eje_x = f"{titulo_eje_x} ({unidad_x})" if unidad_x else titulo_eje_x

            fig.update_layout(
                xaxis_title=texto_eje_x,
                yaxis_title=titulo_eje_y,
                xaxis_type="log" if log_x else "linear",
                yaxis_type="log" if log_y else "linear",
                xaxis_showgrid=show_grid,
                yaxis_showgrid=show_grid,
                hovermode="x unified",
                hoverlabel=dict(bgcolor="white", font_color="black", font_size=14, font_family="Rockwell")
            )
            fig.update_xaxes(showspikes=True, spikecolor="gray", spikesnap="cursor", spikemode="across")
            fig.update_yaxes(showspikes=True, spikecolor="gray", spikethickness=1)
            
            # aplicacion del rango fijo
            fig.update_xaxes(range=[x_min, x_max], autorange=False)

        # titulo del grafico
        fig.update_layout(
            title=dict(
                text=titulo_grafico,
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            )
        )

        # grafico a lo ancho de toda la pantalla
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"El archivo ingresado no tiene un formato soportado. Detalle: {e}")
else:
    st.info("Subir el archivo CSV del osciloscopio en la barra lateral izquierda para generar la gráfica.")