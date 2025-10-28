"""Help utilities for contextual help bubbles and tooltips."""

import streamlit as st


def help_bubble(help_text: str, key: str = None):
    """
    Display a help bubble icon with tooltip.
    
    Args:
        help_text: The help text to display in the tooltip
        key: Unique key for the help component (optional)
    """
    st.markdown(
        f"""
        <span style="cursor: help; color: #4472C4; font-weight: bold;" 
              title="{help_text}">ⓘ</span>
        """,
        unsafe_allow_html=True
    )


def help_info(title: str, content: str):
    """
    Display an info box with help content.
    
    Args:
        title: Title of the help section
        content: Help content (markdown supported)
    """
    st.info(f"**{title}**\n\n{content}")


def help_expander(title: str, content: str, expanded: bool = False):
    """
    Display help content in an expander.
    
    Args:
        title: Title of the expander
        content: Help content (markdown supported)
        expanded: Whether to show expanded by default
    """
    with st.expander(f"ℹ️ {title}", expanded=expanded):
        st.markdown(content)


def metric_with_help(label: str, value: str, help_text: str, delta=None):
    """
    Display a metric with inline help tooltip.
    
    Args:
        label: Metric label
        value: Metric value
        help_text: Help text for tooltip
        delta: Optional delta value
    """
    col1, col2 = st.columns([0.95, 0.05])
    with col1:
        st.metric(label=label, value=value, delta=delta, help=help_text)
    with col2:
        st.markdown(
            f'<div style="margin-top: 20px;" title="{help_text}">ⓘ</div>',
            unsafe_allow_html=True
        )


def section_help(help_text: str):
    """
    Display a small help icon next to a section header.
    
    Args:
        help_text: The help text to display
    """
    st.markdown(
        f'<span style="color: #888; font-size: 0.9em; margin-left: 10px;" '
        f'title="{help_text}">ⓘ Help</span>',
        unsafe_allow_html=True
    )
