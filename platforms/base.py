"""
Base extractor class for all e-commerce platforms
=================================================
Simplified base class with common extraction logic only
Platform-specific logic moved to individual platform files
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseExtractor(ABC):
    """Base class for all platform extractors with common extraction logic."""
    
    def __init__(self):
        self.platform_type = "unknown"  # pagination, infinite_scroll, no_pagination
        self.variant_support = False
    
    @staticmethod
    async def first_text(page, selectors: List[str]) -> Optional[str]:
        """Return first non-empty inner_text for any selector."""
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    text = (await loc.first.inner_text()).strip()
                    if text:
                        return " ".join(text.split())
            except Exception:
                pass
        return None

    @staticmethod
    async def text_by_xpath(page, xpaths: List[str]) -> Optional[str]:
        """Return first non-empty text using XPath selectors."""
        for xp in xpaths:
            try:
                loc = page.locator(f"xpath={xp}")
                if await loc.count() > 0:
                    txt = (await loc.first.inner_text()).strip()
                    if txt:
                        return " ".join(txt.split())
            except Exception:
                pass
        return None
    
    @staticmethod
    async def get_attribute_by_xpath(page, xpaths: List[str], attribute: str) -> Optional[str]:
        """Return first non-empty attribute value using XPath selectors."""
        for xp in xpaths:
            try:
                # Handle XPath with /@attribute suffix (common for OG meta)
                if f"/@{attribute}" in xp:
                    clean_xpath = xp.replace(f"/@{attribute}", "")
                else:
                    clean_xpath = xp
                    
                loc = page.locator(f"xpath={clean_xpath}")
                if await loc.count() > 0:
                    attr_value = await loc.first.get_attribute(attribute)
                    if attr_value and attr_value.strip():
                        return attr_value.strip()
            except Exception:
                pass
        return None
    
    @staticmethod
    async def get_image_url(page, selectors: List[str], use_og_meta: bool = False) -> Optional[str]:
        """Get first valid image URL from selectors, with optional OG meta priority."""
        
        # If OG meta priority is requested, try that first
        if use_og_meta:
            try:
                og_image = await page.evaluate("""
                    () => {
                        const metaOg = document.querySelector('meta[property="og:image"]');
                        if (metaOg && metaOg.content) {
                            return metaOg.content;
                        }
                        return null;
                    }
                """)
                if og_image and og_image.strip() and og_image.startswith(("http", "//")):
                    # Convert protocol relative URLs to https
                    if og_image.startswith("//"):
                        og_image = "https:" + og_image
                    return og_image.strip()
            except Exception:
                pass
        
        # Try provided selectors
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    img_url = await loc.first.get_attribute("src")
                    if not img_url:
                        img_url = await loc.first.get_attribute("data-src")
                    if not img_url:
                        img_url = await loc.first.get_attribute("data-lazy-src")
                    if img_url and img_url.strip() and img_url.startswith(("http", "//")):
                        # Convert protocol relative URLs to https
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        return img_url.strip()
            except Exception:
                pass
        return None
    
    # ==================== COMMON EXTRACTION METHODS ====================
    
    async def extract_common_data(self, page) -> Dict[str, Any]:
        """Extract common product data (title, price, seller, manufacturer, image)."""
        try:
            # Extract title
            title = await self.first_text(page, [
                "h1[id='title']",
                "h1[data-automation-id='product-title']",
                "h1.product-title",
                "h1",
                ".product-title",
                "[data-testid='product-title']"
            ])
            
            # Extract price
            price = await self.first_text(page, [
                ".a-price-whole",
                ".a-price .a-offscreen",
                ".price",
                ".product-price",
                "[data-testid='price']",
                ".a-price-range"
            ])
            
            # Extract seller name
            seller_name = await self.first_text(page, [
                "#sellerProfileTriggerId",
                ".a-size-small.a-color-secondary",
                ".seller-name",
                "[data-testid='seller-name']"
            ])
            
            # Extract manufacturer name
            manufacturer_name = await self.first_text(page, [
                "#bylineInfo",
                ".a-size-small.a-color-secondary",
                ".manufacturer-name",
                "[data-testid='manufacturer-name']"
            ])
            
            # Extract image URL
            image_url = await self.get_image_url(page, [
                "#landingImage",
                ".a-dynamic-image",
                "img[data-old-hires]",
                "img[data-src]",
                "img[src]"
            ], use_og_meta=True)
            
            return {
                "title": title or "",
                "price": price or "",
                "seller_name": seller_name or "",
                "manufacturer_name": manufacturer_name or "",
                "image_url": image_url or ""
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting common data: {e}")
            return {
                "title": "",
                "price": "",
                "seller_name": "",
                "manufacturer_name": "",
                "image_url": ""
            }
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    async def extract_product_data(self, page) -> dict:
        """Extract product data from the page."""
        pass
    
    @abstractmethod
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get product links from listing page."""
        pass
    
    @abstractmethod
    async def go_to_next_page(self, page) -> bool:
        """Navigate to next page. Platform-specific implementation."""
        pass
    
    @abstractmethod
    async def extract_variants(self, page, main_product_url: str) -> List[Dict[str, Any]]:
        """Extract product variants. Platform-specific implementation."""
        pass
