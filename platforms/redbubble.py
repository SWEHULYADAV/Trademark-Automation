"""
Redbubble Extractor
==================
Optimized selectors and logic for Redbubble platform using XPath mapping
"""

from typing import List
from .base import BaseExtractor


class RedbubbleExtractor(BaseExtractor):
    """Redbubble-specific product extractor using XPath analysis."""
    
    async def get_product_links(self, page, limit: int) -> List[str]:
        """Get Redbubble product links from listing page."""
        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
        urls = []
        seen = set()
        patterns = ["/i/", "/shop/p/"]
        
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
            await page.wait_for_selector("a[href*='/i/'], h1", timeout=5000)
        except:
            pass
    
    async def extract_product_data(self, page) -> dict:
        """Extract product data from Redbubble product page using XPath mapping."""
        
        # Wait for content to load
        try:
            await page.wait_for_selector("h1, [data-testid*='title']", timeout=5000)
        except:
            pass
        
        # Give page time to load completely
        import asyncio
        await asyncio.sleep(2)
        
        # Title - Using h1 tag (from your XPath analysis)
        title = await self.text_by_xpath(page, [
            "//h1/text()",  # Primary XPath from your analysis
            "//h1//text()", # Get all text content from h1
        ])
        
        # Clean title if found
        if title:
            title = title.strip()
        
        # Fallback to CSS selectors if XPath fails
        if not title:
            title = await self.first_text(page, [
                "h1",
                "[data-testid*='title']",
                ".product-title"
            ])

        # Artist/Seller - Using exact XPath from your analysis
        artist = await self.text_by_xpath(page, [
            "//p[contains(text(), 'Designed and sold by')]/a/text()",  # Exact XPath from your mapping
        ])
        
        # Clean artist name if found
        if artist:
            artist = artist.strip()
        
        # If exact XPath fails, try variations
        if not artist:
            artist = await self.text_by_xpath(page, [
                "//p[contains(text(), 'Designed and sold by')]/a",  # Get element text
                "//span[contains(text(), 'Designed and sold by')]/a/text()",
                "//div[contains(text(), 'Designed and sold by')]/a/text()",
                "//*[contains(text(), 'Designed and sold by')]/a/text()",
            ])
        
        # Extract artist from URL if still not found
        if not artist:
            import re
            url = page.url
            # Extract from URL like /by-ShopIconicTees9/ 
            artist_match = re.search(r'/by-([^/]+)/', url)
            if artist_match:
                artist = artist_match.group(1).replace('-', ' ')
            else:
                # Try different URL pattern
                artist_match = re.search(r'-by-([^/]+)/', url)
                if artist_match:
                    artist = artist_match.group(1).replace('-', ' ')
        
        # JavaScript fallback for artist if XPath fails
        if not artist:
            try:
                artist = await page.evaluate("""
                    () => {
                        // Look for the exact pattern
                        const elements = Array.from(document.querySelectorAll('p')).filter(
                            el => el.textContent && el.textContent.includes('Designed and sold by')
                        );
                        
                        for (let el of elements) {
                            const link = el.querySelector('a');
                            if (link && link.textContent) {
                                return link.textContent.trim();
                            }
                        }
                        
                        return null;
                    }
                """)
            except Exception as e:
                print(f"🔧 JS evaluation failed for Redbubble artist: {str(e)}")
        
        # Final fallback - extract from URL structure
        if not artist:
            # Set a default based on URL pattern if all else fails
            artist = "Unknown Artist"

        # Price (current) - Using exact XPath from your analysis
        price = None
        currency_symbols = ['€', '$', '£', '¥', '₹']
        
        for symbol in currency_symbols:
            if not price:
                # Use exact XPath from your mapping
                price = await self.text_by_xpath(page, [
                    f"//p[contains(text(), '{symbol}')][1]/text()",  # Exact XPath from your analysis
                ])
                
                if price:
                    # Clean price - extract just the first price amount
                    import re
                    # Find first occurrence of currency + numbers
                    price_match = re.search(f'\\{symbol}[\\d.,]+', price)
                    if price_match:
                        price = price_match.group(0)
                    break
        
        # Alternative selectors if XPath fails
        if not price:
            price = await self.first_text(page, [
                "[data-testid*='price']",
                ".price",
                "[class*='price']"
            ])
            
        # Clean up price if found through alternative method
        if price and not any(symbol in price for symbol in currency_symbols):
            # Try to find price in the text
            import re
            for symbol in currency_symbols:
                price_match = re.search(f'\\{symbol}[\\d.,]+', price)
                if price_match:
                    price = price_match.group(0)
                    break
        
        # Original Price / Discount - Using exact XPath from your analysis
        original_price = None
        for symbol in currency_symbols:
            if not original_price:
                # Check if second price element exists (for discounts)
                original_price = await self.text_by_xpath(page, [
                    f"//p[contains(text(), '{symbol}')][2]/text()",  # Exact XPath from your analysis
                ])
                
                if original_price:
                    import re
                    # Extract the original price amount
                    price_match = re.search(f'\\{symbol}[\\d.,]+', original_price)
                    if price_match:
                        original_price = price_match.group(0)
                    break
        
        # If no separate original price found, but price contains discount info, parse it
        if not original_price and price and ('(' in price or 'off' in price):
            import re
            # Extract original price from strings like "$21.14 $28.19 (25% off)"
            for symbol in currency_symbols:
                # Find all prices in the string
                prices = re.findall(f'\\{symbol}[\\d.,]+', price)
                if len(prices) >= 2:
                    # First is current, second is original
                    price = prices[0]  # Update current price
                    original_price = prices[1]  # Set original price
                    break
        
        # Product Features/Specs (from your XPath analysis)
        features = None
        
        features = await self.text_by_xpath(page, [
            "//div[contains(@class, 'Product features')]/following-sibling::ul[1]/li/text()",  # Primary XPath from your analysis
            "//div[contains(text(), 'Product features')]/following-sibling::ul/li/text()",
            "//div[contains(text(), 'Features')]/following-sibling::ul/li/text()",
            "//ul[contains(@class, 'features')]/li/text()",
        ])
        
        # If features found, format them
        if features:
            if isinstance(features, list):
                features = "; ".join(features)
            features = features.strip()
        else:
            features = "N/A"
        
        # Set manufacturer as artist for Redbubble (artist creates the design)
        manufacturer = artist if artist else "N/A"
        
        # Enhanced debugging for Redbubble
        debug_info = []
        if not title:
            debug_info.append("❌ Title (h1 not found)")
        if not artist or artist == "Unknown Artist":
            debug_info.append("❌ Artist ('Designed and sold by' XPath failed)")
        if not price:
            debug_info.append("❌ Price (currency XPath failed)")
            
        if debug_info:
            print(f"🔍 Redbubble Debug - {page.url[:80]}")
            for info in debug_info:
                print(f"   {info}")
            # Additional debug - show what we actually found
            print(f"   📝 Raw title: {title or 'None'}")
            print(f"   👤 Raw artist: {artist or 'None'}")
            print(f"   💰 Raw price: {price or 'None'}")
        else:
            print(f"✅ Redbubble extraction successful")
            print(f"   Title: {title[:30]}...")
            print(f"   Price: {price}")
            print(f"   Artist: {artist}")
            if original_price:
                print(f"   Original Price: {original_price}")

        # Image URL - Using OG meta as primary (your specification)
        image_url = await self.get_attribute_by_xpath(page, [
            "//meta[@property='og:image']/@content"  # Primary: OG image meta
        ], "content")
        
        if not image_url:
            # DOM-based image extraction as fallback
            image_url = await self.get_image_url(page, [
                ".artwork img",  # Artwork images
                ".product-image img",  # Product images
                "img[src*='redbubble']",  # RedBubble CDN images
                "img[src*='rb-usercontent']",  # RedBubble user content CDN
                ".gallery img",  # Gallery images
                ".design-image img",  # Design images
                ".main-image img",  # Main image
                "img[alt*='artwork']",  # Artwork alt text
                "img[data-testid*='image']"  # Data test id images
            ])

        return {
            "product_url": page.url,
            "title": title,
            "price": price,
            "seller_name": artist,  # Using artist as seller for Redbubble
            "manufacturer_name": manufacturer,
            "image_url": image_url
        }
