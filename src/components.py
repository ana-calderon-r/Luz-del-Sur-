import streamlit as st

def card(titulo, valor, porcentaje, icono, color):

    st.markdown(
        f"""
<div style="
background-color:{color};
border-radius:15px;
padding:20px;
text-align:center;
border:1px solid #E5E5E5;
box-shadow:0px 2px 8px rgba(0,0,0,0.08);
height:190px;
">

<div style="font-size:38px;">
{icono}
</div>

<div style="
font-size:20px;
font-weight:600;
margin-top:5px;
">
{titulo}
</div>

<div style="
font-size:42px;
font-weight:bold;
margin-top:10px;
color:#1E1E1E;
">
{valor:,}
</div>

<div style="
font-size:18px;
color:gray;
margin-top:8px;
">
{porcentaje}
</div>

</div>
""",
        unsafe_allow_html=True
    )