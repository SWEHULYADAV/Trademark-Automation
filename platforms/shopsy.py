"""
Shopsy Extractor
===============
Optimized selectors and logic for Shopsy platform (Flipkart's budget marketplace)
"""

from typing import List
from .base import BaseExtractor


class ShopsyExtractor(BaseExtractor):
    """Shopsy-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Shopsy product links from listing page."""
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
        """Extract product data from Shopsy product page using reliable XPaths."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, [class*='title']", timeout=5000)
        except:
            pass
        
        # Title - Using h1 tag (from your analysis, though example shows DOSTITCH)
        title = await self.text_by_xpath(page, [
            "//h1//text()",  # Primary XPath (general h1)
            "//h1",          # Fallback
            "//h1/span",     # If title is in span within h1
        ])
        
        # Clean title if found
        if title:
            title = title.strip()
        
        # Fallback to CSS selectors if XPath fails
        if not title:
            title = await self.first_text(page, [
                "h1[data-automation-id='product-title']",
                "h1.product-title",
                ".product-name",
                "h1"
            ])

        # Price (Current) - Using ₹ symbol (from your analysis)
        price = await self.text_by_xpath(page, [
            "//₹[contains(text(), '₹')]/text()",  # Your specific XPath
            "//*[contains(text(), '₹')]",        # More general ₹ search
            "//span[contains(text(), '₹')]",     # Span with ₹
            "//div[contains(text(), '₹')]",      # Div with ₹
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
                ".price",
                "[class*='price']",
                ".current-price",
                ".product-price"
            ])

        # Discount Percentage - Using '% off' pattern (from your analysis)
        discount = None
        
        # Check if discount exists (as per your best practice)
        discount_exists = await page.evaluate("""
            () => {
                return document.evaluate("//text()[contains(., '% off')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null;
            }
        """)
        
        if discount_exists:
            discount = await self.text_by_xpath(page, [
                "//text()[contains(., '% off')]/text()",  # Primary XPath from your analysis
                "//*[contains(text(), '% off')]",         # Any element with % off
                "//span[contains(text(), '% off')]",      # Span with % off
                "//div[contains(text(), '% off')]",       # Div with % off
            ])
            
            # Clean discount if found
            if discount:
                import re
                discount_match = re.search(r'\d+\s*%\s*off', discount, re.IGNORECASE)
                if discount_match:
                    discount = discount_match.group(0)
                else:
                    discount = discount.strip()
        
        # Set as N/A if not found
        if not discount:
            discount = "N/A"

        # Seller Name - Using 'Sold By' pattern (from your analysis)
        seller = await self.text_by_xpath(page, [
            "//div[text()='Sold By']/following-sibling::div[1]/text()",  # Primary XPath from your analysis
            "//div[text()='Sold By']/following-sibling::div[1]",         # More flexible
            "//span[text()='Sold By']/following-sibling::*[1]/text()",   # If span instead of div
            "//*[text()='Sold By']/following-sibling::*[1]/text()",      # Any element with 'Sold By'
        ])
        
        # Clean seller name if found
        if seller:
            seller = seller.strip()
        
        # Fallback to CSS selectors for seller
        if not seller:
            seller = await self.first_text(page, [
                ".seller-name",
                "[class*='seller']",
                ".vendor-name"
            ])
        
        # Default seller if not found
        if not seller:
            seller = "Shopsy"

        # Brand - Using 'Brand' text pattern (from your analysis)
        brand = await self.text_by_xpath(page, [
            "//div[text()='Brand']/following-sibling::div[1]/text()",  # Primary XPath from your analysis
            "//div[text()='Brand']/following-sibling::div[1]",         # More flexible
            "//span[text()='Brand']/following-sibling::*[1]/text()",   # If span instead of div
            "//*[text()='Brand']/following-sibling::*[1]/text()",      # Any element with 'Brand'
        ])
        
        # Clean brand if found
        if brand:
            brand = brand.strip()
        
        # Fallback to CSS selectors for brand
        if not brand:
            brand = await self.first_text(page, [
                ".brand-name",
                "[class*='brand']",
                ".manufacturer"
            ])
        
        # Set as N/A if not found
        if not brand:
            brand = "N/A"

        # Specifications Section - Using 'Specifications' pattern (from your analysis)
        specifications = {}
        
        # Check if Specifications section exists
        specs_exist = await page.evaluate("""
            () => {
                return document.evaluate("//div[text()='Specifications']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue !== null;
            }
        """)
        
        if specs_exist:
            # Extract specifications dynamically into a dictionary
            try:
                specs_data = await page.evaluate("""
                    () => {
                        const xpath = "//div[text()='Specifications']/following-sibling::div[1]//div";
                        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        const specs = {};
                        
                        for (let i = 0; i < result.snapshotLength; i += 2) {
                            const keyNode = result.snapshotItem(i);
                            const valueNode = result.snapshotItem(i + 1);
                            
                            if (keyNode && valueNode && keyNode.textContent && valueNode.textContent) {
                                const key = keyNode.textContent.trim();
                                const value = valueNode.textContent.trim();
                                if (key && value && key !== value) {
                                    specs[key] = value;
                                }
                            }
                        }
                        
                        return specs;
                    }
                """)
                
                if specs_data:
                    specifications = specs_data
            except Exception as e:
                print(f"🔧 Specifications extraction failed: {str(e)}")
        
        # Alternative specifications extraction
        if not specifications:
            specs_text = await self.text_by_xpath(page, [
                "//div[text()='Specifications']/following-sibling::div[1]//div/text()",
                "//div[contains(@class, 'spec')]//div/text()",
                "//table//tr/td/text()"
            ])
            if specs_text:
                specifications = {"General": specs_text}
        
        # Convert specifications to string or set as N/A
        specs_str = "; ".join([f"{k}: {v}" for k, v in specifications.items()]) if specifications else "N/A"
        
        # Use brand as manufacturer for Shopsy
        manufacturer = brand if brand != "N/A" else "N/A"
        
        # Debug info
        debug_info = []
        if not title:
            debug_info.append("❌ Title (h1 not found)")
        if not price:
            debug_info.append("❌ Price (₹ symbol not found)")
        if not seller or seller == "Shopsy":
            debug_info.append("🟡 Seller ('Sold By' missing - using Shopsy default)")
        if discount == "N/A":
            debug_info.append("🟡 Discount ('% off' not visible)")
        if brand == "N/A":
            debug_info.append("🟡 Brand (Brand info not available)")
        if specs_str == "N/A":
            debug_info.append("🟡 Specifications (section not available)")
            
        # Image URL (Shopsy product images)
        image_url = await self.get_image_url(page, [
            ".product-image img",  # Product image
            ".image-gallery img",  # Image gallery
            "img[src*='shopsy']",  # Shopsy CDN images
            ".main-image img",  # Main image
            ".slider img",  # Slider images
            ".product-gallery img"  # Product gallery
        ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
