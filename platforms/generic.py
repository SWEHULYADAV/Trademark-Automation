"""
Generic Extractor
=================
Smart fallback extractor for unknown e-commerce platforms.
Uses multiple heuristics and patterns to detect product links and extract data.
"""

from typing import List
from .base import BaseExtractor


class GenericExtractor(BaseExtractor):
    """Smart generic extractor for unknown e-commerce platforms."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get product links using multiple heuristics for unknown platforms."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        # Common e-commerce URL patterns (ordered by priority)
        primary_patterns = ["/product/", "/item/", "/p/", "/prod/", "/dp/"]
        secondary_patterns = ["/sku/", "/goods/", "/detail/", "/view/", "/buy/"]
        tertiary_patterns = ["/catalog/", "/shop/", "/store/", "-p-", "_p_"]
        
        # Try primary patterns first
        for h in hrefs:
            if any(pat in h for pat in primary_patterns) and h not in seen:
                seen.add(h)
                urls.append(h)
                if len(urls) >= limit:
                    break
        
        # If not enough links, try secondary patterns
        if len(urls) < limit // 2:
            for h in hrefs:
                if any(pat in h for pat in secondary_patterns) and h not in seen:
                    seen.add(h)
                    urls.append(h)
                    if len(urls) >= limit:
                        break
        
        # If still not enough, try tertiary patterns
        if len(urls) < limit // 4:
            for h in hrefs:
                if any(pat in h for pat in tertiary_patterns) and h not in seen:
                    seen.add(h)
                    urls.append(h)
                    if len(urls) >= limit:
                        break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data using smart generic selectors and multiple fallback strategies."""
        
        # Title extraction with multiple strategies
        title = None
        
        # Strategy 1: Common e-commerce title selectors
        title = await self.first_text(page, [
            "h1", "h1.product-title", "h1.title", ".product-name",
            "[data-testid*='title']", "[data-test*='title']",
            ".product-title", ".item-title", ".goods-title"
        ])
        
        # Strategy 2: Schema.org markup
        if not title:
            title = await self.first_text(page, [
                "[itemprop='name']", "[itemtype*='Product'] h1",
                "meta[property='og:title']"
            ])
        
        # Strategy 3: Page title as fallback
        if not title:
            try:
                page_title = await page.title()
                # Clean up common suffixes
                for suffix in [" | Buy Online", " - Buy Now", " | Shop", " - Price", " | Best Price"]:
                    if suffix in page_title:
                        title = page_title.split(suffix)[0].strip()
                        break
                else:
                    title = page_title
            except Exception:
                title = None

        # Price extraction with multiple strategies
        price = None
        
        # Strategy 1: Schema.org and common price selectors
        price = await self.first_text(page, [
            "[itemprop='price']", "[itemprop='lowPrice']", "[itemprop='highPrice']",
            "[data-test*='price']", "[data-testid*='price']", 
            ".price", ".product-price", ".current-price", ".sale-price",
            ".price-current", ".price-now", ".final-price"
        ])
        
        # Strategy 2: Currency-based selectors
        if not price:
            price = await self.first_text(page, [
                "[class*='rupee']", "[class*='dollar']", "[class*='euro']",
                "[class*='₹']", "[class*='$']", "[class*='€']",
                ".amount", ".cost", ".rate", ".value"
            ])
        
        # Strategy 3: Common price patterns with XPath
        if not price:
            price = await self.text_by_xpath(page, [
                "//*[contains(text(),'₹') or contains(text(),'$') or contains(text(),'€')][string-length(text()) < 20]",
                "//*[contains(@class,'price') or contains(@id,'price')]"
            ])

        # Seller/Brand extraction
        seller = None
        
        # Strategy 1: Common brand/seller selectors
        seller = await self.first_text(page, [
            "[itemprop='brand']", "[itemprop='manufacturer']",
            ".seller-name", ".brand-name", ".manufacturer",
            "[data-testid*='seller']", "[data-testid*='brand']",
            "a.seller", ".brand", ".company"
        ])
        
        # Strategy 2: "Sold by" text patterns
        if not seller:
            seller = await self.text_by_xpath(page, [
                "//*[contains(normalize-space(),'Sold by')]/following-sibling::*[1]",
                "//*[contains(normalize-space(),'Sold by')]/following::a[1]",
                "//*[contains(normalize-space(),'Brand:')]/following-sibling::*[1]",
                "//*[contains(normalize-space(),'Seller:')]/following-sibling::*[1]"
            ])

        # Manufacturer extraction (often same as seller for generic sites)
        manufacturer = None
        
        # Strategy 1: Specific manufacturer selectors
        manufacturer = await self.first_text(page, [
            "[itemprop='manufacturer']", ".manufacturer-name",
            "[data-testid*='manufacturer']"
        ])
        
        # Strategy 2: Product specification tables
        if not manufacturer:
            manufacturer = await self.text_by_xpath(page, [
                "//tr[td[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'manufacturer')]]/td[2]",
                "//tr[th[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'manufacturer')]]/td[1]",
                "//div[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'manufacturer')]/following-sibling::div[1]"
            ])
        
        # Fallback: use seller as manufacturer if manufacturer not found
        if not manufacturer and seller:
            manufacturer = seller

        # Image URL (Generic platform images)
        image_url = await self.get_image_url(page, [
            "img[alt*='product']",  # Product images with alt text
            ".product-image img",  # Product image containers
            ".main-image img",  # Main image
            "img.product",  # Product class images
            ".gallery img",  # Gallery images
            ".item-image img",  # Item images
            "img[src*='product']",  # URLs containing 'product'
            "[class*='image'] img",  # Any class containing 'image'
            ".img img"  # Generic image containers
        ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
