"""
Nykaa Extractor
===============
Optimized selectors and logic for Nykaa platform
"""

from typing import List, Optional
from .base import BaseExtractor


class NykaaExtractor(BaseExtractor):
    """Nykaa-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Nykaa product links from listing page."""
        
        # Wait for products to load
        try:
            await page.wait_for_selector("a[href*='/p/'], .product-item, .product-card", timeout=5000)
        except:
            pass
        
        # Get all href links
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        # Nykaa product URL patterns
        patterns = [
            "/p/",              # Main product URLs like /p/product-name/12345
            "/product/",        # Product detail URLs
            "-dp-",             # Product detail page identifier
        ]
        
        print(f"🔍 Found {len(hrefs)} total links on page")
        
        for h in hrefs:
            # Check if it's a valid Nykaa product URL
            if any(pat in h for pat in patterns) and h not in seen and "nykaa.com" in h:
                seen.add(h)
                urls.append(h)
                print(f"   ✅ Product link: {h}")
                if len(urls) >= limit:
                    break
        
        # If no product links found, try alternative selectors
        if not urls:
            print("🔄 No direct product links found, trying alternative selectors...")
            
            product_links = await page.evaluate("""
                () => {
                    const selectors = [
                        '.product-item a',
                        '.product-card a', 
                        '[class*="product"] a[href*="nykaa.com"]',
                        'a[href*="/p/"]',
                        '.css-xrzmfa a',  // Common Nykaa product card class
                        '.product-listing a'
                    ];
                    
                    const links = [];
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            if (el.href && el.href.includes('nykaa.com')) {
                                links.push(el.href);
                            }
                        }
                    }
                    return [...new Set(links)];
                }
            """)
            
            for link in product_links:
                if link not in seen:
                    seen.add(link)
                    urls.append(link)
                    print(f"   ✅ Alternative product link: {link}")
                    if len(urls) >= limit:
                        break
        
        print(f"🎯 Total Nykaa product links found: {len(urls)}")
        return urls[:limit]
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Nykaa product page."""
        
        # Initialize result
        result = {
            "product_url": "",
            "title": "",
            "price": "",
            "seller_name": "",
            "manufacturer_name": "", 
            "image_url": ""
        }
        
        try:
            # Product URL - Canonical link (preferred)
            product_url = await self.get_attribute_by_xpath(
                page,
                ["//link[@rel='canonical']/@href"],
                "href"
            )
            if not product_url:
                # Fallback to current URL
                product_url = await page.evaluate("() => window.location.href")
            result["product_url"] = product_url or ""
            
            # Title - OG title (preferred)
            title = await self.get_attribute_by_xpath(
                page,
                ["//meta[@property='og:title']/@content"],
                "content"
            )
            if not title:
                # Fallback to H1
                title = await self.text_by_xpath(
                    page,
                    ["//h1[normalize-space()]"]
                )
            result["title"] = title or ""
            
            # Price - Multiple approaches
            price = ""
            
            # First try meta property for price
            price = await self.get_attribute_by_xpath(
                page,
                ["//meta[@property='product:price:amount']/@content"],
                "content"
            )
            
            if not price:
                # Try JSON-LD structured data
                price = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const script of scripts) {
                            try {
                                const data = JSON.parse(script.textContent);
                                if (data.offers && data.offers.price) {
                                    return data.offers.price;
                                }
                                if (data['@type'] === 'Product' && data.offers) {
                                    const offers = Array.isArray(data.offers) ? data.offers[0] : data.offers;
                                    if (offers.price) return offers.price;
                                }
                            } catch (e) {}
                        }
                        return null;
                    }
                """)
            
            if not price:
                # Try visible text patterns for MRP/price
                price_selectors = [
                    "//*[contains(text(), 'MRP')]/following-sibling::*[contains(text(), '₹')]",
                    "//*[contains(text(), 'Price')]/following-sibling::*[contains(text(), '₹')]",
                    "//*[contains(text(), '₹')]",
                    "//span[contains(@class, 'price')]",
                    "//div[contains(@class, 'price')]"
                ]
                price = await self.text_by_xpath(page, price_selectors)
            
            result["price"] = price or ""
            
            # Seller Name - "Sold by" text pattern
            seller_name = await self.text_by_xpath(
                page,
                [
                    "//text()[contains(., 'Sold by')]/following::text()[normalize-space()][1]",
                    "//*[contains(text(), 'Sold by')]/following-sibling::*[normalize-space()]",
                    "//*[contains(text(), 'Sold by')]/descendant-or-self::*/text()[normalize-space()][last()]"
                ]
            )
            result["seller_name"] = seller_name or ""
            
            # Manufacturer Name - Simplified logic to extract clean manufacturer name
            manufacturer_name = await page.evaluate("""
                () => {
                    // First try to find manufacturer info in visible text elements
                    const allElements = document.querySelectorAll('*');
                    
                    for (const element of allElements) {
                        // Skip script, style, and other non-content elements
                        if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK'].includes(element.tagName)) {
                            continue;
                        }
                        
                        const text = element.textContent || '';
                        
                        // Look for manufacturer patterns
                        if (text.includes('Manufacturer') || text.includes('Manufactured by') || text.includes('Marketed by')) {
                            // Try to extract the value after the keyword
                            let parts = text.split(/Manufacturer[^a-zA-Z]*|Manufactured by[^a-zA-Z]*|Marketed by[^a-zA-Z]*/i);
                            if (parts.length > 1) {
                                let name = parts[1].trim();
                                
                                // Clean up common patterns
                                if (name.includes('"Name"')) {
                                    // Extract from JSON-like pattern: "Name":"Puma Sports India Pvt Ltd"
                                    let match = name.match(/"Name"[^"]*"([^"]+)"/i);
                                    if (match && match[1]) {
                                        name = match[1];
                                    }
                                }
                                
                                // Remove "Name:" prefix pattern
                                if (name.startsWith('Name:')) {
                                    name = name.substring(5).trim();
                                }
                                
                                // Remove quotes, brackets, and extra characters
                                name = name.replace(/["{}]/g, '');
                                name = name.replace(/\\[|\\]/g, '');
                                name = name.split(/[\\n\\r,;]/)[0].trim();
                                
                                // Filter out invalid names
                                if (name && 
                                    name.length > 2 && 
                                    name.length < 100 &&
                                    !name.includes('window.') &&
                                    !name.includes('function') &&
                                    !name.includes('var ') &&
                                    !name.includes('const ')) {
                                    return name;
                                }
                            }
                        }
                    }
                    
                    return null;
                }
            """)
            
            if not manufacturer_name:
                # Try JSON-LD for brand/manufacturer
                manufacturer_name = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const script of scripts) {
                            try {
                                const data = JSON.parse(script.textContent);
                                if (data.brand && data.brand.name) {
                                    return data.brand.name;
                                }
                                if (data.manufacturer && data.manufacturer.name) {
                                    return data.manufacturer.name;
                                }
                            } catch (e) {}
                        }
                        return null;
                    }
                """)
            
            result["manufacturer_name"] = manufacturer_name or ""
            
            # Image URL - OG image (preferred)
            image_url = await self.get_attribute_by_xpath(
                page,
                ["//meta[@property='og:image']/@content"],
                "content"
            )
            
            if not image_url:
                # Fallback to main product images
                image_selectors = [
                    "img[alt*='product']",
                    ".product-image img",
                    ".main-image img",
                    ".product-gallery img",
                    "img[src*='nykaa']"
                ]
                image_url = await self.get_image_url(page, image_selectors)
            
            result["image_url"] = image_url or ""
            
        except Exception as e:
            print(f"❌ Error extracting Nykaa product data: {e}")
        
        return result