"""Theme management utilities for dark mode support."""

import streamlit as st
from typing import Dict, Any
from .state import StateManager, SessionKeys


class ThemeManager:
    """Manage application theme and provide theme-aware styling."""
    
    # Color palettes for light and dark themes
    THEMES = {
        "light": {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f0f2f6",
            "bg_card": "#ffffff",
            "text_primary": "#262730",
            "text_secondary": "#808495",
            "accent_color": "#1f77b4",
            "accent_hover": "#1565c0",
            "border_color": "#e0e0e0",
            "success_color": "#28a745",
            "warning_color": "#ffc107",
            "error_color": "#dc3545",
            "info_color": "#17a2b8",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "hover_bg": "#e8e8e8",
        },
        "dark": {
            "bg_primary": "#0e1117",
            "bg_secondary": "#262730",
            "bg_card": "#1e1e1e",
            "text_primary": "#fafafa",
            "text_secondary": "#a3a8b4",
            "accent_color": "#4da6ff",
            "accent_hover": "#66b3ff",
            "border_color": "#3d3d3d",
            "success_color": "#4caf50",
            "warning_color": "#ff9800",
            "error_color": "#f44336",
            "info_color": "#2196f3",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "hover_bg": "#3a3a3a",
        }
    }
    
    @staticmethod
    def get_current_theme() -> str:
        """Get current theme name.
        
        Returns:
            Theme name ('light' or 'dark')
        """
        return StateManager.get(SessionKeys.THEME, "light")
    
    @staticmethod
    def set_theme(theme: str):
        """Set application theme.
        
        Args:
            theme: Theme name ('light' or 'dark')
        """
        if theme in ThemeManager.THEMES:
            StateManager.set(SessionKeys.THEME, theme)
        else:
            raise ValueError(f"Invalid theme: {theme}")
    
    @staticmethod
    def toggle_theme():
        """Toggle between light and dark themes."""
        current = ThemeManager.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        ThemeManager.set_theme(new_theme)
    
    @staticmethod
    def get_colors() -> Dict[str, str]:
        """Get color palette for current theme.
        
        Returns:
            Dictionary of color values
        """
        theme = ThemeManager.get_current_theme()
        return ThemeManager.THEMES[theme]
    
    @staticmethod
    def get_color(key: str) -> str:
        """Get specific color from current theme.
        
        Args:
            key: Color key (e.g., 'bg_primary', 'text_primary')
            
        Returns:
            Color value as hex or rgba string
        """
        colors = ThemeManager.get_colors()
        return colors.get(key, "#000000")
    
    @staticmethod
    def apply_global_styles():
        """Apply theme-aware global CSS styles."""
        theme = ThemeManager.get_current_theme()
        colors = ThemeManager.THEMES[theme]
        
        st.markdown(f"""
        <style>
            /* CSS Variables for current theme */
            :root {{
                --bg-primary: {colors['bg_primary']};
                --bg-secondary: {colors['bg_secondary']};
                --bg-card: {colors['bg_card']};
                --text-primary: {colors['text_primary']};
                --text-secondary: {colors['text_secondary']};
                --accent-color: {colors['accent_color']};
                --accent-hover: {colors['accent_hover']};
                --border-color: {colors['border_color']};
                --success-color: {colors['success_color']};
                --warning-color: {colors['warning_color']};
                --error-color: {colors['error_color']};
                --info-color: {colors['info_color']};
                --shadow: {colors['shadow']};
                --hover-bg: {colors['hover_bg']};
            }}
            
            /* Global overrides */
            .stApp {{
                background-color: var(--bg-primary);
                color: var(--text-primary);
            }}
            
            [data-testid="stSidebar"] {{
                background-color: var(--bg-secondary);
            }}
            
            /* Headers */
            .main-header {{
                font-size: 2.5rem;
                font-weight: bold;
                color: var(--accent-color);
                margin-bottom: 1rem;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: var(--text-primary);
            }}
            
            /* Cards and containers */
            .metric-card {{
                background-color: var(--bg-card);
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px var(--shadow);
                border: 1px solid var(--border-color);
            }}
            
            /* Dataframes */
            [data-testid="stDataFrame"] {{
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
            }}
            
            /* Buttons */
            .stButton > button {{
                border: 1px solid var(--border-color);
                background-color: var(--bg-card);
                color: var(--text-primary);
            }}
            
            .stButton > button:hover {{
                background-color: var(--hover-bg);
                border-color: var(--accent-color);
            }}
            
            /* Expanders */
            [data-testid="stExpander"] {{
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
            }}
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {{
                background-color: var(--bg-secondary);
            }}
            
            .stTabs [data-baseweb="tab"] {{
                color: var(--text-secondary);
            }}
            
            .stTabs [aria-selected="true"] {{
                color: var(--accent-color);
                border-bottom-color: var(--accent-color);
            }}
            
            /* Metrics */
            [data-testid="stMetricValue"] {{
                color: var(--text-primary);
            }}
            
            [data-testid="stMetricLabel"] {{
                color: var(--text-secondary);
            }}
            
            /* Status messages */
            .element-container .stSuccess {{
                background-color: var(--success-color);
            }}
            
            .element-container .stWarning {{
                background-color: var(--warning-color);
            }}
            
            .element-container .stError {{
                background-color: var(--error-color);
            }}
            
            .element-container .stInfo {{
                background-color: var(--info-color);
            }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def get_chart_theme() -> Dict[str, Any]:
        """Get Plotly/Altair chart theme configuration.
        
        Returns:
            Dictionary with chart theme settings
        """
        theme = ThemeManager.get_current_theme()
        colors = ThemeManager.THEMES[theme]
        
        if theme == "dark":
            return {
                "layout": {
                    "paper_bgcolor": colors['bg_card'],
                    "plot_bgcolor": colors['bg_card'],
                    "font": {"color": colors['text_primary']},
                    "xaxis": {
                        "gridcolor": colors['border_color'],
                        "zerolinecolor": colors['border_color'],
                    },
                    "yaxis": {
                        "gridcolor": colors['border_color'],
                        "zerolinecolor": colors['border_color'],
                    },
                }
            }
        else:
            return {
                "layout": {
                    "paper_bgcolor": colors['bg_card'],
                    "plot_bgcolor": colors['bg_card'],
                    "font": {"color": colors['text_primary']},
                }
            }
    
    @staticmethod
    def get_pygwalker_theme() -> str:
        """Get PyGWalker theme name.
        
        Returns:
            'dark' or 'light'
        """
        return ThemeManager.get_current_theme()
    
    @staticmethod
    def show_theme_toggle(location: str = "sidebar"):
        """Render theme toggle button.
        
        Args:
            location: Where to render ('sidebar' or 'main')
        """
        current_theme = ThemeManager.get_current_theme()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Theme**")
        with col2:
            theme_icon = "🌙" if current_theme == "light" else "☀️"
            if st.button(theme_icon, key=f"theme_toggle_{location}", help="Toggle dark/light mode"):
                ThemeManager.toggle_theme()
                st.rerun()
