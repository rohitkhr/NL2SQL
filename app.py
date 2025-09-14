import streamlit as st
from nl_to_sql import NLToSQLEngine
import plotly.graph_objects as go

st.set_page_config(page_title="NL2SQL Web Interface", layout="wide")
# --- Accessibility: Custom CSS for fonts and high-contrast colors ---
st.markdown("""
    <style>
    body, .stApp {
        font-family: 'Segoe UI', 'Arial', sans-serif !important;
        background-color: #fff !important;
        color: #222 !important;
    }
    .stTitle, .stHeader, .stSubheader {
        color: #1a237e !important;
        font-weight: bold !important;
    }
    .stDataFrame, .stTable {
        background-color: #f5f5f5 !important;
        color: #222 !important;
    }
    .stButton>button {
        background-color: #1a237e !important;
        color: #fff !important;
        border-radius: 4px !important;
        font-size: 1rem !important;
    }
    .stSelectbox label {
        font-weight: bold !important;
        color: #1a237e !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Talk to your database")
st.write("Type a question about your data and get results!")

engine = NLToSQLEngine()

# --- Schema Explorer Sidebar ---
schema_info = engine.schema_info
with st.sidebar:
    st.header("Schema Explorer")
    for table_name, table_info in schema_info.items():
        with st.expander(f"Table: {table_name}"):
            st.write("Columns:")
            for col in table_info['columns']:
                pk = " (PK)" if col['primary_key'] else ""
                nn = " NOT NULL" if col['not_null'] else ""
                st.write(f"- {col['name']} ({col['type']}){pk}{nn}")
            if table_info['foreign_keys']:
                st.write("Foreign Keys:")
                for fk in table_info['foreign_keys']:
                    st.write(f"- {fk[3]} -> {fk[2]}.{fk[4]}")
    # --- Example Queries in Sidebar ---
    st.markdown("**Example queries:**")
    example_queries = [
        "Show me all customers",
        "What are the total sales for each customer?",
        "Show me all electronics products",
        "Which customers are from California?",
        "What orders were placed in February 2024?",
        "Show me the most expensive products (You can also ask 'Show me the 3 most expensive products')",
        "Which customer has spent the most money?"
    ]
    for ex in example_queries:
        st.write(f"- {ex}")

user_query = st.text_input("Ask me anything about your database:")

if user_query:
    result = engine.process_natural_language_query(user_query)
    if result['success']:
        st.subheader("SQL Query")
        st.code(result['sql_query'], language='sql')
        st.subheader(f"Results ({result['row_count']} rows)")
        st.dataframe(result['results'])
        # --- Download Results ---
        st.markdown("### Download Results")
        csv = result['results'].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv"
        )
        try:
            import io
            excel_buffer = io.BytesIO()
            result['results'].to_excel(excel_buffer, index=False)
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="Download as Excel",
                data=excel_data,
                file_name="query_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.info("Excel download unavailable: pandas 'to_excel' requires 'openpyxl' or 'xlsxwriter'.")
        # --- Visualization Options ---
        st.markdown("### Visualize Results")
        chart_type = st.selectbox("Choose chart type", ["None", "Bar Chart", "Line Chart", "Pie Chart"])
        if chart_type != "None":
            columns = list(result['results'].columns)
            if chart_type == "Pie Chart":
                col_x = st.selectbox("Label column", columns)
                col_y = st.selectbox("Value column", columns)
                fig = go.Figure(data=[go.Pie(labels=result['results'][col_x], values=result['results'][col_y])])
                fig.update_layout(title=f"{col_y} by {col_x}")
                st.plotly_chart(fig)
            else:
                col_x = st.selectbox("X axis", columns)
                col_y = st.selectbox("Y axis", columns)
                if chart_type == "Bar Chart":
                    st.bar_chart(result['results'].set_index(col_x)[col_y])
                elif chart_type == "Line Chart":
                    st.line_chart(result['results'].set_index(col_x)[col_y])
    else:
        st.error(result['error'])
        if 'sql_query' in result:
            st.write("Generated SQL:")
            st.code(result['sql_query'], language='sql')
