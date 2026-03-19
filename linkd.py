import undetected_chromedriver as uc
import json
import time
import random
import os
import tempfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from humancursor import WebCursor

class SalesNavigatorScraper:
    def __init__(self, cookie_file='linkedin_cookies.json'):
        self.cookie_file = cookie_file
        self.driver = None
        self.cursor = None  # HumanCursor WebCursor instance
        self.cookies = self.load_cookies()
        
    def load_cookies(self):
        """Load cookies from linkedin_cookies.json"""
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            print(f"✅ Loaded {len(cookies)} cookies from file")
            
            # Verify critical cookies for Sales Navigator
            cookie_names = [c.get('name') for c in cookies]
            
            # Regular LinkedIn cookies
            regular_cookies = ['li_at', 'JSESSIONID', 'li_rm']
            
            # Sales Navigator specific cookies (CRITICAL)
            sales_nav_cookies = ['li_a', 'li_ep_auth_context']
            
            regular_present = [c for c in regular_cookies if c in cookie_names]
            sales_present = [c for c in sales_nav_cookies if c in cookie_names]
            
            print(f"📋 Regular LinkedIn cookies: {len(regular_present)}/{len(regular_cookies)}")
            print(f"📋 Sales Navigator cookies: {len(sales_present)}/{len(sales_nav_cookies)}")
            
            if len(sales_present) < 2:
                print("⚠️ WARNING: Missing Sales Navigator enterprise cookies!")
                print("   You need to export cookies AFTER logging into Sales Navigator")
                print("   Not just regular LinkedIn!")
            
            return cookies
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return None
    
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            print("🔄 Initializing Chrome driver...")
            
            self.driver = uc.Chrome(
                use_subprocess=True,
                headless=False,
            )
            
            time.sleep(2)
            self.cursor = WebCursor(self.driver)
            print("✅ Driver setup complete")
            print("🖱️  HumanCursor WebCursor initialized")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def human_idle(self, min_moves=2, max_moves=5):
        """Perform random human-like mouse movements over the visible page area"""
        if not self.cursor:
            return
        try:
            viewport_w = self.driver.execute_script("return window.innerWidth")
            viewport_h = self.driver.execute_script("return window.innerHeight")
            moves = random.randint(min_moves, max_moves)
            for _ in range(moves):
                x = random.randint(int(viewport_w * 0.1), int(viewport_w * 0.9))
                y = random.randint(int(viewport_h * 0.1), int(viewport_h * 0.85))
                self.cursor.move_to([x, y])
                time.sleep(random.uniform(0.3, 1.2))
        except Exception as e:
            pass  # Never block on human cursor errors

    def human_scroll(self, direction='down', times=3):
        """Scroll the page naturally like a human reading"""
        try:
            for _ in range(times):
                scroll_px = random.randint(250, 500) * (1 if direction == 'down' else -1)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_px});")
                time.sleep(random.uniform(0.6, 1.5))
                self.human_idle(1, 2)
        except Exception:
            pass

    def human_hover_elements(self, css_selector):
        """Find elements and hover over the first few like a human scanning the page"""
        if not self.cursor:
            return
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            targets = elements[:min(3, len(elements))]
            for el in targets:
                try:
                    self.cursor.move_to(el, relative_position=[random.uniform(0.2, 0.8), random.uniform(0.2, 0.8)])
                    time.sleep(random.uniform(0.4, 1.0))
                except Exception:
                    pass
        except Exception:
            pass

    def apply_stealth_after_load(self):
        """Apply stealth scripts after page is loaded"""
        try:
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                }
            """)
            print("✅ Stealth scripts applied")
        except Exception as e:
            print(f"⚠️ Stealth script error: {e}")
        self.inject_cursor_overlay()

    def inject_cursor_overlay(self):
        """Inject a visible cursor overlay so ActionChains mouse movements can be seen on screen.

        Selenium's ActionChains dispatches real DOM 'mousemove' events, so a JS listener can
        track the synthetic cursor position and render a visible dot that follows it.
        The overlay is a small circle that stays on top of all page content via a fixed-position
        div with a high z-index.  It is re-injected safely (idempotent guard via window flag).
        """
        try:
            self.driver.execute_script("""
                if (window.__humanCursorOverlayActive) return;
                window.__humanCursorOverlayActive = true;

                // Create the cursor indicator element
                var dot = document.createElement('div');
                dot.id = '__hc_cursor_dot';
                dot.style.cssText = [
                    'position: fixed',
                    'top: 0',
                    'left: 0',
                    'width: 18px',
                    'height: 18px',
                    'border-radius: 50%',
                    'background: rgba(255, 60, 60, 0.75)',
                    'border: 2px solid rgba(255,255,255,0.9)',
                    'box-shadow: 0 0 6px 2px rgba(255,60,60,0.45)',
                    'pointer-events: none',
                    'z-index: 2147483647',
                    'transform: translate(-50%, -50%)',
                    'transition: top 0.04s linear, left 0.04s linear'
                ].join(';');

                // Outer ring for a more visible halo effect
                var ring = document.createElement('div');
                ring.id = '__hc_cursor_ring';
                ring.style.cssText = [
                    'position: fixed',
                    'top: 0',
                    'left: 0',
                    'width: 34px',
                    'height: 34px',
                    'border-radius: 50%',
                    'border: 1.5px solid rgba(255,60,60,0.5)',
                    'pointer-events: none',
                    'z-index: 2147483646',
                    'transform: translate(-50%, -50%)',
                    'transition: top 0.08s linear, left 0.08s linear'
                ].join(';');

                document.body.appendChild(ring);
                document.body.appendChild(dot);

                // Track every mousemove event (ActionChains fires these as real DOM events)
                window.addEventListener('mousemove', function(e) {
                    var x = e.clientX + 'px';
                    var y = e.clientY + 'px';
                    dot.style.left = x;
                    dot.style.top  = y;
                    ring.style.left = x;
                    ring.style.top  = y;
                }, true);

                // Also track mousedown/mouseup for click feedback
                window.addEventListener('mousedown', function() {
                    dot.style.transform = 'translate(-50%, -50%) scale(0.6)';
                    dot.style.background = 'rgba(255, 150, 0, 0.9)';
                }, true);
                window.addEventListener('mouseup', function() {
                    dot.style.transform = 'translate(-50%, -50%) scale(1)';
                    dot.style.background = 'rgba(255, 60, 60, 0.75)';
                }, true);
            """)
        except Exception as e:
            pass  # Never block on overlay errors
    
    def inject_cookies(self):
        """Inject cookies into browser"""
        try:
            # First visit Google
            print("📡 Warming up browser...")
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            self.apply_stealth_after_load()
            
            # Navigate to LinkedIn
            print("📡 Navigating to LinkedIn...")
            self.driver.get("https://www.linkedin.com")
            time.sleep(random.uniform(3, 5))
            self.inject_cursor_overlay()
            self.human_idle(2, 4)  # Simulate human landing on page
            
            # Clear existing cookies
            self.driver.delete_all_cookies()
            print("🧹 Cleared existing cookies")
            
            # Add cookies one by one
            success_count = 0
            for cookie in self.cookies:
                try:
                    cookie_dict = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.linkedin.com',
                        'path': '/',
                    }
                    
                    if cookie.get('secure', False):
                        cookie_dict['secure'] = True
                    
                    if 'expirationDate' in cookie:
                        try:
                            cookie_dict['expiry'] = int(float(cookie['expirationDate']))
                        except:
                            pass
                    
                    self.driver.add_cookie(cookie_dict)
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ↳ Could not add {cookie.get('name')}: {str(e)[:50]}")
                    continue
            
            print(f"✅ Added {success_count} out of {len(self.cookies)} cookies")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(random.uniform(4, 6))
            self.inject_cursor_overlay()
            
            # Navigate to feed
            print("🔄 Navigating to feed...")
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(random.uniform(5, 8))
            self.inject_cursor_overlay()
            print("🖱️  Simulating human browsing the feed...")
            self.human_idle(3, 5)       # Look around the page
            self.human_scroll('down', random.randint(2, 4))  # Scroll down like reading
            time.sleep(random.uniform(1, 2))
            self.human_scroll('up', 1)  # Scroll back up slightly
            
            return True
            
        except Exception as e:
            print(f"❌ Cookie injection failed: {e}")
            return False
    
    def verify_connection(self):
        """Verify if cookies successfully authenticated"""
        print("\n" + "="*60)
        print("🔍 VERIFYING LINKEDIN CONNECTION")
        print("="*60)
        
        current_url = self.driver.current_url
        page_title = self.driver.title
        page_source = self.driver.page_source.lower()
        
        print(f"📍 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        
        # Check if logged in to regular LinkedIn
        is_logged_in = False
        reasons = []
        
        # Method 1: Check URL (but careful with login redirects)
        if 'feed' in current_url and 'login' not in current_url:
            is_logged_in = True
            reasons.append("On LinkedIn feed")
        
        # Method 2: Check for profile element
        try:
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".profile-rail-card, .feed-identity-module, .global-nav__me")
            if profile_elements:
                is_logged_in = True
                reasons.append("Profile element found")
                # Hover over the nav like a human would
                self.human_hover_elements(".global-nav__me")
        except:
            pass
        
        # Method 3: Check page content for logged-in indicators
        if 'notification' in page_source and 'message' in page_source and 'feed' in page_source:
            is_logged_in = True
            reasons.append("Found notification/message elements")
        
        print("\n📊 Authentication Results:")
        print(f"  {'✅' if is_logged_in else '❌'} Logged In: {is_logged_in}")
        if reasons:
            print(f"  📌 Evidence: {', '.join(reasons)}")
        
        # Take screenshot
        screenshot_file = f'linkedin_state_{int(time.time())}.png'
        self.driver.save_screenshot(screenshot_file)
        print(f"📸 Screenshot saved: {screenshot_file}")
        
        if is_logged_in:
            print("\n✅✅✅ SUCCESS: Connected to LinkedIn! ✅✅✅")
        else:
            print("\n❌❌❌ FAILED: Not connected to LinkedIn ❌❌❌")
        
        return is_logged_in
    
    def verify_sales_navigator_access(self):
        """Check if user has Sales Navigator access"""
        print("\n" + "="*60)
        print("🔍 CHECKING SALES NAVIGATOR ACCESS")
        print("="*60)
        
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        
        print(f"📍 Current URL: {current_url}")
        
        has_access = False
        reasons = []
        
        # Check if we're in Sales Navigator
        if 'sales' in current_url:
            has_access = True
            reasons.append("URL contains 'sales'")
        
        # Check for Sales Navigator specific elements
        if has_access:
            try:
                # Look for Sales Navigator specific elements
                sales_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".search-results__results-container, .sn-search-bar, .advanced-search-filters")
                if sales_elements:
                    reasons.append("Found Sales Navigator UI elements")
            except:
                pass
        
        # Check if we were redirected to upgrade page
        if 'upgrade' in current_url or 'premium' in current_url:
            print("❌ You don't have Sales Navigator access - redirected to upgrade page")
            return False
        
        print("\n📊 Sales Navigator Access Results:")
        print(f"  {'✅' if has_access else '❌'} Has Access: {has_access}")
        if reasons:
            print(f"  📌 Evidence: {', '.join(reasons)}")
        
        if has_access:
            print("\n✅✅✅ SUCCESS: You have Sales Navigator access! ✅✅✅")
            self.driver.save_screenshot('sales_navigator_success.png')
            print("📸 Screenshot saved as 'sales_navigator_success.png'")
        else:
            print("\n❌❌❌ FAILED: Cannot access Sales Navigator ❌❌❌")
            print("\n👉 Possible reasons:")
            print("   1. Your LinkedIn account doesn't have Sales Navigator subscription")
            print("   2. Your cookies are from regular LinkedIn, not Sales Navigator")
            print("   3. You need to log into Sales Navigator manually first")
        
        return has_access
    
    def run_verification(self):
        """Complete verification workflow"""
        print("\n" + "="*60)
        print("🚀 STARTING LINKEDIN VERIFICATION")
        print("="*60)
        
        if not self.cookies:
            print("❌ No cookies loaded. Exiting.")
            return False
        
        # Step 1: Setup driver
        if not self.setup_driver():
            return False
        
        # Step 2: Inject cookies
        if not self.inject_cookies():
            print("\n❌ Cookie injection failed.")
            self.cleanup()
            return False
        
        # Step 3: Verify regular LinkedIn connection
        if not self.verify_connection():
            print("\n❌ Cannot connect to regular LinkedIn.")
            self.cleanup()
            return False
        
        print("\n✅ Successfully connected to regular LinkedIn!")
        
        # Step 4: Automatically navigate to Sales Navigator
        print("\n🚀 Navigating to Sales Navigator...")
        self.driver.get("https://www.linkedin.com/sales/home")
        time.sleep(random.uniform(5, 8))
        self.inject_cursor_overlay()
        print("🖱️  Simulating human exploring Sales Navigator home...")
        self.human_idle(2, 4)
        self.human_scroll('down', random.randint(1, 3))
        time.sleep(random.uniform(1, 2))
        has_sales_nav = self.verify_sales_navigator_access()
        
        if has_sales_nav:
            print("\n✅✅✅ FULL SUCCESS! You can now scrape Sales Navigator! ✅✅✅")

            # Navigate to the target search URL and scrape all results
            search_url = (
                "https://www.linkedin.com/sales/search/people"
                "?page=2&query=(recentSearchParam%3A(id%3A4243190873%2CdoLogHistory%3Atrue)"
                "%2Cfilters%3AList((type%3ACURRENT_COMPANY%2Cvalues%3AList((id%3Aurn%253Ali"
                "%253Aorganization%253A66888315%2Ctext%3ANewCo%2520Capital%2520Group"
                "%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))))))"
                "&sessionId=4EskMkiwQJy%2BYzkxzD03rA%3D%3D&viewAllFilters=true"
            )

            leads = self.scrape_search_results(
                search_url=search_url,
                max_pages=5,
                output_file='newco_capital_leads.json'
            )

            if leads:
                print(f"\n🎉 Scraped {len(leads)} leads total!")
                print("📁 Files saved: newco_capital_leads.json + newco_capital_leads.csv")
            else:
                # Fallback: save raw HTML for manual inspection
                self.save_page_html('search_results.html')
        else:
            print("\n❌ Sales Navigator access failed.")
            print("\n📌 To fix this:")
            print("   1. Open Chrome manually and go to linkedin.com/sales")
            print("   2. Log in to Sales Navigator")
            print("   3. Use EditThisCookie to export cookies AGAIN")
            print("   4. Save the new cookies to 'linkedin_cookies.json'")
            print("   5. Run this script again")
        
        input("\nPress Enter to close browser...")
        self.cleanup()
        return True
    
    def extract_sample_data(self):
        """Extract sample data from Sales Navigator search results"""
        print("\n📊 Extracting sample data from search results...")
        
        try:
            search_url = (
                "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(doLogHistory%3Atrue)%2Cfilters%3AList((type%3ACURRENT_COMPANY%2Cvalues%3AList((id%3Aurn%253Ali%253Aorganization%253A67535055%2Ctext%3AElite%2520EPM%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))))))&sessionId=aNsocAN4TE6fWN7%2Bf2bBSg%3D%3D&viewAllFilters=true"
            )
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))
            self.inject_cursor_overlay()
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results__results-container"))
                )
                print("✅ Search results loaded")
                print("🖱️  Simulating human scanning results...")
                self.human_idle(2, 3)
                self.human_hover_elements(".search-results__result-item, .linked-area, .artdeco-entity-lockup")
                self.human_scroll('down', random.randint(3, 5))
                time.sleep(random.uniform(1.5, 3))
                self.human_scroll('up', random.randint(1, 2))
                
                # Save full rendered HTML
                self.save_page_html('extract_sample_data.html')

                # Take screenshot of results
                self.driver.save_screenshot('sales_navigator_results.png')
                print("📸 Results screenshot saved")
                
            except:
                print("⚠️ Could not find search results")
                
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
    
    def scrape_search_results(self, search_url, max_pages=5, output_file='scraped_leads.json'):
        """
        Navigate to a Sales Navigator search URL, scroll through results,
        scrape all lead data across multiple pages, and save to JSON + CSV.
        """
        import csv
        from bs4 import BeautifulSoup

        print(f"\n{'='*60}")
        print("📋 SCRAPING SALES NAVIGATOR SEARCH RESULTS")
        print(f"{'='*60}")

        all_leads = []
        page = 1

        while page <= max_pages:
            # Build page URL
            if page == 1:
                page_url = search_url
            else:
                if 'page=' in search_url:
                    import re
                    page_url = re.sub(r'page=\d+', f'page={page}', search_url)
                else:
                    separator = '&' if '?' in search_url else '?'
                    page_url = f"{search_url}{separator}page={page}"

            print(f"\n📄 Scraping page {page}/{max_pages}...")
            self.driver.get(page_url)
            time.sleep(random.uniform(5, 8))
            self.apply_stealth_after_load()

            # Wait for results panel to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-sn-view-name="module-lead-search-results"]')
                    )
                )
                print("✅ Results panel loaded")
            except Exception:
                print("⚠️  Results panel not found — page may be empty or blocked")
                break

            # Human-like: look around the page first
            self.human_idle(2, 3)
            time.sleep(random.uniform(1, 2))

            # Scroll the RIGHT panel (results list) naturally
            print("🖱️  Scrolling through results like a human...")
            self._scroll_results_panel()

            # Parse the fully rendered DOM
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract each lead card
            page_leads = self._extract_leads_from_soup(soup)

            if not page_leads:
                print(f"⚠️  No leads found on page {page} — stopping.")
                break

            print(f"✅ Found {len(page_leads)} leads on page {page}")
            all_leads.extend(page_leads)

            # Random human pause between pages
            if page < max_pages:
                wait = random.uniform(4, 8)
                print(f"⏳ Waiting {wait:.1f}s before next page...")
                self.human_idle(1, 3)
                time.sleep(wait)

            page += 1

        # ── Save results ──────────────────────────────────────────────
        print(f"\n📊 Total leads scraped: {len(all_leads)}")

        if all_leads:
            # JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_leads, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved JSON → '{output_file}'")

            # CSV
            csv_file = output_file.replace('.json', '.csv')
            fieldnames = ['name', 'title', 'location', 'company', 'metadata', 'profile_url']
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(all_leads)
            print(f"💾 Saved CSV  → '{csv_file}'")
        else:
            print("❌ No leads were scraped.")

        return all_leads

    def _scroll_results_panel(self):
        """Scroll the right-side results panel in a human-like way to load all cards"""
        try:
            # The results panel container
            panel_selector = '[data-sn-view-name="module-lead-search-results"]'
            panel = self.driver.find_element(By.CSS_SELECTOR, panel_selector)

            last_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", panel
            )

            scroll_attempts = 0
            max_scroll_attempts = 15

            while scroll_attempts < max_scroll_attempts:
                # Scroll down by a random human-like amount
                scroll_px = random.randint(300, 600)
                self.driver.execute_script(
                    "arguments[0].scrollBy(0, arguments[1]);", panel, scroll_px
                )
                time.sleep(random.uniform(0.8, 1.8))

                # Occasionally move cursor over results (human scanning)
                if random.random() < 0.4:
                    self.human_hover_elements(
                        'a[data-control-name="view_lead_panel_via_search_lead_name"]'
                    )
                    time.sleep(random.uniform(0.3, 0.8))

                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", panel
                )

                if new_height == last_height:
                    # Try once more after a longer wait (lazy loading)
                    time.sleep(random.uniform(1.5, 2.5))
                    new_height = self.driver.execute_script(
                        "return arguments[0].scrollHeight", panel
                    )
                    if new_height == last_height:
                        break  # Truly at the bottom

                last_height = new_height
                scroll_attempts += 1

            # Scroll back to top of panel before extracting
            self.driver.execute_script("arguments[0].scrollTo(0, 0);", panel)
            time.sleep(random.uniform(0.5, 1.0))
            print(f"  ↳ Scrolled {scroll_attempts} times through results panel")

        except Exception as e:
            # Fallback: scroll the whole page
            print(f"  ↳ Panel scroll fallback (page scroll): {e}")
            self.human_scroll('down', random.randint(4, 7))
            self.human_scroll('up', 1)

    def _extract_leads_from_soup(self, soup):
        """Parse BeautifulSoup HTML and extract lead data from result cards"""
        leads = []

        # Find all name links — each is one person result
        name_links = soup.find_all(
            'a',
            attrs={'data-control-name': 'view_lead_panel_via_search_lead_name'}
        )

        for link in name_links:
            lead = {}

            # ── Name ──────────────────────────────────────
            lead['name'] = link.get_text(strip=True)

            # ── Profile URL ───────────────────────────────
            href = link.get('href', '')
            lead['profile_url'] = f"https://www.linkedin.com{href}" if href.startswith('/') else href

            # ── Walk up to the lockup content container ───
            # Structure: a[name] → div.__title → div.__content → div[lockup]
            content_div = link.find_parent(class_='artdeco-entity-lockup__content')

            if content_div:
                # Title / Role
                subtitle = content_div.find(class_='artdeco-entity-lockup__subtitle')
                lead['title'] = subtitle.get_text(separator=' ', strip=True) if subtitle else ''

                # Location
                caption = content_div.find(class_='artdeco-entity-lockup__caption')
                lead['location'] = caption.get_text(separator=' ', strip=True) if caption else ''

                # Company / extra metadata
                metadata = content_div.find(class_='artdeco-entity-lockup__metadata')
                lead['company'] = metadata.get_text(separator=' ', strip=True) if metadata else ''
            else:
                lead['title'] = ''
                lead['location'] = ''
                lead['company'] = ''

            # Only add if we got at least a name
            if lead['name']:
                leads.append(lead)

        return leads

    def cleanup(self):
        """Clean up resources"""
        try:
            self.driver.quit()
        except:
            pass

    def save_page_html(self, filename=None):
        """Save the fully rendered DOM (like DevTools Elements panel) to an HTML file"""
        try:
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f'page_source_{timestamp}.html'

            # Get the live rendered DOM (post-JS, same as Elements panel in DevTools)
            rendered_html = self.driver.execute_script(
                "return document.documentElement.outerHTML;"
            )

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(rendered_html)

            print(f"✅ Full page HTML saved to '{filename}' ({len(rendered_html):,} characters)")
            return filename
        except Exception as e:
            print(f"❌ Failed to save HTML: {e}")
            return None

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     LINKEDIN SALES NAVIGATOR ACCESS VERIFIER             ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    COOKIE_FILE = 'linkedin_cookies.json'
    
    # Check if cookie file exists
    if not os.path.exists(COOKIE_FILE):
        print(f"❌ Cookie file '{COOKIE_FILE}' not found!")
        print("\n📌 First time setup:")
        print("   1. Open Chrome and go to https://www.linkedin.com/sales")
        print("   2. Log into your Sales Navigator account")
        print("   3. Install 'EditThisCookie' from Chrome Web Store")
        print("   4. Click the cookie icon and export cookies as JSON")
        print("   5. Save as 'linkedin_cookies.json' in this folder")
        print("   6. Run this script again")
        exit()
    
    # Run the verifier
    scraper = SalesNavigatorScraper(COOKIE_FILE)
    scraper.run_verification()