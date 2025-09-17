"""
IndiaMART Extractor
==================
Flexible, configuration-based extractor for IndiaMART platform
Easy to update selectors without changing core logic
"""

from typing import List, Dict, Any
from .base import BaseExtractor


class IndiaMARTExtractor(BaseExtractor):
    """IndiaMART-specific product extractor with configurable selectors."""
    
    # Configuration: Easy to update selectors
    SELECTORS_CONFIG = {
        "product_links": {
            "patterns": ["/proddetail/", "/product-detail/", "/products/", "/p/"]
        },
        
        "title": {
            "xpath": [
                "//h1[@itemprop='name']",
                "//h1[contains(@class,'pdp-title')]", 
                "//h1[contains(@class,'product-title')]",
                "//h1[contains(@class,'title')]",
                "//meta[@property='og:title']/@content",
                "//meta[@name='twitter:title']/@content"
            ],
            "css": [
                "h1[itemprop='name']",
                "h1.pdp-title",
                "h1.product-title", 
                "h1[class*='title']"
            ],
            "meta": ["og:title", "twitter:title"],
            "cleanup": ["Response", "IndiaMART"]  # Values to filter out
        },
        
        "price": {
            "xpath": [
                "//*[@itemprop='price']",
                "//*[contains(@class,'pdp-price')]//*[contains(@class,'amount')]",
                "//*[contains(@class,'price')]//*[contains(@class,'amount')]",
                "//*[contains(@class,'final-price')]",
                "//*[contains(@class,'price')]//*[contains(@class,'amt')]",
                "//meta[@property='product:price:amount']/@content",
                "//meta[@name='twitter:data1']/@content"
            ],
            "css": [
                "[itemprop='price']",
                ".pdp-price .amount",
                ".price .amount",
                ".final-price",
                "[class*='price'] [class*='amt']"
            ]
        },
        
        "seller_name": {
            "xpath": [
                "//h2[@class='fs15']",
                "//a[@class='color6 pd_txu bo']",
                "//*[contains(@class,'cmp-name')]",
                "//*[contains(@class,'cmp-nm')]",
                "//*[contains(@class,'supplier-name')]",
                "//*[contains(@class,'company-name')]",
                "//a[contains(@class,'company-name')]",
                "//*[contains(@class,'sup-name')]"
            ],
            "css": [
                "h2.fs15",
                "a.color6.pd_txu.bo", 
                ".cmp-name",
                ".cmp-nm",
                ".supplier-name",
                ".company-name",
                "a.company-name",
                ".sup-name"
            ],
            "cleanup": ["IndiaMART", "Response"]
        },
        
        "manufacturer_name": {
            "xpath": [
                "//table//tr[th[normalize-space()='Manufacturer']]/td[1]",
                "//table//tr[th[normalize-space()='Brand']]/td[1]", 
                "//table//tr[th[normalize-space()='Make']]/td[1]",
                "//dl/dt[normalize-space()='Manufacturer']/following-sibling::dd[1]",
                "//dl/dt[normalize-space()='Brand']/following-sibling::dd[1]",
                "//*[contains(@class,'spec')]//*[contains(@class,'value')]",
                "//*[contains(@class,'attr')]//*[contains(@class,'value')]"
            ],
            "labels": ["manufacturer", "brand", "make", "company name"],
            "cleanup": ["not specified", "na", "n/a", "nil", "none", "other"]
        },
        
        "image_url": {
            "xpath": [
                "//img[@itemprop='image']/@src",
                "//img[@itemprop='image']/@data-src",
                "//img[@id='zoom']/@src",
                "//img[contains(@class,'pdp')]/@src",
                "//meta[@property='og:image']/@content",
                "//meta[@name='twitter:image']/@content"
            ],
            "css": [
                "img[itemprop='image']",
                "img#zoom",
                "img[class*='pdp']",
                "img[class*='product']",
                "img[class*='main']"
            ],
            "meta": ["og:image", "twitter:image"]
        }
    }
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get IndiaMART product links from listing page."""
        print("🔍 Debugging IndiaMART product links...")
        
        # Wait for page to load
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        # Get all links from the page
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        print(f"🔗 Found {len(hrefs)} total links on page")
        
        urls = []
        seen = set()
        
        # Use configurable patterns
        patterns = self.SELECTORS_CONFIG["product_links"]["patterns"]
        
        # Debug: Show some URLs to understand the pattern
        sample_urls = hrefs[:10]
        print(f"🔍 Sample URLs: {sample_urls}")
        
        for h in hrefs:
            if not h or h in seen:
                continue
                
            # Check if URL matches IndiaMART product patterns
            if any(pattern in h for pattern in patterns):
                # Clean URL - remove unnecessary parameters
                clean_url = h.split('?')[0].split('#')[0]
                if clean_url not in seen:
                    urls.append(clean_url)
                    seen.add(clean_url)
                    print(f"✅ Found product URL: {clean_url}")
                    
                    if len(urls) >= limit:
                        break
        
        print(f"📦 Total IndiaMART product URLs found: {len(urls)}")
        return urls
    
    async def wait_for_products(self, page):
        """Wait for IndiaMART products to load."""
        try:
            await page.wait_for_selector("h1[itemprop='name'], h1.pdp-title, .cmp-name", timeout=5000)
        except:
            pass
    
    async def _extract_field(self, page, field_name: str) -> str:
        """Generic field extraction using configuration."""
        config = self.SELECTORS_CONFIG.get(field_name, {})
        result = None
        
        # Try XPath selectors first
        if config.get("xpath"):
            result = await self.text_by_xpath(page, config["xpath"])
        
        # Try CSS selectors if XPath failed
        if not result and config.get("css"):
            result = await self.first_text(page, config["css"])
        
        # Try meta tags if available
        if not result and config.get("meta"):
            for meta_name in config["meta"]:
                try:
                    if meta_name.startswith("og:"):
                        meta_result = await page.get_attribute(f"meta[property='{meta_name}']", "content")
                    else:
                        meta_result = await page.get_attribute(f"meta[name='{meta_name}']", "content")
                    if meta_result and meta_result.strip():
                        result = meta_result.strip()
                        break
                except:
                    continue
        
        # Apply cleanup filters
        if result and config.get("cleanup"):
            for cleanup_term in config["cleanup"]:
                if cleanup_term.lower() in result.lower():
                    result = None
                    break
        
        return result
    
    async def _extract_manufacturer_with_labels(self, page) -> str:
        """Extract manufacturer using label-based matching."""
        config = self.SELECTORS_CONFIG["manufacturer_name"]
        
        # Try JavaScript-based label matching
        try:
            result = await page.evaluate(f"""
                () => {{
                    const labels = {config["labels"]};
                    const cleanup = {config["cleanup"]};
                    
                    // Check tables
                    const tables = document.querySelectorAll('table');
                    for (const table of tables) {{
                        const rows = table.querySelectorAll('tr');
                        for (const row of rows) {{
                            const cells = row.querySelectorAll('th, td');
                            for (let i = 0; i < cells.length - 1; i++) {{
                                const label = cells[i].textContent.toLowerCase().trim();
                                if (labels.some(l => label === l || label.includes(l))) {{
                                    const value = cells[i + 1].textContent.trim();
                                    if (value && value.length > 1 && value.length < 100) {{
                                        const lowerValue = value.toLowerCase();
                                        if (!cleanup.some(c => lowerValue.includes(c))) {{
                                            return value;
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    // Check definition lists
                    const dls = document.querySelectorAll('dl');
                    for (const dl of dls) {{
                        const dts = dl.querySelectorAll('dt');
                        for (const dt of dts) {{
                            const label = dt.textContent.toLowerCase().trim();
                            if (labels.some(l => label === l || label.includes(l))) {{
                                const dd = dt.nextElementSibling;
                                if (dd && dd.tagName === 'DD') {{
                                    const value = dd.textContent.trim();
                                    if (value && value.length > 1 && value.length < 100) {{
                                        const lowerValue = value.toLowerCase();
                                        if (!cleanup.some(c => lowerValue.includes(c))) {{
                                            return value;
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    return null;
                }}
            """)
            if result:
                return result
        except:
            pass
        
        # Fallback to XPath
        return await self.text_by_xpath(page, config["xpath"])
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data using flexible configuration."""
        
        print(f"🔍 Extracting data from: {page.url}")
        
        # Wait for page to load
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        # Get product URL (canonical if available)
        product_url = await self.get_attribute_by_xpath(page, [
            "//link[@rel='canonical']/@href"
        ], "href") or page.url
        
        # Extract all fields using configuration
        title = await self._extract_field(page, "title")
        price = await self._extract_field(page, "price")
        seller_name = await self._extract_field(page, "seller_name")
        
        # Special handling for manufacturer (label-based)
        manufacturer_name = await self._extract_manufacturer_with_labels(page)
        
        # Extract image URL
        image_url = await self._extract_field(page, "image_url")
        if not image_url:
            image_url = await self.get_image_url(page, 
                self.SELECTORS_CONFIG["image_url"]["css"], 
                use_og_meta=True)
        
        # Additional title extraction if needed
        if not title:
            try:
                page_title = await page.title()
                if page_title and " - " in page_title:
                    title = page_title.split(" - ")[0].strip()
                elif page_title and " | " in page_title:
                    title = page_title.split(" | ")[0].strip()
            except:
                pass
        
        result = {
            "product_url": product_url,
            "title": title,
            "price": price,
            "seller_name": seller_name,
            "manufacturer_name": manufacturer_name,
            "image_url": image_url,
        }
        
        print(f"📊 Extracted data: title='{title}', price='{price}', seller='{seller_name}'")
        return result
    
    @classmethod
    def update_selectors(cls, field_name: str, new_selectors: Dict[str, Any]):
        """Update selectors configuration dynamically.
        
        Usage:
        IndiaMARTExtractor.update_selectors("title", {
            "xpath": ["//h1[@class='new-title']"],
            "css": [".new-title-class"]
        })
        """
        if field_name in cls.SELECTORS_CONFIG:
            cls.SELECTORS_CONFIG[field_name].update(new_selectors)
            print(f"✅ Updated {field_name} selectors: {new_selectors}")
        else:
            print(f"❌ Field {field_name} not found in configuration")
    
    @classmethod
    def add_selector(cls, field_name: str, selector_type: str, selector: str):
        """Add a single selector to existing configuration.
        
        Usage:
        IndiaMARTExtractor.add_selector("title", "xpath", "//h1[@class='newest-title']")
        """
        if field_name in cls.SELECTORS_CONFIG:
            if selector_type in cls.SELECTORS_CONFIG[field_name]:
                cls.SELECTORS_CONFIG[field_name][selector_type].insert(0, selector)
                print(f"✅ Added {selector_type} selector for {field_name}: {selector}")
            else:
                cls.SELECTORS_CONFIG[field_name][selector_type] = [selector]
                print(f"✅ Created new {selector_type} list for {field_name}: {selector}")
        else:
            print(f"❌ Field {field_name} not found in configuration")
    
    @classmethod
    def get_current_config(cls) -> Dict[str, Any]:
        """Get current configuration for debugging."""
        return cls.SELECTORS_CONFIG
    
    @classmethod
    def print_config(cls, field_name: str = None):
        """Print current configuration for a field or all fields."""
        if field_name:
            if field_name in cls.SELECTORS_CONFIG:
                print(f"📋 Configuration for {field_name}:")
                for key, value in cls.SELECTORS_CONFIG[field_name].items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ Field {field_name} not found")
        else:
            print("📋 Full IndiaMART Configuration:")
            for field, config in cls.SELECTORS_CONFIG.items():
                print(f"\n{field}:")
                for key, value in config.items():
                    print(f"  {key}: {value}")

# Usage Examples:
# 
# # Add new selector at runtime
# IndiaMARTExtractor.add_selector("title", "xpath", "//h1[@class='new-title-class']")
#
# # Update entire selector group
# IndiaMARTExtractor.update_selectors("seller_name", {
#     "xpath": ["//span[@class='new-seller-class']"],
#     "css": [".new-seller"]
# })
#
# # Print current config
# IndiaMARTExtractor.print_config("title")
