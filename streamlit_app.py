from __future__ import annotations

from build_streamlit_html_dashboard import build_dashboard_html

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Social Farm Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_shell_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stHeader"],
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }

        .block-container {
            max-width: none;
            padding: 0;
        }

        iframe {
            border: 0;
            border-radius: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_shell_styles()
    html = build_dashboard_html()
    components.html(html, height=4600, scrolling=True)


if __name__ == "__main__":
    main()
