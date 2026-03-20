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
        
        if is_logged_in:
            print("\n✅✅✅ SUCCESS: Connected to LinkedIn! ✅✅✅")
        else:
            print("\n❌❌❌ FAILED: Not connected to LinkedIn ❌❌❌")
        
        return is_logged_in
    
    def navigate_to_sales_navigator(self):
        """
        Click the 'Go to Sales Navigator' link that appears directly in the
        left sidebar of the LinkedIn feed page.
        Falls back to direct URL only if the element cannot be found.
        """
        print("\n🖱️  Attempting to navigate to Sales Navigator via UI click...")

        sn_link = None

        # ── CSS selectors targeting the left-sidebar link ─────────────────────
        # Real DOM: <a href="https://www.linkedin.com/sales"
        #              class="feed-left-nav-growth-widgets_link ...">
        #             <span>Go to Sales Navigator</span>
        #           </a>
        sn_css_selectors = [
            'a.feed-left-nav-growth-widgets_link',
            'a[href="https://www.linkedin.com/sales"]',
            'a[href*="linkedin.com/sales"]',
        ]

        for sel in sn_css_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    sn_link = els[0]
                    print(f"  ✅ Found Sales Navigator link via: {sel}")
                    break
            except Exception:
                continue

        # ── XPath fallback: match by the visible span text ────────────────────
        if not sn_link:
            try:
                sn_link = self.driver.find_element(
                    By.XPATH,
                    '//span[normalize-space(text())="Go to Sales Navigator"]/ancestor::a'
                )
                print("  ✅ Found Sales Navigator link via XPath text match")
            except Exception:
                pass

        # ── Click it ──────────────────────────────────────────────────────────
        if sn_link:
            try:
                original_handles = set(self.driver.window_handles)
                self.cursor.click_on(sn_link)
                print("  🖱️  Clicked 'Go to Sales Navigator' link in left sidebar")

                # The link has target="_blank" — it opens in a NEW TAB.
                # Wait up to 10 s for the new tab to appear, then switch to it.
                new_handle = None
                for _ in range(20):
                    time.sleep(0.5)
                    current_handles = set(self.driver.window_handles)
                    diff = current_handles - original_handles
                    if diff:
                        new_handle = diff.pop()
                        break

                if new_handle:
                    self.driver.switch_to.window(new_handle)
                    print(f"  🔀 Switched to new tab: {self.driver.current_url}")
                else:
                    print("  ⚠️  No new tab detected — may have opened in same tab")

                # Wait for Sales Navigator to fully load
                try:
                    WebDriverWait(self.driver, 20).until(
                        lambda d: "sales" in d.current_url
                    )
                    print(f"  ✅ Confirmed on Sales Navigator: {self.driver.current_url}")
                except Exception:
                    print(f"  ⚠️  Timed out waiting for sales URL, current: {self.driver.current_url}")

                time.sleep(random.uniform(3, 5))
                self.inject_cursor_overlay()
                self.human_idle(2, 3)
                return True
            except Exception as e:
                print(f"  ⚠️  click_on failed: {e}")

        # ── Fallback: direct URL ───────────────────────────────────────────────
        print("  ⚠️  UI navigation failed — falling back to direct URL")
        self.driver.get("https://www.linkedin.com/sales/home")
        time.sleep(random.uniform(5, 8))
        self.inject_cursor_overlay()
        self.human_idle(2, 3)
        return False

    def click_lead_filters(self):
        """
        On the Sales Navigator home/search page, click the 'Lead filters' button.
        Real DOM: <a href="/sales/search/people?viewAllFilters=true">Lead filters</a>
        """
        print("\n🖱️  Looking for 'Lead filters' button...")

        lead_filter_link = None

        # ── CSS selectors from the actual DOM ─────────────────────────────────
        selectors = [
            'a[href="/sales/search/people?viewAllFilters=true"]',
            'a[href*="viewAllFilters=true"]',
            'a[href*="sales/search/people"]',
        ]

        for sel in selectors:
            try:
                els = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel))
                )
                if els:
                    lead_filter_link = els[0]
                    print(f"  ✅ Found Lead filters via: {sel}")
                    break
            except Exception:
                continue

        # ── XPath fallback: match visible span text ────────────────────────────
        if not lead_filter_link:
            try:
                lead_filter_link = self.driver.find_element(
                    By.XPATH,
                    '//span[normalize-space(text())="Lead filters"]/ancestor::a'
                )
                print("  ✅ Found Lead filters via XPath text match")
            except Exception:
                pass

        if lead_filter_link:
            try:
                self.cursor.click_on(lead_filter_link)
                print("  🖱️  Clicked 'Lead filters' button")
                # Wait until the search/people page with filters loads
                WebDriverWait(self.driver, 15).until(
                    lambda d: 'sales/search/people' in d.current_url
                )
                print(f"  ✅ Lead filters page loaded: {self.driver.current_url}")
                time.sleep(random.uniform(2, 4))
                self.inject_cursor_overlay()
                self.human_idle(1, 2)
                return True
            except Exception as e:
                print(f"  ⚠️  Lead filters click failed: {e}")
        else:
            print("  ⚠️  Lead filters button not found on page")

        return False

    def enter_company_filter(self, company_name: str):
        """
        On the Sales Navigator search/people page (after clicking Lead filters):
          1. Wait for the 'Current company' fieldset to be present
          2. Scroll it into view so cursor actions work
          3. Click the toggle button to ensure the section is expanded & focused
          4. Find the typeahead input inside the fieldset
          5. Click it, type the company name at human speed
          6. Click the first autocomplete suggestion (Enter as fallback)
        """
        from selenium.webdriver.common.keys import Keys

        print(f"\n🏢 Entering company filter: '{company_name}'...")

        # ── Step 1: Wait for the Current company fieldset ────────────────────
        fieldset_sel = 'fieldset[data-x-search-filter="CURRENT_COMPANY"]'
        try:
            fieldset = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, fieldset_sel))
            )
            print("  ✅ Found Current company fieldset")
        except Exception:
            print("  ⚠️  Current company fieldset not found — filters panel may not be open")
            return False

        # ── Step 2: Scroll the fieldset into view ────────────────────────────
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", fieldset
        )
        time.sleep(random.uniform(0.5, 1.0))

        # ── Step 3: Click the Current company toggle button ──────────────────
        # The button lives just below the "Company" legend inside the fieldset:
        #   <fieldset data-x-search-filter="CURRENT_COMPANY">
        #     <div class="ph4 flex align-items-center relative">
        #       <legend …>…</legend>
        #       <button aria-expanded="false"
        #               class="… search-filter_focus-target--button …">
        #
        # We must click it whenever aria-expanded="false" so the section
        # expands and the typeahead input becomes visible in the DOM.
        toggle_btn = None
        toggle_btn_selectors = [
            'button.search-filter_focus-target--button',
            'button[aria-expanded]',
            'button.button--fill-click-area',
        ]
        for sel in toggle_btn_selectors:
            try:
                els = fieldset.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    toggle_btn = els[0]
                    print(f"  ✅ Found Company toggle button via: {sel}")
                    break
            except Exception:
                continue

        if toggle_btn is None:
            # XPath fallback — look for the expand/collapse button directly
            try:
                toggle_btn = fieldset.find_element(
                    By.XPATH,
                    './/button[@aria-expanded]'
                )
                print("  ✅ Found Company toggle button via XPath")
            except Exception:
                pass

        if toggle_btn:
            # Scroll the button itself into view so cursor coordinates are correct
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", toggle_btn
            )
            time.sleep(random.uniform(0.3, 0.6))

            is_expanded = toggle_btn.get_attribute('aria-expanded')
            print(f"  ℹ️  Company toggle aria-expanded='{is_expanded}'")

            if is_expanded == 'false':
                print("  🖱️  Clicking Company toggle button to expand the section...")
                # Primary: human cursor click
                clicked = False
                try:
                    self.cursor.click_on(toggle_btn)
                    clicked = True
                except Exception as e:
                    print(f"  ⚠️  cursor.click_on failed ({e}) — trying JS click")

                if not clicked:
                    try:
                        self.driver.execute_script("arguments[0].click();", toggle_btn)
                        clicked = True
                        print("  ✅ JS click succeeded")
                    except Exception as e2:
                        print(f"  ⚠️  JS click also failed: {e2}")

                # Wait for the section to actually expand (aria-expanded becomes "true")
                try:
                    WebDriverWait(self.driver, 8).until(
                        lambda d: toggle_btn.get_attribute('aria-expanded') == 'true'
                    )
                    print("  ✅ Company section expanded")
                except Exception:
                    print("  ⚠️  aria-expanded did not switch to true — continuing anyway")
                time.sleep(random.uniform(0.6, 1.2))
            else:
                print("  ✅ Company section already expanded")
        else:
            print("  ⚠️  Company toggle button not found — section may already be expanded")

        # ── Step 4: Find the input inside the fieldset ───────────────────────
        # The input only appears AFTER the section is expanded; use
        # visibility_of_element_located so we wait for it to be truly visible.
        company_input = None
        input_selectors = [
            'input[placeholder="Add current companies and account lists"]',
            'input.search-filter_focus-target--input',
            'input.artdeco-typeahead__input',
            'input[type="text"]',
        ]

        for sel in input_selectors:
            try:
                company_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, f'{fieldset_sel} {sel}')
                    )
                )
                print(f"  ✅ Found company input via: {sel}")
                break
            except Exception:
                continue

        if not company_input:
            try:
                company_input = self.driver.find_element(
                    By.XPATH,
                    f'//fieldset[@data-x-search-filter="CURRENT_COMPANY"]'
                    f'//input[contains(@placeholder, "companies")]'
                )
                print("  ✅ Found company input via XPath")
            except Exception:
                pass

        if not company_input:
            print("  ⚠️  Company filter input not found inside fieldset")
            return False

        # ── Step 5: Click the input and type the company name ─────────────────
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", company_input
        )
        time.sleep(random.uniform(0.3, 0.6))

        try:
            self.cursor.click_on(company_input)
            time.sleep(random.uniform(0.5, 1.0))
        except Exception as e:
            print(f"  ⚠️  Could not click input: {e}")
            return False

        print(f"  ⌨️  Typing '{company_name}'...")
        for char in company_name:
            company_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.18))

        # Wait for autocomplete dropdown to populate
        time.sleep(random.uniform(1.8, 2.8))

        # ── Step 6: Click the first matching suggestion ───────────────────────
        suggestion = None
        suggestion_selectors = [
            '.artdeco-typeahead__results-list li:first-child',
            '[role="option"]:first-child',
            '.search-filter-typeahead-result:first-child',
            '.basic-typeahead__selectable:first-child',
        ]

        for sel in suggestion_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    suggestion = els[0]
                    print(f"  ✅ Found suggestion via: {sel}")
                    break
            except Exception:
                continue

        if not suggestion:
            try:
                suggestion = self.driver.find_element(
                    By.XPATH,
                    f'//*[@role="option" and contains(., "{company_name.split()[0]}")]'
                )
                print("  ✅ Found suggestion via XPath text match")
            except Exception:
                pass

        if suggestion:
            try:
                self.cursor.click_on(suggestion)
                print(f"  🖱️  Clicked suggestion for '{company_name}'")
            except Exception as e:
                print(f"  ⚠️  Could not click suggestion ({e}) — pressing Enter instead")
                company_input.send_keys(Keys.RETURN)
        else:
            print("  ℹ️  No suggestion found — pressing Enter")
            company_input.send_keys(Keys.RETURN)

        # Wait for results to refresh with the company filter applied
        time.sleep(random.uniform(2.5, 4.0))
        self.inject_cursor_overlay()
        self.human_idle(1, 2)
        print(f"  ✅ Company filter applied for '{company_name}'")
        return True

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
        
        # Step 4: Navigate to Sales Navigator by clicking through the UI
        print("\n🚀 Navigating to Sales Navigator via UI clicks...")
        self.navigate_to_sales_navigator()
        print("🖱️  Simulating human exploring Sales Navigator home...")
        self.human_idle(2, 4)
        self.human_scroll('down', random.randint(1, 3))
        time.sleep(random.uniform(1, 2))
        has_sales_nav = self.verify_sales_navigator_access()

        # Step 5: Click 'Lead filters' to navigate to the people search page
        if has_sales_nav:
            self.click_lead_filters()

        # Step 6: Type company name in the company filter input and select suggestion
        if has_sales_nav:
            self.enter_company_filter("serviceocean AG")

        if has_sales_nav:
            print("\n FULL SUCCESS! You can now scrape Sales Navigator !")

            # Use the current URL (fresh session, valid sessionId) instead of
            # any hardcoded/old URL — avoids LinkedIn redirecting back to feed
            # due to an expired sessionId.
            current_search_url = self.driver.current_url
            print(f"🔗 Using live search URL: {current_search_url}")

            leads = self.scrape_search_results(
                search_url=current_search_url,
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

        # Load the first page via URL, then use Next button clicks for subsequent pages
        # If the driver is already on the correct search page (e.g. after click_lead_filters),
        # skip the driver.get() to avoid a redundant navigation with a potentially stale URL.
        already_on_page = (
            'sales/search/people' in self.driver.current_url
            or 'sales/search' in self.driver.current_url
        )

        if already_on_page:
            print(f"\n📄 Already on search page — skipping navigation, scraping page 1...")
            # Still apply stealth and wait for panel
            self.apply_stealth_after_load()
        else:
            print(f"\n📄 Loading page 1 — navigating to search URL...")
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))
            self.apply_stealth_after_load()

        while page <= max_pages:
            print(f"\n📄 Scraping page {page}/{max_pages}...")

            # Wait for results panel to be present
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

            # Scroll the RIGHT side of the page to the bottom (triggers lazy loading)
            print("🖱️  Scrolling to bottom of results page...")
            self._scroll_results_panel()

            # Parse the fully rendered DOM after all cards have lazy-loaded
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract each lead card
            page_leads = self._extract_leads_from_soup(soup)

            if not page_leads:
                print(f"⚠️  No leads found on page {page} — stopping.")
                break

            print(f"✅ Found {len(page_leads)} leads on page {page}")
            all_leads.extend(page_leads)

            # Stop if we've hit the max or there is no next page
            if page >= max_pages:
                break

            # Human pause then click Next
            wait = random.uniform(3, 6)
            print(f"⏳ Waiting {wait:.1f}s before next page...")
            self.human_idle(1, 2)
            time.sleep(wait)

            if not self._click_next_page():
                print("🏁 No more pages — done.")
                break

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
        """
        Scroll the RIGHT results panel of Sales Navigator to the bottom so all
        lead cards lazy-load.

        Sales Navigator uses a split-pane layout: the right panel is its own
        scrollable container — it only responds to scroll when the mouse is
        hovering over it.  Strategy:
          1. Find the first visible lead card.
          2. Move the cursor onto it (mouse now hovers over the right panel).
          3. Use JS to walk up the DOM and find the actual scrollable parent.
          4. Repeatedly scrollBy on that element until scrollHeight stops growing.
        """
        print("  📜 Scrolling right results panel to bottom (lazy-load)...")

        # ── Step 1: locate first lead card link ──────────────────────────────
        lead_card = None
        try:
            lead_card = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    'a[data-control-name="view_lead_panel_via_search_lead_name"]'
                ))
            )
        except Exception:
            pass

        # ── Step 2: move cursor onto the card so the panel receives events ───
        if lead_card:
            try:
                self.cursor.move_to(lead_card)
                time.sleep(random.uniform(0.4, 0.8))
            except Exception:
                pass

        # ── Step 3: find the scrollable parent of the lead card via JS ───────
        # Walks up the DOM tree and returns the first element whose computed
        # overflow-y is 'scroll' or 'auto' and whose scrollHeight > clientHeight.
        scroll_panel = None
        if lead_card:
            try:
                scroll_panel = self.driver.execute_script("""
                    var el = arguments[0];
                    while (el && el !== document.body) {
                        var style = window.getComputedStyle(el);
                        var oy = style.overflowY;
                        if ((oy === 'scroll' || oy === 'auto') &&
                                el.scrollHeight > el.clientHeight) {
                            return el;
                        }
                        el = el.parentElement;
                    }
                    return null;
                """, lead_card)
            except Exception:
                pass

        if scroll_panel:
            print("  ✅ Found scrollable right panel via DOM walk")
        else:
            print("  ⚠️  Scrollable panel not found — falling back to window scroll")

        # ── Step 4: scroll to the bottom, waiting for lazy loads ─────────────
        scroll_attempts  = 0
        max_scroll_attempts = 25

        def _get_height():
            if scroll_panel:
                return self.driver.execute_script(
                    "return arguments[0].scrollHeight", scroll_panel
                )
            return self.driver.execute_script("return document.body.scrollHeight")

        def _scroll_down(px):
            if scroll_panel:
                self.driver.execute_script(
                    "arguments[0].scrollBy(0, arguments[1]);", scroll_panel, px
                )
            else:
                self.driver.execute_script(f"window.scrollBy(0, {px});")

        def _scroll_top():
            if scroll_panel:
                self.driver.execute_script("arguments[0].scrollTo(0, 0);", scroll_panel)
            else:
                self.driver.execute_script("window.scrollTo(0, 0);")

        last_height = _get_height()

        while scroll_attempts < max_scroll_attempts:
            scroll_px = random.randint(300, 550)
            _scroll_down(scroll_px)
            time.sleep(random.uniform(0.8, 1.6))

            # Occasionally re-hover a card so the panel keeps focus
            if random.random() < 0.4 and lead_card:
                try:
                    self.cursor.move_to(lead_card)
                    time.sleep(random.uniform(0.2, 0.5))
                except Exception:
                    pass

            new_height = _get_height()
            if new_height == last_height:
                # Give lazy-loading extra time
                time.sleep(random.uniform(2.0, 3.0))
                new_height = _get_height()
                if new_height == last_height:
                    print(f"  ↳ Reached bottom after {scroll_attempts} scrolls")
                    break

            last_height = new_height
            scroll_attempts += 1

        # Return to top of panel before extraction
        _scroll_top()
        time.sleep(random.uniform(0.5, 1.0))

    def _click_next_page(self):
        """
        Click the Next page button on Sales Navigator search results using
        cursor.click_on() for human-like movement.
        Returns True if the next page loaded, False if no Next button found.
        """
        next_btn = None

        # Standard Sales Navigator pagination — 'Next' button
        next_selectors = [
            'button[aria-label="Next"]',
            'button[aria-label="next"]',
            '[data-test-pagination-page-btn="next"]',
            'button.artdeco-pagination__button--next',
        ]

        for sel in next_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].is_enabled():
                    next_btn = els[0]
                    print(f"  ✅ Found Next button via: {sel}")
                    break
            except Exception:
                continue

        if not next_btn:
            try:
                next_btn = self.driver.find_element(
                    By.XPATH,
                    '//button[normalize-space(.)="Next" or @aria-label="Next"]'
                )
                print("  ✅ Found Next button via XPath")
            except Exception:
                pass

        if next_btn:
            try:
                current_url = self.driver.current_url

                # ── Scroll the button fully into the visible viewport ─────────
                # This prevents HumanCursor's MoveTargetOutOfBoundsException which
                # happens when the target element is outside the viewport bounds.
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                    next_btn
                )
                time.sleep(random.uniform(0.6, 1.2))

                # ── Re-fetch the button right before clicking ─────────────────
                # After the scroll LinkedIn's React layer may re-render, making
                # the old element reference stale.  Re-query to get a fresh node.
                fresh_btn = None
                for sel in next_selectors:
                    try:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if els and els[0].is_enabled():
                            fresh_btn = els[0]
                            break
                    except Exception:
                        continue
                if fresh_btn is None:
                    fresh_btn = next_btn  # fall back to original if re-fetch fails

                # Scroll the fresh reference into center as well
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                    fresh_btn
                )
                time.sleep(random.uniform(0.3, 0.6))

                # ── Primary click: HumanCursor ─────────────────────────────────
                click_ok = False
                try:
                    self.cursor.click_on(fresh_btn)
                    click_ok = True
                    print("  🖱️  Clicked Next page button (human cursor)")
                except Exception as ce:
                    print(f"  ⚠️  cursor.click_on failed ({ce}) — trying JS click")

                # ── Fallback click: JavaScript ─────────────────────────────────
                if not click_ok:
                    try:
                        self.driver.execute_script("arguments[0].click();", fresh_btn)
                        click_ok = True
                        print("  🖱️  Clicked Next page button (JS fallback)")
                    except Exception as je:
                        print(f"  ⚠️  JS click also failed: {je}")

                if not click_ok:
                    print("  ⚠️  All click strategies failed for Next button")
                    return False

                # ── Wait for the page to advance ───────────────────────────────
                # Sales Navigator may update the URL (page param) or just swap
                # the results panel in-place without a URL change.  We wait for
                # either the URL to change OR the results panel to go stale and
                # reload (detected via a brief staleness check).
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda d: d.current_url != current_url
                    )
                    print(f"  ✅ New page loaded: {self.driver.current_url}")
                except Exception:
                    # URL did not change — SPA in-place update; wait a moment for
                    # the results panel to re-render
                    print("  ℹ️  URL unchanged — waiting for results panel to refresh...")
                    time.sleep(random.uniform(3, 5))

                time.sleep(random.uniform(2, 4))
                self.inject_cursor_overlay()
                return True
            except Exception as e:
                print(f"  ⚠️  Next button click failed: {e}")

        print("  ℹ️  No Next button found — likely on the last page")
        return False

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