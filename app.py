import streamlit as st

# Set up the main page configuration
st.set_page_config(page_title="EISA AND ESA", page_icon="🇷🇼", layout="wide")

# Create the navigation menu
pages = [
    st.Page("app_esa.py", title="ESA Projects", icon="🌍"),
    st.Page("app_eisa.py", title="EISA Projects", icon="🏗️")
]

# Run the navigation
pg = st.navigation(pages)

# Display the selected page
pg.run()