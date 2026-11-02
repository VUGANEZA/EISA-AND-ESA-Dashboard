import streamlit as st
import pandas as pd
import plotly.express as px
import csv

st.title("🌍 ESA Projects Dashboard")
st.markdown("Explore, search, and analyze Environmental and Social Assessments (ESA) across Rwanda.")

if "reset_esa" not in st.session_state:
    st.session_state.reset_esa = False

def clear_filters():
    st.session_state.reset_esa = True

@st.cache_data
def load_esa_data():
    try:
        with open("esa.csv", "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(10000)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            delimiter = dialect.delimiter

        df = pd.read_csv("esa.csv", sep=delimiter, on_bad_lines='skip', engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        if 'Project Title' in df.columns:
            df = df.dropna(subset=['Project Title'])
            df = df[df['Project Title'].astype(str).str.strip() != '']

        # --- STRICT 30 DISTRICTS RULE ---
        if 'District' in df.columns:
            df['District'] = df['District'].astype(str).str.replace(',', ', ')
            df = df.assign(District=df['District'].str.split(',')).explode('District')
            df['District'] = df['District'].astype(str).apply(lambda x: x.title().strip() if pd.notna(x) and str(x).strip() != '' else "Unknown")
            
            rwanda_districts = [
                "Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana", 
                "Gasabo", "Kicukiro", "Nyarugenge", "Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo", 
                "Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango", 
                "Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"
            ]
            # Keep ONLY the 30 official districts
            df = df[df['District'].isin(rwanda_districts)]
        else:
            df['District'] = "Unknown"

        if 'Project Category' in df.columns:
            df['Project Category'] = df['Project Category'].astype(str).str.replace(',', ', ')
            df = df.assign(**{'Project Category': df['Project Category'].str.split(',')}).explode('Project Category')
            df['Project Category'] = df['Project Category'].astype(str).apply(lambda x: str(x).title().strip() if pd.notna(x) and str(x).strip() != '' else "Unknown")
        else:
            df['Project Category'] = "Unknown"

        return df
    except Exception as e:
        st.error(f"Error loading esa.csv: {e}")
        return None

@st.fragment(run_every="2s")
def live_dashboard():
    load_esa_data.clear() 
    df_esa = load_esa_data()

    if df_esa is not None:
        st.sidebar.header("ESA Controls")
        st.sidebar.button("🔄 Reset ESA Filters", on_click=clear_filters, use_container_width=True)

        if st.session_state.reset_esa:
            st.session_state.search_esa = ""
            st.session_state.dist_esa = "All Districts"
            st.session_state.cat_esa = "All Categories"
            st.session_state.reset_esa = False 

        search_query = st.sidebar.text_input("🔍 Search Text:", key="search_esa")
        df_filtered = df_esa.copy()
        
        if search_query:
            mask = (
                df_filtered['District'].str.contains(search_query, case=False, na=False) |
                df_filtered['Project Category'].str.contains(search_query, case=False, na=False) |
                df_filtered['Project Title'].str.contains(search_query, case=False, na=False)
            )
            df_filtered = df_filtered[mask]

        st.sidebar.markdown("### Dropdown Filters")

        if 'District' in df_filtered.columns:
            available_districts = sorted(df_filtered['District'].dropna().unique())
            st.sidebar.selectbox("Select District:", options=["All Districts"] + list(available_districts), key="dist_esa")
            if st.session_state.dist_esa != "All Districts":
                df_filtered = df_filtered[df_filtered['District'] == st.session_state.dist_esa]

        if 'Project Category' in df_filtered.columns:
            available_categories = sorted([str(c) for c in df_filtered['Project Category'].dropna().unique() if str(c) != ''])
            st.sidebar.selectbox("Select Category:", options=["All Categories"] + available_categories, key="cat_esa")
            if st.session_state.cat_esa != "All Categories":
                df_filtered = df_filtered[df_filtered['Project Category'] == st.session_state.cat_esa]
            
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total ESA Projects", len(df_filtered))
        if 'District' in df_filtered.columns:
            col2.metric("Districts Covered", df_filtered[df_filtered['District'] != 'Unknown']['District'].nunique())
        if 'Project Category' in df_filtered.columns:
            col3.metric("Categories", df_filtered[df_filtered['Project Category'] != 'Unknown']['Project Category'].nunique())

        st.markdown("---")
        st.subheader("Data Visualizations")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            chart_data = df_filtered[df_filtered['District'] != 'Unknown']
            if len(chart_data) > 0:
                district_counts = chart_data['District'].value_counts().head(15).reset_index()
                district_counts.columns = ['District', 'Count']
                fig_district = px.bar(district_counts, x='District', y='Count', title="Top 15 Districts", text='Count', color='District')
                fig_district.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
                fig_district.update_xaxes(tickangle=45)
                st.plotly_chart(fig_district, use_container_width=True)

        with col_chart2:
            chart_data = df_filtered[df_filtered['Project Category'] != 'Unknown']
            if len(chart_data) > 0:
                top_cats = chart_data['Project Category'].value_counts().head(8).index
                df_pie = chart_data[chart_data['Project Category'].isin(top_cats)]
                fig_category = px.pie(df_pie, names='Project Category', title="Top 8 Categories", hole=0.4)
                fig_category.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig_category, use_container_width=True)

        st.markdown("---")
        st.subheader("Project Data Table")
        table_header_col1, table_header_col2 = st.columns([3, 1])
        with table_header_col1:
            st.write(f"Showing **{len(df_filtered)}** records.")
        with table_header_col2:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", data=csv_data, file_name='esa_filtered.csv', mime='text/csv', use_container_width=True)

        display_cols = []
        for col in ['Reference', 'Project Title', 'District', 'Project Category', 'Issue date']:
            if col in df_filtered.columns:
                display_cols.append(col)

        st.dataframe(df_filtered[display_cols], use_container_width=True, height=500)

live_dashboard()