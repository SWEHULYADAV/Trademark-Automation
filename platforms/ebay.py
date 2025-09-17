"""
eBay Extractor - Updated with Correct XPath Mapping
===================================================
Using the accurate eBay XPath selectors provided
"""

from typing import List
from .base import BaseExtractor


class EbayExtractor(BaseExtractor):
    """eBay-specific product extractor using updated XPath mapping."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get eBay product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        patterns = ["/itm/", "/p/"]
        
        for h in hrefs:
            if any(pat in h for pat in patterns) and h not in seen:
                seen.add(h)
                urls.append(h)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def wait_for_products(self, page):
        """Wait for products to load."""
        try:
            await page.wait_for_selector("a[href*='/itm/'], h1", timeout=5000)
        except:
            pass
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from eBay product page using updated XPath mapping."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, [id*='itemTitle']", timeout=10000)
        except:
            pass
        
        # Give page more time to load completely
        import asyncio
        await asyncio.sleep(3)
        
        # Title - Using updated XPath from your mapping
        title = await self.text_by_xpath(page, [
            "//h1[contains(@id, 'itemTitle')]/text()",  # Primary XPath from your updated mapping
            "//h1[contains(@id, 'itemTitle')]//text()", # More flexible
            "//h1//text()",  # Fallback
        ])
        
        # CSS fallback for title
        if not title:
            title = await self.first_text(page, [
                "h1[id*='itemTitle']",
                "h1[id*='title']", 
                "h1",
                "[data-testid*='title']"
            ])
        
        # Clean title if found
        if title:
            title = title.strip()
            # Skip error pages
            if "page is missing" in title.lower() or "not found" in title.lower():
                title = None

        # Price (MRP) - Using updated XPath from your mapping with flexible ID approach
        price = None
        
        # Try specific price IDs from your mapping
        price_ids = ["prcIsum", "mm-saleDscPrc"]
        for price_id in price_ids:
            try:
                price = await self.text_by_xpath(page, [
                    f"//span[@id='{price_id}']/text()",
                ])
                if price:
                    break
            except:
                continue
        
        # Try class-based selector from your mapping
        if not price:
            price = await self.text_by_xpath(page, [
                "//span[contains(@class, 'notranslate')]/text()",  # From your mapping
                "//span[@id='prcIsum' or @id='mm-saleDscPrc' or contains(@class, 'notranslate')]/text()",  # Combined from your mapping
            ])
        
        # CSS fallback for price
        if not price:
            price = await self.first_text(page, [
                "#prcIsum",
                "#mm-saleDscPrc", 
                ".notranslate",
                "[class*='price']",
                ".x-price-primary"
            ])
        
        # Clean price if found
        if price:
            import re
            # Remove JavaScript artifacts and clean
            price = re.sub(r'\$ssg.*?;', '', price)
            price = re.sub(r'new Date\(\).*', '', price)
            # Extract clean price with currency
            price_match = re.search(r'[$€£¥₹]\s*[\d,]+(?:\.\d+)?', price.replace('\n', ' '))
            if price_match:
                price = price_match.group(0)

        # Seller Name - Using updated XPath from your mapping with improved extraction
        seller = await self.text_by_xpath(page, [
            "//span[@class='mbg-nw']//text()",  # Get all text content, not just first text node
            "//span[@class='mbg-nw']/text()",   # Primary XPath from your updated mapping
            "//span[contains(@class, 'mbg-nw')]//text()",  # More flexible
        ])
        
        # If XPath gets partial text, try JavaScript extraction
        if not seller or (seller and len(seller.strip()) <= 2):
            try:
                seller = await page.evaluate("""
                    () => {
                        const sellerElement = document.querySelector('span.mbg-nw');
                        if (sellerElement) {
                            return sellerElement.textContent || sellerElement.innerText;
                        }
                        
                        // Try alternative selectors for seller
                        const altSelectors = [
                            'span[class*="mbg"]',
                            '.seller-name',
                            '[data-testid*="seller"]',
                            'a[href*="/usr/"]'
                        ];
                        
                        for (const sel of altSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent && el.textContent.trim().length > 2) {
                                return el.textContent.trim();
                            }
                        }
                        return null;
                    }
                """)
            except:
                pass
        
        # CSS fallback for seller
        if not seller:
            seller = await self.first_text(page, [
                ".mbg-nw",
                "span.mbg-nw",
                "[class*='seller'] a",
                ".seller-info a"
            ])
        
        # Clean seller name if found
        if seller:
            import re
            # Remove extra info, ratings, and parentheses
            seller = re.split(r'\s*\(|\s*-|\s*\d+%', seller)[0].strip()
            seller = re.sub(r'\s*(Seller|Store|Shop)\s*$', '', seller, flags=re.IGNORECASE)
            seller = seller.strip()

        # Manufacturer/Brand - Using updated XPath from your mapping
        manufacturer = await self.text_by_xpath(page, [
            "//td[contains(text(),'Brand')]/following-sibling::td[1]/text()",  # Primary XPath from your updated mapping
            "//td[contains(text(),'Manufacturer')]/following-sibling::td[1]/text()",  # Alternative
            "//th[contains(text(),'Brand')]/following-sibling::td[1]/text()",  # If using th instead of td
            "//th[contains(text(),'Manufacturer')]/following-sibling::td[1]/text()",
        ])
        
        # Clean manufacturer
        if manufacturer:
            manufacturer = manufacturer.strip()
        else:
            manufacturer = "N/A"

        # Return Eligibility Info - From your mapping
        return_info = await self.text_by_xpath(page, [
            "//*[contains(text(), 'returns')]/text()",  # From your mapping
            "//*[contains(text(), 'return')]/text()",
            "//*[contains(text(), 'Return')]/text()",
        ])
        
        if return_info:
            return_info = return_info.strip()
        else:
            return_info = "N/A"

        # Availability Info - From your mapping
        availability = "Available"  # Default
        
        # Check for out of stock
        out_of_stock = await self.text_by_xpath(page, [
            "//*[contains(text(), 'Out of stock')]/text()",  # From your mapping
            "//*[contains(text(), 'Sold out')]/text()",
            "//*[contains(text(), 'Not available')]/text()",
        ])
        
        if out_of_stock:
            availability = "Sold Out"

        # Seller Profile URL - Extract from seller links
        seller_profile_url = await page.evaluate("""
            () => {
                const selectors = [
                    ".mbg-nw", 
                    "[class*='seller'] a",
                    "a[href*='/usr/']"
                ];
                
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        // If it's a link itself
                        if (element.href) {
                            return element.href;
                        }
                        // If it contains a link
                        const link = element.querySelector('a');
                        if (link && link.href) {
                            return link.href;
                        }
                    }
                }
                return null;
            }
        """)

        # JavaScript fallback for missing data (following your tips)
        if not title or not price or not seller:
            try:
                js_data = await page.evaluate("""
                    () => {
                        const result = {};
                        
                        // Title fallback using ID-based approach
                        if (!result.title) {
                            const titleEl = document.querySelector('h1[id*="itemTitle"], h1');
                            if (titleEl && titleEl.textContent) {
                                result.title = titleEl.textContent.trim();
                            }
                        }
                        
                        // Price fallback using ID-based approach (from your tips)
                        if (!result.price) {
                            const priceIds = ['prcIsum', 'mm-saleDscPrc'];
                            for (const pid of priceIds) {
                                const priceEl = document.getElementById(pid);
                                if (priceEl && priceEl.textContent) {
                                    result.price = priceEl.textContent.trim();
                                    break;
                                }
                            }
                            
                            // Try notranslate class
                            if (!result.price) {
                                const priceEl = document.querySelector('.notranslate');
                                if (priceEl && priceEl.textContent && /[$€£¥₹]/.test(priceEl.textContent)) {
                                    result.price = priceEl.textContent.trim();
                                }
                            }
                        }
                        
                        // Seller fallback using class-based approach (from your mapping)
                        if (!result.seller) {
                            const sellerEl = document.querySelector('.mbg-nw');
                            if (sellerEl && sellerEl.textContent) {
                                result.seller = sellerEl.textContent.trim();
                            }
                        }
                        
                        return result;
                    }
                """)
                
                # Use JavaScript results if our extraction failed
                if not title and js_data.get('title'):
                    title = js_data['title']
                if not price and js_data.get('price'):
                    price = js_data['price']
                    # Clean JavaScript price
                    import re
                    price_match = re.search(r'[$€£¥₹]\s*[\d,]+(?:\.\d+)?', price)
                    if price_match:
                        price = price_match.group(0)
                if not seller and js_data.get('seller'):
                    seller = js_data['seller']
                    # Clean JavaScript seller
                    import re
                    seller = re.split(r'\s*\(|\s*-|\s*\d+%', seller)[0].strip()
                        
            except Exception as e:
                print(f"🔧 JavaScript fallback failed: {str(e)}")

        # Debug info - Updated for new XPath mapping
        debug_info = []
        if not title:
            debug_info.append("❌ Title (h1[id*='itemTitle'] XPath failed)")
        if not price:
            debug_info.append("❌ Price (prcIsum/mm-saleDscPrc XPath failed)")
        if not seller:
            debug_info.append("❌ Seller (mbg-nw XPath failed)")
        if manufacturer == "N/A":
            debug_info.append("🟡 Manufacturer (Brand table not found)")
            
        if debug_info:
            print(f"🔍 eBay Debug - {page.url}")
            for info in debug_info:
                print(f"   {info}")
        else:
            print(f"✅ eBay extraction successful for: {page.url}")
            print(f"   Title: {title[:50] + '...' if title and len(title) > 50 else title}")
            print(f"   Price: {price}")
            print(f"   Seller: {seller}")
            print(f"   Manufacturer: {manufacturer}")
            print(f"   Return Info: {return_info}")
            print(f"   Availability: {availability}")

        # Image URL (eBay product images)
        image_url = await self.get_image_url(page, [
            "#icImg",  # Main eBay image
            ".notranslate img",  # Image container
            "#vi_main_img_fs img",  # Full screen image
            "img[id*='icImg']",  # Image variants
            ".img img",  # Generic image
            "img[src*='ebayimg']",  # eBay CDN images
            ".zoom img",  # Zoom images
            "#mainContent img"  # Main content images
        ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "seller_profile_url": seller_profile_url,
            "manufacturer_name": manufacturer,
            "image_url": image_url,
            "return_info": return_info,
            "availability": availability
        }
