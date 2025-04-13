from config.settings import (
    GMAIL_FILE,
    USED_GMAIL_FILE,
    ACCOUNTS_FILE,
    FIVE_SIM_API_KEY,
    FIVE_SIM_COUNTRY,
    FIVE_SIM_OPERATOR,
    PROXY_TYPE,
    PROXY_HOST,
    PROXY_PORT,
    PROXY_USER,
    PROXY_PASS,
    PROXY_ROTATE_URL,
    WAIT_TIME_AFTER_REGISTRATION
)
from services.sms_handler import get_phone_number_and_sms
from services.proxy_manager import rotate_ip
from services.reddit_signup import RedditSignup
from services.gmail_handler import get_verification_code
from services.activity_warmup import warmup_reddit_activity
from utils.helpers import load_unused_gmail_accounts, mark_gmail_as_used, save_account_data
from utils.logger import log
from services.emulator import LDPlayerManager

from appium import webdriver
import time
import random
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def init_driver(port=5555):
    """Initialize Appium driver with W3C-compatible capabilities"""
    desired_caps = {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "emulator-5554",
        "appium:noReset": True,
        "appium:ignoreHiddenApiPolicyError": True,
        "appium:disableSuppressAccessibilityService": True,
        "appium:unicodeKeyboard": True,
        "appium:resetKeyboard": True
    }

    try:
        log(f"[INIT] Starting Appium session on port {port}...")
        driver = webdriver.Remote("http://127.0.0.1:4723", desired_caps)
        driver.implicitly_wait(10)
        log("[SUCCESS] Driver initialized")
        return driver
    except Exception as e:
        log(f"[DRIVER ERROR] Initialization failed: {str(e)}")
        raise RuntimeError(f"Appium session creation failed: {str(e)}")
    
def create_account(driver, email, password, recovery_email):
    """Complete Reddit registration flow with enhanced error handling"""
    log(f"[START] Creating account: {email}")
    signup = RedditSignup(driver)

    try:
        # Phase 1: App launch and email registration
        if not signup.launch_reddit_app():
            raise RuntimeError("Failed to launch Reddit app")

        # Wait for the login screen to appear
        login_button = wait_for_element(driver, (By.ID, "com.reddit.frontpage:id/login_button"))
        if not login_button:
            raise RuntimeError("Login button not found")
        login_button.click()

        if not signup._click_continue_with_email():
            raise RuntimeError("Failed to click 'Continue with email'")

        if not signup.enter_email_credentials(email, password):
            raise RuntimeError("Email credential entry failed")

        if not signup.submit_login():
            raise RuntimeError("Login submission failed")

        # Phase 2: Username generation
        username = signup.handle_username_screen()
        if not username:
            raise RuntimeError("Username generation failed")
        log(f"[STATUS] Generated username: {username}")

        # Phase 3: Onboarding
        if not signup.complete_onboarding():
            log("[WARNING] Onboarding skipped or incomplete")

        # Phase 4: Email verification
        if "@gmail" in email.lower():
            verification_code = get_verification_code(email, password)
            if verification_code:
                if not signup.enter_verification_code(verification_code):
                    raise RuntimeError("Verification code entry failed")
                log("[SUCCESS] Email verified")
            else:
                log("[WARNING] Failed to get verification code")
                return False

        return True

    except Exception as e:
        log(f"[ACCOUNT ERROR] {email}: {type(e).__name__}: {str(e)}")
        if driver:
            try:
                driver.save_screenshot(f"error_{email.replace('@', '_')}.png")
            except:
                log("[WARNING] Failed to save screenshot")
        return False

def wait_for_element(driver, locator, timeout=30):
    """Wait for an element to be present on the screen."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator)
    )

def main():
    try:
        # Initialize emulator
        emulator = LDPlayerManager()
        log("[INIT] Starting emulator...")
        
        if not emulator.start_emulator():
            log("[FATAL] Emulator failed to start")
            return 1
            
        log("[STATUS] Waiting for emulator to fully boot...")
        time.sleep(45)  # Extended wait for Android system
        
        if not emulator.adb_connect():
            log("[FATAL] Failed to establish ADB connection")
            return 1
            
        if not emulator.is_emulator_online():
            log("[FATAL] Emulator not responding")
            return 1
            
        log("[SUCCESS] Emulator ready")

        if not emulator.adb_connect():
            log("[ERROR] Failed to connect ADB. Continuing without ADB.")
        else:
            log("[SUCCESS] ADB connected successfully")

        # Get user input
        try:
            count = min(10, max(1, int(input("Enter number of accounts to create (1-10): "))))
            warmup_minutes = max(1, int(input("Enter warm-up time in minutes per account: ")))
        except ValueError:
            log("[ERROR] Invalid input. Using default values (1 account, 2 minutes)")
            count = 1
            warmup_minutes = 2

        log(f"[CONFIG] Creating {count} accounts with {warmup_minutes} min warmup each")

        # Load accounts
        accounts = load_unused_gmail_accounts(GMAIL_FILE, USED_GMAIL_FILE)
        if not accounts:
            log("[FATAL] No available accounts in gmail_accounts.csv")
            return 1

        created = 0
        for idx, (email, password, recovery) in enumerate(accounts[:count], 1):
            driver = None
            try:
                log(f"\n[PROGRESS] Account {idx}/{count}: {email}")
                
                # Initialize driver
                driver = init_driver(emulator.adb_port)
                time.sleep(5)  # Short pause after driver init

                # Prepare Reddit app
                if not emulator.prepare_reddit(driver):
                    log("[ERROR] Failed to prepare Reddit app - retrying...")
                    time.sleep(10)
                    if not emulator.prepare_reddit(driver):
                        raise RuntimeError("Reddit preparation failed after retry")

                # Create account
                if create_account(driver, email, password, recovery):
                    # Post-registration actions
                    log(f"[STATUS] Warming up account for {warmup_minutes} minutes...")
                    warmup_reddit_activity(driver, warmup_minutes)
                    
                    save_account_data(email, password, recovery, ACCOUNTS_FILE)
                    mark_gmail_as_used(email, USED_GMAIL_FILE)
                    created += 1
                    log(f"[SUCCESS] Created {created}/{count} accounts")

            except Exception as e:
                log(f"[PROCESS ERROR] {email}: {type(e).__name__}: {str(e)}")
            finally:
                # Cleanup
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                
                # Rotate proxy if needed
                if idx < count and PROXY_ROTATE_URL:
                    rotate_ip(PROXY_ROTATE_URL)
                
                # Random delay between accounts
                delay = random.uniform(10, 30)
                log(f"[STATUS] Waiting {delay:.1f} seconds before next account...")
                time.sleep(delay)

        log(f"\n[COMPLETED] Successfully created {created} of {count} accounts")
        return 0 if created == count else 1

    except KeyboardInterrupt:
        log("\n[STOPPED] Process interrupted by user")
        return 1
    except Exception as e:
        log(f"\n[FATAL ERROR] {type(e).__name__}: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())