"""
Platform-specific extractors for e-commerce scraping
====================================================
Enhanced with variant detection, pagination support, and real-time saving
"""

from .amazon import AmazonExtractor
from .flipkart import FlipkartExtractor
from .myntra import MyntraExtractor
from .meesho import MeeshoExtractor
from .ajio import AjioExtractor
from .ebay import EbayExtractor
from .redbubble import RedbubbleExtractor
from .snapdeal import SnapdealExtractor
from .shopsy import ShopsyExtractor
from .nykaa import NykaaExtractor
from .tatacliq import TataCliqExtractor
from .indiamart import IndiaMARTExtractor
from .walmart import WalmartExtractor
from .generic import GenericExtractor

# Platform registry - Add new platforms here
PLATFORM_EXTRACTORS = {
    "amazon": AmazonExtractor,
    "flipkart": FlipkartExtractor,
    "myntra": MyntraExtractor,
    "meesho": MeeshoExtractor,
    "ajio": AjioExtractor,
    "ebay": EbayExtractor,
    "redbubble": RedbubbleExtractor,
    "snapdeal": SnapdealExtractor,
    "shopsy": ShopsyExtractor,
    "nykaa": NykaaExtractor,
    "tatacliq": TataCliqExtractor,
    "indiamart": IndiaMARTExtractor,
    "walmart": WalmartExtractor,
    "generic": GenericExtractor,
}

# Platform types for pagination handling
PLATFORM_TYPES = {
    "amazon": "pagination",
    "flipkart": "pagination", 
    "myntra": "pagination",
    "ebay": "pagination",
    "redbubble": "pagination",
    "shopsy": "pagination",
    "walmart": "pagination",
    "meesho": "infinite_scroll",
    "ajio": "infinite_scroll",
    "indiamart": "infinite_scroll",
    "nykaa": "infinite_scroll",
    "snapdeal": "infinite_scroll",
    "tatacliq": "no_pagination",
    "generic": "pagination"
}

# Platform variant support
PLATFORM_VARIANT_SUPPORT = {
    "amazon": True,
    "flipkart": True,
    "myntra": True,
    "ebay": True,
    "walmart": True,
    "meesho": False,
    "ajio": True,
    "indiamart": False,
    "nykaa": True,
    "snapdeal": False,
    "redbubble": True,
    "shopsy": False,
    "tatacliq": True,
    "generic": False
}

def detect_platform(host: str) -> str:
    """Detect e-commerce platform from hostname."""
    host = host.lower()
    if "amazon." in host:
        return "amazon"
    elif "flipkart." in host:
        return "flipkart"
    elif "myntra." in host:
        return "myntra"
    elif "meesho." in host:
        return "meesho"
    elif "ajio." in host:
        return "ajio"
    elif "ebay." in host:
        return "ebay"
    elif "redbubble." in host:
        return "redbubble"
    elif "snapdeal." in host:
        return "snapdeal"
    elif "shopsy." in host:
        return "shopsy"
    elif "nykaa." in host:
        return "nykaa"
    elif "tatacliq." in host:
        return "tatacliq"
    elif "indiamart." in host:
        return "indiamart"
    elif "walmart." in host:
        return "walmart"
    else:
        return "generic"

def get_platform_display_name(platform: str) -> str:
    """Get display name for platform."""
    names = {
        "amazon": "AMAZON",
        "flipkart": "FLIPKART", 
        "myntra": "MYNTRA",
        "meesho": "MEESHO",
        "ajio": "AJIO",
        "ebay": "EBAY",
        "redbubble": "REDBUBBLE",
        "snapdeal": "SNAPDEAL",
        "shopsy": "SHOPSY",
        "nykaa": "NYKAA",
        "tatacliq": "TATA CLIQ",
        "indiamart": "INDIAMART",
        "walmart": "WALMART",
        "generic": "UNKNOWN PLATFORM (Generic Mode)"
    }
    return names.get(platform, platform.upper())

def get_extractor(platform: str):
    """Get extractor class for the platform."""
    return PLATFORM_EXTRACTORS.get(platform, GenericExtractor)

def get_platform_type(platform: str) -> str:
    """Get platform type (pagination, infinite_scroll, no_pagination)."""
    return PLATFORM_TYPES.get(platform, "pagination")

def get_platform_variant_support(platform: str) -> bool:
    """Check if platform supports variant extraction."""
    return PLATFORM_VARIANT_SUPPORT.get(platform, False)
