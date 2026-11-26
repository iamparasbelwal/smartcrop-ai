"""Shared look and feel for SmartCrop.AI.

One place for the warm, assistant-style styling: off-white canvas, near-black
ink, a single brick accent, thin borders, serif display headings, lots of air.
The palette itself lives in `.streamlit/config.toml` so Streamlit's own widgets
follow it; this file handles shapes, spacing and typography accents.
"""

from __future__ import annotations

import html
import time

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

/* Hide internal subpages from sidebar navigation */
a[data-testid="stSidebarNavLink"][href*="Project_access"],
a[data-testid="stSidebarNavLink"][href*="project_access"] {
    display: none !important;
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
.st-key-people_layout,
.st-key-access_layout {
    max-width: 940px !important;
    margin: 0 auto !important;
}

/* Wide full-canvas layout for Lab admin utilizing leftover space */
.st-key-admin_layout {
    max-width: 100% !important;
    padding: 0.6rem 2.2rem 2.5rem 2.2rem !important;
    box-sizing: border-box !important;
}
.st-key-verify_layout,
.st-key-audit_layout {
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
.st-key-admin_people_table,
.st-key-verify_table_card,
.st-key-audit_table_card {
    margin-top: 1.1rem !important;
    padding: 1.4rem 1.6rem !important;
}
.st-key-people_table_card .panel-title,
.st-key-admin_people_table .panel-title,
.st-key-verify_table_card .panel-title,
.st-key-audit_table_card .panel-title {
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
.roster-cell.num {
    justify-content: flex-end;
    font-variant-numeric: tabular-nums;
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
.st-key-admin_people_table [data-testid="stButton"] button,
.st-key-verify_table_card [data-testid="stButton"] button,
.st-key-audit_table_card [data-testid="stButton"] button {
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
.st-key-auth-form [data-testid="stForm"] [data-testid="InputInstructions"],
.st-key-panel_chat [data-testid="stForm"] [data-testid="InputInstructions"] { display: none !important; }
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
.st-key-panel_chat,
.st-key-panel_spec {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 18px !important;
    padding: 1.25rem 1.45rem !important;
    box-shadow: 0 1px 3px rgba(34, 32, 28, 0.04) !important;
    min-height: clamp(600px, 72vh, 760px) !important;
}
.st-key-panel_chat {
    display: flex !important;
    flex-direction: column !important;
    gap: 0.55rem !important;
}
.st-key-panel_chat > [data-testid="stVerticalBlock"],
.st-key-panel_chat [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    gap: 0.55rem !important;
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
}
.st-key-panel_chat [data-testid="stElementContainer"]:has(.chat-log),
.st-key-panel_chat .element-container:has(.chat-log),
.st-key-panel_chat [data-testid="stEmpty"]:has(.chat-log) {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 280px !important;
}
.st-key-panel_chat [data-testid="stElementContainer"]:has(.chat-log) > div,
.st-key-panel_chat .element-container:has(.chat-log) > div {
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
}
.st-key-panel_chat [data-testid="stHorizontalBlock"] {
    align-items: center !important;
}
.st-key-panel_chat [data-testid="stForm"] {
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background: transparent !important;
}
.st-key-panel_chat [data-testid="stForm"] [data-testid="stTextInputRootElement"] {
    min-height: 2.5rem !important;
    height: 2.5rem !important;
    border-radius: 11px !important;
    border: 1px solid var(--line) !important;
    background: #faf8f2 !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
}
.st-key-panel_chat [data-testid="stForm"] [data-testid="stTextInputRootElement"] input {
    font-size: 0.9rem !important;
    padding: 0.35rem 0.8rem !important;
    line-height: 1.35 !important;
}
.st-key-panel_chat [data-testid="stForm"] [data-testid="stTextInputRootElement"]:focus-within {
    border-color: var(--accent) !important;
    background: #ffffff !important;
}
.st-key-panel_chat [data-testid="stForm"] [data-testid="stBaseButton-primaryFormSubmit"] {
    min-height: 2.5rem !important;
    height: 2.5rem !important;
    border-radius: 11px !important;
    padding: 0 1rem !important;
}

.chat-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.6rem;
    margin-bottom: 0.6rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--line);
}
.chat-header {
    margin-bottom: 0.6rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--line);
}
.chat-header-rule {
    border-bottom: 1px solid var(--line);
    margin: 0.45rem 0 0.35rem !important;
}
.st-key-workbench_model {
    max-width: 230px !important;
    width: 100% !important;
    margin-left: auto !important;
}
.st-key-workbench_model [data-baseweb="select"] > div {
    min-height: 1.95rem !important;
    background: var(--sand) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    font-size: 0.78rem !important;
    color: var(--ink) !important;
    box-shadow: none !important;
}
.st-key-workbench_model [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent) !important;
}
.chat-engine-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 0.3rem;
}
.chat-engine {
    display: inline-block;
    flex-shrink: 0;
    font-size: 0.6rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b665c;
    background: var(--sand);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 0.12rem 0.5rem;
    white-space: nowrap;
}
.chat-meta {
    display: block;
    margin-top: 0.4rem;
    padding-top: 0.35rem;
    border-top: 1px solid rgba(34, 32, 28, 0.08);
    font-size: 0.6rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #857f73;
}
.chat-row:last-child { animation: rise-in 0.3s cubic-bezier(0.22, 1, 0.36, 1) both; }
.ai-note {
    margin-top: 0.75rem;
    padding: 0.7rem 0.85rem;
    background: #fbf3ee;
    border: 1px solid #f0dcd1;
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    color: #4c4842;
    font-size: 0.84rem;
    line-height: 1.55;
}
.ai-note .ai-note-label {
    display: block;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8a5a2b;
    margin-bottom: 0.25rem;
}

