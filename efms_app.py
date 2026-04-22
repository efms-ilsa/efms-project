import streamlit as st

st.title("EFMS Dashboard")
st.write("Hello! Your Streamlit app is running successfully.")

# Example of adding a simple widget
name = st.text_input("Enter your name:")
if name:
    st.success(f"Welcome, {name}!")