import undetected_chromedriver as uc
import json
import time
import random
import os
import tempfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SalesNavigatorScraper:
    def __init__(self, cookie_file='linkedin_cookies.json'):
        self.cookie_file = cookie_file
        self.driver = None
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
            print("✅ Driver setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
            
            # Navigate to feed
            print("🔄 Navigating to feed...")
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(random.uniform(5, 8))
            
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
        has_sales_nav = self.verify_sales_navigator_access()
        
        if has_sales_nav:
            print("\n✅✅✅ FULL SUCCESS! You can now scrape Sales Navigator! ✅✅✅")
            
            # Optional: Extract some data
            response = input("\n🔍 Try extracting sample data? (y/n): ")
            if response.lower() == 'y':
                self.extract_sample_data()
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
        """Extract sample data from Sales Navigator"""
        print("\n📊 Extracting sample data...")
        
        try:
            # Navigate to search (you can modify this URL)
            search_url = "https://www.linkedin.com/sales/search/people"
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results__results-container"))
                )
                print("✅ Search results loaded")
                
                # Take screenshot of results
                self.driver.save_screenshot('sales_navigator_results.png')
                print("📸 Results screenshot saved")
                
            except:
                print("⚠️ Could not find search results")
                
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.driver.quit()
        except:
            pass

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