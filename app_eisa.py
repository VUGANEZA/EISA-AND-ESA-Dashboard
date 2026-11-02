import streamlit as st
import pandas as pd
import plotly.express as px
import csv

st.title("🏗️ EISA Projects Dashboard")
st.markdown("Explore, search, and analyze Environmental and Social Impact Assessments (EISA) across Rwanda.")

if "reset_eisa" not in st.session_state:
    st.session_state.reset_eisa = False

def clear_filters():
    st.session_state.reset_eisa = True

@st.cache_data
def load_eisa_data():
    try:
        with open("eisa.csv", "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(10000)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            delimiter = dialect.delimiter

        df = pd.read_csv("eisa.csv", sep=delimiter, skiprows=1, on_bad_lines='skip', engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        if 'Project Title' in df.columns:
            df = df.dropna(subset=['Project Title'])
            df = df[df['Project Title'].astype(str).str.strip() != '']

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
            df = df[df['District'].isin(rwanda_districts)]
        else:
            df['District'] = "Unknown"

        if 'Project Category' in df.columns:
            df['Project Category'] = df['Project Category'].astype(str).apply(lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != '' else "Unknown")
        else:
            df['Project Category'] = "Unknown"

        if 'Developer name' in df.columns:
            df['Developer name'] = df['Developer name'].astype(str).apply(lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != '' else "Unknown")
        else:
            df['Developer name'] = "Unknown"

        return df
    except Exception as e:
        st.error(f"Error loading eisa.csv: {e}")
        return None

@st.fragment(run_every="2s")
def live_dashboard():
    load_eisa_data.clear() 
    df_eisa = load_eisa_data()

    if df_eisa is not None:
        st.sidebar.header("EISA Controls")
        
        st.sidebar.button("🔄 Reset EISA Filters", on_click=clear_filters, use_container_width=True)

        if st.session_state.reset_eisa:
            st.session_state.search_eisa = ""
            st.session_state.dist_eisa = "All Districts"
            st.session_state.cat_eisa = "All Categories"
            st.session_state.dev_eisa = "All Developers"
            st.session_state.reset_eisa = False 

        search_query = st.sidebar.text_input("🔍 Search Text:", key="search_eisa")
        
        df_filtered = df_eisa.copy()
        
        if search_query:
            mask = (
                df_filtered['District'].str.contains(search_query, case=False, na=False) |
                df_filtered['Developer name'].str.contains(search_query, case=False, na=False) |
                df_filtered['Project Title'].str.contains(search_query, case=False, na=False)
            )
            df_filtered = df_filtered[mask]

        st.sidebar.markdown("### Dropdown Filters")

        if 'District' in df_filtered.columns:
            available_districts = sorted(df_filtered['District'].dropna().unique())
            st.sidebar.selectbox("Select District:", options=["All Districts"] + list(available_districts), key="dist_eisa")
            if st.session_state.dist_eisa != "All Districts":
                df_filtered = df_filtered[df_filtered['District'] == st.session_state.dist_eisa]

        if 'Project Category' in df_filtered.columns:
            available_categories = sorted([str(c) for c in df_filtered['Project Category'].dropna().unique() if str(c) != ''])
            st.sidebar.selectbox("Select Category:", options=["All Categories"] + available_categories, key="cat_eisa")
            if st.session_state.cat_eisa != "All Categories":
                df_filtered = df_filtered[df_filtered['Project Category'] == st.session_state.cat_eisa]

        if 'Developer name' in df_filtered.columns:
            available_devs = sorted([str(d) for d in df_filtered['Developer name'].dropna().unique() if str(d).strip() != ''])
            st.sidebar.selectbox("Select Developer:", options=["All Developers"] + available_devs, key="dev_eisa")
            if st.session_state.dev_eisa != "All Developers":
                df_filtered = df_filtered[df_filtered['Developer name'] == st.session_state.dev_eisa]
            
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Projects", len(df_filtered))
        if 'Developer name' in df_filtered.columns:
            col2.metric("Developers", df_filtered[df_filtered['Developer name'] != 'Unknown']['Developer name'].nunique())
        if 'District' in df_filtered.columns:
            col3.metric("Districts Covered", df_filtered[df_filtered['District'] != 'Unknown']['District'].nunique())
        if 'Project Category' in df_filtered.columns:
            col4.metric("Categories", df_filtered[df_filtered['Project Category'] != 'Unknown']['Project Category'].nunique())

        st.markdown("---")
        st.subheader("Data Visualizations")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            chart_data = df_filtered[df_filtered['District'] != 'Unknown']
            if len(chart_data) > 0:
                district_counts = chart_data['District'].value_counts().head(15).reset_index()
                district_counts.columns = ['District', 'Count']
                # ADDED: color='District' and a distinct color sequence
                fig_district = px.bar(district_counts, x='District', y='Count', title="Top 15 Districts by Project Count", text='Count', color='District', color_discrete_sequence=px.colors.qualitative.Plotly)
                fig_district.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
                fig_district.update_xaxes(tickangle=45)
                st.plotly_chart(fig_district, use_container_width=True)

        with col_chart2:
            chart_data = df_filtered[df_filtered['Project Category'] != 'Unknown']
            if len(chart_data) > 0:
                top_cats = chart_data['Project Category'].value_counts().head(8).index
                df_pie = chart_data[chart_data['Project Category'].isin(top_cats)]
                # ADDED: distinct color sequence for the pie chart
                fig_category = px.pie(df_pie, names='Project Category', title="Top 8 Categories", hole=0.4, color_discrete_sequence=px.colors.qualitative.Plotly)
                fig_category.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig_category, use_container_width=True)

        st.markdown("---")
        st.subheader("Project Data Table")
        table_header_col1, table_header_col2 = st.columns([3, 1])
        
        with table_header_col1:
            st.write(f"Showing **{len(df_filtered)}** records.")
        with table_header_col2:
            csv_data = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", data=csv_data, file_name='eisa_filtered.csv', mime='text/csv', use_container_width=True)

        display_cols = []
        for col in ['Reference', 'Project Title', 'Developer name', 'District', 'Project Category', 'Issue date']:
            if col in df_filtered.columns:
                display_cols.append(col)

        st.dataframe(df_filtered[display_cols], use_container_width=True, height=500)

live_dashboard()