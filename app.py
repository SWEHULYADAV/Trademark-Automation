#app.py
# # E-Commerce Automation Tool
# Comprehensive multi-platform product scraping with variant extraction
# Version: 2.0

import asyncio
import argparse
import csv
import os
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List, Tuple, Dict, Any
from dotenv import load_dotenv
import pandas as pd
import tldextract
from browser_use import Agent, ActionResult
from browser_use.llm import ChatGoogle, ChatOpenAI, ChatAnthropic, ChatGroq
from browser_use.browser.session import BrowserSession

# Import platform-specific extractors
from platforms import detect_platform, get_extractor, get_platform_display_name


class ECommerceAutomation:
    """Main E-Commerce Automation Tool"""
    
    def __init__(self):
        self.results_dir = Path("results")
        self.timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        self.platform_name = ""
        self.domain_name = ""
        self.session_dir = None
        self.products_csv = None
        self.variants_csv = None
        self.whitelisted_sellers = []
        self.llm_provider = None
        self.llm_model = None
        self.llm_instance = None
        
    def setup_environment(self):
        """Setup environment and load configuration"""
        load_dotenv()
        
        # Auto-detect LLM provider
        self.llm_provider, self.llm_model, self.llm_instance = self.detect_llm_provider()
        
        # Load whitelisted sellers
        self.whitelisted_sellers = self.load_whitelisted_sellers()
        
        print(f"🔍 Detected LLM Provider: {self.llm_provider}")
        print(f"🤖 Using Model: {self.llm_model}")
        print(f"✅ Whitelisted Sellers: {len(self.whitelisted_sellers)} loaded")
    
    def detect_llm_provider(self) -> Tuple[str, str, Any]:
        """Auto-detect LLM provider from .env file"""
        providers = [
        {
            'name': 'OpenAI',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL'),
            'llm_class': ChatOpenAI
        },
        {
            'name': 'Anthropic', 
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'model': os.getenv('ANTHROPIC_MODEL'),
            'llm_class': ChatAnthropic
        },
        {
            'name': 'Google',
            'api_key': os.getenv('GOOGLE_API_KEY'),
            'model': os.getenv('GOOGLE_MODEL'),
            'llm_class': ChatGoogle
        },
        {
            'name': 'Groq',
            'api_key': os.getenv('GROQ_API_KEY'),
            'model': os.getenv('GROQ_MODEL'),
            'llm_class': ChatGroq
        }
        ]
        
        for provider in providers:
            if provider['api_key']:
                if not provider['model']:
                    raise RuntimeError(f"❌ {provider['name']} API key found but no model specified. Please set {provider['name'].upper()}_MODEL in .env file.")
                print(f"🔑 Using {provider['name']} API key: {provider['api_key'][:10]}...")
                print(f"🤖 Using {provider['name']} model: {provider['model']}")
                return provider['name'], provider['model'], provider['llm_class']
        
        raise RuntimeError("❌ No valid API key found in .env file. Please uncomment one provider section.")

    def load_whitelisted_sellers(self) -> List[str]:
        """Load whitelisted sellers from .env file"""
        whitelisted_str = os.getenv("WHITELISTED_SELLERS", "")
        if not whitelisted_str:
            return []
        
        # Split by comma and clean up
        sellers = [seller.strip() for seller in whitelisted_str.split(",") if seller.strip()]
        return sellers
    
    def check_whitelisted_seller(self, seller_name: str = "", manufacturer_name: str = "") -> str:
        """Check if seller or manufacturer is whitelisted"""
        if not self.whitelisted_sellers:
            return "False"
        
        names_to_check = []
        if seller_name:
            names_to_check.append(seller_name.strip())
        if manufacturer_name:
            names_to_check.append(manufacturer_name.strip())
        
        for name in names_to_check:
            if not name:
                continue
                
            for whitelisted in self.whitelisted_sellers:
                # Case-insensitive matching
                if (name.lower() == whitelisted.lower() or 
                    whitelisted.lower() in name.lower() or 
                    name.lower() in whitelisted.lower()):
                    return "Whitelisted"
        
        return "False"

    def get_platform_type(self, platform: str) -> str:
        """Get platform type (pagination, infinite_scroll, no_pagination)."""
        from platforms import get_platform_type
        return get_platform_type(platform)
    
    def get_pagination_input(self) -> int:
        """Get pagination input from user."""
        while True:
            try:
                user_input = input("\n📄 Enter Value To Paginate (0 = All Possible Pages, Default 100): ").strip()
                
                if not user_input:  # Empty input - use default
                    return 100
                
                value = int(user_input)
                if value < 0:
                    print("❌ Please enter a positive number or 0 for all pages")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid number")
                continue
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                return 0
    
    def get_scroll_input(self) -> int:
        """Get scroll input from user."""
        while True:
            try:
                user_input = input("\n🔄 Enter Value To Scroll (0 = Possible Scroll, Default 100): ").strip()
                
                if not user_input:  # Empty input - use default
                    return 100
                
                value = int(user_input)
                if value < 0:
                    print("❌ Please enter a positive number or 0 for all scrolls")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid number")
                continue
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                return 0
    
    def is_single_product_url(self, url: str, platform: str) -> bool:
        """Check if URL is a single product URL or listing page"""
        if platform == "amazon":
            # Amazon single product URLs contain /dp/ or /gp/product/
            return "/dp/" in url or "/gp/product/" in url
        elif platform == "flipkart":
            # Flipkart single product URLs contain /p/ or /item/
            return "/p/" in url or "/item/" in url
        elif platform == "myntra":
            # Myntra single product URLs contain /buy/
            return "/buy/" in url
        elif platform == "ebay":
            # eBay single product URLs contain /itm/
            return "/itm/" in url
        elif platform == "walmart":
            # Walmart single product URLs contain /ip/
            return "/ip/" in url
        else:
            # For other platforms, check if it looks like a single product
            # Single product URLs are usually longer and contain product identifiers
            return len(url.split('/')) > 6 and any(keyword in url.lower() for keyword in ['product', 'item', 'buy', 'dp', 'p/', 'itm', 'ip/'])
    
    def get_url_input(self) -> str:
        """Get URL input from user."""
        while True:
            try:
                url = input("\n🌐 Enter Product URL (Single Product or Listing Page): ").strip()
                if url:
                    return url
                print("❌ Please enter a valid URL")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                return ""
    
    def setup_results_directory(self, platform: str, domain: str):
        """Setup organized results directory structure"""
        self.platform_name = platform
        self.domain_name = domain
        
        # Create session directory
        session_name = f"{platform}-{domain}-{self.timestamp}"
        self.session_dir = self.results_dir / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup CSV files
        self.products_csv = self.session_dir / f"Product-{session_name}.csv"
        self.variants_csv = self.session_dir / f"Variant-{session_name}.csv"
        
        # Initialize CSV files with headers
        self.initialize_csv_files()
        
        print(f"📁 Results directory: {self.session_dir}")
        print(f"📄 Products CSV: {self.products_csv}")
        print(f"📄 Variants CSV: {self.variants_csv}")
    
    def initialize_csv_files(self):
        """Initialize CSV files with proper headers"""
        # Products CSV headers
        product_headers = [
            "product_url", "title", "price", "seller_name", 
            "manufacturer_name", "image_url", "is_whitelisted"
        ]
        
        with open(self.products_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(product_headers)
        
        # Variants CSV headers
        variant_headers = [
            "variant_product_url", "main_product_url", "title", "variant_price",
            "seller_name", "manufacturer_name", "image_url", "is_whitelisted"
        ]
        
        with open(self.variants_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(variant_headers)

    def save_product_to_csv(self, product_data: Dict[str, Any]):
        """Save product data to CSV in real-time"""
        with open(self.products_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                product_data.get("product_url", ""),
                product_data.get("title", ""),
                product_data.get("price", ""),
                product_data.get("seller_name", ""),
                product_data.get("manufacturer_name", ""),
                product_data.get("image_url", ""),
                product_data.get("is_whitelisted", "False")
            ])
    
    def save_variant_to_csv(self, variant_data: Dict[str, Any]):
        """Save variant data to CSV in real-time"""
        with open(self.variants_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                variant_data.get("variant_product_url", ""),
                variant_data.get("main_product_url", ""),
                variant_data.get("title", ""),
                variant_data.get("variant_price", ""),
                variant_data.get("seller_name", ""),
                variant_data.get("manufacturer_name", ""),
                variant_data.get("image_url", ""),
                variant_data.get("is_whitelisted", "False")
            ])
    
    def save_to_excel(self):
        """Convert CSV files to Excel with multiple sheets"""
        excel_file = self.session_dir / f"{self.platform_name}-{self.domain_name}-{self.timestamp}.xlsx"
        
        try:
            # Read CSV files
            products_df = pd.read_csv(self.products_csv)
            variants_df = pd.read_csv(self.variants_csv)
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                products_df.to_excel(writer, sheet_name='Products', index=False)
                variants_df.to_excel(writer, sheet_name='Variants', index=False)
            
            print(f"📊 Excel file saved: {excel_file}")
            return excel_file
            
        except Exception as e:
            print(f"❌ Error saving Excel file: {e}")
            return None

    async def run_scraping_session(self, url: str, max_pages: int = None):
        """Main scraping session"""
        try:
            # Parse URL and detect platform
            parsed_url = urlparse(url)
            domain = parsed_url.hostname or ""
            platform = detect_platform(domain)
            platform_display = get_platform_display_name(platform)
            
            print(f"🎯 Platform: {platform_display}")
            print(f"🌐 Domain: {domain}")
            
            # Check if it's a single product URL or listing page
            if self.is_single_product_url(url, platform):
                print("🛍️ Single Product URL detected - extracting product details only")
                # Setup results directory for single product
                self.setup_results_directory(platform, domain)
                await self.scrape_single_product(url, platform)
                return
            
            print("📄 Product Listing URL detected - extracting all products with pagination")
            
            # Get platform type for pagination/scroll control
            platform_type = self.get_platform_type(platform)
            
            # Ask user for pagination/scroll control based on platform type
            if platform_type == "pagination":
                max_pages = self.get_pagination_input()
            elif platform_type == "infinite_scroll":
                max_pages = self.get_scroll_input()
            else:  # no_pagination
                max_pages = 1
                print("📄 No pagination needed - Single page only")
            
            print(f"📄 Max Pages: {'All pages' if max_pages == 0 else max_pages}")
            
            # Setup results directory
            self.setup_results_directory(platform, domain)
            
            # Get platform extractor
            extractor_class = get_extractor(platform)
            extractor = extractor_class()
            
            # Setup browser with latest API and visibility support
            # Create agent with latest API
            agent = Agent(
                task=f"Go to {url} and scrape all products with variants. Navigate through pages and extract product data including variants.",
                llm=self.llm_instance(model=self.llm_model),
                llm_timeout=300,  # 5 minutes timeout
                step_timeout=60,  # 1 minute timeout per step
            )
            
            # Run scraping with direct method
            await self.scrape_platform_products_with_browser(agent, extractor, platform, max_pages, url)
            
            # Save to Excel
            excel_file = self.save_to_excel()
            
            print(f"\n✅ Scraping completed!")
            print(f"📁 Results saved in: {self.session_dir}")
            if excel_file:
                print(f"📊 Excel file: {excel_file}")
            
        except Exception as e:
            print(f"❌ Error in scraping session: {e}")
            raise
    
    
    async def scrape_platform_products_with_browser(self, agent, extractor, platform: str, max_pages: int, url: str):
        """Scraping with latest browser-use API and visibility support"""
        try:
            # Skip browser-use for now and use direct Playwright for reliable scraping
            print("🌐 Using direct Playwright for reliable scraping with color bounded elements...")
            
            # Use direct Playwright for reliable scraping with color bounded elements
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser with color bounded elements visible
                browser = await p.chromium.launch(
                    headless=False,  # Show browser for color bounded elements
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--enable-paint-checking',
                        '--enable-gpu-rasterization',
                        '--force-color-profile=srgb'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Navigate to URL with proper waiting
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for elements to be visible and bounded
                await page.wait_for_timeout(5000)  # Wait for dynamic content
                
                # Scroll to ensure all elements are loaded
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(2000)
            
                total_products = 0
                total_variants = 0
                current_page = 1
                
                while max_pages == 0 or current_page <= max_pages:
                    print(f"\n📄 Processing Page {current_page}...")
                    
                    # Get product links with real-time CSV update
                    product_links = await extractor.get_product_links(page, 50)
                    if not product_links:
                        print("⚠️ No products found, stopping pagination")
                        break
                    
                    # Process each product with real-time CSV update
                    for i, product_url in enumerate(product_links):
                        try:
                            print(f"🔄 Processing product {i+1}/{len(product_links)}: {product_url[:80]}...")
                            
                            # Open product in new tab
                            new_tab = await context.new_page()
                            await new_tab.goto(product_url, wait_until="domcontentloaded", timeout=60000)
                            
                            # Wait for product page elements to be visible
                            await new_tab.wait_for_timeout(3000)
                            
                            # Scroll to ensure all elements are loaded
                            await new_tab.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await new_tab.wait_for_timeout(1000)
                            await new_tab.evaluate("window.scrollTo(0, 0)")
                            await new_tab.wait_for_timeout(1000)
                            
                            # Extract product data
                            product_data = await extractor.extract_product_data(new_tab)
                            
                            # Check whitelist status
                            seller_name = product_data.get('seller_name', '')
                            manufacturer_name = product_data.get('manufacturer_name', '')
                            product_data['is_whitelisted'] = self.check_whitelisted_seller(seller_name, manufacturer_name)
                            
                            # Save product data IMMEDIATELY to prevent data loss
                            if product_data.get('title') or product_data.get('price'):
                                self.save_product_to_csv(product_data)
                                total_products += 1
                                print(f"   ✅ Product saved: {product_data.get('title', 'Unknown')[:50]}...")
                            
                            # Check for variants with real-time CSV update
                            variants = await extractor.extract_variants(new_tab, product_url)
                            if variants:
                                print(f"   🎨 Found {len(variants)} variants")
                                for variant in variants:
                                    variant['is_whitelisted'] = self.check_whitelisted_seller(
                                        variant.get('seller_name', ''), 
                                        variant.get('manufacturer_name', '')
                                    )
                                    # Save variant data IMMEDIATELY
                                    self.save_variant_to_csv(variant)
                                    total_variants += 1
                            
                            await new_tab.close()
                            
                            # Human-like delay between products
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"   ❌ Error processing product {product_url}: {e}")
                            try:
                                await new_tab.close()
                            except:
                                pass
                            continue
                    
                    # Move to next page
                    if max_pages == 0 or current_page < max_pages:
                        next_page_success = await extractor.go_to_next_page(page)
                        if not next_page_success:
                            print("⚠️ No more pages available, stopping pagination")
                            break
                        current_page += 1
                        
                        # Wait for new page to load
                        await page.wait_for_timeout(3000)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                        await page.evaluate("window.scrollTo(0, 0)")
                        await page.wait_for_timeout(2000)
                    else:
                        break
                
                await browser.close()
                
                print(f"\n📊 Scraping Complete!")
                print(f"✅ Total Products: {total_products}")
                print(f"✅ Total Variants: {total_variants}")
                print(f"📁 Results saved in: {self.results_dir}")
                
        except Exception as e:
            print(f"❌ Error in browser scraping: {e}")
            raise
    
    async def scrape_single_product(self, url: str, platform: str):
        """Scrape single product details without pagination"""
        try:
            print("🛍️ Scraping single product details...")
            
            # Get platform extractor
            extractor_class = get_extractor(platform)
            extractor = extractor_class()
            
            # Use direct Playwright for reliable scraping
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser with color bounded elements visible
                browser = await p.chromium.launch(
                    headless=False,  # Show browser for color bounded elements
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--enable-paint-checking',
                        '--enable-gpu-rasterization',
                        '--force-color-profile=srgb'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Navigate to product URL
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for product page elements to be visible
                await page.wait_for_timeout(5000)
                
                # Scroll to ensure all elements are loaded
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(2000)
                
                total_products = 0
                total_variants = 0
                
                print(f"🔄 Processing single product: {url[:80]}...")
                
                # Extract product data
                product_data = await extractor.extract_product_data(page)
                
                # Check whitelist status
                seller_name = product_data.get('seller_name', '')
                manufacturer_name = product_data.get('manufacturer_name', '')
                product_data['is_whitelisted'] = self.check_whitelisted_seller(seller_name, manufacturer_name)
                
                # Save product data IMMEDIATELY
                if product_data.get('title') or product_data.get('price'):
                    self.save_product_to_csv(product_data)
                    total_products += 1
                    print(f"   ✅ Product saved: {product_data.get('title', 'Unknown')[:50]}...")
                
                # Check for variants
                variants = await extractor.extract_variants(page, url)
                if variants:
                    print(f"   🎨 Found {len(variants)} variants")
                    for variant in variants:
                        variant['is_whitelisted'] = self.check_whitelisted_seller(
                            variant.get('seller_name', ''), 
                            variant.get('manufacturer_name', '')
                        )
                        # Save variant data IMMEDIATELY
                        self.save_variant_to_csv(variant)
                        total_variants += 1
                
                await browser.close()
                
                print(f"\n📊 Single Product Scraping Complete!")
                print(f"✅ Total Products: {total_products}")
                print(f"✅ Total Variants: {total_variants}")
                print(f"📁 Results saved in: {self.results_dir}")
                
        except Exception as e:
            print(f"❌ Error in single product scraping: {e}")
            raise

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="E-Commerce Automation Tool - Multi-platform product scraping with variant extraction")
    parser.add_argument("--url", help="Product listing page URL (optional - will be asked if not provided)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_args()
    
    automation = ECommerceAutomation()
    automation.setup_environment()
    
    url = args.url
    if not url:
        print("🚀 E-Commerce Automation Tool Started!")
        print("=" * 50)
        url = automation.get_url_input()
        if not url:
            return
    else:
        print("🚀 E-Commerce Automation Tool Started!")
        print("=" * 50)
    
    await automation.run_scraping_session(url)

if __name__ == "__main__":
    asyncio.run(main())
