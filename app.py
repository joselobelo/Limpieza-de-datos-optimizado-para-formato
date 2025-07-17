import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página de la Aplicación ---
st.set_page_config(
    page_title="Generador de Bases Inteligente",
    page_icon="🧠",
    layout="wide"
)

# --- Función Principal de Extracción y Formateo ---
def extract_and_format(df, phone_cols, name_cols):
    """
    Recorre el DataFrame, extrae el primer teléfono y el primer NOMBRE REAL de cada fila,
    ignorando palabras cortas o "basura".
    """
    final_records = []
    phone_regex = re.compile(r'\b(3\d{9})\b')

    for index, row in df.iterrows():
        found_phone = None
        found_name = None

        # 1. Buscar el primer teléfono válido en la fila
        for col in phone_cols:
            phones = phone_regex.findall(str(row.get(col, '')))
            if phones:
                found_phone = phones[0]
                break
        
        if not found_phone:
            continue

        # 2. Buscar el primer NOMBRE VÁLIDO en la misma fila
        for col in name_cols:
            name_raw = str(row.get(col, ''))
            name_clean = re.sub(r'[^a-zA-Z\s]', '', name_raw).strip()
            words = name_clean.split()
            
            for word in words:
                if len(word) > 2:
                    found_name = word.capitalize()
                    break
            
            if found_name:
                break

        if not found_name:
            found_name = "Contacto"

        final_records.append({
            "Numero telefono": found_phone, "value1": found_name, "value2": "", 
            "value3": "", "value4": "", "value5": "", "Estado": ""
        })

    if not final_records: return pd.DataFrame()
    results_df = pd.DataFrame(final_records)
    results_df.drop_duplicates(subset=['Numero telefono'], inplace=True, keep='first')
    return results_df

# --- Interfaz Gráfica de la Aplicación ---
st.title("🧠 Generador de Bases Inteligente")
st.markdown("La herramienta ignora iniciales y 'basura' para encontrar el primer nombre real y asociarlo a su teléfono.")

uploaded_files = st.file_uploader(
    "Arrastra todos tus archivos Excel de origen aquí",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

if uploaded_files:
    # --- SECCIÓN CORREGIDA PARA MANEJAR ERRORES DE CARGA ---
    valid_dfs = []
    for f in uploaded_files:
        try:
            # Intenta leer cada archivo subido
            df_temp = pd.read_excel(f, dtype=str)
            valid_dfs.append(df_temp)
        except Exception as e:
            # Si falla (p.ej. es un archivo temporal ~$), lo ignora y avisa al usuario
            st.warning(f"Advertencia: Se omitió el archivo '{f.name}' porque no es un archivo Excel válido o está dañado.")

    # Solo se procede si se cargó al menos un archivo válido
    if not valid_dfs:
        st.error("❌ No se pudo leer ninguno de los archivos subidos. Asegúrate de que no estén dañados o sean archivos temporales.")
    else:
        # Concatenar solo los DataFrames que se leyeron correctamente
        df = pd.concat(valid_dfs, ignore_index=True)
        st.success(f"✅ ¡Carga completa! Se han unido {len(valid_dfs)} archivos válidos. Total de filas: {len(df)}.")
        
        st.header("1. Configurar Búsqueda")
        all_cols = df.columns.tolist()

        name_keywords = ['nombre', 'name', 'tutor', 'student']
        default_name_cols = [c for c in all_cols if any(k in c.lower() for k in name_keywords)]
        name_columns = st.multiselect("¿Columnas que contienen Nombres?", options=all_cols, default=default_name_cols)

        phone_keywords = ['tel', 'phone', 'grupo', 'email', 'teléfono']
        default_phone_cols = [c for c in all_cols if any(k in c.lower() for k in phone_keywords)]
        phone_columns = st.multiselect("¿Columnas que contienen Teléfonos?", options=all_cols, default=default_phone_cols)

        if st.button("🚀 Generar Base para la App", type="primary"):
            final_df = extract_and_format(df, phone_columns, name_columns)
            
            st.header("2. Resultados y Descarga")
            if final_df.empty:
                st.error("No se encontraron contactos válidos. Revisa las columnas seleccionadas.")
            else:
                st.dataframe(final_df)
                st.success(f"Se ha generado una base con {len(final_df)} contactos únicos.")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False, sheet_name='BASE APPP')
                
                st.download_button(
                    label="⬇️ Descargar BASE APPP",
                    data=output.getvalue(),
                    file_name="BASE_APPP.xlsx",
                    mime="application/vnd.ms-excel"
                )
