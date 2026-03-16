import undetected_chromedriver as uc
import json
import time
import random
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By

class SalesNavigatorScraper:
    def __init__(self, cookie_file='linkedin_cookies.json'):
        """Initialize with your cookies"""
        self.cookie_file = cookie_file
        self.driver = None
        self.cookies = self.load_cookies()
        
    def load_cookies(self):
        """Load cookies from linkedin_cookies.json"""
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            print(f"✅ Loaded {len(cookies)} cookies from file")
            
            # Verify critical cookies are present
            critical_cookies = ['li_a', 'li_ep_auth_context', 'JSESSIONID', 'li_at']
            cookie_names = [c.get('name') for c in cookies]
            
            missing = [c for c in critical_cookies if c not in cookie_names]
            if missing:
                print(f"⚠️ Warning: Missing critical cookies: {missing}")
            else:
                print("✅ All critical cookies present!")
                
            return cookies
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return None
    
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        try:
            self.driver = uc.Chrome()
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Driver setup complete")
            return True
        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            return False
    
    def inject_cookies(self):
        """Inject cookies into browser"""
        try:
            # First navigate to LinkedIn domain
            self.driver.get("https://www.linkedin.com")
            time.sleep(random.uniform(3, 5))
            
            # Add each cookie
            success_count = 0
            for cookie in self.cookies:
                try:
                    # Prepare cookie dict with required fields
                    cookie_dict = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.linkedin.com',
                        'path': cookie.get('path', '/'),
                    }
                    
                    # Add optional fields if present
                    if 'secure' in cookie:
                        cookie_dict['secure'] = cookie['secure']
                    if 'httpOnly' in cookie:
                        cookie_dict['httpOnly'] = cookie['httpOnly']
                    if 'expiry' in cookie or 'expirationDate' in cookie:
                        expiry = cookie.get('expiry') or cookie.get('expirationDate')
                        if expiry:
                            cookie_dict['expiry'] = int(expiry)
                    
                    self.driver.add_cookie(cookie_dict)
                    success_count += 1
                except Exception as e:
                    print(f"  ↳ Could not add cookie {cookie.get('name')}: {str(e)[:50]}")
            
            print(f"✅ Added {success_count} out of {len(self.cookies)} cookies")
            
            # Navigate to feed to apply cookies and confirm login
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(random.uniform(4, 7))
            
            return True
        except Exception as e:
            print(f"❌ Cookie injection failed: {e}")
            return False
    
    def verify_connection(self):
        """Verify if cookies successfully authenticated"""
        print("\n" + "="*60)
        print("🔍 VERIFYING LINKEDIN CONNECTION")
        print("="*60)
        
        # Check current URL after cookie injection
        current_url = self.driver.current_url
        page_title = self.driver.title
        
        print(f"📍 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        
        # Check for authentication indicators
        auth_indicators = {
            'feed': 'feed' in current_url or '/feed/' in current_url,
            'sales': 'sales' in current_url,
            'logged_in': any(indicator in page_title.lower() for indicator in ['linkedin', 'home', 'feed']),
            'no_login': 'login' not in current_url and 'authwall' not in current_url
        }
        
        # Check for specific cookie verification
        print("\n📊 Authentication Check:")
        for key, value in auth_indicators.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # Overall verdict
        if auth_indicators['feed'] or auth_indicators['sales']:
            print("\n✅✅✅ SUCCESS: You are connected to LinkedIn! ✅✅✅")
            return True
        elif auth_indicators['logged_in'] and auth_indicators['no_login']:
            print("\n✅✅✅ SUCCESS: Authenticated on LinkedIn (on home page)! ✅✅✅")
            return True
        elif 'checkpoint' in current_url:
            print("\n⚠️ Security checkpoint detected - manual verification may be needed")
            return False
        else:
            print("\n❌❌❌ FAILED: Not connected to LinkedIn ❌❌❌")
            return False
    
    def navigate_to_sales_navigator(self, search_url=None):
        """Navigate to Sales Navigator"""
        if not search_url:
            # Default to Sales Navigator home
            search_url = "https://www.linkedin.com/sales/home"
        
        print(f"\n🚀 Navigating to: {search_url}")
        self.driver.get(search_url)
        time.sleep(random.uniform(5, 8))
        
        # Verify we're in Sales Navigator
        current_url = self.driver.current_url
        if 'sales' in current_url:
            print(f"✅ Successfully in Sales Navigator: {current_url}")
            
            # Take screenshot for verification
            self.driver.save_screenshot('sales_nav_verification.png')
            print("📸 Screenshot saved as 'sales_nav_verification.png'")
            
            return True
        else:
            print(f"❌ Failed to reach Sales Navigator. Current URL: {current_url}")
            return False
    
    def extract_basic_info(self):
        """Extract basic profile/connection info"""
        print("\n📊 Extracting Basic Information...")
        
        info = {}
        
        # Try to get user info from page
        try:
            # Look for profile menu
            profile_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".profile-rail-card__actor-link, .nav-item__profile-member-photo, .profile-icon"
            )
            if profile_elements:
                info['profile_found'] = True
                print("✅ Profile element found")
            else:
                info['profile_found'] = False
        except:
            info['profile_found'] = False
        
        # Get page source for additional verification
        page_source = self.driver.page_source
        
        # Check for logged-in indicators in HTML
        info['has_session'] = 'JSESSIONID' in page_source or 'csrf' in page_source.lower()
        
        return info
    
    def run_verification(self):
        """Complete verification workflow"""
        print("\n" + "="*60)
        print("🚀 STARTING LINKEDIN CONNECTION VERIFICATION")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Step 1: Setup driver
        if not self.setup_driver():
            return False
        
        # Step 2: Inject cookies
        if not self.inject_cookies():
            self.driver.quit()
            return False
        
        # Step 3: Verify connection
        if self.verify_connection():
            print("\n✅ COOKIES ARE WORKING! You can now:")
            print("   • Navigate to Sales Navigator")
            print("   • Scrape search results")
            print("   • Extract profile data")
            
            # Optional: Try Sales Navigator
            response = input("\nTry navigating to Sales Navigator? (y/n): ")
            if response.lower() == 'y':
                search_url = input("Enter Sales Navigator search URL (or press Enter for home): ")
                if search_url.strip():
                    self.navigate_to_sales_navigator(search_url)
                else:
                    self.navigate_to_sales_navigator()
            
            # Extract basic info
            self.extract_basic_info()
            
            print("\n✅ Verification complete. Browser will stay open for you to inspect.")
            input("Press Enter to close browser...")
        else:
            print("\n❌ Cookie verification failed. Common issues:")
            print("   • Cookies may be expired (refresh them)")
            print("   • Missing critical cookies (li_a, li_ep_auth_context)")
            print("   • Browser fingerprint detected")
        
        try:
            self.driver.quit()
        except Exception:
            pass
        return True

