import streamlit as st
import pandas as pd
import re
import io

# --- Configuración de la Página de la Aplicación ---
st.set_page_config(
    page_title="Generador de Bases para APPP",
    page_icon="📲",
    layout="wide"
)

# --- Función Principal de Extracción y Formateo ---
def extract_and_format(df, phone_cols, name_cols):
    """
    Recorre el DataFrame, extrae el primer teléfono y el primer nombre válido de cada fila,
    y los formatea en la estructura final.
    """
    final_records = []
    # Regex para encontrar números de celular colombianos (10 dígitos empezando por 3)
    phone_regex = re.compile(r'\b(3\d{9})\b')

    for index, row in df.iterrows():
        found_phone = None
        found_name = None

        # 1. Buscar el primer teléfono válido en las columnas seleccionadas para la fila actual
        for col in phone_cols:
            # .get(col, '') es para evitar errores si una columna no existe en alguna fila (poco probable con concat)
            phones = phone_regex.findall(str(row.get(col, '')))
            if phones:
                found_phone = phones[0]
                break  # Nos quedamos con el primer teléfono encontrado

        # Si no se encontró un teléfono en esta fila, la saltamos y vamos a la siguiente
        if not found_phone:
            continue

        # 2. Buscar el primer nombre válido en la MISMA fila
        for col in name_cols:
            name_raw = str(row.get(col, ''))
            # Criterio para un "nombre válido": tiene más de una palabra y más de 4 letras en total.
            # Esto ayuda a ignorar iniciales como "AC", "Yo", "Mb".
            if len(name_raw.split()) > 1 and len(re.sub(r'[^a-zA-Z]', '', name_raw)) > 4:
                # Limpiar caracteres extraños y tomar la primera palabra
                name_clean = re.sub(r'[^a-zA-Z\s]', '', name_raw).strip()
                found_name = name_clean.split()[0].capitalize()
                break  # Nos quedamos con el primer nombre válido encontrado
        
        # Si, después de buscar, no se encontró un nombre válido, usamos un valor por defecto
        if not found_name:
            found_name = "Contacto" # O puedes dejarlo en blanco cambiando a ""

        # Añadir el registro formateado
        final_records.append({
            "Numero telefono": found_phone,
            "value1": found_name,
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
    results_df.drop_duplicates(subset=['Numero telefono'], inplace=True, keep='first')
    return results_df

# --- Interfaz Gráfica de la Aplicación con Streamlit ---
st.title("📲 Generador de Bases para Mensajería Masiva")
st.markdown("Sube tus archivos de origen y la herramienta creará la base formateada para tu aplicación.")

uploaded_files = st.file_uploader(
    "Arrastra todos tus archivos Excel de origen aquí",
    type=['xlsx', 'xls'],
    accept_multiple_files=True
)

if uploaded_files:
    # Une todos los archivos cargados en una sola tabla de datos
    df = pd.concat([pd.read_excel(f) for f in uploaded_files], ignore_index=True)
    st.success(f"✅ ¡Carga completa! Se han unido {len(uploaded_files)} archivos. Total de filas a analizar: {len(df)}.")
    
    st.header("1. Configurar Búsqueda")
    all_cols = df.columns.tolist()

    # Selección de columnas de NOMBRE (con detección automática)
    name_keywords = ['nombre', 'name', 'tutor', 'student']
    default_name_cols = [c for c in all_cols if any(k in c.lower() for k in name_keywords)]
    name_columns = st.multiselect(
        "¿En qué columnas están los Nombres?",
        options=all_cols,
        default=default_name_cols,
        help="Selecciona las columnas que contienen los nombres completos de los contactos."
    )

    # Selección de columnas de TELÉFONO (con detección automática)
    phone_keywords = ['tel', 'phone', 'grupo', 'email', 'teléfono']
    default_phone_cols = [c for c in all_cols if any(k in c.lower() for k in phone_keywords)]
    phone_columns = st.multiselect(
        "¿Dónde busco los Teléfonos?",
        options=all_cols,
        default=default_phone_cols,
        help="Selecciona todas las columnas donde puedan existir números de teléfono."
    )

    if st.button("🚀 Generar Base para la App", type="primary"):
        final_df = extract_and_format(df, phone_columns, name_columns)
        
        st.header("2. Resultados y Descarga")
        if final_df.empty:
            st.error("No se encontraron contactos válidos con la configuración actual. Revisa las columnas seleccionadas.")
        else:
            st.dataframe(final_df)
            st.success(f"Se ha generado una base con {len(final_df)} contactos únicos.")
            
            # Preparar el archivo Excel para la descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='BASE APPP')
            
            st.download_button(
                label="⬇️ Descargar BASE APPP",
                data=output.getvalue(),
                file_name="BASE_APPP.xlsx",
                mime="application/vnd.ms-excel"
            )
