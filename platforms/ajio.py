"""
AJIO Extractor
==============
Optimized selectors and logic for AJIO platform
"""

from urllib.parse import urlparse, urljoin
from typing import List, Optional
from .base import BaseExtractor


class AjioExtractor(BaseExtractor):
    """AJIO-specific product extractor."""
    
    def canonical_ajio_link(self, href: str, base: str) -> Optional[str]:
        """Return canonical AJIO product link if valid, else None."""
        if not href:
            return None
        if href.startswith("/"):
            href = urljoin(base, href)
        
        # AJIO product URLs typically have pattern like /brand-product-name/p/product-id
        if "/p/" in href and "ajio.com" in href:
            return href.split("?")[0]  # Remove query parameters
        return None
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get AJIO product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        for h in hrefs:
            can = self.canonical_ajio_link(h, page.url)
            if can and can not in seen:
                seen.add(can)
                urls.append(can)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from AJIO product page."""
        
        # Product URL - canonical link or current URL
        product_url = page.url
        
        # Try canonical first
        try:
            canonical = await page.get_attribute('link[rel="canonical"]', 'href')
            if canonical:
                product_url = canonical
        except:
            pass

        # Title - AJIO uses h1 for product title
        title = await self.first_text(page, [
            "h1",  # Primary title selector for AJIO
            ".pdp-product-name",
            ".product-title", 
            ".product-name"
        ])
        
        # Also try meta og:title as fallback
        if not title:
            try:
                title = await page.get_attribute('meta[property="og:title"]', 'content')
                # Clean up the title from meta tag
                if title and " by " in title and " Online | Ajio.com" in title:
                    title = title.split(" by ")[0].replace("Buy ", "")
            except:
                pass

        # Price - AJIO shows prices in elements containing ₹
        price = None
        
        # Look for the selling price (not MRP)
        try:
            # Find all elements with ₹ and get the actual selling price
            price_elements = await page.locator("text=₹").all()
            for elem in price_elements:
                try:
                    text = await elem.inner_text()
                    # Skip MRP, get the actual price
                    if "MRP" not in text and text.startswith("₹") and len(text) < 15:
                        price = text.strip()
                        break
                except:
                    continue
        except:
            pass
        
        # Fallback price selectors
        if not price:
            price = await self.first_text(page, [
                ".pdp-price",
                ".price-current",
                ".current-price", 
                ".price",
                ".rupee"
            ])

        # Seller name - AJIO typically shows brand name
        seller_name = None
        
        # Try to extract brand from title or meta data
        try:
            page_title = await page.title()
            if " by " in page_title:
                seller_name = page_title.split(" by ")[1].split(" Online")[0].strip()
        except:
            pass
        
        # Fallback seller selectors
        if not seller_name:
            seller_name = await self.first_text(page, [
                ".brand-name", 
                ".pdp-brand",
                ".supplier-name",
                "[data-testid*='brand']"
            ])

        # Manufacturer name - extract from specific AJIO product details section
        manufacturer_name = None
        
        # Wait a bit for dynamic content to load
        try:
            await page.wait_for_timeout(2000)  # Wait 2 seconds for content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to trigger loading
            await page.wait_for_timeout(1000)  # Wait another second
        except:
            pass
        
        # Method 1: Try to find "Manufactured By" in product list
        try:
            # Wait for prod-list to appear
            await page.wait_for_selector("ul.prod-list", timeout=5000)
            li_elements = await page.locator("ul.prod-list li").all()
            
            for li in li_elements:
                li_text = await li.inner_text()
                if "Manufactured By" in li_text:
                    if ":" in li_text:
                        manufacturer_part = li_text.split(":", 1)[1].strip()
                        # Extract company name (before address details like "No.")
                        if "No." in manufacturer_part:
                            manufacturer_name = manufacturer_part.split("No.")[0].strip()
                        elif "Pvt" in manufacturer_part:
                            # Handle "Pvt Ltd" case
                            manufacturer_name = manufacturer_part.split("Pvt")[0].strip() + " Pvt"
                        else:
                            manufacturer_name = manufacturer_part
                        break
        except:
            pass
        
        # Method 2: Try specific CSS selector (your original one)
        if not manufacturer_name:
            try:
                css_selectors = [
                    "ul[class='prod-list'] li:nth-child(5)",  # Manufactured By is usually in 5th li
                    "ul[class='prod-list'] li:nth-child(6)",  # Fallback to 6th
                    "ul[class='prod-list'] li:nth-child(4)"   # Sometimes in 4th
                ]
                
                for selector in css_selectors:
                    css_element = page.locator(selector)
                    if await css_element.count() > 0:
                        css_text = await css_element.first.inner_text()
                        if "Manufactured By" in css_text and ":" in css_text:
                            manufacturer_part = css_text.split(":", 1)[1].strip()
                            if "No." in manufacturer_part:
                                manufacturer_name = manufacturer_part.split("No.")[0].strip()
                            elif "Pvt" in manufacturer_part:
                                manufacturer_name = manufacturer_part.split("Pvt")[0].strip() + " Pvt"
                            else:
                                manufacturer_name = manufacturer_part
                            break
            except:
                pass
        
        # Method 3: XPath fallback for any element containing "Manufactured By"
        if not manufacturer_name:
            try:
                manufactured_elements = await page.locator("text=Manufactured By").all()
                if manufactured_elements:
                    for elem in manufactured_elements:
                        # Try to get the next sibling or parent content
                        parent = elem.locator("..")
                        parent_text = await parent.inner_text()
                        if ":" in parent_text:
                            manufacturer_part = parent_text.split(":", 1)[1].strip()
                            if "No." in manufacturer_part:
                                manufacturer_name = manufacturer_part.split("No.")[0].strip()
                                break
            except:
                pass
        
        # Final cleanup and validation
        if manufacturer_name:
            manufacturer_name = manufacturer_name.strip()
            # Remove any unwanted prefixes/suffixes
            if manufacturer_name.startswith(":"):
                manufacturer_name = manufacturer_name[1:].strip()
            # If it looks like JavaScript or contains weird characters, discard it
            if any(x in manufacturer_name.lower() for x in ['window', '__env__', 'javascript', 'function', 'undefined']):
                manufacturer_name = None
            # If too short, likely not a real manufacturer name
            if manufacturer_name and len(manufacturer_name) < 3:
                manufacturer_name = None
        
        # Fallback to seller name if manufacturer not found or invalid
        if not manufacturer_name or len(manufacturer_name.strip()) == 0:
            manufacturer_name = seller_name

        # Image URL - try OG image first, then other selectors
        image_url = None
        
        # Try og:image first
        try:
            image_url = await page.get_attribute('meta[property="og:image"]', 'content')
        except:
            pass
        
        # Fallback to other image selectors
        if not image_url:
            image_url = await self.get_image_url(page, [
                ".pdp-image img",
                ".product-image img",
                ".main-image img",
                ".hero-image img", 
                ".gallery img",
                "img[data-testid*='product-image']",
                "img[alt*='product']"
            ])

        return {
            "product_url": product_url,
            "title": title,
            "price": price,
            "seller_name": seller_name,
            "manufacturer_name": manufacturer_name,
            "image_url": image_url
        }
