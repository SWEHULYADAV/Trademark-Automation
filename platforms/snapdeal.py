"""
Snapdeal Extractor
=================
Optimized selectors and logic for Snapdeal platform
"""

from typing import List
from .base import BaseExtractor


class SnapdealExtractor(BaseExtractor):
    """Snapdeal-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Snapdeal product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        patterns = ["/product/", "/p/"]
        
        for h in hrefs:
            if any(pat in h for pat in patterns) and h not in seen:
                seen.add(h)
                urls.append(h)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Snapdeal product page using reliable XPaths."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, [class*='title']", timeout=5000)
        except:
            pass
        
        # Title - Using h1 with pdp-title class or itemprop (from your analysis)
        title = await self.text_by_xpath(page, [
            "//h1[contains(@class, 'pdp-title') or @itemprop='name']/text()",  # Primary XPath from your analysis
            "//h1[contains(@class, 'pdp-title')]/text()",  # More specific
            "//h1[@itemprop='name']/text()",               # Alternative
            "//h1//text()",                                # Fallback
        ])
        
        # Clean title if found
        if title:
            title = title.strip()
        
        # Fallback to CSS selectors if XPath fails
        if not title:
            title = await self.first_text(page, [
                "h1.pdp-title",
                "h1[itemprop='name']",
                ".pdp-title",
                ".product-title",
                "h1"
            ])
        
        # Alternative: Check for JSON data in script tags
        if not title:
            try:
                title = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const text = script.textContent;
                            if (text && text.includes('productDetail')) {
                                try {
                                    const match = text.match(/"name"\\s*:\\s*"([^"]+)"/);
                                    if (match) return match[1];
                                } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
            except:
                pass

        # Price (Selling Price) - Using payBlkBig or product-price class (from your analysis)
        price = await self.text_by_xpath(page, [
            "//span[contains(@class, 'payBlkBig') or contains(@class, 'product-price')]/text()",  # Primary XPath
            "//span[contains(@class, 'payBlkBig')]/text()",     # More specific
            "//span[contains(@class, 'product-price')]/text()", # Alternative
            "//*[contains(@class, 'price')]//text()",           # Fallback
        ])
        
        # Clean price if found
        if price:
            import re
            # Extract price with ₹ symbol
            price_match = re.search(r'₹\s*\d+(?:,\d+)*(?:\.\d+)?', price.replace('\n', ' '))
            if price_match:
                price = price_match.group(0)
            else:
                price = price.split('\n')[0].strip()
        
        # Fallback to CSS selectors for price
        if not price:
            price = await self.first_text(page, [
                ".payBlkBig",
                ".product-price",
                ".price",
                "[class*='price']"
            ])
        
        # Alternative: Check for price in JSON data
        if not price:
            try:
                price = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const text = script.textContent;
                            if (text && text.includes('productDetail')) {
                                try {
                                    const match = text.match(/"price"\\s*:\\s*"?([^",}]+)"?/);
                                    if (match) return '₹' + match[1];
                                } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
            except:
                pass

        # Original Price - Using pdpCutPrice class (from your analysis)
        original_price = await self.text_by_xpath(page, [
            "//span[contains(@class, 'pdpCutPrice')]/text()",  # Primary XPath from your analysis
            "//span[contains(@class, 'cut-price')]/text()",    # Alternative
            "//span[contains(@class, 'original')]/text()",     # Fallback
            "//*[contains(@class, 'strike')]//text()",         # Generic strikethrough
        ])
        
        # Clean original price if found
        if original_price:
            import re
            price_match = re.search(r'₹\s*\d+(?:,\d+)*(?:\.\d+)?', original_price.replace('\n', ' '))
            if price_match:
                original_price = price_match.group(0)
            else:
                original_price = original_price.split('\n')[0].strip()
        
        # Set as N/A if not found
        if not original_price:
            original_price = "N/A"

        # Seller Name - Using 'Sold by' pattern (from your analysis)
        seller = await self.text_by_xpath(page, [
            "//span[contains(text(), 'Sold by')]/following-sibling::a/text()",  # Primary XPath from your analysis
            "//span[contains(text(), 'Sold by')]/following-sibling::a",         # More flexible
            "//*[contains(text(), 'Sold by')]/following-sibling::a/text()",     # Any element
            "//*[contains(text(), 'Sold by')]/following::a[1]/text()",          # Following instead of sibling
        ])
        
        # Clean seller name if found
        if seller:
            seller = seller.strip()
        
        # Check if seller section exists (as per your best practice)
        if not seller:
            seller_exists = await page.evaluate("""
                () => {
                    return document.evaluate("//span[contains(text(), 'Sold by')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null;
                }
            """)
            
            if not seller_exists:
                seller = "Snapdeal"  # Default for Snapdeal-owned products
        
        # Fallback to CSS selectors for seller
        if not seller or seller == "Snapdeal":
            seller_css = await self.first_text(page, [
                ".seller-name",
                "[class*='seller'] a",
                ".vendor-name"
            ])
            if seller_css:
                seller = seller_css

        # Manufacturer/Brand - Using Brand text pattern (from your analysis)
        manufacturer = await self.text_by_xpath(page, [
            "//div[contains(text(), 'Brand')]/following-sibling::div[1]/text()",  # Primary XPath from your analysis
            "//div[contains(text(), 'Brand')]/following-sibling::div[1]",         # More flexible
            "//td[contains(text(), 'Brand')]/following-sibling::td[1]/text()",    # Table format
            "//span[contains(text(), 'Brand:')]/following-sibling::span[1]/text()", # Colon format
            "//*[contains(text(), 'Brand')]/following-sibling::*[1]/text()",      # Any element
        ])
        
        # Clean manufacturer if found
        if manufacturer:
            manufacturer = manufacturer.strip()
        
        # Alternative: Check for brand in JSON data
        if not manufacturer:
            try:
                manufacturer = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const text = script.textContent;
                            if (text && text.includes('productDetail') || text.includes('brand')) {
                                try {
                                    const match = text.match(/"brand"\\s*:\\s*"([^"]+)"/);
                                    if (match) return match[1];
                                } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
            except:
                pass
        
        # Fallback to CSS selectors for manufacturer
        if not manufacturer:
            manufacturer = await self.first_text(page, [
                ".brand-name",
                "[class*='brand']",
                ".manufacturer"
            ])
        
        # Set as N/A if still not found
        if not manufacturer:
            manufacturer = "N/A"
        
        # Debug info
        debug_info = []
        if not title:
            debug_info.append("❌ Title (h1 with pdp-title/itemprop not found)")
        if not price:
            debug_info.append("❌ Price (payBlkBig/product-price not found)")
        if not seller or seller == "Snapdeal":
            debug_info.append("🟡 Seller ('Sold by' missing - using Snapdeal default)")
        if original_price == "N/A":
            debug_info.append("🟡 Original Price (pdpCutPrice not visible - no discount)")
        # Image URL (Snapdeal product images)
        image_url = await self.get_image_url(page, [
            ".product-images img",  # Product image container
            "#bx-slider img",  # Slider images
            ".gallery img",  # Gallery images
            "img[src*='snapdeal']",  # Snapdeal CDN images
            ".slider-container img",  # Slider container
            "#mainProductImage",  # Main product image
            ".img-responsive"  # Responsive images
        ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
