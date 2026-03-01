import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def scrape_url(url: str) -> str:
    """Fetches a URL using a headless browser and extracts the main text content."""
    if not url.startswith("http"):
        url = "https://" + url

    logger.info(f"WebSearch: Scraping URL - {url}")
    
    try:
        async with async_playwright() as p:
            # Launch chromium headlessly
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Go to URL, wait until network is mostly idle
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Get the fully rendered HTML
            html_content = await page.content()
            await browser.close()
            
            # Parse with BeautifulSoup to strip HTML tags and scripts
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script, style, and navigation elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
                
            text = soup.get_text(separator="\n", strip=True)
            
            # Truncate to avoid exploding context windows (e.g. max ~10,000 chars)
            if len(text) > 15000:
                text = text[:15000] + "\n...[Content Truncated]..."
                
            return text

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return f"Failed to scrape {url}. Error: {str(e)}"