.chat-log {
    flex: 1 1 auto;
    height: clamp(320px, 48vh, 560px);
    min-height: 280px;
    overflow-y: auto;
    overscroll-behavior: contain;
    scroll-behavior: smooth;
    padding: 0.45rem 0.35rem 0.45rem 0.15rem;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    scrollbar-width: thin;
}
.chat-log::-webkit-scrollbar { width: 6px; }
.chat-log::-webkit-scrollbar-thumb { background: #e0dbcb; border-radius: 999px; }
.chat-log:empty { display: none; }

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
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    line-height: 1.25;
    margin: 0.25rem 0 0.2rem !important;
}
.chat-row.ai .chat-bubble,
.chat-row.me .chat-bubble { overflow-wrap: anywhere; word-break: break-word; white-space: normal; }

/* Claude-style inline thinking & GIF status row inside chat stream */
.ai-status-row {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.25rem 0.15rem 0.35rem;
    color: var(--muted);
    font-size: 0.86rem;
    animation: rise-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.ai-status-gif {
    width: 24px;
    height: 24px;
    object-fit: contain;
    flex-shrink: 0;
    background: transparent !important;
}
.ai-status-text {
    color: #5b564d;
    font-weight: 500;
}
.ai-status-chevron {
    color: #9b9487;
    font-size: 1rem;
    line-height: 1;
    margin-left: 0.05rem;
}
.ai-thought-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    max-width: 90%;
    gap: 0.35rem;
}
.ai-thought-wrap .chat-bubble {
    max-width: 100% !important;
}
details.ai-thought {
    width: 100%;
    font-size: 0.82rem;
    color: var(--muted);
}
details.ai-thought summary {
    list-style: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.18rem 0.25rem;
    color: #6b655b;
    font-weight: 500;
    user-select: none;
}
details.ai-thought summary::-webkit-details-marker { display: none; }
details.ai-thought summary:hover { color: var(--ink); }
details.ai-thought[open] summary .ai-status-chevron {
    transform: rotate(90deg);
    display: inline-block;
}
.ai-thought-dots {
    display: inline-flex;
    align-items: center;
    gap: 2px;
}
.ai-thought-dots i {
    display: inline-block;
    width: 3.5px;
    height: 3.5px;
    border-radius: 50%;
    background: var(--accent);
}
.ai-thought-body {
    margin: 0.25rem 0 0.35rem 0.2rem;
    padding: 0.6rem 0.8rem;
    background: #fbf9f4;
    border: 1px solid var(--line);
    border-left: 2px solid #d8cfc0;
    border-radius: 10px;
    font-size: 0.8rem;
    line-height: 1.5;
    color: #59544b;
}

