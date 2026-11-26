"""Sign in page (public). Local demo accounts, not production security."""

import streamlit as st

import auth
import ui

# If already signed in via persistent session, jump straight to Home
if auth.current_user() is not None:
    st.switch_page("pages/1_Home.py")

ui.show_page_skeleton("auth")

notice = auth.take_notice()
if notice:
    st.warning(notice)

with st.container(key="auth_split"):
    left_col, right_col = st.columns([1.12, 1.0], gap="large", vertical_alignment="center")

    with left_col:
        with st.container(border=True, key="auth_welcome_card"):
            st.markdown(
                '<div class="hero-eyebrow auth-left-eyebrow">SmartCrop.AI</div>'
                '<h1 class="hero-title auth-left-title">Welcome back</h1>'
                '<p class="hero-sub auth-left-sub">AI R&amp;D co-pilot for clean-label plant-based formulations. '
                "Every output is a starting point that needs lab validation.</p>",
                unsafe_allow_html=True,
            )

    with right_col:
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
            with st.expander("Demo accounts", expanded=True):
                st.markdown(
                    "| Role | Email | Password |\n"
                    "| --- | --- | --- |\n"
                    "| Lab admin | paras@smartcrop.ai | Admin@123 |\n"
                    "| Lab worker | shivam@smartcrop.ai | Worker@123 |\n"
                    "| Lab worker | shreyshi@smartcrop.ai | Worker@123 |"
                )
                st.markdown('<div style="height: 0.4rem;"></div>', unsafe_allow_html=True)
                st.caption("Quick sign-in as:")
                qc1, qc2, qc3 = st.columns(3, gap="small")
                with qc1:
                    if st.button("Paras (Admin)", key="quick_paras", use_container_width=True):
                        auth.sign_in("paras@smartcrop.ai", "Admin@123")
                        st.rerun()
                with qc2:
                    if st.button("Shivam (Worker)", key="quick_shivam", use_container_width=True):
                        auth.sign_in("shivam@smartcrop.ai", "Worker@123")
                        st.rerun()
                with qc3:
                    if st.button("Shreyshi (Worker)", key="quick_shreyshi", use_container_width=True):
                        auth.sign_in("shreyshi@smartcrop.ai", "Worker@123")
                        st.rerun()
                st.caption(
                    "Local demo accounts stored in data/users.csv. The lab admin can add or "
                    "deactivate workers from the Lab admin page."
                )
