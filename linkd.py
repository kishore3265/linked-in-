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
            
            # Verify critical cookies
            cookie_names = [c.get('name') for c in cookies]
            critical = ['li_a', 'li_ep_auth_context', 'li_at', 'JSESSIONID']
            present = [c for c in critical if c in cookie_names]
            print(f"📋 Critical cookies present: {len(present)}/{len(critical)}")
            
            return cookies
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return None
    
    def setup_driver(self):
        """Setup undetected Chrome driver - FIXED VERSION"""
        try:
            print("🔄 Initializing Chrome driver...")
            
            # SIMPLIFIED APPROACH - Let undetected_chromedriver handle everything
            # Don't specify version_main - let it auto-detect
            self.driver = uc.Chrome(
                use_subprocess=True,
                headless=False,  # Set to True if you want headless mode
            )
            
            # Wait a bit for driver to fully initialize
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
            # Only run this after a page is loaded
            self.driver.execute_script("""
                // Override navigator properties safely
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add chrome object if it doesn't exist
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
            # First visit Google to establish normal session
            print("📡 Warming up browser...")
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Apply stealth after first page load
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
                    # Prepare cookie dict with required fields only
                    cookie_dict = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.linkedin.com',
                        'path': '/',
                    }
                    
                    # Add secure flag if present (must be boolean)
                    if cookie.get('secure', False):
                        cookie_dict['secure'] = True
                    
                    # Add expiry if present (must be int)
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
        
        # Check if logged in
        is_logged_in = False
        reasons = []
        
        # Method 1: Check URL
        if 'feed' in current_url or '/feed/' in current_url:
            is_logged_in = True
            reasons.append("URL contains 'feed'")
        elif 'sales' in current_url:
            is_logged_in = True
            reasons.append("URL contains 'sales'")
        
        # Method 2: Check for login prompts
        login_indicators = ['sign in', 'join now', 'authwall', 'login', 'password']
        has_login_prompts = any(indicator in page_source for indicator in login_indicators)
        
        # Method 3: Check for profile element
        try:
            profile_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".profile-rail-card, .feed-identity-module, .global-nav__me")
            if profile_elements:
                is_logged_in = True
                reasons.append("Profile element found")
        except:
            pass
        
        print("\n📊 Authentication Results:")
        print(f"  {'✅' if is_logged_in else '❌'} Logged In: {is_logged_in}")
        if reasons:
            print(f"  📌 Evidence: {', '.join(reasons)}")
        print(f"  {'⚠️' if has_login_prompts else '✅'} Login Prompts: {'Found' if has_login_prompts else 'None'}")
        
        # Take screenshot
        screenshot_file = f'linkedin_state_{int(time.time())}.png'
        self.driver.save_screenshot(screenshot_file)
        print(f"📸 Screenshot saved: {screenshot_file}")
        
        if is_logged_in:
            print("\n✅✅✅ SUCCESS: Connected to LinkedIn! ✅✅✅")
        else:
            print("\n❌❌❌ FAILED: Not connected to LinkedIn ❌❌❌")
            if has_login_prompts:
                print("👉 Login page detected - cookies are not working")
        
        return is_logged_in
    
    def try_sales_navigator(self):
        """Attempt to access Sales Navigator"""
        print("\n🚀 Attempting to access Sales Navigator...")
        
        # Try to access Sales Navigator
        self.driver.get("https://www.linkedin.com/sales/home")
        time.sleep(random.uniform(5, 8))
        
        if 'sales' in self.driver.current_url:
            print("✅ Successfully in Sales Navigator!")
            self.driver.save_screenshot('sales_navigator.png')
            print("📸 Screenshot saved as 'sales_navigator.png'")
            return True
        else:
            print(f"❌ Failed to reach Sales Navigator. Current URL: {self.driver.current_url}")
            return False
    
    def run_verification(self):
        """Complete verification workflow"""
        print("\n" + "="*60)
        print("🚀 STARTING LINKEDIN CONNECTION VERIFICATION")
        print("="*60)
        
        # Check if cookies loaded
        if not self.cookies:
            print("❌ No cookies loaded. Exiting.")
            return False
        
        # Step 1: Setup driver
        if not self.setup_driver():
            return False
        
        # Step 2: Inject cookies
        if not self.inject_cookies():
            print("\n❌ Cookie injection failed.")
            try:
                self.driver.quit()
            except:
                pass
            return False
        
        # Step 3: Verify connection
        if self.verify_connection():
            print("\n✅✅✅ COOKIES WORK IN BROWSER! ✅✅✅")
            
            # Ask about Sales Navigator
            response = input("\n🔍 Try accessing Sales Navigator? (y/n): ")
            if response.lower() == 'y':
                self.try_sales_navigator()
            
            print("\n✨ Verification complete! Browser will stay open for inspection.")
            input("Press Enter to close browser...")
        else:
            print("\n❌ Verification failed. Troubleshooting steps:")
            print("   1. Check the screenshot to see what page loaded")
            print("   2. If you see a login page, your cookies have expired")
            print("   3. Export fresh cookies using EditThisCookie extension")
            print("   4. Make sure you're logged into Sales Navigator in your browser")
            
            input("\nPress Enter to close browser...")
        
        # Clean up
        try:
            self.driver.quit()
        except:
            pass
        
        return True

# ==================== QUICK VERIFICATION FUNCTION ====================

def quick_verify_cookies(cookie_file='linkedin_cookies.json'):
    """Quick verification using requests (no browser)"""
    import requests
    
    print("\n🔍 QUICK COOKIE VERIFICATION (Requests)")
    print("="*50)
    
    try:
        # Load cookies
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies_list = json.load(f)
        
        # Convert to dict
        cookies = {c['name']: c['value'] for c in cookies_list if 'name' in c and 'value' in c}
        
        print(f"📦 Loaded {len(cookies)} cookies")
        
        # Test LinkedIn feed
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            'https://www.linkedin.com/feed/',
            cookies=cookies,
            headers=headers,
            allow_redirects=True,
            timeout=10
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📍 Final URL: {response.url}")
        
        if response.status_code == 200 and 'feed' in response.url:
            print("✅✅✅ COOKIES VALID - Connected to LinkedIn! ✅✅✅")
            return True
        elif 'login' in response.url:
            print("❌ Redirected to login - Cookies expired")
            return False
        else:
            print("⚠️ Unexpected response")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     LINKEDIN SALES NAVIGATOR COOKIE VERIFICATION         ║
    ║              (Enhanced Stealth Mode)                     ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    COOKIE_FILE = 'linkedin_cookies.json'
    
    # Step 1: Quick verification with requests
    print("\n📋 Step 1: Quick verification with requests...")
    if quick_verify_cookies(COOKIE_FILE):
        print("\n✅ Quick verification passed! Cookies are valid.")
        print("   Proceeding to browser verification...\n")
        
        # Step 2: Full browser verification
        scraper = SalesNavigatorScraper(COOKIE_FILE)
        scraper.run_verification()
    else:
        print("\n❌ Quick verification failed.")
        print("   Your cookies are expired or invalid.")
        print("\n📌 Next steps:")
        print("   1. Open Chrome and log into LinkedIn Sales Navigator")
        print("   2. Install 'EditThisCookie' extension from Chrome Web Store")
        print("   3. Click the cookie icon and export cookies as JSON")
        print("   4. Save the exported cookies as 'linkedin_cookies.json'")
        print("   5. Run this script again")


        