/* Narrow screens: the two workbench columns stack and the chat keeps a readable height. */
@media (max-width: 900px) {
    .chat-log { height: clamp(260px, 40vh, 460px); }
    .st-key-panel_chat, .st-key-panel_spec { min-height: 0 !important; }
    .chat-row.ai .chat-bubble { max-width: 96%; }
    .chat-row.me .chat-bubble { max-width: 92%; }
    .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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

/* Empty formulation skeleton wireframe */
.skel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.05rem;
}
.skel-actions { display: flex; gap: 0.45rem; }
.skel-btn-ghost {
    width: 62px;
    height: 30px;
    border-radius: 8px;
    border: 1px dashed var(--line);
    background: #fbf9f4;
}
.skel-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.7rem;
    margin-bottom: 1.15rem;
}
.skel-kpi-card {
    background: #fbf9f4;
    border: 1px dashed var(--line);
    border-radius: 12px;
    padding: 0.65rem 0.8rem;
}
@keyframes skel-shimmer {
    0% { background-position: 180% 0; }
    100% { background-position: -80% 0; }
}
.skel-bar {
    background: linear-gradient(90deg, #eae6da 25%, #f4f1e8 50%, #eae6da 75%);
    background-size: 220% 100%;
    animation: skel-shimmer 1.5s ease-in-out infinite;
    border-radius: 6px;
}
.st-key-page_skel_host {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    min-height: 0 !important;
}
.st-key-page_skel_host:not(:has(.skel-page)) {
    display: none !important;
}
.skel-page {
    display: flex;
    flex-direction: column;
    gap: 1.05rem;
}
.skel-page-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    padding-bottom: 0.25rem;
}
.skel-page-head-left {
    flex: 1 1 auto;
    min-width: 0;
}
.skel-page-head-actions {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    flex-shrink: 0;
}
.skel-hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 0.9rem 0 0.5rem;
}
.skel-search-row {
    display: grid;
    grid-template-columns: 3.5fr 1.2fr;
    gap: 0.9rem;
    align-items: center;
}
.skel-input-ghost {
    height: 42px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--panel);
    padding: 0 0.9rem;
    display: flex;
    align-items: center;
}
.skel-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
}
.skel-pcard {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.25rem 1.45rem;
    min-height: 112px;
    display: grid;
    grid-template-columns: 3.8fr 1.4fr;
    gap: 1.2rem;
    align-items: center;
}
.skel-kpi-3 {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.9rem;
}
.skel-kpi-4 {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.9rem;
}
.skel-stat-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.05rem 1.25rem;
    height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.skel-filter-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.85rem;
    margin-bottom: 0.3rem;
}
.skel-table-line {
    display: grid;
    gap: 0.9rem;
    align-items: center;
    padding: 0.72rem 0.15rem;
    border-bottom: 1px solid #f1eee4;
}
.skel-table-line:last-child { border-bottom: none; }
.skel-auth-wrap {
    max-width: 430px;
    width: 100%;
    margin: 0.5rem auto 0;
}
@media (max-width: 900px) {
    .skel-kpi-3, .skel-kpi-4, .skel-filter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .skel-pcard, .skel-search-row { grid-template-columns: 1fr; }
}
.skel-val { width: 58%; height: 20px; margin: 0.4rem 0 0.35rem; }
.skel-sub { width: 76%; height: 9px; opacity: 0.7; }
.skel-tab-bar {
    display: flex;
    gap: 1.1rem;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.55rem;
    margin-bottom: 0.75rem;
}
.skel-tab {
    font-size: 0.84rem;
    color: #a19b8e;
    font-weight: 500;
}
.skel-tab.active {
    color: var(--muted);
    font-weight: 600;
    border-bottom: 2px solid var(--line);
    padding-bottom: 0.55rem;
    margin-bottom: -0.62rem;
}
.skel-table-head {
    display: grid;
    grid-template-columns: 2.3fr 1.1fr 1.3fr 0.9fr;
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9e988c;
    padding: 0.35rem 0.2rem 0.55rem;
    border-bottom: 1px solid var(--line);
}
.skel-row {
    display: grid;
    grid-template-columns: 2.3fr 1.1fr 1.3fr 0.9fr;
    align-items: center;
    padding: 0.72rem 0.2rem;
    border-bottom: 1px solid #f3f0e5;
}
.skel-empty-note {
    margin-top: 1.25rem;
    padding: 1rem 1.15rem;
    background: #fbf9f4;
    border: 1px dashed var(--line);
    border-radius: 12px;
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.55;
    text-align: center;
}
.skel-empty-note strong { color: var(--ink); font-weight: 600; }

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
.st-key-access_head,
.st-key-verify_head,
.st-key-audit_head,
.st-key-access_layout [data-testid="stExpander"],
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
.st-key-access_head { animation-delay: 20ms; }
.st-key-verify_head { animation-delay: 20ms; }
.st-key-audit_head { animation-delay: 20ms; }
.st-key-access_layout [data-testid="stExpander"] { animation-duration: 0.35s; }
.st-key-access_layout [data-testid="stExpander"]:nth-of-type(1) { animation-delay: 60ms; }
.st-key-access_layout [data-testid="stExpander"]:nth-of-type(2) { animation-delay: 110ms; }
.st-key-access_layout [data-testid="stExpander"]:nth-of-type(3) { animation-delay: 160ms; }
.st-key-access_layout [data-testid="stExpander"]:nth-of-type(4) { animation-delay: 210ms; }
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
    .st-key-verify_head,
    .st-key-audit_head,
    [class*="st-key-admin_"],
    [class*="st-key-card_"],
    [class*="st-key-panel_"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stAlert"] {
        animation: none !important;
    }
}

