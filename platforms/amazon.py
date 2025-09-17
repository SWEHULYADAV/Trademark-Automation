"""
Amazon Extractor
================
Enhanced Amazon extractor with variant detection and pagination support
"""

from typing import List, Dict, Any
from .base import BaseExtractor
import re
import logging

logger = logging.getLogger(__name__)

class AmazonExtractor(BaseExtractor):
    """Amazon-specific product extractor with variant detection and pagination."""
    
    def __init__(self):
        super().__init__()
        self.platform_type = "pagination"  # Amazon uses pagination
        self.variant_support = True  # Amazon has variants
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Amazon product links from listing page, filtering out sponsored/tracking URLs."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        
        # Strict pattern for Amazon product URLs
        # Only capture URLs that have '/dp/' followed by a product ID (alphanumeric)
        # and don't contain tracking parameters or sponsored URL patterns
        pattern = r'/dp/[A-Z0-9]{10}'
        sponsored_patterns = [
            'aax-eu-zaz.amazon.in',  # Tracking URLs for sponsored products
            'amazon.in/x/c/',
            'amazon.in/s?k=',
            'amazon.in/s?ie=',
            'amazon.in/ref='
        ]
        
        for h in hrefs:
            # Skip if it's a sponsored/tracking URL
            if any(spn in h for spn in sponsored_patterns):
                continue
                
            # Only keep URLs that match the product ID pattern
            if re.search(pattern, h):
                # Clean URL to standard format
                clean_url = h.split("?")[0]
                # Remove any tracking parameters
                clean_url = clean_url.split("#")[0]
                
                if clean_url not in seen and "amazon.in" in clean_url:
                    seen.add(clean_url)
                    urls.append(clean_url)
                    if len(urls) >= limit:
                        break
        
        return urls
    
    async def extract_product_data(self, page) -> dict:
        """Extract Amazon product data using common extraction + Amazon-specific logic."""
        try:
            # Wait for critical elements to load
            try:
                await page.wait_for_selector("h1#title, span#productTitle", timeout=10000)
            except:
                logger.warning("Critical product elements not found on Amazon page")

            # Use common extraction for basic data
            common_data = await self.extract_common_data(page)
            
            # Amazon-specific price cleaning
            if common_data.get('price'):
                price = common_data['price']
                price = re.sub(r'[^\d.,₹]', '', price)
                if '₹' not in price and not price.startswith('$'):
                    price = f"₹{price}"
                common_data['price'] = price
            
            # Handle "Out of stock" scenario
            out_of_stock = await self.first_text(page, [
                "div#availability span",
                "div#outOfStock",
                "div#unavailable",
                "span.a-size-medium.a-color-state"
            ])
            if out_of_stock and "out of stock" in out_of_stock.lower():
                common_data['price'] = "Out of stock"
        
            # Amazon-specific seller extraction
            if not common_data.get('seller_name'):
                seller = await self.first_text(page, [
                    "span#bylineInfo",
                    "a#bylineInfo",
                    "a.a-link-normal",
                    "div#merchant-info",
                    "div#sellerProfileTriggerId",
                    "div#sellerProfileTriggerId span"
                ])
                
                # Fallback for seller using XPath
                if not seller:
                    seller = await self.text_by_xpath(page, [
                        "//span[contains(text(),'Sold by')]/following-sibling::span[1]",
                        "//span[contains(text(),'Ships from')]/following-sibling::span[1]",
                        "//a[contains(@id, 'sellerProfileTriggerId')]",
                        "//div[contains(@id, 'merchant-info')]//a"
                    ])
                
                common_data['seller_name'] = seller or ""
            
            # Amazon-specific manufacturer extraction
            if not common_data.get('manufacturer_name'):
                manufacturer = await self.text_by_xpath(page, [
                    "//ul[@class='a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list']/li[contains(., 'Brand:')]",
                    "//ul[@class='a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list']/li[contains(., 'Manufacturer:')]",
                    "//div[@id='productDetails_detailBullets_sections1']//th[contains(text(), 'Brand')]/following-sibling::td",
                    "//div[@id='productDetails_detailBullets_sections1']//th[contains(text(), 'Manufacturer')]/following-sibling::td",
                    "//div[@id='productDetails']//th[contains(text(), 'Brand')]/following-sibling::td",
                    "//div[@id='productDetails']//th[contains(text(), 'Manufacturer')]/following-sibling::td",
                    "//div[@id='detailBulletsWrapper_feature_div']//span[contains(text(), 'Brand')]/following-sibling::span",
                    "//div[@id='detailBulletsWrapper_feature_div']//span[contains(text(), 'Manufacturer')]/following-sibling::span"
                ])
                
                # Clean manufacturer name
                if manufacturer:
                    manufacturer = re.sub(r'^(Brand:|Manufacturer:)\s*', '', manufacturer)
                    manufacturer = manufacturer.strip().strip(':').strip()
                    manufacturer = manufacturer.split('Packer')[0].strip()
                    manufacturer = manufacturer.split('Seller')[0].strip()
                    manufacturer = manufacturer.split('Imported by')[0].strip()
                    manufacturer = manufacturer.split('Brand:')[0].strip()
                    manufacturer = manufacturer.split('Manufacturer:')[0].strip()
            
                    common_data['manufacturer_name'] = manufacturer or ""
            
            # Amazon-specific image extraction
            if not common_data.get('image_url'):
                image_url = await self.get_image_url(page, [
                    "img#landingImage",
                    "img#imgBlkFront",
                    "img#main-image",
                    "img#imageBlockFront",
                    "img#productImage",
                    "img#acrImage"
                ], use_og_meta=True)
                common_data['image_url'] = image_url or ""
            
            # Add product URL
            common_data['product_url'] = page.url
            
            return common_data
            
        except Exception as e:
            print(f"⚠️ Error extracting Amazon product data: {e}")
            return {
                "product_url": page.url,
                "title": "",
                "price": "",
                "seller_name": "",
                "manufacturer_name": "",
                "image_url": ""
            }
    
    # ==================== AMAZON-SPECIFIC PAGINATION ====================
    
    async def go_to_next_page(self, page) -> bool:
        """Amazon-specific next page navigation."""
        try:
            # Amazon pagination selectors
            next_selectors = [
                "a[aria-label='Next Page']",
                ".a-pagination .a-last a",
                "a:has-text('Next')",
                ".a-pagination .a-next a",
                "[data-testid='pagination-next-button']",
                ".s-pagination-next"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = page.locator(selector)
                    if await next_button.count() > 0:
                        # Check if button is disabled
                        is_disabled = await next_button.get_attribute("aria-disabled")
                        if is_disabled == "true":
                            return False
                        
                        await next_button.click()
                        await page.wait_for_timeout(5000)  # Wait for page load
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False
    
    # ==================== AMAZON-SPECIFIC VARIANT EXTRACTION ====================
    
    async def extract_variants(self, page, main_product_url: str) -> List[Dict[str, Any]]:
        """Extract Amazon product variants (size, color, style, etc.)."""
        try:
            variants = []
            
            # Wait for variant selectors to load
            await page.wait_for_timeout(2000)
            
            # Detect Amazon variant dimensions
            variant_dimensions = await self._detect_amazon_variants(page)
            
            if not variant_dimensions:
                return []
            
            print(f"🎨 Found Amazon variants: {list(variant_dimensions.keys())}")
            
            # Extract variants for each dimension
            for dim_name, options in variant_dimensions.items():
                print(f"   📏 {dim_name}: {len(options)} options")
                
                for option in options:
                    try:
                        # Select the variant option
                        await self._select_amazon_variant(page, dim_name, option)
                        await page.wait_for_timeout(3000)
                        
                        # Extract variant data
                        variant_data = await self._extract_amazon_variant_data(page, main_product_url, dim_name, option)
                        if variant_data:
                            variants.append(variant_data)
                            print(f"      ✅ {dim_name}: {option['name']} - {variant_data.get('variant_price', 'N/A')}")
                        
                    except Exception as e:
                        print(f"      ❌ Error extracting {dim_name} variant {option['name']}: {e}")
                        continue
            
            return variants
            
        except Exception as e:
            print(f"⚠️ Error in Amazon variant extraction: {e}")
            return []
    
    async def _detect_amazon_variants(self, page) -> Dict[str, List[Dict[str, Any]]]:
        """Detect Amazon variant dimensions and options."""
        try:
            variant_data = await page.evaluate("""
                    () => {
                    const dimensions = {};
                    
                    // Look for Amazon's inline-twister-row containers
                    const twisterRows = document.querySelectorAll('div[id*="inline-twister-row-"]');
                    
                    for (const row of twisterRows) {
                        const dimName = row.id.replace('inline-twister-row-', '').replace('_name', '');
                        const options = [];
                        
                        // Get options from li elements with data-asin
                        const optionElements = row.querySelectorAll('li[data-asin]');
                        for (const option of optionElements) {
                            if (option.getAttribute('data-initiallyUnavailable') !== 'true') {
                                const asin = option.getAttribute('data-asin');
                                const name = option.querySelector('.swatch-title-text-display')?.textContent?.trim() ||
                                           option.querySelector('img')?.alt?.trim() ||
                                           option.querySelector('.a-button-text')?.textContent?.trim() || 'Unknown';
                                
                                options.push({
                                    name: name,
                                    asin: asin,
                                    value: asin
                                });
                            }
                        }
                        
                        if (options.length > 0) {
                            dimensions[dimName] = options;
                        }
                    }
                    
                    // Also check for select dropdowns
                    const selectElements = document.querySelectorAll('select[name*="dropdown_selected"]');
                    for (const select of selectElements) {
                        const name = select.name.replace('dropdown_selected_', '').replace('_name', '');
                        const options = [];
                        
                        for (const option of select.options) {
                            if (option.value && option.textContent.trim() !== 'Select') {
                                options.push({
                                    name: option.textContent.trim(),
                                    asin: option.getAttribute('data-asin') || option.value,
                                    value: option.value
                                });
                            }
                        }
                        
                        if (options.length > 0) {
                            dimensions[name] = options;
                        }
                    }
                    
                    return dimensions;
                    }
                """)
            
            return variant_data
            
        except Exception as e:
            print(f"⚠️ Error detecting Amazon variants: {e}")
            return {}
    
    async def _select_amazon_variant(self, page, dim_name: str, option: Dict[str, Any]):
        """Select a specific Amazon variant option."""
        try:
            # Try different Amazon variant selector patterns
            selectors = [
                f'li[data-asin="{option["asin"]}"]',
                f'select[name="dropdown_selected_{dim_name}_name"]',
                f'select[id="variation_{dim_name}_name"]',
                f'[data-asin="{option["asin"]}"]'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        # Check if it's a select dropdown
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        
                        if tag_name == 'select':
                            await element.select_option(option['value'])
                        else:
                            await element.click()
                        
                        return
                except Exception:
                    continue
            
            # If not found, try clicking on the option text
            try:
                text_selector = f'li:has-text("{option["name"]}")'
                text_element = page.locator(text_selector)
                if await text_element.count() > 0:
                    await text_element.click()
                    return
            except Exception as e:
                print(f"⚠️ Error selecting Amazon variant: {e}")
        
        except Exception as e:
            print(f"⚠️ Error in Amazon variant selection: {e}")
    
    async def _extract_amazon_variant_data(self, page, main_product_url: str, dim_name: str, option: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for a specific Amazon variant."""
        try:
            # Get current page URL (might be different for variants)
            variant_url = page.url
            
            # Extract basic product data
            variant_data = await self.extract_product_data(page)
            
            # Add variant-specific information
            variant_data.update({
                'variant_product_url': variant_url,
                'main_product_url': main_product_url,
                'variant_price': variant_data.get('price', ''),
                'variant_type': dim_name,
                'variant_option': option['name'],
                'variant_asin': option.get('asin', '')
            })
            
            return variant_data
            
        except Exception as e:
            print(f"⚠️ Error extracting Amazon variant data: {e}")
            return None