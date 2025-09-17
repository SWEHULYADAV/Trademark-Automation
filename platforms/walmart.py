"""
Walmart Extractor
=================
Optimized selectors and logic for Walmart platform
"""

import re
import json
from urllib.parse import urlparse, urljoin
from typing import List, Optional
from .base import BaseExtractor


class WalmartExtractor(BaseExtractor):
    """Walmart-specific product extractor."""
    
    def canonical_walmart_link(self, href: str, base: str) -> Optional[str]:
        """Return canonical Walmart product link if present, else None."""
        if not href:
            return None
        if href.startswith("/"):
            href = urljoin(base, href)
        
        # Walmart product URLs typically contain /ip/ pattern
        if "/ip/" in href and "walmart.com" in href:
            return href.split('?')[0]  # Remove query parameters
        return None
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Walmart product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        for h in hrefs:
            can = self.canonical_walmart_link(h, page.url)
            if can and can not in seen:
                seen.add(can)
                urls.append(can)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def parse_json_ld(self, page) -> dict:
        """Parse JSON-LD structured data from the page."""
        try:
            json_ld_scripts = await page.locator('script[type="application/ld+json"]').all()
            for script in json_ld_scripts:
                content = await script.inner_text()
                if content.strip():
                    data = json.loads(content)
                    
                    # Handle different JSON-LD structures
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                return item
                    elif data.get('@type') == 'Product':
                        return data
                    elif data.get('@graph'):
                        for item in data['@graph']:
                            if item.get('@type') == 'Product':
                                return item
            return {}
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")
            return {}
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Walmart product page."""
        
        # Get canonical URL
        product_url = await self.get_attribute_by_xpath(page, [
            "//link[@rel='canonical']/@href"
        ], "href")
        
        if not product_url:
            product_url = page.url
        
        # Parse JSON-LD data
        json_ld_data = await self.parse_json_ld(page)
        
        # Title - from JSON-LD first, then fallback to CSS selectors
        title = None
        if json_ld_data.get('name'):
            title = json_ld_data['name']
        
        if not title:
            title = await self.first_text(page, [
                'h1[data-testid="product-title"]',
                'h1[data-automation-id="product-title"]',
                'h1[aria-label*="product"]',
                'h1.prod-ProductTitle',
                'h1[class*="title"]',
                'h1[class*="product"]',
                '.product-title h1',
                '[data-testid="product-name"] h1'
            ])
        
        # Price - from JSON-LD first, then fallback
        price = None
        price_currency = "USD"
        
        if json_ld_data.get('offers'):
            offers = json_ld_data['offers']
            if isinstance(offers, list) and offers:
                offer = offers[0]
            elif isinstance(offers, dict):
                offer = offers
            else:
                offer = {}
            
            if offer.get('price'):
                price = str(offer['price'])
                price_currency = offer.get('priceCurrency', 'USD')
        
        if not price:
            price = await self.first_text(page, [
                '[data-testid="price-current"]',
                '[data-automation-id="product-price"]',
                '.price-current',
                '.price-display',
                '[aria-label*="current price"]',
                '.price-group .price',
                '[data-testid="price"] span',
                '.prod-PriceSection span[itemprop="price"]'
            ])
        
        # Seller name - from JSON-LD first, then fallback
        seller = None
        if json_ld_data.get('offers'):
            offers = json_ld_data['offers']
            if isinstance(offers, list) and offers:
                offer = offers[0]
            elif isinstance(offers, dict):
                offer = offers
            else:
                offer = {}
            
            if offer.get('seller', {}).get('name'):
                seller = offer['seller']['name']
        
        if not seller:
            seller = await self.first_text(page, [
                '[data-testid="seller-name"]',
                '[data-automation-id="seller-name"]',
                '.seller-name',
                '.prod-sellerName',
                '[data-testid="fulfillment-badge"] + div',
                '.seller-info .seller',
                '.marketplace-seller-name'
            ])
        
        # Default to Walmart if no seller found
        if not seller:
            seller = "Walmart"
        
        # Manufacturer/Brand - from JSON-LD first, then fallback
        manufacturer = None
        if json_ld_data.get('manufacturer', {}).get('name'):
            manufacturer = json_ld_data['manufacturer']['name']
        elif json_ld_data.get('brand', {}).get('name'):
            manufacturer = json_ld_data['brand']['name']
        elif isinstance(json_ld_data.get('brand'), str):
            manufacturer = json_ld_data['brand']
        
        if not manufacturer:
            manufacturer = await self.first_text(page, [
                '[data-testid="product-brand"]',
                '[data-automation-id="product-brand"]',
                '.prod-brandName',
                '.brand-name',
                '[data-testid="brand-name"]',
                '.product-brand',
                '[itemprop="brand"]'
            ])
        
        # Image URL - from JSON-LD first, then fallback
        image_url = None
        if json_ld_data.get('image'):
            images = json_ld_data['image']
            if isinstance(images, list) and images:
                image_url = images[0]
            elif isinstance(images, str):
                image_url = images
        
        if not image_url:
            image_url = await self.get_image_url(page, [
                '[data-testid="hero-image"] img',
                '[data-automation-id="product-image"] img',
                '.prod-hero-image img',
                '.slider-container img',
                '.product-image img',
                '[data-testid="product-image"] img',
                '.prod-ProductImage img',
                'img[data-testid*="image"]'
            ])
        
        return {
            "product_url": product_url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
