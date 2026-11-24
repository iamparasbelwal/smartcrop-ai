"""Sign in page (public). Local demo accounts, not production security."""

import streamlit as st

import auth
import ui

# If already signed in via persistent session, jump straight to Home
if auth.current_user() is not None:
    st.switch_page("pages/1_Home.py")

notice = auth.take_notice()
if notice:
    st.warning(notice)

with st.container(key="auth-hero"):
    st.markdown('<div class="hero-eyebrow">SmartCrop.AI</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Welcome back</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">AI R&amp;D co-pilot for clean-label plant-based formulations. '
        "Every output is a starting point that needs lab validation.</p>",
        unsafe_allow_html=True,
    )

with st.container(key="auth-form"):
    with st.form("sign_in_form", border=False):
        email = st.text_input(
            "Email",
            placeholder="you@lab.org",
            key="sign_in_email",
            label_visibility="collapsed",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="sign_in_password",
            placeholder="Password",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Sign in", type="primary", width="stretch")

if submitted:
    ok, message = auth.sign_in(email, password)
    if ok:
        st.rerun()
    else:
        st.error(message)

with st.container(key="auth-demo"):
    with st.expander("Demo accounts"):
        st.markdown(
            "| Role | Email | Password |\n"
            "| --- | --- | --- |\n"
            "| Lab admin | paras@smartcrop.ai | Admin@123 |\n"
            "| Lab worker | shivam@smartcrop.ai | Worker@123 |\n"
            "| Lab worker | shreyshi@smartcrop.ai | Worker@123 |"
        )
        st.caption(
            "Local demo accounts stored in data/users.csv. The lab admin can add or "
            "deactivate workers from the Lab admin page."
        )