/* ---------- sign in ---------- */
.st-key-auth_split {
    max-width: 1120px !important;
    margin: 1.5rem auto 0 !important;
}
.st-key-auth_welcome_card {
    background: var(--sand) !important;
    border: 2px solid #d5cfc0 !important;
    border-radius: 22px !important;
    padding: 3rem 2.7rem !important;
    box-shadow: 0 1px 2px rgba(34, 32, 28, 0.03), 0 18px 40px -30px rgba(34, 32, 28, 0.45) !important;
    min-height: 520px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}
.auth-left-eyebrow {
    text-align: left !important;
    margin-bottom: 0.9rem !important;
}
h1.auth-left-title {
    text-align: left !important;
    margin: 0 0 0.85rem !important;
}
p.auth-left-sub {
    text-align: left !important;
    margin: 0 !important;
    max-width: 31rem !important;
}
.st-key-auth-form, .st-key-auth-demo {
    max-width: 470px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: 0 !important;
}
.st-key-auth-form { margin-top: 0 !important; }
.st-key-auth-demo { margin-top: 0.9rem !important; }
.st-key-auth-demo [data-testid="stBaseButton-secondary"] {
    font-size: 0.8rem !important;
    padding: 0.35rem 0.5rem !important;
    white-space: nowrap !important;
}
@media (max-width: 900px) {
    .st-key-auth_welcome_card { min-height: 0 !important; padding: 1.8rem !important; }
    .st-key-auth-form, .st-key-auth-demo { max-width: none !important; margin-left: 0 !important; }
}
</style>
""".replace("SERIF_PLACEHOLDER", SERIF)


def apply_theme() -> None:
    """Inject the shared stylesheet. Call once, right after set_page_config."""
    st.markdown(CSS, unsafe_allow_html=True)


def esc(value: str) -> str:
    """Escape text that is placed inside the small HTML snippets."""
    return html.escape(value or "")


def autoscroll(selector: str = ".chat-log") -> None:
    """Keep the chat pinned to its newest message without a rerun."""
    import streamlit.components.v1 as components

    components.html(
        "<script>"
        "const box = window.parent.document.querySelector('" + selector + "');"
        "if (box) { box.scrollTop = box.scrollHeight; }"
        "</script>",
        height=0,
    )


def ai_note(text: str, label: str = "Gemini") -> str:
    """A tinted callout for a model-written paragraph."""
    return (
        f'<div class="ai-note"><span class="ai-note-label">{esc(label)}</span>{esc(text)}</div>'
    )


def loading_gif_base64() -> str:
    """Return the base64-encoded string of the loading biscuit flask GIF."""
    import base64
    from pathlib import Path
    gif_path = Path(__file__).resolve().parent / "assets" / "loading_biscuit_flask.gif"
    if gif_path.exists():
        return base64.b64encode(gif_path.read_bytes()).decode("utf-8")
    return ""


def status_html(text: str = "Searching private crop database") -> str:
    """Claude-style inline progress row with transparent biscuit-in-flask GIF."""
    b64 = loading_gif_base64()
    icon = (
        f'<img src="data:image/gif;base64,{b64}" class="ai-status-gif" alt="" />'
        if b64
        else '<span class="ai-thought-dots"><i></i><i></i><i></i></span>'
    )
    return (
        f'<div class="ai-status-row">'
        f"{icon}"
        f'<span class="ai-status-text">{esc(text)}</span>'
        f'<span class="ai-status-chevron">&rsaquo;</span>'
        f"</div>"
    )


def spinner_html(text: str = "Formulating...") -> str:
    """Return HTML snippet for a centered loading animation with the custom GIF."""
    b64 = loading_gif_base64()
    if not b64:
        return f'<div style="text-align: center; color: var(--muted); padding: 1.5rem;">{esc(text)}</div>'
    return (
        f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem 0; gap: 0.65rem;">'
        f'<img src="data:image/gif;base64,{b64}" width="64" height="64" alt="Loading..." style="display: block; background: transparent;" />'
        f'<div style="font-size: 0.86rem; color: var(--muted); font-weight: 500; letter-spacing: 0.02em;">{esc(text)}</div>'
        f'</div>'
    )


def _skel_bar(width: str, height: int = 12, style: str = "") -> str:
    extra = f"; {style}" if style else ""
    return f'<div class="skel-bar" style="width: {width}; height: {height}px{extra};"></div>'


def _skel_page_head(action_widths: tuple[int, ...] = (140,)) -> str:
    actions = "".join(
        f'<div class="skel-btn-ghost" style="width: {w}px; height: 38px; border-radius: 11px;"></div>'
        for w in action_widths
    )
    return (
        '<div class="skel-page-head">'
        '<div class="skel-page-head-left">'
        + _skel_bar("170px", 10, "margin-bottom: 0.55rem")
        + _skel_bar("260px", 30, "margin-bottom: 0.55rem")
        + _skel_bar("62%", 12)
        + '</div>'
        + (f'<div class="skel-page-head-actions">{actions}</div>' if actions else "")
        + '</div>'
    )


def _skel_kpi_row(count: int = 3) -> str:
    cls = "skel-kpi-4" if count == 4 else "skel-kpi-3"
    cards = "".join(
        '<div class="skel-stat-card">'
        + _skel_bar("52%", 10)
        + _skel_bar("34%", 24, "margin: 0.55rem 0 0.45rem")
        + _skel_bar("68%", 10, "opacity: 0.75")
        + '</div>'
        for _ in range(count)
    )
    return f'<div class="{cls}">{cards}</div>'


def _skel_table_card(col_widths: tuple[str, ...], rows: int = 5, *, with_badge: bool = True) -> str:
    template = " ".join("1.2fr" if i else "2fr" for i in range(len(col_widths)))
    head_cells = "".join(_skel_bar(w, 10, "opacity: 0.75") for w in col_widths)
    body_rows = ""
    for r in range(rows):
        cells = "".join(
            _skel_bar("72%" if idx == 0 else ("64%" if r % 2 == 0 else "52%"), 13 if idx == 0 else 11)
            for idx in range(len(col_widths))
        )
        body_rows += f'<div class="skel-table-line" style="grid-template-columns: {template};">{cells}</div>'
    badge_html = '<div class="skel-btn-ghost" style="width: 78px; height: 24px; border-radius: 999px;"></div>' if with_badge else ""
    return (
        '<div class="skel-card">'
        '<div class="skel-head" style="margin-bottom: 0.85rem;">'
        '<div>'
        + _skel_bar("180px", 18, "margin-bottom: 0.45rem")
        + _skel_bar("300px", 10, "opacity: 0.8")
        + '</div>'
        + badge_html
        + '</div>'
        f'<div class="skel-table-line" style="grid-template-columns: {template}; border-bottom: 1px solid var(--line);">{head_cells}</div>'
        + body_rows
        + '</div>'
    )


def _skel_project_cards(count: int = 3) -> str:
    widths = ("46%", "38%", "52%")
    cards = ""
    for i in range(count):
        cards += (
            '<div class="skel-pcard">'
            '<div>'
            '<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.55rem;">'
            + _skel_bar(widths[i % len(widths)], 16)
            + '<div class="skel-btn-ghost" style="width: 84px; height: 20px; border-radius: 999px;"></div>'
            + '</div>'
            + _skel_bar("78%", 11, "margin-bottom: 0.45rem; opacity: 0.85")
            + _skel_bar("44%", 10, "opacity: 0.65")
            + '</div>'
            '<div class="skel-btn-ghost" style="width: 100%; height: 38px; border-radius: 12px;"></div>'
            '</div>'
        )
    return cards


def page_skeleton_html(page_key: str) -> str:
    """Layout-matched skeleton loading wireframe for each SmartCrop.AI page."""
    if page_key == "auth":
        inner = (
            '<div style="max-width: 1120px; margin: 1.5rem auto 0; display: grid; grid-template-columns: 1.12fr 1fr; gap: 1.5rem; align-items: center;">'
            '<div class="skel-card" style="background: var(--sand); border: 2px solid #d5cfc0; border-radius: 22px; padding: 3rem 2.7rem; min-height: 520px; display: flex; flex-direction: column; justify-content: center;">'
            + _skel_bar("110px", 10, "margin-bottom: 0.9rem")
            + _skel_bar("220px", 34, "margin-bottom: 0.85rem")
            + _skel_bar("88%", 13, "margin-bottom: 0.45rem")
            + _skel_bar("68%", 13)
            + '</div>'
            '<div style="max-width: 470px; width: 100%; margin-left: auto; display: flex; flex-direction: column; gap: 0.9rem;">'
            '<div class="skel-card" style="padding: 1.2rem;">'
            + _skel_bar("100%", 38, "margin-bottom: 0.8rem")
            + _skel_bar("100%", 38, "margin-bottom: 0.9rem")
            + '<div class="skel-btn-ghost" style="width: 100%; height: 40px; border-radius: 12px;"></div>'
            + '</div>'
            '<div class="skel-card" style="padding: 1.15rem 1.4rem;">'
            + _skel_bar("130px", 14, "margin-bottom: 0.8rem")
            + _skel_bar("100%", 90, "opacity: 0.65")
            + '</div></div></div>'
        )
    elif page_key == "home":
        inner = (
            '<div class="skel-hero">'
            + _skel_bar("150px", 10, "margin-bottom: 0.9rem")
            + _skel_bar("290px", 36, "margin-bottom: 0.7rem")
            + _skel_bar("410px", 13)
            + '</div>'
            '<div class="skel-search-row">'
            '<div class="skel-input-ghost">' + _skel_bar("45%", 12) + '</div>'
            '<div class="skel-btn-ghost" style="width: 100%; height: 42px; border-radius: 12px;"></div>'
            '</div>'
            '<div class="skel-page-head" style="padding: 0.4rem 0 0;">'
            + _skel_bar("200px", 20)
            + _skel_bar("180px", 11, "opacity: 0.75")
            + '</div>'
            + _skel_project_cards(3)
        )
    elif page_key == "people":
        inner = (
            _skel_page_head((150,))
            + _skel_kpi_row(3)
            + _skel_table_card(("55%", "65%", "45%", "45%", "50%"), rows=4, with_badge=False)
        )
    elif page_key == "admin":
        inner = (
            _skel_page_head((125, 195))
            + _skel_table_card(("55%", "65%", "45%", "45%", "55%"), rows=4, with_badge=True)
        )
    elif page_key == "access":
        cards = "".join(
            '<div class="skel-card" style="padding: 1rem 1.25rem;">'
            + _skel_bar("48%", 15, "margin-bottom: 0.7rem")
            + _skel_bar("82%", 11, "margin-bottom: 0.45rem; opacity: 0.75")
            + _skel_bar("74%", 11, "opacity: 0.65")
            + '</div>'
            for _ in range(3)
        )
        inner = _skel_page_head((150,)) + cards
    elif page_key == "verify":
        filters = (
            '<div class="skel-filter-grid">'
            + "".join('<div class="skel-input-ghost">' + _skel_bar("60%", 11) + '</div>' for _ in range(4))
            + '</div>'
        )
        inner = (
            _skel_page_head((120,))
            + _skel_kpi_row(4)
            + filters
            + _skel_table_card(("60%", "48%", "40%", "40%", "40%", "48%", "48%", "45%"), rows=6, with_badge=True)
        )
    else:  # audit
        filters = (
            '<div class="skel-filter-grid">'
            + "".join('<div class="skel-input-ghost">' + _skel_bar("60%", 11) + '</div>' for _ in range(4))
            + '</div>'
        )
        inner = (
            _skel_page_head((150,))
            + _skel_kpi_row(3)
            + filters
            + _skel_table_card(("45%", "55%", "70%", "45%", "60%", "35%"), rows=6, with_badge=True)
        )
    return f'<div class="skel-page" aria-busy="true">{inner}</div>'


def empty_skeleton_card_html(title: str, subtitle: str, *, rows: int = 3, card_mode: bool = False) -> str:
    """Dashed wireframe placeholder paired with an empty/filtered message."""
    if card_mode:
        ghosts = "".join(
            '<div class="skel-kpi-card" style="margin-bottom: 0.65rem;">'
            + _skel_bar("38%", 14, "margin-bottom: 0.45rem")
            + _skel_bar("68%", 10, "opacity: 0.7")
            + '</div>'
            for _ in range(rows)
        )
    else:
        ghosts = "".join(
            '<div class="skel-table-line" style="grid-template-columns: 2fr 1.2fr 1.2fr 1fr;">'
            + _skel_bar(w, 12)
            + _skel_bar("55%", 10, "opacity: 0.7")
            + _skel_bar("60%", 10, "opacity: 0.7")
            + _skel_bar("48%", 10, "opacity: 0.6")
            + '</div>'
            for w in ("72%", "58%", "66%")[:rows]
        )
    return (
        f'{ghosts}'
        '<div class="skel-empty-note">'
        f'<strong>{esc(title)}</strong><br>{esc(subtitle)}'
        '</div>'
    )


def mark_active_page(page_key: str) -> None:
    """Record the active page key so navigating away and back triggers skeleton loading cleanly."""
    st.session_state["_active_page"] = page_key


def show_page_skeleton(page_key: str, delay: float = 0.35) -> None:
    """Render a layout-matched skeleton loading shimmer once per page navigation."""
    if st.session_state.get("_active_page") == page_key:
        return
    st.session_state["_active_page"] = page_key
    with st.container(key="page_skel_host"):
        slot = st.empty()
        slot.markdown(page_skeleton_html(page_key), unsafe_allow_html=True)
        time.sleep(delay)
        slot.empty()
