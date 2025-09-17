"""
Flipkart Extractor
==================
Optimized selectors and logic for Flipkart platform
"""

from typing import List
from .base import BaseExtractor


class FlipkartExtractor(BaseExtractor):
    """Flipkart-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Flipkart product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        patterns = ["/p/", "/product/"]
        
        for h in hrefs:
            if any(pat in h for pat in patterns) and h not in seen:
                seen.add(h)
                urls.append(h)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Flipkart product page."""
        # Title (updated selectors)
        title = await self.first_text(page, [
            "span.VU-ZEz", "span.B_NuCI", "h1.yhB1nd", ".B_NuCI", 
            "span[data-automation-id='product-title']",
            "h1._6EBuvT", "span._35KyD6"
        ])

        # Price (updated selectors for new Flipkart layout)
        price = await self.first_text(page, [
            "div.Nx9bqj.CxhGGd", "._30jeq3._16Jk6d", "._30jeq3", 
            ".Nx9bqj", "._1_WHN1", ".CEmiEU", "._16Jk6d",
            "div._25b18c span", "div._30jeq3"
        ])

        # Seller (updated selectors)
        seller = await self.first_text(page, [
            "div#sellerName span", "._3l0lbp", "._2b4iJl a",
            "div._2A6eBh span", "div._3dqZjq a",
            "span._2hCDtv", "div._1fOgr8 span"
        ])
        
        if not seller:
            seller = await self.text_by_xpath(page, [
                "//*[contains(text(),'Sold by')]/following::span[1]",
                "//*[contains(text(),'Seller')]/following::a[1]",
                "//*[contains(text(),'Fulfilled by')]/following::span[1]",
                "//div[contains(@class,'seller')]//span[1]"
            ])

        # Manufacturer/Brand (enhanced extraction)
        manufacturer = await self.first_text(page, [
            "[data-automation-id='brand']", "._2b4iJl",
            "div._2NHrnP span", "span._2AV08x",
            "div._1UhVsV a", "span._35KyD6 a"
        ])
        
        if not manufacturer:
            manufacturer = await self.text_by_xpath(page, [
                "//tr[td[contains(text(),'Brand') or contains(text(),'Manufacturer')]]/td[2]",
                "//div[contains(text(),'Brand')]/following-sibling::div[1]",
                "//li[contains(text(),'Brand:')]/following::span[1]",
                "//span[contains(text(),'Brand:')]/following::span[1]"
            ])
        
        # Fallback: use seller as manufacturer if not found
        if not manufacturer and seller:
            manufacturer = seller

        # Image URL (Flipkart product images)
        image_url = await self.get_image_url(page, [
            "div._1AtVbE img",  # Main product image container
            "img._2r_T1I",  # Product image
            "div._396cs4 img",  # Image container variant
            "img[src*='rukminim']",  # Flipkart CDN images
            ".CXW8mj img",  # Image wrapper
            "._2_AcLJ img",  # Alternative image container
            "img._53J4C-",  # Another image selector
            "div._1sfDU2 img",  # Product image variant
            ".qkWVU8 img"  # Image container
        ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
