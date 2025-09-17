"""
Meesho Extractor
================
Optimized selectors and logic for Meesho platform
"""

from typing import List
from .base import BaseExtractor


class MeeshoExtractor(BaseExtractor):
    """Meesho-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Meesho product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        # Meesho uses multiple URL patterns
        patterns = ["/product/", "/p/", "/products/"]
        
        for h in hrefs:
            if any(pat in h for pat in patterns) and h not in seen and "meesho.com" in h:
                seen.add(h)
                urls.append(h)
                if len(urls) >= limit:
                    break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Meesho product page."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, .product-title, [class*='title']", timeout=5000)
        except:
            pass
        
        # Try JavaScript evaluation for dynamic content
        try:
            js_data = await page.evaluate("""
                () => {
                    // Extract title from various sources
                    let title = null;
                    const titleSelectors = ['h1', '[class*="title"]', '[class*="Title"]', '[class*="name"]', '[class*="Name"]'];
                    for (let selector of titleSelectors) {
                        const el = document.querySelector(selector);
                        if (el && el.innerText && el.innerText.trim().length > 5) {
                            title = el.innerText.trim();
                            break;
                        }
                    }
                    
                    // Extract price
                    let price = null;
                    const priceSelectors = ['[class*="price"]', '[class*="Price"]', '[class*="amount"]', '[class*="cost"]'];
                    for (let selector of priceSelectors) {
                        const el = document.querySelector(selector);
                        if (el && el.innerText && (el.innerText.includes('₹') || el.innerText.includes('Rs'))) {
                            price = el.innerText.trim();
                            break;
                        }
                    }
                    
                    // Extract seller/supplier
                    let seller = null;
                    const sellerSelectors = ['[class*="supplier"]', '[class*="Supplier"]', '[class*="seller"]', 'a[href*="supplier"]'];
                    for (let selector of sellerSelectors) {
                        const el = document.querySelector(selector);
                        if (el && el.innerText && el.innerText.trim().length > 2) {
                            seller = el.innerText.trim();
                            break;
                        }
                    }
                    
                    return { title, price, seller };
                }
            """)
            
            if js_data.get('title'):
                title = js_data['title']
            if js_data.get('price'):
                price = js_data['price']
            if js_data.get('seller'):
                seller = js_data['seller']
                
        except Exception as e:
            print(f"🔧 JS evaluation failed for Meesho: {str(e)}")
        
        # Use specific XPath expressions (more reliable for Meesho)
        
        # Title - Most reliable with h1 tag
        if 'title' not in locals() or not title:
            title = await self.text_by_xpath(page, [
                "//h1",  # Primary XPath from your analysis
                "//h1//text()",  # Get text content from h1
                "//h1/span",     # If title is in span within h1
            ])
        
        # Fallback to page title if h1 not found
        if not title:
            try:
                page_title = await page.title()
                if page_title and "Meesho" in page_title:
                    # Clean Meesho page title
                    title = page_title.replace(" - Meesho", "").replace(" | Meesho", "").strip()
            except:
                pass
        
        # Price - Using h4 with ₹ symbol (from your analysis)
        if 'price' not in locals() or not price:
            price = await self.text_by_xpath(page, [
                "//h4[contains(text(), '₹')]",  # Primary XPath from your analysis
                "//h4[contains(., '₹')]",       # Alternative with contains
                "//*[contains(text(),'₹')][name()='h4']",  # Backup
                "//span[contains(text(), '₹')]", # Fallback to span if not h4
                "//*[contains(text(),'₹')][string-length(normalize-space(text())) < 30]"  # Any element with ₹
            ])
            
        # Clean price - Remove extra text and newlines
        if price:
            import re
            # Extract only the first price with ₹
            price_match = re.search(r'₹\s*\d+(?:,\d+)*', price.replace('\n', ' '))
            if price_match:
                price = price_match.group(0)
            else:
                # Fallback - take text before any newline or "off"
                price = price.split('\n')[0].split('off')[0].strip()

        # Seller - Using 'Sold By' text pattern (from your analysis)
        if 'seller' not in locals() or not seller:
            seller = await self.text_by_xpath(page, [
                "//div[text()='Sold By']/following-sibling::div[1]",  # Primary XPath from your analysis
                "//div[contains(text(),'Sold By')]/following-sibling::div[1]",  # More flexible
                "//span[text()='Sold By']/following-sibling::*[1]",   # If span instead of div
                "//div[text()='Sold By']/following::div[1]",          # Following instead of sibling
                "//*[text()='Sold By']/following-sibling::*[1]",      # Any element with 'Sold By'
                "//*[contains(text(),'Supplier')]/following-sibling::*[1]"  # Alternative pattern
            ])
            
        # Clean seller name - Remove extra shop info
        if seller:
            import re
            # Extract only the seller name (before "View Shop" or ratings)
            seller_match = re.search(r'^([^V]+?)(?:\s+View\s+Shop|$)', seller.strip())
            if seller_match:
                seller = seller_match.group(1).strip()
            else:
                # Fallback - take text before any numbers (ratings)
                seller = re.split(r'\s+\d+', seller)[0].strip()

        # Manufacturer - Try "More Information" popup first, then fallback to direct extraction
        manufacturer = None
        
        # First try: Click "More Information" and extract from popup
        try:
            # Look for "More Information" button/link
            more_info_selectors = [
                "//button[contains(text(), 'More Information')]",
                "//a[contains(text(), 'More Information')]",
                "//div[contains(text(), 'More Information')]",
                "//span[contains(text(), 'More Information')]",
                "//*[contains(@class, 'more-info')]",
                "//*[contains(@class, 'MoreInfo')]"
            ]
            
            more_info_clicked = False
            for selector in more_info_selectors:
                try:
                    more_info_element = page.locator(f"xpath={selector}")
                    if await more_info_element.count() > 0:
                        await more_info_element.first.click()
                        await page.wait_for_timeout(2000)  # Wait for popup to open
                        more_info_clicked = True
                        print("   🔍 Clicked 'More Information' button")
                        break
                except Exception as e:
                    continue
            
            # If popup opened, try to extract manufacturer from popup
            if more_info_clicked:
                manufacturer = await self.text_by_xpath(page, [
                    "//div[@class='AttributesModal__AttributeBox-sc-cqg6t9-0 hWOZtZ']",  # Your exact selector
                    "//div[contains(@class, 'AttributesModal__AttributeBox')]",  # More flexible
                    "//div[contains(@class, 'AttributeBox')]",  # Simplified
                    "//div[contains(text(), 'Manufacturer')]/following-sibling::*[1]",  # Manufacturer in popup
                    "//div[contains(text(), 'Brand')]/following-sibling::*[1]",  # Brand in popup
                    "//*[contains(text(), 'Manufacturer')]/following-sibling::*[1]"  # Any manufacturer text
                ])
                
                # Close popup if it's still open
                try:
                    close_selectors = [
                        "//button[contains(@class, 'close')]",
                        "//button[contains(@class, 'Close')]",
                        "//*[@aria-label='Close']",
                        "//*[contains(@class, 'modal-close')]",
                        "//button[text()='×']",
                        "//button[text()='✕']"
                    ]
                    
                    for close_selector in close_selectors:
                        try:
                            close_element = page.locator(f"xpath={close_selector}")
                            if await close_element.count() > 0:
                                await close_element.first.click()
                                await page.wait_for_timeout(1000)
                                break
                        except:
                            continue
                except:
                    pass
                    
        except Exception as e:
            print(f"   ⚠️  More Information popup failed: {str(e)[:50]}")
        
        # Fallback: Direct extraction if popup method failed
        if not manufacturer:
            manufacturer = await self.text_by_xpath(page, [
                "//li[.//text()[contains(.,'Manufacturer')]]//*[self::span or self::div][last()]",  # Your exact XPath
                "//li[contains(.,'Manufacturer')]//*[self::span or self::div][last()]",  # Simplified version
                "//*[contains(text(),'Manufacturer')]/following-sibling::*[1]",  # Following sibling
                "//*[contains(text(),'Brand')]/following-sibling::*[1]",  # Brand as manufacturer fallback
                "//div[text()='Manufacturer Information']/following-sibling::div[1]",  # Legacy fallback
                "//div[text()='Brand']/following-sibling::div[1]"  # Brand info fallback
            ])
        
        # Debug info based on your analysis
        debug_info = []
        if not title:
            debug_info.append("❌ Title (h1 not found)")
        if not price:
            debug_info.append("❌ Price (h4 with ₹ not found)")
        if not seller:
            debug_info.append("🟡 Seller ('Sold By' section missing - normal for some products)")
        if not manufacturer:
            debug_info.append("🔴 Manufacturer (tried popup + direct extraction - not found)")
            
        if debug_info:
            print(f"🔍 Meesho Debug - {page.url}")
            for info in debug_info:
                print(f"   {info}")
        else:
            print(f"✅ Meesho extraction successful for: {page.url}")
            print(f"   Title: {title[:50] + '...' if title and len(title) > 50 else title}")
            print(f"   Price: {price}")
            print(f"   Seller: {seller or 'Not available'}")
            print(f"   Manufacturer: {manufacturer or 'Not available (normal for Meesho)'}")

        # Image URL - Updated using your specifications
        # Primary: OG meta image, Fallback: picture/img pattern
        image_url = await self.get_attribute_by_xpath(page, [
            "//meta[@property='og:image']/@content"  # Primary: OG image meta
        ], "content")
        
        if not image_url:
            # DOM-based image extraction as fallback using your pattern
            image_url = await self.get_attribute_by_xpath(page, [
                "(//picture//img[@src or @data-src or @srcset])[1]/@src",  # Your exact XPath
                "(//picture//img[@src or @data-src or @srcset])[1]/@data-src",  # Data-src variant
                "//img[contains(@class,'product')]/@src",  # Product class images
                "//img[contains(@alt,'product')]/@src"  # Product alt images
            ], "src")
        
        if not image_url:
            # Additional CSS selector fallbacks
            image_url = await self.get_image_url(page, [
                "picture img",  # Picture elements
                ".product-image img",  # Product image containers
                ".carousel img",  # Image carousel
                "img[src*='meesho']",  # Meesho CDN images
                ".image-container img",  # Image container
                ".product-gallery img",  # Product gallery
                "img.lazy-image",  # Lazy loaded images
                "img[data-src]"  # Data-src images
            ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
