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

# --- Función Principal de Extracción y Formateo (CON LA CORRECCIÓN FINAL) ---
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
                # --- ¡ESTA ES LA CORRECCIÓN! ---
                # Tomamos el primer elemento [0] de la lista de resultados
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
    df = pd.concat([pd.read_excel(f, dtype=str) for f in uploaded_files], ignore_index=True)
    st.success(f"✅ ¡Carga completa! Se han unido {len(uploaded_files)} archivos. Total de filas: {len(df)}.")
    
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
