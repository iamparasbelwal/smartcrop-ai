"""SmartCrop.AI entry point.

One auth gate wraps the whole app: signed-out visitors only ever see the sign-in
page; signed-in users get the lab's pages, and lab admins get Lab admin as well.
The sidebar carries the lab's project list under the navigation.

Run with:  .venv\\Scripts\\python -m streamlit run app.py
"""

import streamlit as st

import auth
import cleanlabel
import formulations
import ingredients
import projects
import ui

st.set_page_config(
    page_title="SmartCrop.AI",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.apply_theme()

auth.bootstrap()
projects.bootstrap()
ingredients.bootstrap()
cleanlabel.bootstrap()
formulations.bootstrap()

sign_in_page = st.Page("pages/0_Sign_in.py", title="Sign in", icon=":material/login:", default=True)
home_page = st.Page("pages/1_Home.py", title="Home", icon=":material/home:")
project_page = st.Page(
    "pages/2_Project.py", title="Workbench", icon=":material/science:"
)
people_page = st.Page(
    "pages/5_People.py", title="People", icon=":material/group:"
)
lab_admin_page = st.Page(
    "pages/4_Lab_admin.py", title="Lab admin", icon=":material/manage_accounts:"
)
project_access_page = st.Page(
    "pages/6_Project_access.py", title="Project access", icon=":material/lock_open:"
)
verify_page = st.Page(
    "pages/7_Verify_data.py", title="Verify data", icon=":material/fact_check:"
)
audit_page = st.Page(
    "pages/8_Audit_log.py", title="Audit log", icon=":material/history:"
)


@st.fragment(run_every=5)
def watch_account(user_id: str) -> None:
    """End the session within ~5 s if an admin deactivates the account."""
    if not auth.user_is_active(user_id):
        auth.force_sign_out(
            "This account was deactivated by the lab admin. Ask your lab admin to reactivate it."
        )
        st.rerun(scope="app")


user = auth.refresh_session_user()

if user is None:
    navigation = st.navigation([sign_in_page], position="hidden")
else:
    with st.sidebar:
        # Pinned footer at bottom of sidebar
        with st.container(key="side_bottom"):
            first_letter = (user["name"][:1] if user["name"] else "U").upper()
            st.markdown(
                f'<div class="side-user-row">'
                f'<div class="side-avatar">{ui.esc(first_letter)}</div>'
                f'<div class="side-user-details">'
                f'<div class="side-user">{ui.esc(user["name"])}</div>'
                f'<div class="side-role">{auth.ROLE_LABELS.get(user["role"], user["role"])} · {user["lab_id"]}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Sign out", key="sign_out_button", width="stretch", icon=":material/logout:"):
                auth.sign_out()
                st.rerun()

    watch_account(user["user_id"])

    pages = [home_page, project_page, people_page]
    if user["role"] == "lab_admin":
        pages.extend([lab_admin_page, verify_page, audit_page, project_access_page])
    navigation = st.navigation(pages)

navigation.run()
