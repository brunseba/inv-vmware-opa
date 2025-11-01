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
    
    def navigate_to_page(self, page_name: str):
        """Navigate to a specific dashboard page."""
        try:
            # Find and click the navigation button
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for button in buttons:
                if page_name.lower() in button.text.lower():
                    button.click()
                    time.sleep(2)  # Wait for page to load
                    return True
            print(f"⚠ Navigation button for '{page_name}' not found")
            return False
        except Exception as e:
            print(f"⚠ Error navigating to page: {e}")
            return False
    
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
    
    def capture_dashboard_tour(self):
        """Capture a complete tour of the dashboard."""
        pages = [
            "Overview",
            "Data Explorer",
            "Advanced Explorer",
            "Analytics",
            "Resources",
            "Infrastructure",
            "Folder Analysis",
        ]
        
        print("\n📸 Starting dashboard tour...")
        
        for page in pages:
            print(f"\n📄 Capturing: {page}")
            
            # Navigate to page
            if self.navigate_to_page(page):
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
