"""Shared look and feel for SmartCrop.AI.

One place for the warm, assistant-style styling: off-white canvas, near-black
ink, a single brick accent, thin borders, serif display headings, lots of air.
The palette itself lives in `.streamlit/config.toml` so Streamlit's own widgets
follow it; this file handles shapes, spacing and typography accents.
"""

from __future__ import annotations

import html

import streamlit as st

SERIF = '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif'

CSS = """
<style>
:root {
    --canvas: #faf9f5;
    --panel: #ffffff;
    --sand: #f2f0e8;
    --ink: #22201c;
    --muted: #6f6a60;
    --line: #e6e2d6;
    --accent: #c2603c;
    --accent-dark: #a94f2f;
    --accent-soft: #f7e9e2;
}

.stApp, [data-testid="stAppViewContainer"] { background: var(--canvas) !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer, [data-testid="stStatusWidget"] { display: none !important; }

.block-container { max-width: 1380px !important; margin: 0 auto !important; padding: 2.2rem 2.2rem 5rem !important; }

/* ---------- sidebar ---------- */
/* Completely remove the collapse/expand chevron arrow buttons */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarHeader"] button {
    display: none !important;
}

/* ---------- Standard Global Sidebar (Home, Projects, People, Lab Admin) ---------- */
[data-testid="stSidebar"] {
    background: var(--sand) !important;
    border-right: 1px solid var(--line) !important;
    visibility: visible !important;
    transform: none !important;
    margin-left: 0 !important;
    height: 100vh !important;
    width: 240px !important;
    min-width: 240px !important;
    max-width: 240px !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    scrollbar-width: none !important;
}

[data-testid="stSidebar"] ::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    transform: none !important;
    margin-left: 0 !important;
    visibility: visible !important;
    display: block !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    height: 100vh !important;
    max-height: 100vh !important;
    width: 240px !important;
    box-sizing: border-box !important;
    padding: 1.2rem 0.9rem 1.4rem !important;
    overflow: hidden !important;
    overflow-y: hidden !important;
    scrollbar-width: none !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}
[data-testid="stSidebarNav"] {
    flex-shrink: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}
[data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] .block-container {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
    padding: 0 !important;
    margin: 0 !important;
    max-width: none !important;
    box-sizing: border-box !important;
}
[data-testid="stSidebarNavLink"] {
    display: flex !important;
    align-items: center !important;
    border-radius: 12px !important;
    padding: 0.35rem 0.6rem !important;
    margin-bottom: 0.25rem !important;
    text-decoration: none !important;
}
[data-testid="stSidebarNavLink"] span {
    font-size: 0.94rem !important;
}

[data-testid="stSidebar"] hr { margin: 1rem 0; border-color: var(--line); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { font-size: 0.8rem !important; color: var(--muted) !important; }

/* Sticky footer at sidebar bottom */
.st-key-side_bottom {
    margin-top: auto !important;
    padding-top: 0.8rem !important;
    border-top: 1px solid var(--line) !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
.side-user-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
}
.side-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #e8e3d5;
    color: var(--ink);
    font-weight: 700;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 1px solid var(--line);
}
.side-user-details {
    overflow: hidden;
    white-space: nowrap;
}
.side-user { font-size: 0.9rem; font-weight: 600; }
.side-role { font-size: 0.76rem; color: var(--muted); margin-bottom: 0.2rem; }

.st-key-side_bottom .stButton button {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.4rem !important;
    border: 1px solid var(--line) !important;
    background: var(--panel) !important;
    border-radius: 10px !important;
    color: #8a3f26 !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.65rem !important;
}
.st-key-side_bottom .stButton button:hover {
    background: var(--accent-soft) !important;
    border-color: #f0d3c8 !important;
    color: #6d3520 !important;
}

/* Header action pushed to the far right */
.st-key-projects_head [data-testid="column"]:last-child,
.st-key-projects_head .stColumn:last-child,
.st-key-people_head [data-testid="column"]:last-child,
.st-key-people_head .stColumn:last-child,
.st-key-access_head [data-testid="column"]:last-child,
.st-key-access_head .stColumn:last-child {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-end !important;
    justify-content: center !important;
}
.st-key-projects_head [data-testid="column"]:last-child > div,
.st-key-projects_head .stColumn:last-child > div,
.st-key-people_head [data-testid="column"]:last-child > div,
.st-key-people_head .stColumn:last-child > div,
.st-key-access_head [data-testid="column"]:last-child > div,
.st-key-access_head .stColumn:last-child > div {
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
    width: 100% !important;
}
.st-key-projects_head [data-testid="column"]:last-child [data-testid="stPageLink-NavLink"],
.st-key-people_head [data-testid="column"]:last-child [data-testid="stPageLink-NavLink"],
.st-key-projects_head .stColumn:last-child [data-testid="stPageLink-NavLink"],
.st-key-people_head .stColumn:last-child [data-testid="stPageLink-NavLink"],
.st-key-projects_head [data-testid="column"]:last-child a,
.st-key-people_head [data-testid="column"]:last-child a,
.st-key-projects_head .stColumn:last-child a,
.st-key-people_head .stColumn:last-child a,
.st-key-access_head [data-testid="stButton"] button {
    margin-left: auto !important;
    text-align: right !important;
    width: fit-content !important;
    float: right !important;
    border: 1px solid var(--line) !important;
    background: var(--panel) !important;
    border-radius: 999px !important;
    padding: 0.35rem 0.9rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--ink) !important;
    box-shadow: 0 1px 2px rgba(34, 32, 28, 0.04) !important;
    text-decoration: none !important;
    transition: all 0.15s ease !important;
}
.st-key-projects_head [data-testid="column"]:last-child a:hover,
.st-key-people_head [data-testid="column"]:last-child a:hover,
.st-key-projects_head .stColumn:last-child a:hover,
.st-key-people_head .stColumn:last-child a:hover,
.st-key-access_head [data-testid="stButton"] button:hover {
    background: #f0ede4 !important;
    border-color: #d8d3c5 !important;
}

/* Layout containers for centered symmetric pages */
.st-key-home_layout,
.st-key-projects_layout,
.st-key-people_layout {
    max-width: 940px !important;
    margin: 0 auto !important;
}

/* Wide full-canvas layout for Lab admin utilizing leftover space */
.st-key-admin_layout {
    max-width: 100% !important;
    padding: 0.6rem 2.2rem 2.5rem 2.2rem !important;
    box-sizing: border-box !important;
}
.st-key-admin_access_card {
    margin-top: 1.2rem !important;
}

/* ---------- People KPI Stat Cards ---------- */
[class*="st-key-stat_"] {
    min-height: 130px !important;
}
[class*="st-key-stat_"] [data-testid="stVerticalBlockBorderWrapper"] {
    min-height: 130px !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    padding: 1.1rem 1.3rem !important;
}
[class*="st-key-stat_"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: flex-start !important;
    text-align: left !important;
    height: 100% !important;
    min-height: 100% !important;
}
[class*="st-key-stat_"] [data-testid="stElementContainer"],
[class*="st-key-stat_"] [data-testid="stMarkdownContainer"] {
    width: 100% !important;
    text-align: left !important;
}
.stat-card-inner {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    text-align: left;
    height: 100%;
    width: 100%;
}

/* ---------- People Roster Table Styles ---------- */
.st-key-people_table_card,
.st-key-admin_people_table {
    margin-top: 1.1rem !important;
    padding: 1.4rem 1.6rem !important;
}
.st-key-people_table_card .panel-title,
.st-key-admin_people_table .panel-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    margin: 0 0 0.4rem 0 !important;
}
.roster-th {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: var(--muted) !important;
}
.roster-header-line {
    border-bottom: 1px solid var(--line);
    margin: 0.35rem 0 0.55rem 0;
}
.roster-row-line {
    border-bottom: 1px solid #f3f0e5;
    margin: 0.35rem 0;
}
.roster-cell {
    font-size: 0.92rem;
    color: var(--ink);
    display: flex;
    align-items: center;
    height: 36px;
}
.roster-cell.roster-name {
    font-weight: 600;
}
.roster-cell.roster-email a {
    color: var(--ink);
    text-decoration: underline;
    text-decoration-color: var(--line);
    text-underline-offset: 3px;
    font-size: 0.88rem;
}
.roster-cell.roster-role {
    font-size: 0.88rem;
    color: #4c4842;
}
.roster-current-tag {
    height: 36px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f4f0e6;
    border: 1px solid var(--line);
    border-radius: 9px;
    font-size: 0.82rem;
    color: var(--muted);
    font-weight: 500;
    box-sizing: border-box;
}
.st-key-people_table_card [data-testid="stButton"] button,
.st-key-admin_people_table [data-testid="stButton"] button {
    height: 36px !important;
    min-height: 36px !important;
    padding: 0 0.8rem !important;
    font-size: 0.84rem !important;
    border-radius: 9px !important;
    line-height: 36px !important;
}

/* ---------- composer card ---------- */
.st-key-composer [data-testid="stForm"],
.st-key-auth-form [data-testid="stForm"] {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 20px !important;
    padding: 1rem 1.2rem 0.8rem !important;
    box-shadow: 0 1px 2px rgba(34, 32, 28, 0.03), 0 18px 40px -30px rgba(34, 32, 28, 0.5);
}
.st-key-composer [data-testid="stForm"] [data-testid="stTextInputRootElement"],
.st-key-auth-form [data-testid="stForm"] [data-testid="stTextInputRootElement"] {
    background: transparent !important; border: none !important; box-shadow: none !important;
}
.st-key-composer [data-testid="stForm"] .stTextInput,
.st-key-auth-form [data-testid="stForm"] .stTextInput { border-bottom: 1px solid var(--line); }
.st-key-composer [data-testid="stForm"] .stTextInput input,
.st-key-auth-form [data-testid="stForm"] .stTextInput input {
    font-size: 1.02rem !important; padding: 0.45rem 0.1rem !important; background: transparent !important;
}
.st-key-composer [data-testid="stForm"] input::placeholder,
.st-key-auth-form [data-testid="stForm"] input::placeholder { color: #a8a29a !important; }
.st-key-composer [data-testid="stForm"] [data-testid="InputInstructions"],
.st-key-auth-form [data-testid="stForm"] [data-testid="InputInstructions"] { display: none !important; }
.composer-hint { color: var(--muted); font-size: 0.75rem; line-height: 1.35; }

/* ---------- what-if chat ---------- */
.chat-preview { color: var(--muted); font-size: 0.72rem; line-height: 1.4; margin: 0.1rem 0 0.55rem; }
.chat-log {
    display: flex; flex-direction: column; gap: 0.45rem;
    max-height: 260px; overflow-y: auto; padding-right: 0.15rem;
}
.chat-row { display: flex; }
.chat-row.me { justify-content: flex-end; }
.chat-bubble {
    max-width: 88%; border-radius: 14px; padding: 0.5rem 0.7rem;
    font-size: 0.84rem; line-height: 1.45; background: var(--sand); color: var(--ink);
}
.chat-row.me .chat-bubble { background: var(--accent-soft); color: #6d3520; border-bottom-right-radius: 5px; }
.chat-row.ai .chat-bubble { border-bottom-left-radius: 5px; }
[class*="st-key-panel_whatif"] [data-testid="stForm"] {
    background: transparent !important; border: none !important; box-shadow: none !important;
    border-top: 1px solid var(--line) !important; border-radius: 0 !important;
    padding: 0.55rem 0 0 !important; margin-top: 0.65rem;
}
[class*="st-key-panel_whatif"] [data-testid="stForm"] [data-testid="stTextInputRootElement"] {
    background: var(--canvas) !important; border: 1px solid var(--line) !important;
    border-radius: 10px !important; box-shadow: none !important;
}
[class*="st-key-panel_whatif"] [data-testid="stForm"] .stTextInput input {
    font-size: 0.86rem !important; padding: 0.3rem 0.5rem !important; background: transparent !important;
}
[class*="st-key-panel_whatif"] [data-testid="stForm"] input::placeholder { color: #a8a29a !important; }
[class*="st-key-panel_whatif"] [data-testid="stForm"] [data-testid="InputInstructions"] { display: none !important; }
[class*="st-key-panel_whatif"] [data-testid="stBaseButton-primaryFormSubmit"] {
    border-radius: 10px !important; padding: 0.35rem 0.6rem !important; min-height: 2.1rem;
}

/* ---------- buttons ---------- */
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--accent) !important; border: 1px solid var(--accent) !important;
    color: #fff !important; border-radius: 12px !important; font-weight: 500 !important;
    padding: 0.45rem 1rem !important; min-height: 2.4rem;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--accent-dark) !important; border-color: var(--accent-dark) !important; }
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p { color: #fff !important; }

[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"] {
    background: var(--panel) !important; border: 1px solid var(--line) !important;
    color: var(--ink) !important; border-radius: 12px !important;
    font-weight: 450 !important; padding: 0.4rem 0.9rem !important;
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover { background: #fdfcf9 !important; border-color: #d5d0c1 !important; }
[data-testid="stBaseButton-secondary"]:disabled,
[data-testid="stBaseButton-secondaryFormSubmit"]:disabled {
    background: var(--accent-soft) !important; border-color: var(--accent-soft) !important;
}
[data-testid="stBaseButton-secondary"]:disabled p,
[data-testid="stBaseButton-secondaryFormSubmit"]:disabled p { color: #8a3f26 !important; }

/* ---------- alerts, expanders, bordered containers ---------- */
[data-testid="stAlert"] { border: 1px solid var(--line) !important; border-radius: 14px !important; box-shadow: none !important; }
[data-testid="stAlert"] > div, [data-testid="stAlert"] [data-baseweb="notification"] { border-radius: 14px !important; }
[data-testid="stAlertContainer"] { border-radius: 14px !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) { background: #edf1e4 !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) { background: #eef1f3 !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background: #f9eddf !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) { background: #f7e4de !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] span { color: var(--ink) !important; }
[data-testid="stExpander"] { border-radius: 14px !important; border-color: var(--line) !important; background: var(--panel) !important; }
[class*="st-key-card_"], [class*="st-key-panel_"] {
    border-color: var(--line) !important; border-radius: 18px !important;
    background: var(--panel) !important; padding: 0.95rem 1.1rem !important;
}
[class*="st-key-card_"]:hover { border-color: #d8d3c4 !important; }

/* ---------- Project cards (Home, Workbench quick-select) ---------- */
[class*="st-key-pcard_"] {
    border-color: var(--line) !important;
    border-radius: 18px !important;
    background: var(--panel) !important;
    margin-bottom: 0.65rem !important;
    transition: border-color 0.15s ease;
}
[class*="st-key-pcard_"]:hover {
    border-color: #d8d3c4 !important;
}
[class*="st-key-pcard_"],
[class*="st-key-pcard_"] [data-testid="stVerticalBlockBorderWrapper"] {
    min-height: 112px !important;
    padding: 1.25rem 1.45rem !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}
[class*="st-key-pcard_"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    height: 100% !important;
    min-height: 100% !important;
}
[class*="st-key-pcard_"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}
[class*="st-key-pcard_"] [data-testid="column"]:first-child,
[class*="st-key-pcard_"] .stColumn:first-child {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}
.project-info-block {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    text-align: left;
    height: 100%;
}

/* Hide Streamlit header hover link icons */
[data-testid="stHeaderActionElements"],
a.anchor-link,
.anchor-link {
    display: none !important;
}

/* ---------- hero ---------- */
.st-key-hero, .st-key-auth-hero { text-align: center !important; padding: 0.8rem 0 0.2rem; }
.hero-eyebrow {
    font-family: "Segoe UI", -apple-system, sans-serif !important;
    font-size: 0.7rem !important; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--muted) !important; margin-bottom: 0.9rem; text-align: center !important;
}
.hero-title, h1.hero-title {
    font-family: SERIF_PLACEHOLDER !important;
    font-size: 2.5rem !important; line-height: 1.15 !important; font-weight: 400 !important;
    letter-spacing: -0.02em !important; margin: 0 0 0.7rem !important;
    color: var(--ink) !important; text-align: center !important;
}
.hero-sub {
    color: var(--muted) !important; font-size: 1rem !important; line-height: 1.55 !important;
    max-width: 32rem; margin: 0 auto !important; text-align: center !important;
}

/* ---------- suggestion chips ---------- */
.st-key-chips { max-width: 720px; margin: 0 auto; }
.chips-label { text-align: center; color: var(--muted); font-size: 0.76rem; margin: 0.9rem 0 0.3rem; }
.st-key-chips [data-testid="stBaseButton-secondary"] {
    width: 100%; border-radius: 999px !important; background: transparent !important;
    font-size: 0.84rem !important; font-weight: 400 !important; padding: 0.28rem 0.4rem !important; min-height: 2.1rem;
}
.st-key-chips [data-testid="stBaseButton-secondary"]:hover { background: var(--panel) !important; }

/* ---------- sections + project cards ---------- */
.st-key-composer { max-width: 720px; margin: 0 auto; }
.section-row { display: flex; align-items: baseline; justify-content: space-between; margin: 2.6rem 0 0.9rem; }
.section-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--ink);
}
.section-count { color: var(--muted); font-size: 0.78rem; }
.card-title { font-size: 0.98rem; font-weight: 600; margin-bottom: 0.2rem; }
.card-desc { color: #4c4842; font-size: 0.87rem; line-height: 1.45; margin-bottom: 0.45rem; }
.card-meta { color: var(--muted); font-size: 0.74rem; }
.card-badge {
    display: inline-block; background: var(--accent-soft); color: #8a3f26;
    border-radius: 999px; padding: 0.08rem 0.48rem; font-size: 0.65rem;
    margin-left: 0.45rem; vertical-align: middle; font-weight: 500;
}
.empty-state {
    border: 1px dashed var(--line); border-radius: 18px; background: #fdfcf8;
    padding: 2rem 1.25rem; text-align: center; color: var(--muted);
    font-size: 0.9rem; line-height: 1.5;
}

/* ---------- project workbench ---------- */
.st-key-wb-head { padding: 0 0 0.5rem; }
.wb-eyebrow {
    font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.55rem;
}
h1.wb-title {
    font-family: SERIF_PLACEHOLDER !important; font-size: 2.05rem !important;
    font-weight: 400 !important; letter-spacing: -0.02em !important;
    margin: 0 0 0.35rem !important; color: var(--ink) !important;
}
.wb-sub {
    color: var(--muted); font-size: 0.95rem; line-height: 1.5;
    max-width: 36rem; margin: 0 0 0.7rem;
}
.wb-disclaimer {
    color: var(--muted); font-size: 0.8rem; line-height: 1.45;
    border-left: 2px solid var(--accent); padding-left: 0.55rem; margin-top: 0.3rem;
}
[class*="st-key-panel_"] { padding: 1.05rem 1.2rem 1.1rem !important; }
.panel-label {
    font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.2rem;
}
.panel-title {
    font-family: SERIF_PLACEHOLDER !important; font-size: 1.15rem !important;
    color: var(--ink); line-height: 1.3; margin-bottom: 0.35rem;
}
.panel-note { color: var(--muted); font-size: 0.78rem; line-height: 1.45; margin-top: 0.5rem; }
.f-table {
    width: 100%; border-collapse: separate; border-spacing: 0;
    margin: 0.8rem 0 0.5rem; font-variant-numeric: tabular-nums;
    border-radius: 12px; overflow: hidden; border: 1px solid var(--line);
    background: #ffffff;
}
.f-table th {
    background: #f8f6f0; font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--muted); font-weight: 600; padding: 0.65rem 0.85rem; border-bottom: 1px solid var(--line);
    text-align: left;
}
.f-table td {
    font-size: 0.88rem; color: var(--ink); padding: 0.6rem 0.85rem;
    border-bottom: 1px solid #f1eee4;
}
.f-table tr:hover td { background: #faf9f5; }
.f-table tr:last-child td { border-bottom: none; }
.f-table .num { text-align: right; }
.f-table tfoot td {
    background: #f8f6f0; font-weight: 600; border-top: 2px solid var(--line);
    border-bottom: none; padding: 0.65rem 0.85rem;
}
.cat-tag {
    display: inline-block; font-size: 0.65rem; background: var(--sand);
    border: 1px solid var(--line); border-radius: 6px; padding: 0.08rem 0.4rem;
    color: var(--muted); font-weight: 500;
}
.share-bar-wrap {
    display: flex; align-items: center; justify-content: flex-end; gap: 0.55rem;
}
.share-bar-bg {
    width: 55px; height: 6px; background: #eeebe1; border-radius: 999px; overflow: hidden;
}
.share-bar-fill {
    height: 100%; background: var(--accent); border-radius: 999px;
}
.ing-local { display: block; color: var(--muted); font-size: 0.74rem; margin-top: 0.1rem; }
.conf {
    font-size: 0.62rem; border-radius: 999px; padding: 0.08rem 0.44rem;
    border: 1px solid var(--line); color: var(--muted); white-space: nowrap;
    display: inline-flex; align-items: center; vertical-align: middle;
}
.conf-verified { background: #edf1e4; color: #3f5230; border-color: #dfe6d2; }
.conf-estimated { background: #f9eddf; color: #8a5a2b; border-color: #f0e0c9; }
.conf-review { background: #f9eddf; color: #8a5a2b; border-color: #f0e0c9; }
.conf-flagged { background: #f7e4de; color: #8a3f26; border-color: #f0d3c8; }
.cl-verdict { margin: 0.15rem 0 0.5rem; }
.cl-item { padding: 0.45rem 0; border-bottom: 1px solid #f1eee4; }
.cl-item:last-child { border-bottom: none; }
.cl-head { display: flex; justify-content: space-between; align-items: baseline; gap: 0.4rem; }
.cl-name { font-size: 0.85rem; color: var(--ink); }
.cl-why { color: var(--muted); font-size: 0.74rem; line-height: 1.45; margin-top: 0.15rem; }
.cl-swap { color: #8a5a2b; font-size: 0.74rem; line-height: 1.45; margin-top: 0.15rem; }
.stat-row {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 0.42rem 0; border-bottom: 1px solid #f1eee4;
}
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #4c4842; font-size: 0.86rem; }
.stat-value { font-size: 0.95rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.stat-unit { color: var(--muted); font-weight: 400; font-size: 0.78rem; margin-left: 0.18rem; }
.cost-big {
    font-family: SERIF_PLACEHOLDER !important; font-size: 2.05rem !important;
    line-height: 1.15; margin: 0.1rem 0 0.25rem; color: var(--ink);
}
.cost-unit { font-family: "Segoe UI", -apple-system, sans-serif; font-size: 0.85rem; color: var(--muted); margin-left: 0.25rem; }
.cost-delta {
    display: inline-block; background: #edf1e4; color: #3f5230;
    border-radius: 999px; padding: 0.1rem 0.55rem; font-size: 0.72rem;
}
.cost-delta.up { background: #f9eddf; color: #8a5a2b; }
.cost-line {
    display: flex; justify-content: space-between; font-size: 0.84rem; color: #4c4842;
    padding: 0.32rem 0; border-top: 1px solid #f1eee4; margin-top: 0.55rem;
}

/* ---------- Workbench 2-Pane & Chat Redesign ---------- */
.st-key-panel_chat {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: 0 1px 3px rgba(34, 32, 28, 0.04) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    min-height: 640px !important;
}

.st-key-panel_spec {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    padding: 1.2rem 1.5rem !important;
    box-shadow: 0 1px 3px rgba(34, 32, 28, 0.04) !important;
    min-height: 640px !important;
}

.chat-header {
    margin-bottom: 0.6rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--line);
}

.chat-log {
    max-height: 520px;
    min-height: 420px;
    overflow-y: auto;
    padding: 0.6rem 0.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    scrollbar-width: thin;
}

.chat-row {
    display: flex;
    width: 100%;
}
.chat-row.ai {
    justify-content: flex-start;
}
.chat-row.me {
    justify-content: flex-end;
}

.chat-row.ai .chat-bubble {
    background: #f4f1e6;
    border: 1px solid #e7e2d2;
    border-radius: 14px 14px 14px 4px;
    padding: 0.75rem 1rem;
    color: var(--ink);
    font-size: 0.9rem;
    line-height: 1.5;
    max-width: 90%;
}

.chat-row.me .chat-bubble {
    background: var(--accent);
    color: #fff;
    border-radius: 14px 14px 4px 14px;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
    line-height: 1.5;
    max-width: 86%;
    box-shadow: 0 2px 6px rgba(194, 96, 60, 0.22);
}

.chat-chips-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin: 0.8rem 0 0.4rem;
}

/* Quick KPI Strip on top of Right Pane */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.kpi-card {
    background: #fbf9f4;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 0.65rem 0.8rem;
}
.kpi-label {
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 500;
}
.kpi-value {
    font-family: SERIF_PLACEHOLDER;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0.12rem 0 0.08rem;
}
.kpi-note {
    font-size: 0.73rem;
    color: #635f56;
}

/* Right pane tabs styling */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.2rem;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
    padding: 0.4rem 0.85rem !important;
    font-size: 0.88rem !important;
    color: var(--muted) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--ink) !important;
    font-weight: 600 !important;
}

/* Reserve the scrollbar gutter: expanding a card must not shift the page sideways. */
html { scrollbar-gutter: stable; }
[data-testid="stMain"] { scrollbar-gutter: stable; }
[data-testid="stSidebar"] { scrollbar-gutter: auto !important; }

/* ---------- entrance motion ---------- */
@keyframes rise-in {
    from { opacity: 0; transform: translate3d(0, 10px, 0); }
    to { opacity: 1; transform: translate3d(0, 0, 0); }
}

.st-key-hero,
.st-key-auth-hero,
.st-key-composer,
.st-key-chips,
.st-key-wb-head,
.st-key-wb_head,
h1.wb-title,
.wb-title,
.wb-eyebrow,
.wb-sub,
.wb-disclaimer,
.st-key-people_head,
[class*="st-key-stat_"],
.st-key-people_table_card,
.st-key-auth-form,
.st-key-auth-demo,
[class*="st-key-admin_"],
[class*="st-key-card_"],
[class*="st-key-panel_"],
[data-testid="stMarkdownContainer"]:has(.section-row),
[data-testid="stMarkdownContainer"]:has(.empty-state),
[data-testid="stAlert"] {
    animation: rise-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

/* stagger so the page settles from the top down instead of all at once */
.st-key-wb-head, .st-key-wb_head { animation-delay: 10ms; }
.wb-eyebrow { animation-delay: 20ms; }
h1.wb-title, .wb-title { animation-delay: 50ms; }
.wb-sub { animation-delay: 90ms; }
.wb-disclaimer { animation-delay: 130ms; }
.st-key-people_head { animation-delay: 20ms; }
.st-key-stat_members, [class*="st-key-stat_"]:nth-child(1) { animation-delay: 60ms; }
.st-key-stat_admins, [class*="st-key-stat_"]:nth-child(2) { animation-delay: 100ms; }
.st-key-stat_workers, [class*="st-key-stat_"]:nth-child(3) { animation-delay: 140ms; }
.st-key-people_table_card { animation-delay: 180ms; }
.st-key-composer { animation-delay: 50ms; }
.st-key-chips { animation-delay: 110ms; }
.st-key-auth-form { animation-delay: 70ms; }
.st-key-auth-demo { animation-delay: 130ms; }
.st-key-admin_head,
.st-key-admin_add,
.st-key-admin_people,
.st-key-admin_access { animation-duration: 0.35s; }
.st-key-admin_head { animation-delay: 0ms; }
.st-key-admin_add { animation-delay: 50ms; }
.st-key-admin_people { animation-delay: 100ms; }
.st-key-admin_access { animation-delay: 150ms; }
[data-testid="stMarkdownContainer"]:has(.section-row) { animation-delay: 140ms; }
[class*="st-key-card_"] { animation-delay: 180ms; }
.st-key-panel_formulation { animation-delay: 50ms; }
.st-key-panel_nutrition { animation-delay: 90ms; }
.st-key-panel_whatif { animation-delay: 130ms; }
.st-key-panel_cost { animation-delay: 170ms; }
.st-key-panel_clean { animation-delay: 250ms; }
[data-testid="stAlert"] { animation-duration: 0.3s; }

@media (prefers-reduced-motion: reduce) {
    .st-key-hero,
    .st-key-auth-hero,
    .st-key-composer,
    .st-key-chips,
    .st-key-wb-head,
    .st-key-auth-form,
    .st-key-auth-demo,
    [class*="st-key-admin_"],
    [class*="st-key-card_"],
    [class*="st-key-panel_"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stAlert"] {
        animation: none !important;
    }
}

/* ---------- sign in ---------- */
.st-key-auth-form, .st-key-auth-demo { max-width: 430px; margin-left: auto !important; margin-right: auto !important; }
.st-key-auth-form { margin-top: 1.6rem !important; }
.st-key-auth-demo { margin-top: 0.9rem !important; }
</style>
""".replace("SERIF_PLACEHOLDER", SERIF)


def apply_theme() -> None:
    """Inject the shared stylesheet. Call once, right after set_page_config."""
    st.markdown(CSS, unsafe_allow_html=True)


def esc(value: str) -> str:
    """Escape text that is placed inside the small HTML snippets."""
    return html.escape(value or "")
