"""
Myntra Extractor
================
Optimized selectors and logic for Myntra platform
"""

from typing import List
from .base import BaseExtractor


class MyntraExtractor(BaseExtractor):
    """Myntra-specific product extractor."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Myntra product links from listing page."""
        
        # Wait for products to load
        try:
            await page.wait_for_selector("a[href*='/buy/'], .product-base, .product-productMetaInfo", timeout=5000)
        except:
            pass
        
        # Get all href links
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        # Myntra product URL patterns
        patterns = [
            "/buy/",           # Main product URLs like /buy/product-name_12345
            "-/p/",           # Alternative product URLs
            "/product/",      # Product detail URLs
        ]
        
        print(f"🔍 Found {len(hrefs)} total links on page")
        
        for h in hrefs:
            # Check if it's a valid Myntra product URL
            if any(pat in h for pat in patterns) and h not in seen and "myntra.com" in h:
                seen.add(h)
                urls.append(h)
                print(f"   ✅ Product link: {h}")
                if len(urls) >= limit:
                    break
        
        # If no /buy/ links found, try alternative selectors
        if not urls:
            print("🔄 No /buy/ links found, trying alternative selectors...")
            
            # Try to find product cards and extract href from them
            product_links = await page.evaluate("""
                () => {
                    const selectors = [
                        '.product-base a',
                        '.product-productMetaInfo a', 
                        '[class*="product"] a[href*="myntra.com"]',
                        'a[href*="/buy/"]',
                        'a[data-refreshpage="true"]'
                    ];
                    
                    const links = [];
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            if (el.href && el.href.includes('myntra.com')) {
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
        
        print(f"📋 Total Myntra product links found: {len(urls)}")
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Myntra product page using your XPath mappings."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, .pdp-price", timeout=5000)
        except:
            pass
        
        # Title - Using your exact XPath mapping: //h1[contains(@class,'pdp-title')]
        # Note: Based on your testing, this gives seller title, so we use it carefully
        title = await self.text_by_xpath(page, [
            "//h1[contains(@class,'pdp-title')]"  # Your exact XPath from mapping
        ])
        
        # If this gives seller name instead of product title, try alternatives
        if title and any(word in title.lower() for word in ['store', 'seller', 'shop', 'brand']):
            title = await self.text_by_xpath(page, [
                "//h1[contains(@class,'pdp-name')]",  # Product name (not seller title)
                "//h1[not(contains(@class,'pdp-title'))]",  # Any h1 that's NOT seller title
                "//span[contains(@class,'pdp-name')]",  # Product name in span
                "//div[contains(@class,'pdp-name')]",   # Product name in div
            ])
        
        # Fallback: Try CSS selectors for product title
        if not title:
            title = await self.first_text(page, [
                ".pdp-name", ".product-title", ".product-name", 
                "h1:not(.pdp-title)", "h2"
            ])
        
        # If still no title, try meta og:title as fallback
        if not title:
            try:
                title = await page.evaluate("""
                    () => {
                        const metaTitle = document.querySelector('meta[property="og:title"]');
                        if (metaTitle && metaTitle.content) {
                            return metaTitle.content;
                        }
                        return null;
                    }
                """)
            except:
                pass

        # Price - Using your exact XPath mapping: //span[contains(@class,'pdp-price')]
        price = await self.text_by_xpath(page, [
            "//span[contains(@class,'pdp-price')]",  # Your exact XPath mapping
            "//span[contains(@class,'price')]",      # Fallback price span
            "//*[contains(text(),'₹')]",             # Fallback with rupee symbol
        ])
        
        # Clean and format price
        if price:
            import re
            # Extract price with ₹ symbol
            price_match = re.search(r'₹\s*[\d,]+', price.replace('\n', ' '))
            if price_match:
                price = price_match.group(0)
            else:
                # Clean any extra text
                price = price.split('\n')[0].strip()

        # Seller Name - Using your XPath mapping: //div[normalize-space()='Sold By']/following-sibling::div[1]
        seller = await self.text_by_xpath(page, [
            "//div[normalize-space()='Sold By']/following-sibling::div[1]",  # Your exact XPath mapping
            "//div[contains(text(),'Sold By')]/following-sibling::div[1]",   # Flexible version
            "//span[text()='Sold By']/following-sibling::span[1]",           # Alternative structure
        ])
        
        # Note: Based on your consistency notes, "Sold By" section may be missing for Myntra-owned items
        if not seller:
            # Use h1.pdp-title as seller for Myntra-owned products
            seller = await self.text_by_xpath(page, [
                "//h1[contains(@class,'pdp-title')]",  # pdp-title contains seller/brand name
            ])
        
        # If still no seller found, use "Myntra" as default
        if not seller:
            seller = "Myntra"
        
        # Clean seller name if found
        if seller and seller != "Myntra":
            import re
            # Remove extra info after seller name
            seller = re.split(r'\s+\d+|View\s+Shop', seller)[0].strip()

        # Manufacturer Name - Using your XPath mapping: //div[normalize-space()='Manufacturer Information']/following-sibling::div[1]
        manufacturer = await self.text_by_xpath(page, [
            "//div[normalize-space()='Manufacturer Information']/following-sibling::div[1]",  # Your exact XPath
            "//div[contains(text(),'Manufacturer Information')]/following-sibling::div[1]",   # Flexible version
            "//span[contains(text(),'Manufacturer')]/following-sibling::span[1]",             # Alternative structure
        ])
        
        # Note: Based on your consistency notes, manufacturer info is "Often but not always" present
        # If no specific manufacturer section, try to extract brand as manufacturer
        if not manufacturer:
            # Try brand-related selectors since brand often equals manufacturer for fashion
            manufacturer = await self.text_by_xpath(page, [
                "//a[contains(@class, 'pdp-brandLink')]",  # Brand link
                "//span[contains(@class, 'pdp-brand')]",    # Brand span
                "//div[contains(@class, 'brand')]",         # Brand div
            ])
        
        # If we have a seller name and no manufacturer, use seller as manufacturer (common for fashion)
        if not manufacturer and seller and seller != "Myntra":
            manufacturer = seller
        
        # Use "N/A" for unavailable manufacturer (as per your schema note)
        if not manufacturer:
            manufacturer = "N/A"
        
        # Debug info
        debug_info = []
        if not title:
            debug_info.append("❌ Title (Product name not found)")
        if not price:
            debug_info.append("❌ Price (//span[contains(@class,'pdp-price')] not found)")
        if not seller or seller == "Myntra":
            debug_info.append("🟡 Seller ('Sold By' missing - normal for Myntra-owned products)")
        if not manufacturer or manufacturer == "N/A":
            debug_info.append("🔴 Manufacturer (rarely present - normal per your mapping)")
            
        if debug_info:
            print(f"🔍 Myntra Debug - {page.url}")
            for info in debug_info:
                print(f"   {info}")
        else:
            print(f"✅ Myntra extraction successful for: {page.url}")
            print(f"   Title: {title[:50] + '...' if title and len(title) > 50 else title}")
            print(f"   Price: {price}")
            print(f"   Seller: {seller}")
            print(f"   Manufacturer: {manufacturer}")

        # Image URL - Using your XPath mapping: //meta[@property='og:image']/@content (Primary)
        # With DOM fallback to gallery <picture><img ...> (as per your notes)
        image_url = None
        
        # Primary: OG meta image (your exact XPath mapping) - ✅ Mostly consistent
        image_url = await self.get_attribute_by_xpath(page, [
            "//meta[@property='og:image']"  # Your exact XPath mapping
        ], "content")
        
        # Secondary: DOM fallback to product gallery images (reliable fallback per your notes)
        if not image_url:
            image_url = await self.get_image_url(page, [
                "picture img",  # Gallery <picture><img ...> as per your notes
                ".image-grid-image",  # Main product image
                ".product-sliderContainer img",  # Image slider
                ".image-grid-container img",  # Image grid
                "div.productImageContainer img",  # Product image container
                ".slides img",  # Slide images
                "img[src*='assets.myntassets.com']",  # Myntra CDN images
                ".product-image img",  # Product image
                ".productDetailImageContainer img",  # Detail image container
                ".product-imageSlider img"  # Image slider variant
            ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": seller,
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
