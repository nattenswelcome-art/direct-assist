from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import asyncio
from utils.logger import get_logger

logger = get_logger("parser_service")

class ParserService:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    async def fetch_text(self, url: str, max_chars: int = 4000) -> str:
        """
        Fetches the URL using Selenium (headless) and extracts visible text.
        """
        if not url.startswith("http"):
            url = "https://" + url
            
        logger.info(f"Fetching URL with Selenium: {url}")
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.options)
            
            # Stealth maneuvering
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            # Allow some time for JS/redirects
            time.sleep(5)
            
            # Save screenshot for debugging
            driver.save_screenshot("debug_last_page.png")
            
            # Check title for common blockers
            title = driver.title.lower()
            logger.info(f"Page Title: {driver.title}")
            
            if "captcha" in title or "access denied" in title or "robot" in title or "security" in title:
                logger.warning(f"Blocking detected in title: {title}")
                return None
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts, styles, etc.
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'noscript', 'iframe', 'svg']):
                element.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Simple cleaning
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = ' '.join(lines)
            
            # Limit length
            if len(cleaned_text) > max_chars:
                cleaned_text = cleaned_text[:max_chars] + "..."
                
            logger.info(f"Extracted {len(cleaned_text)} chars")
            
            # Detection checks
            if len(cleaned_text) < 200 or "captcha" in cleaned_text.lower():
                logger.warning("Extracted text seems to be a CAPTCHA or empty.")
                # We return None to trigger the manual fallback in logic
                return None
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Selenium Parsing error: {e}")
            return None
        finally:
            if driver:
                driver.quit()

parser_service = ParserService()
