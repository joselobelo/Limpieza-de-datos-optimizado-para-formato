import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Generador de Bases para APPP",
    page_icon="📲",
    layout="wide"
)

# --- Funciones de Extracción y Formateo ---
def format_for_app(df, search_cols, name_col):
    """
    Extrae contactos y nombres, y los formatea en la estructura final.
    """
    final_records = []

    email_regex = re.compile(r'[\w\.\-]+@[\w\.\-]+')
    phone_regex = re.compile(r'\b(3\d{9})\b')

    for index, row in df.iterrows():
        # Extraer el primer teléfono válido encontrado en las columnas de búsqueda
        found_phone = None
        for col in search_cols:
            phones_in_cell = phone_regex.findall(str(row[col]))
            if phones_in_cell:
                found_phone = phones_in_cell[0]
                break # Nos quedamos con el primero que encontremos

        # Si no se encuentra un teléfono en la fila, la ignoramos para la base
        if not found_phone:
            continue

        # Extraer el primer nombre de la columna de nombres
        first_name = "CONTACTO" # Valor por defecto si no se puede extraer
        if name_col and name_col in row:
            name_raw = str(row[name_col])
            # Limpiar el nombre (quitar caracteres no alfabéticos y espacios extra)
            name_clean = re.sub(r'[^a-zA-Z\s]', '', name_raw).strip()
            if name_clean:
                # Tomar la primera palabra y capitalizarla
                first_name = name_clean.split()[0].capitalize()
        
        # Añadir el registro a nuestra lista
        final_records.append({
            "Numero telefono": found_phone,
            "value1": first_name,
            "value2": "",
            "value3": "",
            "value4": "",
            "value5": "",
            "Estado": ""
        })

    if not final_records:
        return pd.DataFrame()

    # Convertir a DataFrame y eliminar duplicados basados en el número de teléfono
    results_df = pd.DataFrame(final_records)
    results_df.drop_duplicates(subset=['Numero telefono'], inplace=True)
    
    return results_df

# --- Interfaz de la Aplicación ---
st.title("📲 Generador de Bases para Mensajería Masiva")
st.markdown("Sube tus archivos de origen y descarga una base limpia y formateada lista para usar.")

# 1. Carga de Archivos
st.header("1. Cargar Archivos de Origen")
uploaded_files = st.file_uploader(
    "Arrastra tus archivos Excel de origen aquí",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        df_temp = pd.read_excel(file, engine='openpyxl')
        df_list.append(df_temp)
    
    df = pd.concat(df_list, ignore_index=True)
    st.success(f"✅ ¡Carga completa! Se han unido {len(uploaded_files)} archivos, sumando un total de {len(df)} filas.")
    
    # 2. Mapeo de Columnas
    st.header("2. Mapear Columnas de Origen")
    st.info("Indica a la herramienta dónde buscar la información que necesita.")
    
    all_cols = df.columns.tolist()
    col1, col2 = st.columns(2)

    with col1:
        # Selector para la columna que contiene los NOMBRES
        name_keywords = ['nombre', 'name', 'tutor', 'student']
        default_name_col = next((col for col in all_cols if any(k in str(col).lower() for k in name_keywords)), None)
        name_column = st.selectbox(
            "¿En qué columna está el Nombre?",
            options=[None] + all_cols,
            index=all_cols.index(default_name_col) + 1 if default_name_col else 0,
            help="Selecciona la columna de donde se extraerá el primer nombre para 'value1'."
        )

    with col2:
        # Selector para las columnas que contienen los TELÉFONOS
        contact_keywords = ['tel', 'phone', 'telefono', 'grupo', 'email', 'correo']
        default_search_cols = [col for col in all_cols if any(k in str(col).lower() for k in contact_keywords)]
        search_columns = st.multiselect(
            "¿Dónde busco los teléfonos?",
            options=all_cols,
            default=default_search_cols,
            help="Selecciona todas las columnas donde puedan existir números de teléfono."
        )

    # 3. Procesamiento y Descarga
    if st.button("🚀 Generar Base para la App", type="primary"):
        if not search_columns:
            st.warning("Por favor, selecciona al menos una columna donde buscar teléfonos.")
        elif not name_column:
            st.warning("Por favor, selecciona la columna que contiene los nombres.")
        else:
            with st.spinner('Extrayendo, limpiando y formateando la base de datos...'):
                final_df = format_for_app(df, search_columns, name_column)
            
            st.header("3. Previsualización y Descarga")
            
            if final_df.empty:
                st.error("No se encontraron números de teléfono válidos en las columnas seleccionadas.")
            else:
                st.success(f"¡Proceso completado! Se ha generado una base con {len(final_df)} contactos únicos.")
                st.dataframe(final_df)

                # Preparar archivo para descarga con el formato exacto
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False, sheet_name='BASE APPP') # Nombre de hoja específico
                
                processed_data = output.getvalue()

                st.download_button(
                    label="⬇️ Descargar BASE APPP",
                    data=processed_data,
                    file_name="BASE_APPP_mensajeria.xlsx",
                    mime="application/vnd.ms-excel"
                )