import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# config inicial de la pagina
st.set_page_config(page_title="Lector CSV", layout="wide")
st.title("Lector de archivos CSV de osciloscopio", anchor=False)

## cargar datos en la barra lateral
uploaded_files = st.sidebar.file_uploader("Sube o arrastra tus archivos CSV", type=['csv'], accept_multiple_files=True)

if uploaded_files: # Si la lista de archivos no está vacía
    try:
        ## variables globales para manejar multiples archivos
        datos_procesados = []
        x_min_global = float('inf')
        x_max_global = float('-inf')
        nombres_archivos = []

        ## bucle robusto para leer todos los archivos
        for file in uploaded_files:
            df = pd.read_csv(file, sep=None, engine='python', encoding='latin1')
            df = df.apply(pd.to_numeric, errors='coerce')
            df = df.dropna().reset_index(drop=True)

            if not df.empty:
                col_x = df.columns[0]
                col_canales = df.columns[1:]
                
                # busca los limites absolutos de tiempo entre todos los archivos
                x_min_global = min(x_min_global, float(df[col_x].min()))
                x_max_global = max(x_max_global, float(df[col_x].max()))
                
                datos_procesados.append({
                    'nombre': file.name,
                    'df': df,
                    'col_x': col_x,
                    'canales': col_canales
                })
                nombres_archivos.append(file.name)

        if not datos_procesados:
            st.error("Error: Los archivos están vacíos o no contienen datos numéricos válidos.")
            st.stop()

        # logica de memoria para detectar nuevos archivos y ajustar la escala inicial
        cadena_nombres = ",".join(nombres_archivos)
        if "archivos_actuales" not in st.session_state or st.session_state.archivos_actuales != cadena_nombres:
            st.session_state.archivos_actuales = cadena_nombres
            st.session_state.inicial_x_min = x_min_global
            st.session_state.inicial_x_max = x_max_global

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
            titulo_eje_x = st.sidebar.text_input("Título del eje X", value=str(datos_procesados[0]['col_x']))
            unidad_x = st.sidebar.text_input("Unidad del eje X (Ej: s, ms, µs)", value="s")
            titulo_eje_y = st.sidebar.text_input("Título del eje Y", value="Voltaje (V)")
            
            show_grid = st.sidebar.checkbox("Mostrar grilla", value=True)
            log_x = st.sidebar.checkbox("Escala X logarítmica")
            log_y = st.sidebar.checkbox("Escala Y logarítmica")
            
            escala_x_mult = st.sidebar.number_input(
                "Multiplicador eje X (Ej: 1000000 para pasar a µs)", 
                value=1.0, format="%.1e"
            )

            st.sidebar.markdown("**Límites de pantalla (Eje X)**")
            col1, col2 = st.sidebar.columns(2)
            x_min = col1.number_input("Límite izquierdo", value=st.session_state.inicial_x_min)
            x_max = col2.number_input("Límite derecho", value=st.session_state.inicial_x_max)

        st.sidebar.subheader("Ajustes por canal")
        ajustes_canales = {}
        
        colores_default = ["#FF0000", "#0000FF", "#00FF00", "#FF9900", "#9900FF", "#00FFFF", "#FF00FF", "#000000"]
        color_idx = 0
        
        # lista unificada de todos los canales para el modo XY
        todos_los_canales = []

        # generacion de menus de ajuste agrupados por archivo
        for data in datos_procesados:
            st.sidebar.markdown(f"**📄 {data['nombre']}**")
            for canal in data['canales']:
                identificador_unico = f"{canal} ({data['nombre']})"
                todos_los_canales.append(identificador_unico)
                
                with st.sidebar.expander(f"Ajustes de {canal}"):
                    color_inicial = colores_default[color_idx % len(colores_default)]
                    color_idx += 1
                    
                    if not modo_xy:
                        color = st.color_picker(f"Color", value=color_inicial, key=f"c_{identificador_unico}")
                    else:
                        color = color_inicial
                    
                    escala = st.number_input(f"Amplitud", value=1.0, key=f"esc_{identificador_unico}")
                    offset = st.number_input(f"Desplazamiento Y", value=0.0, step=0.5, key=f"off_{identificador_unico}")
                    
                    if not modo_xy:
                        marcar = st.checkbox(f"Marcar máx/mín", key=f"m_{identificador_unico}")
                    else:
                        marcar = False
                    
                    ajustes_canales[identificador_unico] = {'color': color, 'escala': escala, 'offset': offset, 'marcar': marcar, 'df': data['df'], 'col_x': data['col_x'], 'canal_real': canal}

        ## grafica en la pantalla principal
        fig = go.Figure()

        if modo_xy:
            if len(todos_los_canales) < 2:
                st.warning("Se requieren al menos 2 canales cargados para el modo XY.")
            else:
                col1, col2 = st.columns(2)
                canal_x_xy = col1.selectbox("Eje X (Seleccionar Canal)", todos_los_canales, index=0)
                canal_y_xy = col2.selectbox("Eje Y (Seleccionar Canal)", todos_los_canales, index=1)
                
                ajuste_x = ajustes_canales[canal_x_xy]
                ajuste_y = ajustes_canales[canal_y_xy]
                
                data_x = (ajuste_x['df'][ajuste_x['canal_real']] * ajuste_x['escala']) + ajuste_x['offset']
                data_y = (ajuste_y['df'][ajuste_y['canal_real']] * ajuste_y['escala']) + ajuste_y['offset']
                
                # Sincronizar el tamaño por si un archivo tiene más puntos que otro
                min_len = min(len(data_x), len(data_y))
                
                fig.add_trace(go.Scatter(x=data_x[:min_len], y=data_y[:min_len], mode='lines', name='X-Y'))
                
                fig.update_layout(
                    xaxis_title=canal_x_xy, 
                    yaxis_title=canal_y_xy,
                    xaxis_showgrid=show_grid,
                    yaxis_showgrid=show_grid
                )

        else:
            for id_canal, ajuste in ajustes_canales.items():
                x_data = ajuste['df'][ajuste['col_x']] * escala_x_mult
                y_data = (ajuste['df'][ajuste['canal_real']] * ajuste['escala']) + ajuste['offset']
                
                fig.add_trace(go.Scatter(
                    x=x_data, y=y_data, mode='lines', 
                    name=id_canal, line=dict(color=ajuste['color'])
                ))
                
                if ajuste['marcar']:
                    idx_max = y_data.idxmax()
                    idx_min = y_data.idxmin()
                    fig.add_trace(go.Scatter(
                        x=[x_data[idx_max]], y=[y_data[idx_max]], 
                        mode='markers', marker=dict(size=12, symbol='triangle-up', color='green'), 
                        name=f'Máx {id_canal}'
                    ))
                    fig.add_trace(go.Scatter(
                        x=[x_data[idx_min]], y=[y_data[idx_min]], 
                        mode='markers', marker=dict(size=12, symbol='triangle-down', color='red'), 
                        name=f'Mín {id_canal}'
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
        st.error(f"Se produjo un error al leer los archivos. Detalle: {e}")
else:
    st.info("Sube uno o múltiples archivos CSV del osciloscopio en la barra lateral izquierda para generar la gráfica.")