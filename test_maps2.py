import time
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from playwright.sync_api import sync_playwright, expect
import re
import urllib.parse

@dataclass
class BusinessListing:
    name: str
    address: str
    rating: Optional[float]
    url: Optional[str]

class GoogleMapsScraper:
    def __init__(self, headless: bool = False):
        self.listings: List[BusinessListing] = []
        self.seen_urls: Set[str] = set()
        
    def run(self, search_query: str, min_listings: int = 120) -> List[BusinessListing]:
        print(f"🚀 Scraping: '{search_query}' | Target: {min_listings}")
        print("-" * 90)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                search_url = self._build_search_url(search_query)
                print(f"🔗 Loading: {search_url}")
                
                self._setup_page(page)
                page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for initial results
                page.wait_for_selector('[role="main"], .m6QErb, [role="feed"]', timeout=30000)
                time.sleep(5)
                
                # AGGRESSIVE SCROLLING FOR 120+ RESULTS
                listings = self._aggressive_scroll(page, min_listings)
                self._print_results(listings)
                return listings
                
            finally:
                browser.close()
    
    def _build_search_url(self, query: str) -> str:
        encoded = urllib.parse.quote(query)
        return f"https://www.google.com/maps/search/{encoded}"
    
    def _setup_page(self, page):
        def block_resources(route):
            url = route.request.url.lower()
            if any(x in url for x in ['.png', '.jpg', '.gif', '/images/', '/img/', '/ads/']):
                route.abort()
            else:
                route.continue_()
        page.route("**/*", block_resources)
    
    def _aggressive_scroll(self, page, min_listings: int) -> List[BusinessListing]:
        """Aggressive scrolling to get 120+ results"""
        print("📜 AGGRESSIVE SCROLL STARTED...")
        
        total_scrolls = 0
        max_scrolls = 80
        last_count = 0
        
        while len(self.listings) < min_listings and total_scrolls < max_scrolls:
            total_scrolls += 1
            
            # SCROLL 1: Main results panel (left side)
            self._scroll_results_panel(page)
            
            # SCROLL 2: Entire page
            page.evaluate("window.scrollBy(0, 1500)")
            
            # SCROLL 3: Find any scrollable containers
            self._scroll_all_containers(page)
            
            # Extract
            before_extract = len(self.listings)
            self._extract_all_listings(page)
            new_found = len(self.listings) - before_extract
            
            print(f"📊 Scroll #{total_scrolls:2d} | Found: {len(self.listings):3d} | New: +{new_found:2d}")
            
            # Progressive delays
            time.sleep(2 + (total_scrolls * 0.1))
            
            # Stabilize every 10 scrolls
            if total_scrolls % 10 == 0:
                print("⏸️  Stabilizing...")
                time.sleep(4)
                page.mouse.wheel(0, 200)  # Small scroll to trigger lazy load
        
        print(f"✅ SCROLLING DONE: {len(self.listings)} total listings")
        return self.listings
    
    def _scroll_results_panel(self, page):
        """Scroll main results panel"""
        selectors = [
            '[role="feed"]', '[role="list"]', '.m6QErb', 
            '[jsaction*="pane.result"]', '[role="main"] div[role="main"]'
        ]
        for selector in selectors:
            try:
                container = page.locator(selector).first
                if container.count() > 0:
                    container.scroll_into_view_if_needed()
                    container.evaluate('el => el.scrollTop += 2000')
                    time.sleep(0.8)
                    break
            except:
                continue
    
    def _scroll_all_containers(self, page):
        """Scroll all possible containers"""
        containers = page.locator('div[style*="overflow"], div[style*="scroll"], [role="main"] div').all()
        for container in containers[:5]:  # Top 5 containers
            try:
                container.scroll_into_view_if_needed()
                container.evaluate('el => el.scrollTop += 1000')
                time.sleep(0.3)
            except:
                continue
    
    def _extract_all_listings(self, page):
        """Extract ALL visible listings with multiple passes"""
        all_selectors = [
            # Main listing selectors
            'a[href*="/place/"]',
            'div[role="article"]',
            '.Nv2PK', '.qBF1Pd', 
            '[role="heading"]', 'h3',
            # Additional patterns
            '[data-result-index]', '[data-index]',
            '.section-result', '.section-result-content'
        ]
        
        for selector in all_selectors:
            elements = page.locator(selector).all()
            for elem in elements:
                try:
                    listing = self._parse_listing(elem)
                    if listing and listing.url and listing.url not in self.seen_urls:
                        self.seen_urls.add(listing.url)
                        self.listings.append(listing)
                except:
                    continue
    
    def _parse_listing(self, element) -> Optional[BusinessListing]:
        try:
            # NAME - multiple selectors
            name_selectors = [
                '[role="heading"]', 'h3', '.qBF1Pd', 
                '.Nv2PK', '.fontHeadline', '.section-result-title'
            ]
            name = None
            for sel in name_selectors:
                try:
                    name_elem = element.locator(sel).first
                    if name_elem.count() > 0:
                        name = name_elem.inner_text().strip()
                        if name and len(name) > 2 and name != "Maps":
                            break
                except:
                    continue
            
            if not name:
                return None
            
            # URL
            url_selectors = ['a[href*="/place/"]', 'a[href*="/maps/place/"]']
            url = None
            for sel in url_selectors:
                href_elem = element.locator(sel).first
                if href_elem.count() > 0:
                    href = href_elem.get_attribute('href')
                    if href:
                        match = re.search(r'(https://[^&\s]+/maps/place/[^&\s]+)', href)
                        if match:
                            url = match.group(1)
                            break
            
            # ADDRESS
            address = "N/A"
            addr_selectors = [
                '.W4Efsd', '.fontBodyMedium', 
                '[data-item-id*="address"]', '.Io6YTe'
            ]
            for sel in addr_selectors:
                addr_elem = element.locator(sel).first
                if addr_elem.count() > 0:
                    addr_text = addr_elem.inner_text().strip()
                    if addr_text and addr_text != name and len(addr_text) > 6:
                        address = addr_text[:80]
                        break
            
            # RATING
            rating = None
            rating_selectors = [
                '[aria-label*="rated"]', '.MW4etd', 
                'span[aria-hidden="true"]', '.fontBodySmall'
            ]
            for sel in rating_selectors:
                rating_elem = element.locator(sel).first
                if rating_elem.count() > 0:
                    text = rating_elem.get_attribute('aria-label') or rating_elem.inner_text()
                    match = re.search(r'(\d+\.?\d*)', text)
                    if match:
                        rating = float(match.group(1))
                        break
            
            return BusinessListing(name=name, address=address, rating=rating, url=url)
            
        except:
            return None
    
    def _print_results(self, listings: List[BusinessListing]):
        print("\n" + "="*120)
        print(f"🎉 SUCCESS: {len(listings)} BUSINESSES EXTRACTED")
        print("="*120)
        
        # Stats
        ratings = [l.rating for l in listings if l.rating]
        avg = sum(ratings)/len(ratings) if ratings else 0
        high_rated = sum(1 for r in ratings if r >= 4.0)
        
        print(f"📊 AVG: {avg:.1f}⭐ | 4.0+: {high_rated} | URLs: {len([l for l in listings if l.url])}")
        print("\n🏢 TOP RESULTS:")
        print("-" * 120)
        
        for i, listing in enumerate(listings[:120], 1):
            rating_str = f"{listing.rating:.1f}" if listing.rating else "N/R"
            url_short = listing.url[:60] + "..." if len(listing.url or "") > 60 else (listing.url or "No URL")
            
            print(f"{i:3d} | {listing.name}")
            print(f"     📍 {listing.address}")
            print(f"     ⭐ {rating_str} | {url_short}")
            print("-" * 120)


if __name__ == "__main__":
    scraper = GoogleMapsScraper(headless=False)
    scraper.run("Dentists in Dubai", 120)