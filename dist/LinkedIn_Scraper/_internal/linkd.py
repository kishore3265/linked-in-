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
            print(f"Loaded {len(cookies)} cookies from file")
            
            # Verify critical cookies for Sales Navigator
            cookie_names = [c.get('name') for c in cookies]
            
            # Regular LinkedIn cookies
            regular_cookies = ['li_at', 'JSESSIONID', 'li_rm']
            
            # Sales Navigator specific cookies (CRITICAL)
            sales_nav_cookies = ['li_a', 'li_ep_auth_context']
            
            regular_present = [c for c in regular_cookies if c in cookie_names]
            sales_present = [c for c in sales_nav_cookies if c in cookie_names]
            
            print(f" Regular LinkedIn cookies: {len(regular_present)}/{len(regular_cookies)}")
            print(f" Sales Navigator cookies: {len(sales_present)}/{len(sales_nav_cookies)}")
            
            if len(sales_present) < 2:
                print(" WARNING: Missing Sales Navigator enterprise cookies!")
                print("   You need to export cookies AFTER logging into Sales Navigator")
                print("   Not just regular LinkedIn!")
            
            return cookies
        except Exception as e:
            print(f" Error loading cookies: {e}")
            return None
    
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            print(" Initializing Chrome driver...")
            
            self.driver = uc.Chrome(
                use_subprocess=True,
                headless=False,
                version_main=146,
            )
            
            time.sleep(random.uniform(0.5, 1.0))
            self.cursor = WebCursor(self.driver)
            print(" Driver setup complete")
            print("  HumanCursor WebCursor initialized")
            return True
            
        except Exception as e:
            print(f" Driver setup failed: {e}")
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
                time.sleep(random.uniform(0.5, 1.0))
        except Exception as e:
            pass  # Never block on human cursor errors

    def human_scroll(self, direction='down', times=3):
        """Scroll the page naturally like a human reading"""
        try:
            for _ in range(times):
                scroll_px = random.randint(250, 500) * (1 if direction == 'down' else -1)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_px});")
                time.sleep(random.uniform(0.5, 1.0))
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
                    time.sleep(random.uniform(0.5, 1.0))
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
            print(" Stealth scripts applied")
        except Exception as e:
            print(f" Stealth script error: {e}")
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
            print(" Warming up browser...")
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(0.5, 1.0))
            
            self.apply_stealth_after_load()
            
            # Navigate to LinkedIn
            print(" Navigating to LinkedIn...")
            self.driver.get("https://www.linkedin.com")
            time.sleep(random.uniform(0.5, 1.0))
            self.inject_cursor_overlay()
            self.human_idle(2, 4)  # Simulate human landing on page
            
            # Clear existing cookies
            self.driver.delete_all_cookies()
            print(" Cleared existing cookies")
            
            # Add cookies one by one
            success_count = 0
            for cookie in self.cookies:
                try:
                    # Use the original domain from the exported cookie;
                    # fall back to '.linkedin.com' if missing.
                    domain = cookie.get('domain', '.linkedin.com')
                    # Selenium requires the domain to start with a dot for
                    # domain cookies, but some exports already include it.
                    if not domain.startswith('.'):
                        domain = '.' + domain

                    cookie_dict = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': domain,
                        'path': cookie.get('path', '/'),
                    }
                    
                    if cookie.get('secure', False):
                        cookie_dict['secure'] = True

                    if cookie.get('httpOnly', False):
                        cookie_dict['httpOnly'] = True
                    
                    if 'expirationDate' in cookie:
                        try:
                            cookie_dict['expiry'] = int(float(cookie['expirationDate']))
                        except:
                            pass
                    
                    self.driver.add_cookie(cookie_dict)
                    success_count += 1
                    
                except Exception as e:
                    print(f"   Could not add {cookie.get('name')}: {str(e)[:50]}")
                    continue
            
            print(f" Added {success_count} out of {len(self.cookies)} cookies")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(random.uniform(0.5, 1.0))
            self.inject_cursor_overlay()
            
            # Navigate to feed
            print(" Navigating to feed...")
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(random.uniform(0.5, 1.0))
            self.inject_cursor_overlay()
            print("  Simulating human browsing the feed...")
            self.human_idle(3, 5)       # Look around the page
            self.human_scroll('down', random.randint(2, 4))  # Scroll down like reading
            time.sleep(random.uniform(0.5, 1.0))
            self.human_scroll('up', 1)  # Scroll back up slightly
            
            return True
            
        except Exception as e:
            print(f" Cookie injection failed: {e}")
            return False
    
    def verify_connection(self):
        """Verify if cookies successfully authenticated"""
        print("\n" + "="*60)
        print(" VERIFYING LINKEDIN CONNECTION")
        print("="*60)
        
        current_url = self.driver.current_url
        page_title = self.driver.title
        page_source = self.driver.page_source.lower()
        
        print(f" Current URL: {current_url}")
        print(f" Page Title: {page_title}")
        
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
        
        print("\n Authentication Results:")
        print(f"  {'' if is_logged_in else ''} Logged In: {is_logged_in}")
        if reasons:
            print(f"   Evidence: {', '.join(reasons)}")
        
        if is_logged_in:
            print("\n SUCCESS: Connected to LinkedIn! ")
        else:
            print("\n FAILED: Not connected to LinkedIn ")
        
        return is_logged_in
    
    def navigate_to_sales_navigator(self):
        """
        Click the 'Go to Sales Navigator' link that appears directly in the
        left sidebar of the LinkedIn feed page.
        Falls back to direct URL only if the element cannot be found.
        """
        print("\n  Attempting to navigate to Sales Navigator via UI click...")

        sn_link = None

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
                    print(f"   Found Sales Navigator link via: {sel}")
                    break
            except Exception:
                continue

        #  XPath fallback: match by the visible span text 
        if not sn_link:
            try:
                sn_link = self.driver.find_element(
                    By.XPATH,
                    '//span[normalize-space(text())="Go to Sales Navigator"]/ancestor::a'
                )
                print("   Found Sales Navigator link via XPath text match")
            except Exception:
                pass

        #  Click it 
        if sn_link:
            try:
                original_handles = set(self.driver.window_handles)
                self.cursor.click_on(sn_link)
                print("    Clicked 'Go to Sales Navigator' link in left sidebar")

                # The link has target="_blank"  it opens in a NEW TAB.
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
                    print(f"   Switched to new tab: {self.driver.current_url}")
                else:
                    print("    No new tab detected  may have opened in same tab")

                # Wait for Sales Navigator to fully load
                try:
                    WebDriverWait(self.driver, 20).until(
                        lambda d: "sales" in d.current_url
                    )
                    print(f"   Confirmed on Sales Navigator: {self.driver.current_url}")
                except Exception:
                    print(f"    Timed out waiting for sales URL, current: {self.driver.current_url}")

                time.sleep(random.uniform(0.5, 1.0))
                self.inject_cursor_overlay()
                self.human_idle(2, 3)
                return True
            except Exception as e:
                print(f"    click_on failed: {e}")

        #  Fallback: direct URL 
        print("    UI navigation failed  falling back to direct URL")
        self.driver.get("https://www.linkedin.com/sales/home")
        time.sleep(random.uniform(0.5, 1.0))
        self.inject_cursor_overlay()
        self.human_idle(2, 3)
        return False

    def click_lead_filters(self):
        """
        On the Sales Navigator home/search page, click the 'Lead filters' button.
        Real DOM: <a href="/sales/search/people?viewAllFilters=true">Lead filters</a>
        """
        print("\n  Looking for 'Lead filters' button...")

        lead_filter_link = None

        #  CSS selectors from the actual DOM 
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
                    print(f"   Found Lead filters via: {sel}")
                    break
            except Exception:
                continue

        #  XPath fallback: match visible span text 
        if not lead_filter_link:
            try:
                lead_filter_link = self.driver.find_element(
                    By.XPATH,
                    '//span[normalize-space(text())="Lead filters"]/ancestor::a'
                )
                print("   Found Lead filters via XPath text match")
            except Exception:
                pass

        if lead_filter_link:
            try:
                self.cursor.click_on(lead_filter_link)
                print("    Clicked 'Lead filters' button")
                # Wait until the search/people page with filters loads
                WebDriverWait(self.driver, 15).until(
                    lambda d: 'sales/search/people' in d.current_url
                )
                print(f"   Lead filters page loaded: {self.driver.current_url}")
                time.sleep(random.uniform(0.5, 1.0))
                self.inject_cursor_overlay()
                self.human_idle(1, 2)
                return True
            except Exception as e:
                print(f"    Lead filters click failed: {e}")
        else:
            print("    Lead filters button not found on page")

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

        print(f"\n Entering company filter: '{company_name}'...")

        #  Step 1: Wait for the Current company fieldset 
        fieldset_sel = 'fieldset[data-x-search-filter="CURRENT_COMPANY"]'
        try:
            fieldset = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, fieldset_sel))
            )
            print("   Found Current company fieldset")
        except Exception:
            print("    Current company fieldset not found  filters panel may not be open")
            return False

        #  Step 2: Scroll the fieldset into view 
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", fieldset
        )
        time.sleep(random.uniform(0.5, 1.0))

        #  Step 3: Click the Current company toggle button 
        # The button lives just below the "Company" legend inside the fieldset:
        #   <fieldset data-x-search-filter="CURRENT_COMPANY">
        #     <div class="ph4 flex align-items-center relative">
        #       <legend ></legend>
        #       <button aria-expanded="false"
        #               class=" search-filter_focus-target--button ">
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
                    print(f"   Found Company toggle button via: {sel}")
                    break
            except Exception:
                continue

        if toggle_btn is None:
            # XPath fallback  look for the expand/collapse button directly
            try:
                toggle_btn = fieldset.find_element(
                    By.XPATH,
                    './/button[@aria-expanded]'
                )
                print("   Found Company toggle button via XPath")
            except Exception:
                pass

        if toggle_btn:
            # Scroll the button itself into view so cursor coordinates are correct
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", toggle_btn
            )
            time.sleep(random.uniform(0.5, 1.0))

            is_expanded = toggle_btn.get_attribute('aria-expanded')
            print(f"    Company toggle aria-expanded='{is_expanded}'")

            if is_expanded == 'false':
                print("    Clicking Company toggle button to expand the section...")
                # Primary: human cursor click
                clicked = False
                try:
                    self.cursor.click_on(toggle_btn)
                    clicked = True
                except Exception as e:
                    print(f"    cursor.click_on failed ({e})  trying JS click")

                if not clicked:
                    try:
                        self.driver.execute_script("arguments[0].click();", toggle_btn)
                        clicked = True
                        print("   JS click succeeded")
                    except Exception as e2:
                        print(f"    JS click also failed: {e2}")

                # Wait for the section to actually expand (aria-expanded becomes "true")
                try:
                    WebDriverWait(self.driver, 8).until(
                        lambda d: toggle_btn.get_attribute('aria-expanded') == 'true'
                    )
                    print("   Company section expanded")
                except Exception:
                    print("    aria-expanded did not switch to true  continuing anyway")
                time.sleep(random.uniform(0.5, 1.0))
            else:
                print("   Company section already expanded")
        else:
            print("    Company toggle button not found  section may already be expanded")

        #  Step 4: Find the input inside the fieldset 
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
                print(f"   Found company input via: {sel}")
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
                print("   Found company input via XPath")
            except Exception:
                pass

        if not company_input:
            print("    Company filter input not found inside fieldset")
            return False

        #  Step 5: Click the input and type the company name 
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", company_input
        )
        time.sleep(random.uniform(0.5, 1.0))

        try:
            self.cursor.click_on(company_input)
            time.sleep(random.uniform(0.5, 1.0))
        except Exception as e:
            print(f"    Could not click input: {e}")
            return False

        print(f"    Typing '{company_name}'...")
        for char in company_name:
            company_input.send_keys(char)
            time.sleep(random.uniform(0.5, 1.0))

        # Wait for autocomplete dropdown to populate
        time.sleep(random.uniform(0.5, 1.0))

        #  Step 6: Click the first matching suggestion 
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
                    print(f"   Found suggestion via: {sel}")
                    break
            except Exception:
                continue

        if not suggestion:
            try:
                suggestion = self.driver.find_element(
                    By.XPATH,
                    f'//*[@role="option" and contains(., "{company_name.split()[0]}")]'
                )
                print("   Found suggestion via XPath text match")
            except Exception:
                pass

        if suggestion:
            try:
                self.cursor.click_on(suggestion)
                print(f"    Clicked suggestion for '{company_name}'")
            except Exception as e:
                print(f"    Could not click suggestion ({e})  pressing Enter instead")
                company_input.send_keys(Keys.RETURN)
        else:
            print("    No suggestion found  pressing Enter")
            company_input.send_keys(Keys.RETURN)

        # Wait for results to refresh with the company filter applied
        time.sleep(random.uniform(0.5, 1.0))
        self.inject_cursor_overlay()
        self.human_idle(1, 2)
        print(f"   Company filter applied for '{company_name}'")
        return True

    def verify_sales_navigator_access(self):
        """Check if user has Sales Navigator access"""
        print("\n" + "="*60)
        print(" CHECKING SALES NAVIGATOR ACCESS")
        print("="*60)
        
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()
        
        print(f" Current URL: {current_url}")
        
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
            print(" You don't have Sales Navigator access - redirected to upgrade page")
            return False
        
        print("\n Sales Navigator Access Results:")
        print(f"  {'' if has_access else ''} Has Access: {has_access}")
        if reasons:
            print(f"   Evidence: {', '.join(reasons)}")
        
        if has_access:
            print("\n SUCCESS: You have Sales Navigator access! ")
        else:
            print("\n FAILED: Cannot access Sales Navigator ")
            print("\n Possible reasons:")
            print("   1. Your LinkedIn account doesn't have Sales Navigator subscription")
            print("   2. Your cookies are from regular LinkedIn, not Sales Navigator")
            print("   3. You need to log into Sales Navigator manually first")
        
        return has_access
    
    def run_verification(self):
        """Complete verification workflow"""
        print("\n" + "="*60)
        print(" STARTING LINKEDIN VERIFICATION")
        print("="*60)
        
        if not self.cookies:
            print(" No cookies loaded. Exiting.")
            return False
        
        # Step 1: Setup driver
        if not self.setup_driver():
            return False
        
        # Step 2: Inject cookies
        if not self.inject_cookies():
            print("\n Cookie injection failed.")
            self.cleanup()
            return False
        
        # Step 3: Verify regular LinkedIn connection
        if not self.verify_connection():
            print("\n Cannot connect to regular LinkedIn.")
            self.cleanup()
            return False
        
        print("\n Successfully connected to regular LinkedIn!")
        
        # Step 4: Navigate to Sales Navigator by clicking through the UI
        print("\n Navigating to Sales Navigator via UI clicks...")
        self.navigate_to_sales_navigator()
        print("  Simulating human exploring Sales Navigator home...")
        self.human_idle(2, 4)
        self.human_scroll('down', random.randint(1, 3))
        time.sleep(random.uniform(0.5, 1.0))
        has_sales_nav = self.verify_sales_navigator_access()

        # Step 5: Click 'Lead filters' to navigate to the search page
        if has_sales_nav:
            self.click_lead_filters()

        if has_sales_nav:
            #  Wait for user to apply filters manually, then confirm 
            print("\n" + "="*60)
            print("  FILTERS PAGE IS OPEN  apply your filters in the browser now")
            print("="*60)
            print("    Type the company name, set headcount, location, etc.")
            print("    Once the results are showing, come back here.")
            print("    Type  'y'  and press Enter to START scraping.")
            print("    Type anything else to CANCEL.")
            print("="*60)
            try:
                go = input("  Start scrape? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                go = ''

            if go not in ('y', 'yes'):
                print(" Scrape cancelled by user.")
                input("\nPress Enter to close browser...")
                self.cleanup()
                return False

            current_search_url = self.driver.current_url
            print(f" Using live search URL: {current_search_url}")

            # ── Ask for page range ────────────────────────────────────────
            print("\n" + "="*60)
            print("  ENTER PAGE RANGE TO SCRAPE")
            print("="*60)
            print("    Format : start-end   e.g.  1-30   or   21-30   or   5-15")
            print("    Press Enter alone to default to pages 1-30.")
            print("="*60)
            try:
                page_range_input = input("  Page range [1-30]: ").strip()
            except (EOFError, KeyboardInterrupt):
                page_range_input = ''

            start_page           = 1
            max_pages_to_scrape  = 30
            if page_range_input:
                try:
                    parts               = page_range_input.split('-')
                    start_page          = int(parts[0].strip())
                    end_page            = int(parts[1].strip())
                    max_pages_to_scrape = end_page - start_page + 1
                    if start_page < 1 or max_pages_to_scrape < 1:
                        raise ValueError('invalid range')
                    print(f" Scraping pages {start_page} to {end_page} ({max_pages_to_scrape} page(s))...")
                except Exception:
                    print(" Invalid range format  defaulting to pages 1-30.")
                    start_page          = 1
                    max_pages_to_scrape = 30
            else:
                print(" No range given  scraping all pages 1-30...")

            leads = self.scrape_search_results(
                search_url=current_search_url,
                max_pages=max_pages_to_scrape,
                start_page=start_page,
            )

            if leads:
                print(f"\n Scraped {len(leads)} companies total!")
                print(" Files saved: scraped_leads_<timestamp>.json + .csv")
            else:
                self.save_page_html('search_results.html')

            print(f"\n Pages {start_page}-{start_page + max_pages_to_scrape - 1} done  closing Chrome...")
            self.cleanup()
            return True
        else:
            print("\n Sales Navigator access failed.")
            print("\n To fix this:")
            print("   1. Open Chrome manually and go to linkedin.com/sales")
            print("   2. Log in to Sales Navigator")
            print("   3. Use EditThisCookie to export cookies AGAIN")
            print("   4. Save the new cookies to 'linkedin_cookies.json'")
            print("   5. Run this script again")
            self.cleanup()
            return False
    
    def extract_sample_data(self):
        """Extract sample data from Sales Navigator search results"""
        print("\n Extracting sample data from search results...")
        
        try:
            search_url = (
                "https://www.linkedin.com/sales/search/people?query=(recentSearchParam%3A(doLogHistory%3Atrue)%2Cfilters%3AList((type%3ACURRENT_COMPANY%2Cvalues%3AList((id%3Aurn%253Ali%253Aorganization%253A67535055%2Ctext%3AElite%2520EPM%2CselectionType%3AINCLUDED%2Cparent%3A(id%3A0))))))&sessionId=aNsocAN4TE6fWN7%2Bf2bBSg%3D%3D&viewAllFilters=true"
            )
            self.driver.get(search_url)
            time.sleep(random.uniform(0.5, 1.0))
            self.inject_cursor_overlay()
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results__results-container"))
                )
                print(" Search results loaded")
                print("  Simulating human scanning results...")
                self.human_idle(2, 3)
                self.human_hover_elements(".search-results__result-item, .linked-area, .artdeco-entity-lockup")
                self.human_scroll('down', random.randint(3, 5))
                time.sleep(random.uniform(0.5, 1.0))
                self.human_scroll('up', random.randint(1, 2))
                
                # Save full rendered HTML
                self.save_page_html('extract_sample_data.html')

            except:
                print(" Could not find search results")
                
        except Exception as e:
            print(f" Data extraction failed: {e}")
    
    def scrape_search_results(self, search_url, max_pages=1, output_file='scraped_leads.json', start_page=1):
        """
        Navigate to a Sales Navigator search URL, scroll through results,
        scrape all lead data across multiple pages, and save to JSON + CSV.
        A new timestamped file is created every run; data is appended after each page.

        start_page : which Sales Navigator page to begin on (default 1).
                     When > 1 the script injects ?page=N into the URL and
                     navigates directly to that page before scraping.
        """
        import csv
        import re as _re
        from bs4 import BeautifulSoup

        # Generate a unique timestamped filename for this run
        _ts = time.strftime('%Y%m%d_%H%M%S')
        _base = output_file.replace('.json', '')
        output_file = f"{_base}_{_ts}.json"
        csv_file    = output_file.replace('.json', '.csv')

        print(f"\n{'='*60}")
        print(" SCRAPING SALES NAVIGATOR SEARCH RESULTS")
        print(f"{'='*60}")
        print(f"\n  New output files for this run:")
        print(f"    JSON : {output_file}")
        print(f"    CSV  : {csv_file}")
        print(f"{'='*60}")

        # CSV header written once at the start
        _csv_fieldnames = ['company_name', 'company_url', 'industry',
                           'city', 'state', 'country',
                           'employee_count', 'revenue', 'website']
        with open(csv_file, 'w', newline='', encoding='utf-8') as _cf:
            csv.DictWriter(_cf, fieldnames=_csv_fieldnames, extrasaction='ignore').writeheader()

        # Empty JSON list to start
        with open(output_file, 'w', encoding='utf-8') as _jf:
            json.dump([], _jf)

        already_scraped_urls: set = set()
        all_leads = []

        page = 1   # internal loop counter; always counts from 1 regardless of start_page

        # ── Determine the URL to open first ──────────────────────────────────
        # When start_page > 1 we must navigate to the correct page directly,
        # so we always do a driver.get() and never rely on already_on_page.
        if start_page > 1:
            # Build the page-adjusted URL by injecting / replacing ?page=N
            if 'page=' in search_url:
                nav_url = _re.sub(r'page=\d+', f'page={start_page}', search_url)
            elif '?' in search_url:
                nav_url = search_url + f'&page={start_page}'
            else:
                nav_url = search_url + f'?page={start_page}'

            print(f"\n Jumping directly to page {start_page}  navigating to: {nav_url[:120]}...")
            _pre = random.uniform(0.5, 1.0)
            print(f"   Pre-navigation pause {_pre:.1f}s...")
            time.sleep(_pre)
            self.driver.get(nav_url)
            time.sleep(random.uniform(1.0, 1.5))
            self.apply_stealth_after_load()
            _post = random.uniform(0.5, 1.0)
            print(f"   Post-load settle {_post:.1f}s...")
            time.sleep(_post)

        else:
            # Original logic: start from page 1
            already_on_page = (
                'sales/search/people' in self.driver.current_url
                or 'sales/search' in self.driver.current_url
            )

            if already_on_page:
                print(f"\n Already on search page  skipping navigation, scraping from page 1...")
                self.apply_stealth_after_load()
                _pre = random.uniform(0.5, 1.0)
                print(f"   Settling for {_pre:.1f}s before reading results...")
                time.sleep(_pre)
            else:
                _pre = random.uniform(0.5, 1.0)
                print(f"   Pre-navigation pause {_pre:.1f}s...")
                time.sleep(_pre)
                print(f"\n Loading page 1  navigating to search URL...")
                self.driver.get(search_url)
                time.sleep(random.uniform(0.5, 1.0))
                self.apply_stealth_after_load()
                _post = random.uniform(0.5, 1.0)
                print(f"   Post-load settle {_post:.1f}s...")
                time.sleep(_post)

        while page <= max_pages:
            sn_page = start_page + page - 1   # actual Sales Navigator page number
            end_page_num = start_page + max_pages - 1
            print(f"\n Scraping SN page {sn_page}  (step {page}/{max_pages}, range {start_page}-{end_page_num})...")

            # Wait for results panel to be present (lead search OR account/company search)
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         '[data-sn-view-name="module-lead-search-results"],'
                         '[data-sn-view-name="module-account-search-results"],'
                         '.search-results__results-container')
                    )
                )
                print(" Results panel loaded")
            except Exception:
                print("  Results panel not found  page may be empty or blocked")
                break

            # Human-like: look around the page first
            self.human_idle(2, 3)
            time.sleep(random.uniform(0.5, 1.0))

            # Scroll the RIGHT panel to bottom (triggers lazy loading)
            # Returns the scroll panel element so we can reuse it for Next-button search
            print("  Scrolling to bottom of results page...")
            try:
                right_panel = self._scroll_results_panel()
            except Exception as _scroll_err:
                print(f"  Tab crash during initial scroll: {_scroll_err}")
                print("  Attempting page reload and retry...")
                try:
                    self.driver.get(search_url)
                    time.sleep(random.uniform(0.5, 1.0))
                    self.apply_stealth_after_load()
                    right_panel = self._scroll_results_panel()
                except Exception:
                    print("  Recovery failed  stopping scrape.")
                    break

            # Save the fully rendered HTML for this page to the linkedin/ folder
            # Filename uses the real Sales Navigator page number (e.g. search_page_21.html)
            self.save_page_html(f'search_page_{sn_page}.html')

            # Click each company card and extract data from the company profile page
            page_leads, total_on_page = self._click_and_extract_companies(already_scraped_urls)

            # Only stop if the page had NO companies at all.
            # If companies existed but were all already-scraped, keep going to the next page.
            if total_on_page == 0:
                print(f"  No companies found on SN page {sn_page}  stopping.")
                break

            new_count = len(page_leads)
            print(f" SN page {sn_page}: {total_on_page} companies found, {new_count} new leads scraped")
            all_leads.extend(page_leads)

            # Append new leads to files immediately after each page
            if page_leads:
                # JSON: rewrite full list so file is always valid
                with open(output_file, 'w', encoding='utf-8') as _jf:
                    json.dump(all_leads, _jf, indent=2, ensure_ascii=False)
                # CSV: append rows (no header, file already has header)
                with open(csv_file, 'a', newline='', encoding='utf-8') as _cf:
                    _w = csv.DictWriter(_cf, fieldnames=_csv_fieldnames, extrasaction='ignore')
                    _w.writerows(page_leads)
                print(f"  Appended {new_count} leads -> {output_file} ({len(all_leads)} total)")

            # Stop if we've hit the max pages limit
            if page >= max_pages:
                print(f" Reached last page of range (SN page {sn_page} = end of {start_page}-{end_page_num})  done.")
                break

            #  Find Next button 
            # After _click_and_extract_companies navigates away and back, the
            # right panel scroll resets to the top.  Re-scroll it to the bottom
            # so the pagination bar (containing Next) is visible, then click.
            next_selectors = [
                'button[aria-label="Next"]',
                'button.artdeco-pagination_button--next',
                'button.artdeco-pagination_button[aria-label]',
                '[data-test-pagination-page-btn="next"]',
                'button.artdeco-pagination__button--next',
            ]
            print("\n Re-scrolling panel to find Next button...")
            # Re-scroll the right panel to its bottom  the Next button lives there
            try:
                right_panel = self._scroll_results_panel()
            except Exception as _scroll_err:
                print(f"  Tab crash during panel scroll: {_scroll_err}")
                print("  Attempting page reload and retry...")
                try:
                    self.driver.get(search_url)
                    time.sleep(random.uniform(0.5, 1.0))
                    self.apply_stealth_after_load()
                    right_panel = self._scroll_results_panel()
                except Exception:
                    print("  Recovery failed  stopping scrape.")
                    break
            located_next_btn = self._scroll_until_next_visible(next_selectors, scroll_panel=right_panel)

            if located_next_btn is None:
                print(" Next button not found  this is the last page.")
                break

            print(" Next button is visible on page.")
            print(f"\n SN page {sn_page} scraped  ({len(page_leads)} leads, {len(all_leads)} total so far)  advancing to SN page {sn_page + 1}...")

            #  Step 2: Click the already-located Next button 
            wait = random.uniform(0.5, 1.0)
            print(f" Waiting {wait:.1f}s before clicking Next...")
            self.human_idle(1, 2)
            time.sleep(wait)

            # Re-fetch in case React re-rendered after the wait
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
                fresh_btn = located_next_btn  # fallback to the one we scrolled to

            current_url = self.driver.current_url
            click_ok = False
            try:
                self.cursor.click_on(fresh_btn)
                click_ok = True
                print("    Clicked Next page button (human cursor)")
            except Exception as ce:
                print(f"    cursor.click_on failed ({ce})  trying JS click")
                try:
                    self.driver.execute_script("arguments[0].click();", fresh_btn)
                    click_ok = True
                    print("    Clicked Next page button (JS fallback)")
                except Exception as je:
                    print(f"    JS click also failed: {je}")

            if not click_ok:
                print("    All click strategies failed  stopping.")
                break

            # Wait for next page to load
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.current_url != current_url
                )
                print(f"   New page loaded: {self.driver.current_url}")
            except Exception:
                print("    URL unchanged  waiting for results panel to refresh...")
                time.sleep(random.uniform(0.5, 1.0))

            _between = random.uniform(0.5, 1.0)
            print(f"   Between-page pause {_between:.1f}s...")
            time.sleep(_between)
            time.sleep(random.uniform(0.5, 1.0))
            self.inject_cursor_overlay()
            page += 1

        # Final summary
        print(f"\n Total leads scraped: {len(all_leads)}")
        print(f" JSON saved : {output_file}")
        print(f" CSV  saved : {csv_file}")

        return all_leads

    def _scroll_results_panel(self):
        """
        Scroll the RIGHT results panel of Sales Navigator to the bottom so all
        lead cards lazy-load.

        Sales Navigator uses a split-pane layout: the right panel is its own
        scrollable container  it only responds to scroll when the mouse is
        hovering over it.  Strategy:
          1. Find the first visible lead card.
          2. Move the cursor onto it (mouse now hovers over the right panel).
          3. Use JS to walk up the DOM and find the actual scrollable parent.
          4. Repeatedly scrollBy on that element until scrollHeight stops growing.
        """
        print("   Scrolling right results panel to bottom (lazy-load)...")

        # Check if the tab is still alive before doing anything
        try:
            _ = self.driver.current_url
        except Exception:
            print("  Tab appears crashed  attempting to reload search page...")
            try:
                self.driver.refresh()
                time.sleep(random.uniform(0.5, 1.0))
            except Exception:
                print("  Reload failed  cannot scroll panel.")
                return None

        #  Step 1: locate first visible card link (company OR people card) 
        lead_card = None
        for card_sel in [
            'a[data-control-name="view_company_via_result_name"]',      # company/account card
            'a[data-control-name="view_lead_panel_via_search_lead_name"]',  # people/lead card
        ]:
            try:
                lead_card = WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, card_sel))
                )
                print(f"   Scroll anchor found via: {card_sel}")
                break
            except Exception:
                continue

        #  Step 2: move cursor to the right-side panel, vertically centred 
        # Sales Navigator is a split-pane layout: the RIGHT half is the
        # scrollable results panel.  The scroll events only register when the
        # mouse is actually hovering over that right pane.
        # Position: x = far-right third of viewport, y = vertical centre.
        try:
            viewport_w = self.driver.execute_script("return window.innerWidth")
            viewport_h = self.driver.execute_script("return window.innerHeight")
            # Right side: 75-85% of width; vertical centre: 45-55% of height
            target_x = int(viewport_w * random.uniform(0.75, 0.85))
            target_y = int(viewport_h * random.uniform(0.45, 0.55))
            self.cursor.move_to([target_x, target_y])
            print(f"    Cursor positioned at right-panel centre ({target_x}, {target_y})")
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            # Fallback: hover over the first lead card if coordinate move fails
            if lead_card:
                try:
                    self.cursor.move_to(lead_card)
                    time.sleep(random.uniform(0.5, 1.0))
                except Exception:
                    pass

        #  Step 3: find the scrollable parent of the lead card via JS 
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
            print("   Found scrollable right panel via DOM walk")
        else:
            print("    Scrollable panel not found  falling back to window scroll")

        #  Step 4: gradually scroll to the bottom so every card lazy-loads 
        # IMPORTANT: Never jump/teleport  Sales Navigator lazy-loads cards only
        # when the viewport scrolls past them.  A forced scrollTop = scrollHeight
        # skips all intermediate cards and loses data.  Always use scrollBy.
        scroll_attempts = 0
        max_scroll_attempts = 20   # generous  up to ~80 small steps
        stable_count = 0           # consecutive checks where height did NOT grow
        STABLE_THRESHOLD = 3       # declare bottom only after 3 stable checks in a row

        def _is_tab_alive():
            """Return True if the current tab is still responsive."""
            try:
                _ = self.driver.current_url
                return True
            except Exception:
                return False

        def _get_pos():
            """Returns [scrollTop, clientHeight, scrollHeight], or safe defaults on crash."""
            try:
                if scroll_panel:
                    return self.driver.execute_script(
                        "return [arguments[0].scrollTop, "
                        "arguments[0].clientHeight, "
                        "arguments[0].scrollHeight];",
                        scroll_panel
                    )
                return self.driver.execute_script(
                    "return [window.pageYOffset, window.innerHeight, document.body.scrollHeight];"
                )
            except Exception:
                return [0, 0, 0]  # safe fallback on tab crash

        def _scroll_down(px):
            try:
                if scroll_panel:
                    self.driver.execute_script(
                        "arguments[0].scrollBy(0, arguments[1]);", scroll_panel, px
                    )
                else:
                    self.driver.execute_script(f"window.scrollBy(0, {px});")
            except Exception:
                pass  # ignore scroll errors on crashed tab

        def _scroll_top():
            if scroll_panel:
                self.driver.execute_script("arguments[0].scrollTo(0, 0);", scroll_panel)
            else:
                self.driver.execute_script("window.scrollTo(0, 0);")

        def _at_bottom(st, ch, sh, tolerance=60):
            return (st + ch) >= (sh - tolerance)

        st, ch, sh = _get_pos()
        last_height = sh
        print(f"   Start: scrollTop={int(st)}, clientH={int(ch)}, scrollH={int(sh)}")

        while scroll_attempts < max_scroll_attempts:
            # Scroll down by a small human-like chunk
            scroll_px = random.randint(200, 380)
            _scroll_down(scroll_px)
            time.sleep(random.uniform(0.5, 1.0))

            # Occasionally nudge the cursor slightly within the right panel
            # so it keeps receiving scroll events (Sales Navigator requires hover)
            if random.random() < 0.35:
                try:
                    vw = self.driver.execute_script("return window.innerWidth")
                    vh = self.driver.execute_script("return window.innerHeight")
                    nx = int(vw * random.uniform(0.72, 0.88))
                    ny = int(vh * random.uniform(0.40, 0.60))
                    self.cursor.move_to([nx, ny])
                    time.sleep(random.uniform(0.5, 1.0))
                except Exception:
                    pass

            st, ch, sh = _get_pos()
            scroll_attempts += 1

            # If _get_pos returned all zeros the tab has crashed  stop scrolling
            if st == 0 and ch == 0 and sh == 0:
                print("  Tab crash detected during scroll  stopping panel scroll.")
                break

            print(f"   Scroll {scroll_attempts}: scrollTop={int(st)}, clientH={int(ch)}, scrollH={int(sh)}")

            # Check whether new content appeared
            if sh > last_height:
                # New cards lazy-loaded  reset stable counter and keep going
                stable_count = 0
                last_height = sh
                continue

            # Height did not grow this step
            stable_count += 1

            if _at_bottom(st, ch, sh):
                if stable_count >= STABLE_THRESHOLD:
                    # Truly at the bottom and no new content for several steps
                    print(f"   Reached true bottom after {scroll_attempts} scrolls "
                          f"(stable{stable_count}, scrollTop+clientH={int(st+ch)}, scrollH={int(sh)})")
                    break
                else:
                    # At bottom but give lazy-load more time before declaring done
                    print(f"   At bottom edge  waiting for lazy-load (stable{stable_count})...")
                    time.sleep(random.uniform(0.5, 1.0))
            else:
                # Not at bottom yet but height is stable  wait a bit and retry
                if stable_count >= STABLE_THRESHOLD:
                    print(f"   Height stable for {stable_count} steps  extra wait for lazy-load...")
                    time.sleep(random.uniform(0.5, 1.0))
                    _, _, sh_new = _get_pos()
                    if sh_new == last_height:
                        # Still nothing new  keep scrolling normally
                        stable_count = 0

        st2, ch2, sh2 = _get_pos()
        print(f"   Scroll complete  scrollH={int(sh2)}, staying at bottom (scrollTop={int(st2)})")
        return scroll_panel  # caller can reuse the same panel reference

    def _is_element_in_viewport(self, element) -> bool:
        """
        Returns True if the element's bounding rect is fully inside
        the visible browser viewport (no part is clipped off-screen).
        """
        try:
            rect = self.driver.execute_script("""
                var el = arguments[0];
                var r  = el.getBoundingClientRect();
                return {top: r.top, left: r.left, bottom: r.bottom, right: r.right};
            """, element)
            vh = self.driver.execute_script("return window.innerHeight")
            vw = self.driver.execute_script("return window.innerWidth")
            return (
                rect['top']    >= 0 and
                rect['left']   >= 0 and
                rect['bottom'] <= vh and
                rect['right']  <= vw
            )
        except Exception:
            return False

    def _scroll_until_next_visible(self, next_selectors, max_scrolls=25, scroll_panel=None) -> object:
        """
        Scroll the RIGHT PANEL (or window as fallback) until the Next button is
        visible in the viewport.  Returns the element once visible, or None.

        Sales Navigator's Next button lives at the bottom of the right scroll
        panel  always scroll THAT panel, not document.body.
        """
        print("scrolling panel to find Next button...")

        def _scroll_down_px(px):
            if scroll_panel:
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollBy(0, arguments[1]);", scroll_panel, px
                    )
                    return
                except Exception:
                    pass
            self.driver.execute_script(f"window.scrollBy(0, {px});")

        def _scroll_to_bottom():
            if scroll_panel:
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_panel
                    )
                    return
                except Exception:
                    pass
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # First jump straight to the very bottom of the panel
        _scroll_to_bottom()
        time.sleep(random.uniform(0.5, 1.0))

        for attempt in range(1, max_scrolls + 1):
            # Re-fetch on every iteration to avoid stale references
            btn = None
            for sel in next_selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els and els[0].is_enabled():
                        btn = els[0]
                        break
                except Exception:
                    continue

            if btn is None:
                # XPath fallback
                try:
                    btn = self.driver.find_element(
                        By.XPATH,
                        '//button[@aria-label="Next" or '
                        './/span[contains(@class,"artdeco-button__text") and normalize-space(text())="Next"]]'
                    )
                except Exception:
                    pass

            if btn is not None:
                # Scroll the button into view then verify it is on-screen
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", btn
                    )
                    time.sleep(random.uniform(0.5, 1.0))
                except Exception:
                    pass
                if self._is_element_in_viewport(btn):
                    print(f"   Next button visible in viewport after {attempt} scroll(s)")
                    return btn

            # Not visible yet  nudge down a bit and retry
            scroll_px = random.randint(150, 300)
            _scroll_down_px(scroll_px)
            print(f"   Scroll attempt {attempt}/{max_scrolls} (+{scroll_px}px)...")
            time.sleep(random.uniform(0.5, 1.0))

        print(f"    Next button not visible after {max_scrolls} scroll attempts")
        return None

    def _click_and_extract_companies(self, already_scraped_urls: set = None):
        """
        Extract company data in two steps per company:
          1. Parse card HTML (instant, no navigation) for basic fields.
          2. Open the company profile URL in a NEW TAB, extract richer fields
             (revenue, website, industry, location, employee count), then CLOSE
             the tab and switch back -- search results tab is never disturbed.

        Returns (records, total_on_page).
        """
        import re
        from bs4 import BeautifulSoup

        records = []

        # Snapshot the fully rendered page (already scrolled by caller)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        raw_links = soup.find_all(
            'a', attrs={'data-control-name': 'view_company_via_result_name'}
        )

        companies_on_page = []
        for lnk in raw_links:
            name = lnk.get_text(strip=True)
            href = lnk.get('href', '').split('?')[0]
            url  = f"https://www.linkedin.com{href}" if href.startswith('/') else href
            if name and url:
                companies_on_page.append((name, url, lnk))

        total_on_page = len(companies_on_page)
        print(f"   Found {total_on_page} companies on this page -- opening each in new tab...")

        # Remember the search results tab so we can always switch back
        search_tab = self.driver.current_window_handle

        for idx, (name, url, lnk) in enumerate(companies_on_page, 1):
            if already_scraped_urls and url in already_scraped_urls:
                print(f"    [{idx}/{total_on_page}] Skipping (already scraped): {name}")
                continue

            record = {
                'company_name'  : name,
                'company_url'   : url,
                'industry'      : '',
                'city'          : '',
                'state'         : '',
                'country'       : '',
                'employee_count': '',
                'revenue'       : '',
                'website'       : '',
            }

            # ----------------------------------------------------------------
            # Step 1: card-level extraction (instant fallback)
            # ----------------------------------------------------------------
            card = (
                lnk.find_parent(class_=lambda c: c and 'result-lockup' in c)
                or lnk.find_parent(class_=lambda c: c and 'search-results__result-item' in c)
                or lnk.find_parent(class_=lambda c: c and 'artdeco-entity-lockup' in c)
                or lnk.find_parent('li')
            )
            scope = card if card else soup

            # Industry
            for attr in ['data-anonymize', 'data-x-search-filter']:
                ind = scope.find(attrs={attr: 'industry'})
                if ind:
                    record['industry'] = ind.get_text(strip=True)
                    break
            if not record['industry']:
                subtitle = scope.find(class_=lambda c: c and 'subtitle' in c)
                if subtitle:
                    record['industry'] = subtitle.get_text(strip=True)

            # Location
            loc_el = scope.find(attrs={'data-anonymize': 'location'})
            if not loc_el:
                loc_el = scope.find(class_=lambda c: c and 'location' in (c if isinstance(c, str) else ' '.join(c)))
            if loc_el:
                parts = [p.strip() for p in loc_el.get_text(strip=True).split(',')]
                if len(parts) >= 3:
                    record['city']    = parts[0]
                    record['state']   = parts[1]
                    record['country'] = ', '.join(parts[2:])
                elif len(parts) == 2:
                    record['city']    = parts[0]
                    record['country'] = parts[1]
                elif len(parts) == 1:
                    record['country'] = parts[0]

            # Employee count
            emp_lnk = scope.find('a', attrs={'data-anonymize': 'company-size'})
            if emp_lnk:
                span = emp_lnk.find(class_=lambda c: c and 'link-text' in c)
                if span:
                    m = re.search(r'([\d,]+)', span.get_text(strip=True))
                    if m:
                        record['employee_count'] = int(m.group(1).replace(',', ''))
                if not record['employee_count']:
                    aria = emp_lnk.get('aria-label', '')
                    m = re.search(r'([\d,]+)', aria)
                    if m:
                        record['employee_count'] = int(m.group(1).replace(',', ''))
            if not record['employee_count']:
                card_text = scope.get_text(' ', strip=True)
                for pattern in [
                    r'View\s+all\s+([\d,]+)\s+employees?',
                    r'([\d,]+)\s+employees?\s+on\s+LinkedIn',
                    r'([\d,]+)\s+employees?',
                ]:
                    m = re.search(pattern, card_text, re.I)
                    if m:
                        record['employee_count'] = int(m.group(1).replace(',', ''))
                        break

            # Revenue (from card)
            rev_el = scope.find(attrs={'data-anonymize': 'revenue'})
            if rev_el:
                record['revenue'] = rev_el.get_text(strip=True)

            # Website (from card)
            web_lnk = scope.find('a', attrs={'data-control-name': 'visit_company_website'})
            if web_lnk:
                record['website'] = web_lnk.get('href', '')

            # ----------------------------------------------------------------
            # Step 2: open company profile in a NEW TAB, extract richer data,
            # close the tab, switch back to search results -- tab never navigates
            # ----------------------------------------------------------------
            try:
                # Open new tab and navigate to company profile
                self.driver.execute_script("window.open(arguments[0], '_blank');", url)
                time.sleep(random.uniform(0.5, 1.0))

                # Switch to the newly opened tab
                all_tabs = self.driver.window_handles
                new_tab = [t for t in all_tabs if t != search_tab][-1]
                self.driver.switch_to.window(new_tab)

                # Wait for the page to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except Exception:
                    pass
                time.sleep(random.uniform(0.5, 1.0))

                # Parse the company profile page
                psoup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # Revenue
                if not record['revenue']:
                    rev_p = psoup.find(attrs={'data-anonymize': 'revenue'})
                    if rev_p:
                        record['revenue'] = rev_p.get_text(strip=True)
                if not record['revenue']:
                    page_text = psoup.get_text(' ', strip=True)
                    m = re.search(
                        r'Revenue[:\s]+([\$\d,\.]+\s*(?:billion|million|[BMK])?)',
                        page_text, re.I
                    )
                    if m:
                        record['revenue'] = m.group(1).strip()

                # Website
                if not record['website']:
                    web_p = psoup.find('a', attrs={'data-control-name': 'visit_company_website'})
                    if web_p:
                        record['website'] = web_p.get('href', '')
                if not record['website']:
                    for a in psoup.find_all('a', href=True):
                        h = a['href']
                        if h.startswith('http') and 'linkedin.com' not in h:
                            record['website'] = h
                            break

                # Employee count
                if not record['employee_count']:
                    emp_p = psoup.find('a', attrs={'data-anonymize': 'company-size'})
                    if emp_p:
                        aria = emp_p.get('aria-label', '')
                        m = re.search(r'([\d,]+)', aria)
                        if m:
                            record['employee_count'] = int(m.group(1).replace(',', ''))
                if not record['employee_count']:
                    page_text = psoup.get_text(' ', strip=True)
                    for pattern in [
                        r'View\s+all\s+([\d,]+)\s+employees?',
                        r'([\d,]+)\s+employees?\s+on\s+LinkedIn',
                        r'([\d,]+)\s+employees?',
                    ]:
                        m = re.search(pattern, page_text, re.I)
                        if m:
                            record['employee_count'] = int(m.group(1).replace(',', ''))
                            break

                # Industry
                if not record['industry']:
                    ind_p = psoup.find(attrs={'data-anonymize': 'industry'})
                    if ind_p:
                        record['industry'] = ind_p.get_text(strip=True)

                # Location
                if not record['city'] and not record['country']:
                    loc_p = psoup.find(attrs={'data-anonymize': 'location'})
                    if loc_p:
                        parts = [p.strip() for p in loc_p.get_text(strip=True).split(',')]
                        if len(parts) >= 3:
                            record['city']    = parts[0]
                            record['state']   = parts[1]
                            record['country'] = ', '.join(parts[2:])
                        elif len(parts) == 2:
                            record['city']    = parts[0]
                            record['country'] = parts[1]
                        elif len(parts) == 1:
                            record['country'] = parts[0]

            except Exception as tab_err:
                print(f"   [{idx}/{total_on_page}] Tab error for {name}: {tab_err}")
            finally:
                # Always close the new tab and switch back to search results
                try:
                    if self.driver.current_window_handle != search_tab:
                        self.driver.close()
                except Exception:
                    pass
                try:
                    self.driver.switch_to.window(search_tab)
                except Exception:
                    pass

            print(f"   [{idx}/{total_on_page}] {record['company_name']} | "
                  f"{record['employee_count']} emp | "
                  f"{record['city']}, {record['state']}, {record['country']} | "
                  f"rev: {record['revenue']} | site: {record['website']}")

            records.append(record)

        return records, total_on_page

    def run_continuation(self, continuation_url: str, max_pages: int = 5):
        """
        Resume scraping from a specific page URL (e.g. page 6 of a search).
        Opens Chrome fresh, injects cookies, navigates directly to
        continuation_url, scrapes max_pages pages, then closes Chrome.
        """
        print("\n" + "="*60)
        print(" CONTINUATION SCRAPE SESSION (pages 6-10)")
        print("="*60)
        print(f"  Start URL    : {continuation_url}")
        print(f"  Pages to scrape : {max_pages}")
        print("="*60)

        if not self.cookies:
            print(" No cookies loaded. Exiting.")
            return False

        # Step 1: Setup driver
        if not self.setup_driver():
            return False

        # Step 2: Inject cookies (warms up browser  Google  LinkedIn feed)
        if not self.inject_cookies():
            print("\n Cookie injection failed.")
            self.cleanup()
            return False

        # Step 3: Verify regular LinkedIn connection
        if not self.verify_connection():
            print("\n Cannot connect to LinkedIn.")
            self.cleanup()
            return False

        # Step 4: Navigate directly to continuation_url (e.g. page 6)
        print(f"\n Navigating directly to continuation URL...")
        self.driver.get(continuation_url)
        time.sleep(random.uniform(1.5, 2.5))
        self.apply_stealth_after_load()  # already calls inject_cursor_overlay internally
        self.human_idle(2, 3)

        # Step 5: Scrape max_pages pages starting from this URL
        leads = self.scrape_search_results(
            search_url=continuation_url,
            max_pages=max_pages
        )

        if leads:
            print(f"\n Continuation session scraped {len(leads)} companies!")
        else:
            self.save_page_html('continuation_results.html')

        print("\n Closing Chrome (continuation session complete)...")
        self.cleanup()
        return True

    def cleanup(self):
        """Clean up resources"""
        try:
            self.driver.quit()
        except:
            pass

    def save_page_html(self, filename=None):
        """Save the fully rendered DOM (like DevTools Elements panel) to a file inside the linkedin/ folder"""
        try:
            # Always save inside the 'linkedin' folder
            html_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin')
            os.makedirs(html_dir, exist_ok=True)

            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f'page_source_{timestamp}.html'

            # Strip any directory part the caller may have included
            filename = os.path.join(html_dir, os.path.basename(filename))

            # Get the live rendered DOM (post-JS, same as Elements panel in DevTools)
            rendered_html = self.driver.execute_script(
                "return document.documentElement.outerHTML;"
            )

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(rendered_html)

            print(f" Full page HTML saved to '{filename}' ({len(rendered_html):,} characters)")
            return filename
        except Exception as e:
            print(f" Failed to save HTML: {e}")
            return None

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print("""
         LINKEDIN SALES NAVIGATOR ACCESS VERIFIER             
    """)
    
    COOKIE_FILE = 'linkedin_cookies.json'
    
    # Check if cookie file exists
    if not os.path.exists(COOKIE_FILE):
        print(f" Cookie file '{COOKIE_FILE}' not found!")
        print("\n First time setup:")
        print("   1. Open Chrome and go to https://www.linkedin.com/sales")
        print("   2. Log into your Sales Navigator account")
        print("   3. Install 'EditThisCookie' from Chrome Web Store")
        print("   4. Click the cookie icon and export cookies as JSON")
        print("   5. Save as 'linkedin_cookies.json' in this folder")
        print("   6. Run this script again")
        exit()
    
    # ----------------------------------------------------------------
    # Single session: open browser ONCE, scrape all 30 pages
    # (25 results/page = ~750 leads), then close Chrome.
    # HTML for each page is saved to the linkedin/ folder.
    # ----------------------------------------------------------------
    print(" Starting single-session scrape: 30 pages x 25 results = ~750 leads")
    print(" Browser will stay open until ALL 30 pages are done.")
    print("="*60)

    scraper = SalesNavigatorScraper(COOKIE_FILE)
    scraper.run_verification()

    print("\n" + "="*60)
    print(" All 30 pages complete  Chrome closed.")
    print(" HTML snapshots saved in the linkedin/ folder.")
    print("="*60)