# ==================== SIMPLE VERIFICATION FUNCTION ====================

def quick_verify_cookies(cookie_file='linkedin_cookies.json'):
    """Quick verification using requests (no browser)"""
    import requests
    
    print("\n🔍 QUICK COOKIE VERIFICATION (Requests)")
    print("="*50)
    
    # Load cookies from linkedin_cookies.json
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookies_list = json.load(f)
    
    # Convert to dict
    cookies = {c['name']: c['value'] for c in cookies_list if 'name' in c and 'value' in c}
    
    print(f"📦 Loaded {len(cookies)} cookies")
    
    # Test LinkedIn feed
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(
            'https://www.linkedin.com/feed/',
            cookies=cookies,
            headers=headers,
            allow_redirects=True
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
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Option 1: Quick verification with requests
    print("\n📋 Running quick verification...")
    if quick_verify_cookies('linkedin_cookies.json'):
        print("\n✅ Quick verification passed! Cookies are valid.")
        print("   You can now proceed with browser-based scraping.")
    else:
        print("\n❌ Quick verification failed.")
        print("   Your cookies may be expired. Please export fresh cookies.")
        proceed = input("\nStill try browser verification? (y/n): ")
        if proceed.lower() != 'y':
            exit()
    
    # Option 2: Full browser verification
    print("\n📋 Running full browser verification...")
    scraper = SalesNavigatorScraper('linkedin_cookies.json')
    scraper.run_verification()