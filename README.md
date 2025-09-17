# Trademark Automation Tool

**Version 1.0** | **Developer: Rahul Yadav** | **Copyright: CII (Copyright Integrity International)**

## 📋 Table Of Contents

- [What Is This Tool](#what-is-this-tool)
- [Key Features](#key-features)
- [Supported Platforms](#supported-platforms)
- [Installation Guide](#installation-guide)
- [First Time Setup](#first-time-setup)
- [How To Use](#how-to-use)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)
- [Future Plans](#future-plans)

## 🎯 What Is This Tool

This Is A Powerful **Trademark Automation Tool** That Automatically Extracts Product Information From Online Shopping Websites. It Can Handle Both **Single Product Pages** And **Product Listing Pages** With Advanced Features Like **Variant Detection**, **Real-Time Data Saving**, And **Multi-Platform Support**.

### Why This Tool Was Created

- **Save Time**: No More Manual Copy-Paste Of Product Details
- **Prevent Data Loss**: Real-Time CSV Saving Even During Power Failures
- **Handle Variants**: Automatically Detect And Extract All Product Variants
- **Multi-Platform**: Works With Amazon, Flipkart, Myntra, And More
- **Professional Use**: Perfect For E-Commerce Businesses And Researchers

## ✨ Key Features

### 🔍 **Smart URL Detection**
- **Single Product URLs**: Automatically Detects Individual Product Pages
- **Listing Pages**: Handles Search Results And Category Pages
- **No Manual Input**: Tool Automatically Knows What To Do

### 📊 **Real-Time Data Saving**
- **CSV Files**: Data Saved Immediately After Each Product
- **No Data Loss**: Even If Power Goes Off, Data Is Safe
- **Excel Export**: Final Results Converted To Professional Excel Files

### 🎨 **Variant Extraction**
- **Color Variants**: Different Colors Of Same Product
- **Size Variants**: Different Sizes Available
- **Storage Variants**: Different Storage Options (For Phones, Laptops)
- **Price Changes**: Each Variant Has Its Own Price

### 🛡️ **Whitelist System**
- **Seller Filtering**: Only Extract Products From Trusted Sellers
- **Manufacturer Check**: Verify Product Manufacturers
- **Customizable**: Add Your Own Trusted Sellers List

### 🌐 **Multi-Platform Support**
- **Amazon**: Complete Implementation With All Features
- **Flipkart**: Ready For Implementation
- **Myntra**: Ready For Implementation
- **More Platforms**: Easy To Add New Ones

## 🏪 Supported Platforms

### ✅ **Fully Implemented**
- **Amazon** - Complete With Pagination, Variants, And All Features

### 🚧 **Ready For Implementation**
- **Flipkart** - Pagination Support
- **Myntra** - Infinite Scroll Support
- **eBay** - Pagination Support
- **Walmart** - Pagination Support
- **AJIO** - Infinite Scroll Support
- **Nykaa** - Infinite Scroll Support
- **Snapdeal** - Infinite Scroll Support
- **ShopClues** - Infinite Scroll Support
- **TataCliq** - Single Page Only
- **Redbubble** - Pagination Support
- **Shopsy** - Pagination Support
- **IndiaMart** - Infinite Scroll Support

## 🚀 Installation Guide

### **System Requirements**
- **Python 3.8+** (Recommended: Python 3.11)
- **Windows 10/11**, **macOS 10.15+**, Or **Linux Ubuntu 18.04+**
- **8GB RAM** (Minimum)
- **2GB Free Disk Space**
- **Internet Connection** (For API Calls And Browser Automation)

### **Browser Compatibility** 🌐
- **Chrome/Chromium**: Fully Supported (Recommended)
- **Edge**: Supported
- **Firefox**: Limited Support
- **Safari**: Not Supported
- **Headless Mode**: Available But Not Recommended For Debugging
- **Display Requirements**: Color Bounded Elements Need Visible Browser

### **Key Dependencies**
- **browser-use==0.7.7** - AI-Powered Browser Automation (Uses CDP Protocol)
- **playwright** - Browser Engine For Web Scraping (Used By Our Tool)
- **pandas** - Data Processing And Excel Export
- **openpyxl** - Excel File Creation
- **python-dotenv** - Environment Variable Management
- **tldextract** - Domain Name Extraction
- **asyncio** - Asynchronous Programming Support
- **argparse** - Command Line Argument Parsing

### **Browser-Use 0.7.7 Features** 🚀
- **CDP Protocol**: Uses Chrome DevTools Protocol Instead Of Playwright
- **Better Stability**: Improved Performance And Reliability
- **AI-Powered**: Smart Browser Automation With LLM Integration
- **Human-Like Behavior**: Natural Mouse Movements And Clicking
- **Element Detection**: Advanced Element Finding And Interaction
- **Multi-Platform**: Works With Various E-Commerce Websites

### **Windows Setup**

#### **Step 1: Download Python**
1. Go To [Python.org](https://www.python.org/downloads/)
2. Download **Python 3.11** Or Latest Version
3. **Important**: Check "Add Python to PATH" During Installation
4. Click "Install Now"

#### **Step 2: Download The Tool**
1. Download The Tool Files To Your Desktop
2. Extract The ZIP File
3. You Should See A Folder Named "Trademark Automation"

#### **Step 3: Open Command Prompt**
1. Press **Windows + R**
2. Type `cmd` And Press Enter
3. Navigate To The Tool Folder:
   ```cmd
   cd C:\Users\YourName\Desktop\Trademark Automation
   ```

#### **Step 4: Create Virtual Environment**
```cmd
python -m venv venv
```

#### **Step 5: Activate Virtual Environment**
```cmd
venv\Scripts\activate
```

#### **Step 6: Install Dependencies**
```cmd
pip install -r requirements.txt
```

#### **Step 7: Install Playwright Browsers**
```cmd
# Install Playwright Browsers (Required for our tool's browser automation)
playwright install chromium

# Optional: Install all browsers
playwright install
```

#### **Step 8: Verify Browser-Use Installation**
```cmd
# Test browser-use installation
python -c "import browser_use; print('Browser-use installed successfully!')"

# Check browser-use version
python -c "import browser_use; print(f'Browser-use version: {browser_use.__version__}')"
```

### **macOS Setup**

#### **Step 1: Install Python**
```bash
# Using Homebrew (Recommended)
brew install python3

# Or Download From Python.org
```

#### **Step 2: Download The Tool**
1. Download And Extract The Tool Files
2. Open Terminal
3. Navigate To The Tool Folder:
   ```bash
   cd ~/Desktop/Trademark\ Automation
   ```

#### **Step 3: Create Virtual Environment**
```bash
python3 -m venv venv
```

#### **Step 4: Activate Virtual Environment**
```bash
source venv/bin/activate
```

#### **Step 5: Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **Step 6: Install Playwright Browsers**
```bash
# Install Playwright Browsers (Required for our tool's browser automation)
playwright install chromium

# Optional: Install all browsers
playwright install
```

#### **Step 7: Verify Browser-Use Installation**
```bash
# Test browser-use installation
python3 -c "import browser_use; print('Browser-use installed successfully!')"

# Check browser-use version
python3 -c "import browser_use; print(f'Browser-use version: {browser_use.__version__}')"
```

### **Linux Setup**

#### **Step 1: Install Python**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

#### **Step 2: Download The Tool**
1. Download And Extract The Tool Files
2. Open Terminal
3. Navigate To The Tool Folder:
   ```bash
   cd ~/Desktop/Trademark\ Automation
   ```

#### **Step 3: Create Virtual Environment**
```bash
python3 -m venv venv
```

#### **Step 4: Activate Virtual Environment**
```bash
source venv/bin/activate
```

#### **Step 5: Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **Step 6: Install Playwright Browsers**
```bash
# Install Playwright Browsers (Required for our tool's browser automation)
playwright install chromium

# Optional: Install all browsers
playwright install
```

#### **Step 7: Verify Browser-Use Installation**
```bash
# Test browser-use installation
python3 -c "import browser_use; print('Browser-use installed successfully!')"

# Check browser-use version
python3 -c "import browser_use; print(f'Browser-use version: {browser_use.__version__}')"
```

## ⚙️ First Time Setup

### **Step 1: Configure API Keys** 🔑
1. **Open The `.env` File** In A Text Editor (Notepad, VS Code, etc.)
2. **You Will See Different API Provider Sections** - Each One Is Commented Out With `#`
3. **IMPORTANT: Choose ONLY ONE Provider** And Uncomment It By Removing The `#` Symbols
4. **Add Your API Key** In The Selected Provider Section
5. **Add Your Model Name** In The Selected Provider Section

#### **Example Configuration:**
```env
# ✅ CORRECT: Using Google (Gemini) - Uncommented and configured
GOOGLE_API_KEY=AIzaSyBdqo...your_actual_api_key_here
GOOGLE_MODEL=gemini-2.5-flash

# ❌ WRONG: All other providers should remain commented out
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-sonnet
# GROQ_API_KEY=gsk_...
# GROQ_MODEL=meta-llama/llama-3.1-70b-versatile
```

> **⚠️ CRITICAL WARNING**
> 
> - **Only ONE Provider** Should Be Uncommented At A Time
> - **API Key** Should Be Your Real Key (Not "your_api_key_here")
> - **Model Name** Should Match The Provider You Chose
> - **Keep Other Providers Commented** With `#` Symbol

#### **🤖 API Key Usage Clarification**
**What Are These API Keys Used For?**
- **Browser-Use Integration**: AI-Powered Browser Automation And Navigation
- **Element Detection**: Smart Finding Of Product Elements On Web Pages
- **Human-Like Behavior**: Natural Mouse Movements And Clicking Patterns
- **Error Handling**: Intelligent Recovery From Scraping Issues
- **NOT Used For**: Data Enhancement, Summarization, Or Classification
- **NOT Used For**: Seller Validation (Uses Whitelist System Instead)
- **Primary Purpose**: Making Browser Automation More Intelligent And Reliable

### **Step 2: Get API Keys** 🔑

#### **For Google (Gemini) - Recommended** ⭐
1. **Go To**: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Sign In** With Your Google Account
3. **Click "Create API Key"** Button
4. **Copy The Key** (It Will Look Like: `AIzaSyBdqo...`)
5. **Paste In `.env` File** After `GOOGLE_API_KEY=`
6. **Set Model**: `GOOGLE_MODEL=gemini-2.5-flash`

#### **For OpenAI** 🤖
1. **Go To**: [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Sign In** With Your OpenAI Account
3. **Click "Create New Secret Key"**
4. **Copy The Key** (It Will Look Like: `sk-...`)
5. **Paste In `.env` File** After `OPENAI_API_KEY=`
6. **Set Model**: `OPENAI_MODEL=gpt-4o-mini`

#### **For Anthropic (Claude)** 🧠
1. **Go To**: [Anthropic Console](https://console.anthropic.com/)
2. **Sign In** With Your Anthropic Account
3. **Click "Create Key"**
4. **Copy The Key** (It Will Look Like: `sk-ant-...`)
5. **Paste In `.env` File** After `ANTHROPIC_API_KEY=`
6. **Set Model**: `ANTHROPIC_MODEL=claude-3-sonnet`

#### **For Groq** ⚡
1. **Go To**: [Groq Console](https://console.groq.com/keys)
2. **Sign In** With Your Groq Account
3. **Click "Create API Key"**
4. **Copy The Key** (It Will Look Like: `gsk_...`)
5. **Paste In `.env` File** After `GROQ_API_KEY=`
6. **Set Model**: `GROQ_MODEL=meta-llama/llama-3.1-70b-versatile`

### **Step 3: Configure Whitelisted Sellers**
1. In The `.env` File, Find The `WHITELISTED_SELLERS` Line
2. Add Your Trusted Sellers Separated By Commas:
```env
WHITELISTED_SELLERS="Amazon, Flipkart, Myntra, Puma, Nike, Adidas"
```

### **Step 4: Test The Setup**
```bash
# Windows
python app.py --url "https://www.amazon.in/s?k=test"

# macOS/Linux
python3 app.py --url "https://www.amazon.in/s?k=test"
```

## 🎮 How To Use

> **🚀 QUICK START**
> 
> 1. **Activate Virtual Environment**: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
> 2. **Run The Tool**: `python app.py --url "https://www.amazon.in/s?k=shoes"`
> 3. **Follow Prompts**: Enter Number Of Pages To Scrape
> 4. **Watch Progress**: Browser Opens And Shows Real-Time Scraping
> 5. **Check Results**: Find CSV And Excel Files In `results/` Folder

### **Method 1: Command Line With URL**
```bash
# Single Product URL
python app.py --url "https://www.amazon.in/product/dp/ABC123"

# Listing Page URL
python app.py --url "https://www.amazon.in/s?k=shoes"

# Headless Mode (Not Recommended For Debugging)
python app.py --url "https://www.amazon.in/s?k=shoes" --headless
```

### **Headless Mode Configuration** 🤖
- **Available**: Yes, Using `--headless` Flag
- **Recommended**: No, For Better Debugging And Element Detection
- **Use Cases**: Server Deployment, Background Processing
- **Limitations**: Color Bounded Elements Not Visible
- **Performance**: Slightly Faster But Less Reliable

### **Method 2: Interactive Mode**
```bash
# Run Without URL - Tool Will Ask For Input
python app.py
```

### **What Happens Next**

1. **Tool Detects Platform**: Automatically Identifies Amazon, Flipkart, etc.
2. **Asks For Pagination**: For Listing Pages, Asks How Many Pages To Scrape
3. **Opens Browser**: Shows Browser Window With Color Bounded Elements
4. **Starts Scraping**: Extracts Products One By One
5. **Saves Data**: Real-Time CSV Saving After Each Product
6. **Creates Excel**: Final Excel File With All Data

### **Example Usage**

```bash
# Example 1: Single Product
python app.py --url "https://www.amazon.in/Virat-Jersey-2025-15-16Years-Multicolour/dp/B0FMXNKHSW"

# Example 2: Search Results
python app.py --url "https://www.amazon.in/s?k=rcb+jersey+2025"
# Tool Will Ask: "Enter Value To Paginate (0 = All Possible Pages, Default 100):"
# Type: 5 (For 5 Pages) Or 0 (For All Pages)
```

## 📁 Project Structure

```
Trademark Automation/
├── 📄 app.py                          # Main Application File
├── 📄 .env                            # Configuration File (API Keys)
├── 📄 requirements.txt                # Python Dependencies
├── 📄 README.md                       # This Documentation
├── 📁 venv/                          # Virtual Environment
├── 📁 results/                       # Output Files Directory
│   └── 📁 amazon-www.amazon.in-2025-09-13--16-47-02/
│       ├── 📄 Product-amazon-www.amazon.in-2025-09-13--16-47-02.csv
│       ├── 📄 Variant-amazon-www.amazon.in-2025-09-13--16-47-02.csv
│       └── 📄 amazon-www.amazon.in-2025-09-13--16-47-02.xlsx
└── 📁 platforms/                     # Platform-Specific Extractors
    ├── 📄 __init__.py                # Platform Registry
    ├── 📄 base.py                    # Base Extractor Class
    └── 📄 amazon.py                  # Amazon-Specific Logic
```

### **File Descriptions**

#### **📄 app.py**
- **What**: Main Application File
- **Why**: Orchestrates The Entire Scraping Process
- **How**: Uses Browser Automation And Platform Extractors
- **When**: Runs When User Executes The Tool

#### **📄 .env**
- **What**: Configuration File
- **Why**: Stores API Keys And Settings
- **How**: Read By Python-Dotenv Library
- **When**: Loaded At Application Start

#### **📄 requirements.txt**
- **What**: Python Dependencies List
- **Why**: Ensures All Required Libraries Are Installed
- **How**: Used By Pip Install Command
- **When**: During Setup Process

#### **📁 platforms/**
- **What**: Platform-Specific Code
- **Why**: Each Platform Has Different HTML Structure
- **How**: Modular Design For Easy Maintenance
- **When**: Called During Scraping Process

## 🔧 How It Works

### **File-Wise Explanation** 📁

#### **📄 app.py - Main Application File**
- **What**: Main Orchestration File
- **Why**: Controls The Entire Scraping Process
- **How**: Uses Browser Automation And Platform Extractors
- **When**: Runs When User Executes The Tool
- **Where**: Root Directory
- **Key Functions**:
  - `detect_llm_provider()` - Auto-Detects API Provider From .env
  - `is_single_product_url()` - Checks If URL Is Single Product Or Listing
  - `scrape_single_product()` - Handles Single Product Extraction
  - `scrape_platform_products_with_browser()` - Handles Listing Page Scraping
  - `save_product_to_csv()` - Real-Time Data Saving

#### **📄 .env - Configuration File**
- **What**: Stores API Keys And Settings
- **Why**: Keeps Sensitive Data Separate From Code
- **How**: Read By Python-Dotenv Library
- **When**: Loaded At Application Start
- **Where**: Root Directory
- **Contains**:
  - API Keys (OpenAI, Google, Anthropic, Groq)
  - Model Names
  - Whitelisted Sellers List

#### **📄 platforms/__init__.py - Platform Registry**
- **What**: Central Registry For All Platforms
- **Why**: Easy Platform Management And Detection
- **How**: Maps Domain Names To Platform Extractors
- **When**: Called During Platform Detection
- **Where**: platforms/ Directory
- **Functions**:
  - `detect_platform()` - Identifies Platform From Domain
  - `get_extractor()` - Returns Platform-Specific Extractor
  - `get_platform_type()` - Returns Pagination Type

#### **📄 platforms/base.py - Base Extractor Class**
- **What**: Abstract Base Class For All Extractors
- **Why**: Common Functionality For All Platforms
- **How**: Defines Abstract Methods And Common Utilities
- **When**: Inherited By Platform-Specific Extractors
- **Where**: platforms/ Directory
- **Key Methods**:
  - `extract_common_data()` - Common Product Data Extraction
  - `first_text()` - Find First Matching Text Element
  - `text_by_xpath()` - Extract Text Using XPath

#### **📄 platforms/amazon.py - Amazon Extractor**
- **What**: Amazon-Specific Scraping Logic
- **Why**: Amazon Has Unique HTML Structure
- **How**: Implements Base Extractor Methods
- **When**: Called When Amazon Platform Is Detected
- **Where**: platforms/ Directory
- **Key Methods**:
  - `get_product_links()` - Finds All Product URLs On Page
  - `extract_product_data()` - Extracts Product Details
  - `extract_variants()` - Finds Product Variants
  - `go_to_next_page()` - Handles Amazon Pagination

#### **📄 requirements.txt - Dependencies List**
- **What**: Python Package Dependencies
- **Why**: Ensures All Required Libraries Are Installed
- **How**: Used By Pip Install Command
- **When**: During Setup Process
- **Where**: Root Directory
- **Contains**:
  - browser-use==0.7.7
  - playwright
  - pandas
  - openpyxl
  - python-dotenv

### **Step-By-Step Process** 🔄

#### **Step 1: URL Analysis**
```
User Input URL → Parse Domain → Detect Platform → Check URL Type
```

#### **Step 2: Platform Detection**
- **Amazon**: Detects "amazon.in", "amazon.com", etc.
- **Flipkart**: Detects "flipkart.com"
- **Myntra**: Detects "myntra.com"
- **More**: Easy To Add New Platforms

#### **Step 3: URL Type Detection**
- **Single Product**: Contains "/dp/", "/p/", "/buy/" patterns
- **Listing Page**: Search Results, Category Pages
- **Action**: Different Scraping Strategy For Each Type

#### **Step 4: Browser Launch**
- **Engine**: Hybrid Approach (Browser-Use + Playwright)
- **Browser-Use**: AI-Powered Navigation And Task Management
- **Playwright**: Direct Browser Control For Reliable Scraping
- **Mode**: Non-Headless (Visible Browser)
- **Features**: Color Bounded Elements, Human-Like Behavior
- **Why**: Combines AI Intelligence With Reliable Browser Control

#### **Step 5: Data Extraction**
- **Product Links**: Find All Product URLs On Page
- **Product Details**: Extract Title, Price, Seller, Manufacturer
- **Variants**: Detect Color, Size, Storage Options
- **Images**: Extract Product Image URLs

#### **Step 6: Real-Time Saving**
- **CSV Files**: Save After Each Product
- **Excel Export**: Convert To Professional Format
- **Data Safety**: No Data Loss Even During Failures

#### **Step 7: Pagination/Scroll**
- **Pagination**: Click "Next Page" Button
- **Infinite Scroll**: Scroll Down To Load More Products
- **Smart Detection**: Automatically Knows Which Method To Use

## 📊 Output Files

### **CSV Files (Real-Time)**
- **Product-*.csv**: Main Product Data
- **Variant-*.csv**: Product Variants Data

### **Excel File (Final)**
- **Sheet 1**: "Products" - All Main Products
- **Sheet 2**: "Variants" - All Product Variants

### **Data Columns**

#### **Product CSV Columns**
- `product_url`: Link To Product Page
- `title`: Product Name
- `price`: Product Price
- `seller_name`: Who Is Selling
- `manufacturer_name`: Who Made It
- `image_url`: Product Image Link
- `is_whitelisted`: Is Seller Trusted? (Whitelisted/False)

#### **Variant CSV Columns**
- `variant_product_url`: Link To Specific Variant
- `main_product_url`: Link To Main Product
- `title`: Variant Name
- `variant_price`: Price For This Variant
- `seller_name`: Who Is Selling
- `manufacturer_name`: Who Made It
- `image_url`: Variant Image Link
- `is_whitelisted`: Is Seller Trusted?

## ⚠️ Known Limitations

> **🚧 CURRENT LIMITATIONS**
> 
> - **Amazon Only**: Currently Only Amazon Is Fully Implemented
> - **Other Platforms**: Flipkart, Myntra, eBay Are Ready But Not Implemented
> - **Rate Limiting**: Some Websites May Block Too Many Requests
> - **Dynamic Content**: Very Dynamic Websites May Need Manual Selector Updates
> - **Captcha Handling**: Does Not Automatically Solve Captchas
> - **Login Required**: Cannot Access Login-Protected Product Pages
> - **Geographic Restrictions**: Some Products May Not Be Available In All Regions
> - **Mobile Apps**: Cannot Scrape Mobile App-Only Content
> - **Real-Time Data**: Prices May Change Between Scraping And Purchase

### **Technical Limitations** 🔧
- **Browser Resources**: Requires Significant RAM For Large Scraping Sessions
- **Internet Speed**: Slow Internet May Cause Timeout Issues
- **Website Changes**: Website Structure Changes May Break Selectors
- **JavaScript Heavy Sites**: Some Sites May Not Load Properly
- **Anti-Bot Measures**: Advanced Anti-Bot Systems May Block The Tool

### **Data Limitations** 📊
- **Image Quality**: Extracted Images May Not Be High Resolution
- **Variant Availability**: Some Variants May Not Be Detected
- **Price Accuracy**: Prices May Not Include Taxes Or Shipping
- **Stock Status**: Real-Time Stock Availability May Not Be Accurate
- **Seller Information**: Some Sellers May Not Be Properly Identified

## 🛠️ Troubleshooting

### **Common Issues**

#### **"Module Not Found" Error**
```bash
# Solution: Activate Virtual Environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### **"API Key Not Found" Error**
```bash
# Solution: Check .env File
# Make Sure One Provider Is Uncommented
# Verify API Key Is Correct
```

#### **"Browser Launch Failed" Error**
```bash
# Solution: Install Playwright Browsers
pip install playwright
playwright install chromium

# If Still Failing, Try:
playwright install --force
```

#### **"Playwright Not Found" Error**
```bash
# Solution: Reinstall Playwright
pip uninstall playwright
pip install playwright
playwright install chromium
```

#### **"Chromium Download Failed" Error**
```bash
# Solution: Manual Browser Installation
# Windows
playwright install chromium --with-deps

# macOS
brew install playwright
playwright install chromium

# Linux
sudo apt-get install playwright
playwright install chromium
```

#### **"Browser-Use Import Error" Error**
```bash
# Solution: Reinstall browser-use
pip uninstall browser-use
pip install browser-use==0.7.7

# Verify installation
python -c "import browser_use; print('Success!')"
```

#### **"CDP Connection Failed" Error**
```bash
# Solution: Check Chrome installation
# Make sure Chrome/Chromium is installed
# Windows: Download from google.com/chrome
# macOS: brew install --cask google-chrome
# Linux: sudo apt install google-chrome-stable
```

#### **"Permission Denied" Error**
```bash
# Solution: Run As Administrator (Windows)
# Or Use Sudo (Linux/macOS)
```

> **💡 PERFORMANCE TIPS**
> 
> 1. **Close Other Programs**: Free Up RAM For Better Performance
> 2. **Stable Internet**: Ensure Good Internet Connection
> 3. **Don't Interrupt**: Let The Tool Complete Its Work
> 4. **Check Results**: Verify Output Files Are Created
> 5. **Use Visible Browser**: Headless Mode May Miss Some Elements
> 6. **Monitor Progress**: Watch The Console For Real-Time Updates
> 7. **Save Frequently**: Tool Saves Data In Real-Time, But Check Files

## 🚀 Future Plans

### **Version 1.1 (Coming Soon)**
- **Flipkart Support**: Complete Implementation
- **Myntra Support**: Complete Implementation
- **Better Error Handling**: More Robust Error Recovery

### **Version 1.2 (Planned)**
- **GUI Interface**: Easy-To-Use Graphical Interface
- **Much More**: Thinking

### **Version 2.0 (Future)**
- **Web Application**: Browser-Based Interface
- **Database Integration**: Store Data In Database
- **API Endpoints**: REST API For Integration

### **Web Application Preview** 🌐
**Coming Soon**: A Modern Web-Based Interface For The E-Commerce Automation Tool
- **Hint**: User-Friendly Interface For Non-Technical Users
- **Hint**: Planning Wait ...

## 📞 Support

### **For Technical Issues**
- **Check This README**: Most Issues Are Covered Here
- **Check Error Messages**: They Usually Tell You What's Wrong
- **Verify Setup**: Make Sure All Steps Are Followed Correctly

### **For Feature Requests & Contact**
- **Developer**: Rahul Yadav
- **GitHub**: [https://github.com/SWEHULYADAV](https://github.com/SWEHULYADAV)
- **Organization**: CII (Copyright Integrity International)
- **Version**: 1.0

## 🙏 Special Thanks

### **Technical Leadership**
- **Kiran Rao** - **Technical Chief, CII (Copyright Integrity International)**
  - **Role**: Technical Oversight And Architecture Guidance
  - **Contribution**: Strategic Technical Direction And Quality Assurance
  - **Expertise**: Advanced Software Development And System Architecture
  - **Contact**: Available Through CII (Copyright Integrity International)

### **Development Team**
- **Rahul Yadav** - **Lead Developer**
  - **Role**: Full-Stack Development And Implementation
  - **Contribution**: Core Application Development And Feature Implementation

### **Organization**
- **CII (Copyright Integrity International)**
  - **Mission**: Advancing Technology Solutions For Business Automation
  - **Vision**: Creating Innovative Tools For E-Commerce Excellence

## 📄 License

**Copyright © 2025 CII (Copyright Integrity International)**
**Developer: Rahul Yadav**
**Technical Chief: Kiran Rao**

This Tool Is Developed For Professional E-Commerce Automation Purposes. Please Use Responsibly And In Accordance With Website Terms Of Service.

---

**Thank You For Using Trademark Automation Tool! 🎉**

*Happy Scraping!* 🚀
