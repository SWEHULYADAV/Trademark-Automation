"""
Tata CLiQ Extractor
==================
Optimized selectors and logic for Tata CLiQ platform
Based on detailed PDP selector mapping with JSON-LD support
"""

import json
import re
from typing import List, Optional, Dict, Any
from .base import BaseExtractor


class TataCliqExtractor(BaseExtractor):
    """Tata CLiQ-specific product extractor with comprehensive selector mapping."""
    
    # Detailed configuration based on your PDP analysis
    SELECTORS = {
        'product_url': {
            'css': ['link[rel="canonical"]', 'meta[property="og:url"]'],
            'xpath': ['//link[@rel="canonical"]/@href', '//meta[@property="og:url"]/@content'],
            'attrs': ['href', 'content']
        },
        'title': {
            'css': ['meta[property="og:title"]', 'h1[data-test="pdpProductName"]', 'h1[class*="ProductName"]'],
            'xpath': ['//meta[@property="og:title"]/@content', '//h1[@data-test="pdpProductName"]', '//h1[contains(@class,"ProductName")]'],
            'attrs': ['content', 'text', 'text']
        },
        'image_url': {
            'css': ['meta[property="og:image"]', 'img[data-test="pdpImage"]', '[data-test="image-gallery"] img'],
            'xpath': ['//meta[@property="og:image"]/@content', '//img[@data-test="pdpImage"]/@src', '//*[@data-test="image-gallery"]//img/@src'],
            'attrs': ['content', 'src', 'src']
        },
        'price': {
            'css': ['meta[property="product:price:amount"]', '[data-test="pdpPrice"]', 'span[data-test="pdpDiscountedPrice"]'],
            'xpath': ['//meta[@property="product:price:amount"]/@content', '//*[@data-test="pdpPrice"]//text()', '//span[@data-test="pdpDiscountedPrice"]//text()'],
            'attrs': ['content', 'text', 'text']
        },
        'seller_name': {
            'css': ['#pd-brand-name', 'h2.ProductDetailsMainCard__brandName', '[itemprop="name"]'],
            'xpath': ['//h2[@id="pd-brand-name"]', '//h2[contains(@class,"ProductDetailsMainCard__brandName")]', '//h2[@id="pd-brand-name"]//*[@itemprop="name"]'],
            'attrs': ['text', 'text', 'text']
        },
        'manufacturer_name': {
            'css': ['div.MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)', 'li.MoreProductInfoComponent__details'],
            'xpath': ['(//div[@class="MoreProductInfoComponent__content"]/ul[8]/li[1])[1]', '//li[@class="MoreProductInfoComponent__details"][1]'],
            'attrs': ['text', 'text']
        }
    }
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Tata CLiQ product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        # Tata CLiQ product URL patterns
        patterns = [
            "/p-",           # Main product URLs like /brand-product-name/p-12345
            "/product/",     # Alternative product URLs
            "product-id"     # Product detail URLs with ID
        ]
        
        for h in hrefs:
            if not h or h in seen:
                continue
                
            # Check if it's a valid Tata CLiQ product URL
            if any(pat in h for pat in patterns) and "tatacliq.com" in h:
                clean_url = h.split('?')[0].split('#')[0]
                if clean_url not in seen:
                    urls.append(clean_url)
                    seen.add(clean_url)
                    
                    if len(urls) >= limit:
                        break
        
        return urls
    
    async def wait_for_products(self, page):
        """Wait for Tata CLiQ products to load."""
        try:
            await page.wait_for_selector('h1[data-test="pdpProductName"], h1[class*="ProductName"], [data-test="pdpPrice"], #pd-brand-name', timeout=5000)
        except:
            pass
    
    async def extract_json_ld_data(self, page) -> Optional[Dict[str, Any]]:
        """Extract JSON-LD structured data from Tata CLiQ page."""
        try:
            json_ld_text = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.textContent.trim());
                            
                            // Look for Product schema directly
                            if (data['@type'] === 'Product') {
                                console.log('Found Product JSON-LD');
                                return script.textContent;
                            }
                            
                            // Handle array of structured data
                            if (Array.isArray(data)) {
                                for (const item of data) {
                                    if (item && item['@type'] === 'Product') {
                                        console.log('Found Product in array');
                                        return JSON.stringify(item);
                                    }
                                }
                            }
                            
                            // Handle nested objects (@graph)
                            if (data['@graph']) {
                                for (const item of data['@graph']) {
                                    if (item && item['@type'] === 'Product') {
                                        console.log('Found Product in @graph');
                                        return JSON.stringify(item);
                                    }
                                }
                            }
                            
                        } catch (e) {
                            console.log('JSON parse error:', e.message);
                            continue;
                        }
                    }
                    console.log('No Product JSON-LD found');
                    return null;
                }
            """)
            
            if json_ld_text:
                data = json.loads(json_ld_text)
                print(f"✅ Found JSON-LD Product data: {list(data.keys())}")
                return data
            else:
                print("⚠️  No JSON-LD Product schema found")
                
        except Exception as e:
            print(f"⚠️  JSON-LD extraction failed: {e}")
        
        return None
    
    async def extract_more_product_info(self, page) -> Dict[str, Optional[str]]:
        """
        Click on 'More Product Information' to open popup and extract detailed info.
        Returns manufacturer details, specifications, and other product information.
        """
        print("🔍 Looking for 'More Product Information' link...")
        
        # Look for common patterns for "More Product Information" link
        more_info_selectors = [
            'a:has-text("More Product Information")',
            'button:has-text("More Product Information")', 
            'span:has-text("More Product Information")',
            'div:has-text("More Product Information")',
            '[class*="more"][class*="product"]',
            '[class*="more"][class*="info"]',
            '[data-test*="more"]',
            'a[href*="more"]',
            'button[class*="more"]'
        ]
        
        more_info_clicked = False
        
        for selector in more_info_selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    print(f"   ✅ Found 'More Product Info' element: {selector}")
                    
                    # Click to open popup
                    await element.click()
                    more_info_clicked = True
                    
                    # Wait for popup/modal to appear
                    await page.wait_for_timeout(2000)
                    
                    # Wait for popup content to load
                    try:
                        await page.wait_for_selector('.modal, .popup, [class*="modal"], [class*="popup"], [class*="MoreProductInfo"]', timeout=3000)
                        print("   ✅ Popup opened successfully")
                    except:
                        print("   ⚠️  Popup might not have opened or different structure")
                    
                    break
                    
            except Exception as e:
                print(f"   ❌ Failed to click: {selector} - {e}")
                continue
        
        if not more_info_clicked:
            print("   ⚠️  'More Product Information' link not found - trying to extract from existing DOM")
        
        # Extract detailed information from popup or existing DOM
        details = {}
        
        # Try to extract manufacturer information
        print("🔍 Extracting manufacturer details...")
        manufacturer_selectors = [
            # In popup
            '.modal .MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)',
            '.popup .MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)',
            '[class*="modal"] .MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)',
            '[class*="popup"] .MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)',
            
            # Direct from page
            'div.MoreProductInfoComponent__content ul:nth-child(8) li:nth-child(1)',
            'li.MoreProductInfoComponent__details',
            
            # Generic manufacturer patterns
            '[class*="manufacturer"]',
            '[data-test*="manufacturer"]',
            'li:has-text("Manufacturer")',
            'div:has-text("Manufacturer")'
        ]
        
        for selector in manufacturer_selectors:
            try:
                result = await page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            const text = el.textContent || el.innerText || '';
                            if (text.trim() && text.length > 10) {{  // Ensure meaningful content
                                return text.trim();
                            }}
                        }}
                        return null;
                    }}
                """)
                
                if result:
                    details['manufacturer'] = result
                    print(f"   ✅ Manufacturer found: {selector} = '{result[:50]}'")
                    break
                    
            except Exception as e:
                print(f"   ❌ Manufacturer selector failed: {selector} - {e}")
                continue
        
        # Try to extract brand information from popup
        print("🔍 Extracting brand details...")
        brand_selectors = [
            # In popup
            '.modal #pd-brand-name',
            '.popup #pd-brand-name', 
            '[class*="modal"] #pd-brand-name',
            '[class*="popup"] #pd-brand-name',
            '.modal [itemprop="name"]',
            '.popup [itemprop="name"]',
            
            # Direct from page (original selectors)
            '#pd-brand-name',
            'h2.ProductDetailsMainCard__brandName',
            '[itemprop="name"]'
        ]
        
        for selector in brand_selectors:
            try:
                result = await page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            const text = el.textContent || el.innerText || '';
                            if (text.trim()) {{
                                return text.trim();
                            }}
                        }}
                        return null;
                    }}
                """)
                
                if result:
                    details['brand'] = result
                    print(f"   ✅ Brand found: {selector} = '{result[:50]}'")
                    break
                    
            except Exception as e:
                print(f"   ❌ Brand selector failed: {selector} - {e}")
                continue
        
        # Close popup if it was opened
        if more_info_clicked:
            try:
                # Look for close button
                close_selectors = [
                    '.modal .close, .modal [class*="close"]',
                    '.popup .close, .popup [class*="close"]',
                    '[data-dismiss="modal"]',
                    'button:has-text("Close")',
                    'button:has-text("×")',
                    '[class*="modal"] button',
                    '[class*="popup"] button'
                ]
                
                for close_selector in close_selectors:
                    try:
                        close_element = page.locator(close_selector).first
                        if await close_element.count() > 0:
                            await close_element.click()
                            print("   ✅ Popup closed")
                            break
                    except:
                        continue
                        
                # If no close button found, try ESC key
                if not any([await page.locator(sel).first.count() > 0 for sel in close_selectors]):
                    await page.keyboard.press('Escape')
                    print("   ✅ Popup closed with ESC key")
                    
            except Exception as e:
                print(f"   ⚠️  Could not close popup: {e}")
        
        return details
    
    async def extract_field_with_config(self, page, field_name: str) -> Optional[str]:
        """Extract a field using the configured selectors with robust error handling."""
        if field_name not in self.SELECTORS:
            return None
        
        config = self.SELECTORS[field_name]
        
        # Try CSS selectors first
        for i, css_selector in enumerate(config['css']):
            try:
                attr_type = config['attrs'][i] if i < len(config['attrs']) else 'text'
                
                if attr_type == 'text':
                    # Multiple approaches for text extraction
                    result = await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('{css_selector}');
                            if (el) {{
                                return el.textContent || el.innerText || '';
                            }}
                            return null;
                        }}
                    """)
                    if result and result.strip():
                        print(f"   ✅ CSS text found: {css_selector} = '{result.strip()[:50]}'")
                        return result.strip()
                        
                elif attr_type == 'content':
                    element = page.locator(css_selector).first
                    if await element.count() > 0:
                        result = await element.get_attribute('content')
                        if result and result.strip():
                            print(f"   ✅ CSS content found: {css_selector} = '{result.strip()[:50]}'")
                            return result.strip()
                        
                else:  # src, href, etc.
                    element = page.locator(css_selector).first
                    if await element.count() > 0:
                        result = await element.get_attribute(attr_type)
                        if result and result.strip():
                            print(f"   ✅ CSS {attr_type} found: {css_selector} = '{result.strip()[:50]}'")
                            return result.strip()
                        
            except Exception as e:
                print(f"   ❌ CSS selector failed: {css_selector} - {e}")
                continue
        
        # Try XPath selectors as fallback
        for i, xpath in enumerate(config['xpath']):
            try:
                attr_type = config['attrs'][i] if i < len(config['attrs']) else 'text'
                
                if attr_type == 'text':
                    result = await page.evaluate(f"""
                        () => {{
                            const result = document.evaluate('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                            const node = result.singleNodeValue;
                            if (node) {{
                                return node.textContent || node.innerText || '';
                            }}
                            return null;
                        }}
                    """)
                    if result and result.strip():
                        print(f"   ✅ XPath text found: {xpath} = '{result.strip()[:50]}'")
                        return result.strip()
                else:
                    result = await page.evaluate(f"""
                        () => {{
                            const result = document.evaluate('{xpath}', document, null, XPathResult.STRING_TYPE, null);
                            return result.stringValue || null;
                        }}
                    """)
                    if result and result.strip():
                        print(f"   ✅ XPath {attr_type} found: {xpath} = '{result.strip()[:50]}'")
                        return result.strip()
                        
            except Exception as e:
                print(f"   ❌ XPath failed: {xpath} - {e}")
                continue
        
        print(f"   ⚠️  No data found for {field_name}")
        return None
    
    async def extract_seller_with_enhanced_logic(self, page) -> Optional[str]:
        """Extract seller/brand name with enhanced logic for Tata CLiQ structure."""
        print("🔍 Extracting seller/brand...")
        
        # Try popup first for enhanced brand information  
        popup_details = await self.extract_more_product_info(page)
        
        if popup_details.get('brand'):
            print(f"   ✅ Brand from popup: '{popup_details['brand']}'")
            return popup_details['brand']
        
        # Try configured selectors
        seller = await self.extract_field_with_config(page, 'seller_name')
        
        if seller:
            return seller
        
        # Enhanced brand extraction for Tata CLiQ specific structure
        try:
            seller = await page.evaluate("""
                () => {
                    // Look for pd-brand-name ID specifically
                    const brandElement = document.querySelector('#pd-brand-name');
                    if (brandElement) {
                        const itempropName = brandElement.querySelector('[itemprop="name"]');
                        if (itempropName) {
                            return itempropName.textContent.trim();
                        }
                        return brandElement.textContent.trim();
                    }
                    
                    // Fallback to ProductDetailsMainCard__brandName
                    const brandCard = document.querySelector('h2.ProductDetailsMainCard__brandName');
                    if (brandCard) {
                        return brandCard.textContent.trim();
                    }
                    
                    // Generic itemprop name search
                    const itempropElement = document.querySelector('[itemprop="name"]');
                    if (itempropElement) {
                        return itempropElement.textContent.trim();
                    }
                    
                    return null;
                }
            """)
            
            if seller:
                print(f"   ✅ Enhanced seller extraction: '{seller}'")
                return seller
                
        except Exception as e:
            print(f"   ❌ Enhanced seller extraction failed: {e}")
        
        return None
    
    async def extract_manufacturer_with_details(self, page) -> Optional[str]:
        """Extract manufacturer with detailed component logic and popup interaction."""
        print("🔍 Extracting manufacturer details...")
        
        # First try popup interaction to get detailed information
        popup_details = await self.extract_more_product_info(page)
        
        if popup_details.get('manufacturer'):
            print(f"   ✅ Manufacturer from popup: '{popup_details['manufacturer'][:50]}...'")
            return popup_details['manufacturer']
        
        # Try configured selectors
        manufacturer = await self.extract_field_with_config(page, 'manufacturer_name')
        
        if manufacturer:
            return manufacturer
        
        # Enhanced manufacturer extraction from product details
        try:
            manufacturer = await page.evaluate("""
                () => {
                    // Look for MoreProductInfoComponent__content structure
                    const infoContent = document.querySelector('div.MoreProductInfoComponent__content');
                    if (infoContent) {
                        // Try ul:nth-child(8) li:nth-child(1) approach
                        const ul8 = infoContent.querySelector('ul:nth-child(8)');
                        if (ul8) {
                            const li1 = ul8.querySelector('li:nth-child(1)');
                            if (li1) {
                                return li1.textContent.trim();
                            }
                        }
                        
                        // Fallback: look for any li with details class
                        const detailsLi = infoContent.querySelector('li.MoreProductInfoComponent__details');
                        if (detailsLi) {
                            return detailsLi.textContent.trim();
                        }
                        
                        // Generic approach: look for manufacturer-related text
                        const allLis = infoContent.querySelectorAll('li');
                        for (const li of allLis) {
                            const text = li.textContent.toLowerCase();
                            if (text.includes('manufactured') || text.includes('company') || text.includes('ltd') || text.includes('inc')) {
                                return li.textContent.trim();
                            }
                        }
                    }
                    
                    return null;
                }
            """)
            
            if manufacturer:
                print(f"   ✅ Enhanced manufacturer extraction: '{manufacturer[:50]}...'")
                return manufacturer
                
        except Exception as e:
            print(f"   ❌ Enhanced manufacturer extraction failed: {e}")
        
        return None
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Tata CLiQ product page with comprehensive selectors."""
        
        print(f"🔍 Extracting Tata CLiQ data from: {page.url}")
        
        # Wait for page to load completely
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
            print("✅ Page loaded (networkidle)")
        except Exception as e:
            print(f"⚠️  Network idle timeout: {e}")
        
        # Additional wait for specific Tata CLiQ elements
        try:
            await page.wait_for_selector('h1, [data-test="pdpProductName"], meta[property="og:title"], #pd-brand-name', timeout=5000)
            print("✅ Basic elements found")
        except Exception as e:
            print(f"⚠️  Element wait timeout: {e}")
        
        # Try JSON-LD first (highly recommended for Tata CLiQ)
        print("🔍 Checking for JSON-LD structured data...")
        json_ld_data = await self.extract_json_ld_data(page)
        
        # Extract using JSON-LD if available, otherwise fallback to selectors
        if json_ld_data:
            print("✅ Using JSON-LD structured data")
            
            # Get product URL
            product_url = (json_ld_data.get('url') or 
                          await self.extract_field_with_config(page, 'product_url') or 
                          page.url)
            
            # Get title
            title = (json_ld_data.get('name') or 
                    await self.extract_field_with_config(page, 'title'))
            
            # Get image URL
            image_data = json_ld_data.get('image')
            if isinstance(image_data, list) and image_data:
                image_url = image_data[0]  # Pick largest/first image
            elif isinstance(image_data, str):
                image_url = image_data
            else:
                image_url = await self.extract_field_with_config(page, 'image_url')
            
            # Get price
            offers = json_ld_data.get('offers', {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            price = (offers.get('price') or 
                    offers.get('lowPrice') or
                    await self.extract_field_with_config(page, 'price'))
            
            # Get manufacturer/brand from JSON-LD
            brand_data = json_ld_data.get('brand', {})
            manufacturer_data = json_ld_data.get('manufacturer', {})
            
            if isinstance(brand_data, dict):
                manufacturer_name = brand_data.get('name')
            elif isinstance(brand_data, str):
                manufacturer_name = brand_data
            elif isinstance(manufacturer_data, dict):
                manufacturer_name = manufacturer_data.get('name')
            elif isinstance(manufacturer_data, str):
                manufacturer_name = manufacturer_data
            else:
                manufacturer_name = await self.extract_manufacturer_with_details(page)
            
        else:
            print("⚠️  No JSON-LD found, using selector-based extraction")
            
            # Fallback to selector-based extraction
            print("🔍 Extracting product URL...")
            product_url = await self.extract_field_with_config(page, 'product_url') or page.url
            
            print("🔍 Extracting title...")
            title = await self.extract_field_with_config(page, 'title')
            
            print("🔍 Extracting image URL...")
            image_url = await self.extract_field_with_config(page, 'image_url')
            
            print("🔍 Extracting price...")
            price = await self.extract_field_with_config(page, 'price')
            
            print("🔍 Extracting manufacturer...")
            manufacturer_name = await self.extract_manufacturer_with_details(page)
        
        # Extract seller/brand name (use enhanced logic for Tata CLiQ structure)
        seller_name = await self.extract_seller_with_enhanced_logic(page)
        
        # Normalize price (strip currency, spaces, commas)
        if price:
            original_price = price
            # Convert to string if it's a number
            if isinstance(price, (int, float)):
                price = str(price)
            
            # Remove currency and normalize
            price = price.replace(',', '').replace('₹', '').replace('Rs.', '').replace('INR', '').strip()
            # Remove any non-numeric characters except decimal point
            price = re.sub(r'[^\d.]', '', price)
            print(f"   💰 Price normalized: '{original_price}' → '{price}'")
        
        # Resolve image URL to absolute if needed
        if image_url:
            if not image_url.startswith(('http', '//')):
                image_url = f"https://www.tatacliq.com{image_url}"
            elif image_url.startswith('//'):
                image_url = f"https:{image_url}"
        
        result = {
            "product_url": product_url,
            "title": title,
            "price": price,
            "seller_name": seller_name,
            "manufacturer_name": manufacturer_name,
            "image_url": image_url,
        }
        
        print(f"📊 Final Extracted Data:")
        print(f"   📄 Title: '{title}'")
        print(f"   💰 Price: '{price}'")
        print(f"   🏪 Seller: '{seller_name}'")
        print(f"   🏭 Manufacturer: '{manufacturer_name}'")
        print(f"   🖼️  Image: '{image_url[:50] if image_url else None}...'")
        
        return result
