#!/usr/bin/env python3
"""
Screenshot automation tool for VMware Inventory Dashboard documentation.

This script uses Selenium to capture screenshots of the dashboard in both
light and dark modes for documentation purposes.

Usage:
    python tools/screenshot_dashboard.py --url http://localhost:8501 --output docs/images

Requirements:
    pip install selenium webdriver-manager pillow
"""

import argparse
import io
import time
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image


@dataclass
class Screenshot:
    """Screenshot configuration."""
    name: str
    path: str
    wait_selector: str = "[data-testid='stApp']"
    wait_time: int = 2
    width: int = 1920
    height: int = 1080
    scroll_to: str = None
    click_elements: List[str] = None


class DashboardScreenshotter:
    """Automated screenshot capture for Streamlit dashboard."""
    
    def __init__(self, base_url: str, output_dir: Path, headless: bool = True):
        """
        Initialize the screenshotter.
        
        Args:
            base_url: Dashboard URL (e.g., http://localhost:8501)
            output_dir: Directory to save screenshots
            headless: Run browser in headless mode
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        # Enable software rendering for WebGL in headless mode
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--enable-webgl")
        self.chrome_options.add_argument("--ignore-gpu-blocklist")
        self.chrome_options.add_argument("--enable-unsafe-swiftshader")  # Software WebGL
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable automation detection
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
    
    def start_browser(self):
        """Start the Chrome browser."""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        self.driver.set_window_size(1920, 1080)
        print(f"✓ Browser started")
    
    def stop_browser(self):
        """Stop the Chrome browser."""
        if self.driver:
            self.driver.quit()
            print(f"✓ Browser stopped")
    
    def wait_for_streamlit(self, timeout: int = 10):
        """Wait for Streamlit app to be ready."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stApp']"))
            )
            # Additional wait for content to render
            time.sleep(2)
            return True
        except Exception as e:
            print(f"⚠ Timeout waiting for Streamlit: {e}")
            return False
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        try:
            # Look for theme toggle button (moon/sun emoji)
            # This assumes the button has specific text or is identifiable
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if "theme" in button.get_attribute("key") or button.text in ["🌙", "☀️"]:
                    button.click()
                    time.sleep(1)  # Wait for theme transition
                    return True
            print("⚠ Theme toggle button not found")
            return False
        except Exception as e:
            print(f"⚠ Error toggling theme: {e}")
            return False
    
    def navigate_to_page(self, page_name: str, use_uri: bool = True):
        """Navigate to a specific dashboard page.
        
        Args:
            page_name: Name of the page (e.g., "Data Explorer")
            use_uri: If True, use direct URI navigation (faster and more reliable)
        """
        if use_uri:
            # Use direct URI navigation based on API-ENDPOINTS.md
            return self.navigate_to_page_uri(page_name)
        
        # Fallback to UI button navigation
        try:
            # First, try to find and expand any collapsed expanders
            expanders = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stExpander']")
            for expander in expanders:
                try:
                    # Check if expander is collapsed by looking for the summary element
                    summary = expander.find_element(By.TAG_NAME, "summary")
                    # Try to click it to expand (if already expanded, this is harmless)
                    summary.click()
                    time.sleep(0.5)  # Brief wait for expansion animation
                except:
                    pass  # Expander might already be expanded or not clickable
            
            # Now find and click the navigation button
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if page_name.lower() in button.text.lower():
                    try:
                        # Check if button is visible and clickable
                        if not button.is_displayed():
                            continue
                        
                        # Scroll to button to ensure it's in viewport
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                        time.sleep(0.5)
                        
                        # Try JavaScript click if regular click fails
                        try:
                            button.click()
                        except Exception:
                            # Fallback to JavaScript click
                            self.driver.execute_script("arguments[0].click();", button)
                        
                        time.sleep(2)  # Wait for page to load
                        return True
                    except Exception as click_error:
                        # Try next matching button
                        continue
            
            print(f"⚠ Navigation button for '{page_name}' not found")
            return False
        except Exception as e:
            print(f"⚠ Error navigating to page: {e}")
            return False
    
    def navigate_to_page_uri(self, page_name: str) -> bool:
        """Navigate to page using direct URI (based on API-ENDPOINTS.md).
        
        This is faster and more reliable than clicking through the UI.
        
        Args:
            page_name: Name of the page (e.g., "Data Explorer")
            
        Returns:
            True if navigation succeeded, False otherwise
        """
        try:
            # Convert page name to URI format (spaces to underscores)
            page_param = page_name.replace(" ", "_")
            
            # Build URI
            page_uri = f"{self.base_url}/?page={page_param}"
            
            # Navigate directly
            self.driver.get(page_uri)
            
            # Wait for Streamlit to load
            if self.wait_for_streamlit(timeout=10):
                print(f"✓ Navigated to {page_name} via URI")
                return True
            else:
                print(f"⚠ Failed to load {page_name} via URI")
                return False
                
        except Exception as e:
            print(f"⚠ Error navigating to {page_name} via URI: {e}")
            return False
    
    @staticmethod
    def get_all_pages_from_api_endpoints() -> List[Tuple[str, str]]:
        """Get all 20 pages from API-ENDPOINTS.md documentation.
        
        Returns:
            List of (page_name, uri) tuples
        """
        pages = [
            # Main Navigation (1 page)
            "Overview",
            # Explore & Analyze (7 pages)
            "Data Explorer",
            "Advanced Explorer",
            "VM Explorer",
            "VM Search",
            "Analytics",
            "Comparison",
            "Data Quality",
            # Infrastructure (4 pages)
            "Resources",
            "Infrastructure",
            "Folder Analysis",
            "Folder Labelling",
            # Migration (4 pages)
            "Migration Targets",
            "Strategy Configuration",
            "Migration Planning",
            "Migration Scenarios",
            # Management (2 pages)
            "Data Import",
            "Database Backup",
            # Export & Help (2 pages)
            "PDF Export",
            "Help",  # Maps to "Documentation" page
        ]
        
        # Convert to (name, uri_param) tuples
        return [(page, page.replace(" ", "_")) for page in pages]
    
    def capture_screenshot(self, filename: str, full_page: bool = False) -> Path:
        """
        Capture a screenshot.
        
        Args:
            filename: Output filename (without extension)
            full_page: Capture full page (requires scrolling)
            
        Returns:
            Path to saved screenshot
        """
        output_path = self.output_dir / f"{filename}.png"
        
        if full_page:
            # Get full page dimensions
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Capture screenshots while scrolling
            screenshots = []
            scroll_position = 0
            
            while scroll_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                time.sleep(0.5)
                
                screenshot = self.driver.get_screenshot_as_png()
                screenshots.append(Image.open(io.BytesIO(screenshot)))
                
                scroll_position += viewport_height
            
            # Stitch screenshots together
            total_width = screenshots[0].width
            final_image = Image.new('RGB', (total_width, total_height))
            
            y_offset = 0
            for img in screenshots:
                final_image.paste(img, (0, y_offset))
                y_offset += img.height
            
            final_image.save(output_path)
        else:
            # Simple screenshot
            self.driver.save_screenshot(str(output_path))
        
        print(f"✓ Screenshot saved: {output_path}")
        return output_path
    
    def capture_page_screenshots(self, page_name: str, themes: List[str] = ["light", "dark"]):
        """
        Capture screenshots of a page in multiple themes.
        
        Args:
            page_name: Name of the page to capture
            themes: List of themes to capture (light, dark)
        """
        for theme in themes:
            if theme == "dark":
                self.toggle_theme()
            
            filename = f"{page_name.lower().replace(' ', '_')}_{theme}"
            self.capture_screenshot(filename)
    
    def capture_dashboard_tour(self, use_uri: bool = True):
        """Capture a complete tour of the dashboard.
        
        Captures all 20 pages from API-ENDPOINTS.md documentation.
        
        Args:
            use_uri: If True, use direct URI navigation (faster and more reliable)
        """
        # Get all 20 pages from API-ENDPOINTS.md
        pages = [name for name, _ in self.get_all_pages_from_api_endpoints()]
        
        print("\n📸 Starting dashboard tour...")
        print(f"   Pages: {len(pages)} total (from API-ENDPOINTS.md)")
        print(f"   Navigation method: {'Direct URI' if use_uri else 'UI buttons'}")
        
        for page in pages:
            print(f"\n📄 Capturing: {page}")
            
            # Navigate to page
            if self.navigate_to_page(page, use_uri=use_uri):
                # Capture in light mode
                self.capture_screenshot(f"{page.lower().replace(' ', '_')}_light")
                
                # Toggle to dark mode
                if self.toggle_theme():
                    time.sleep(1)
                    self.capture_screenshot(f"{page.lower().replace(' ', '_')}_dark")
                    
                    # Toggle back to light mode
                    self.toggle_theme()
                    time.sleep(1)
            else:
                print(f"⚠ Skipping {page} - navigation failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Capture dashboard screenshots for documentation")
    parser.add_argument(
        "--url",
        default="http://localhost:8501",
        help="Dashboard URL (default: http://localhost:8501)"
    )
    parser.add_argument(
        "--output",
        default="docs/images/screenshots",
        help="Output directory (default: docs/images/screenshots)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run in headless mode (default: True)"
    )
    parser.add_argument(
        "--page",
        help="Specific page to capture (default: all pages)"
    )
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "both"],
        default="both",
        help="Theme to capture (default: both)"
    )
    
    args = parser.parse_args()
    
    print("🚀 VMware Dashboard Screenshot Tool")
    print(f"📍 URL: {args.url}")
    print(f"📁 Output: {args.output}")
    print(f"🌙 Theme: {args.theme}")
    print()
    
    screenshotter = DashboardScreenshotter(
        base_url=args.url,
        output_dir=Path(args.output),
        headless=args.headless
    )
    
    try:
        screenshotter.start_browser()
        
        # Navigate to dashboard
        screenshotter.driver.get(args.url)
        
        if not screenshotter.wait_for_streamlit():
            print("❌ Failed to load dashboard")
            return 1
        
        print("✓ Dashboard loaded")
        
        # Capture screenshots
        if args.page:
            # Single page
            themes = ["both"] if args.theme == "both" else [args.theme]
            screenshotter.capture_page_screenshots(args.page, themes)
        else:
            # Full tour
            screenshotter.capture_dashboard_tour()
        
        print("\n✅ Screenshot capture complete!")
        print(f"📁 Screenshots saved to: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        screenshotter.stop_browser()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
