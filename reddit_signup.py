from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
import time
import random

def wait_for_element(driver, locator, timeout=30):
    """Wait for an element to be present on the screen."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator)
    )

class RedditSignup:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    def launch_reddit_app(self):
        """Handles the initial app launch and sign up process"""
        try:
            log("[STEP] Launching Reddit app")
            time.sleep(10)  # Extended wait for app to load

            # Try to find and click the sign up button with multiple strategies
            if not self._click_sign_up_button():
                log("[WARNING] Falling back to direct email flow")
                self._go_directly_to_email_flow()

            return True
            
        except Exception as e:
            log(f"[ERROR] App launch failed: {str(e)}")
            return False

    def _click_sign_up_button(self):
        """Attempts to click the sign up button with multiple fallbacks"""
        try:
            # Все возможные локаторы для кнопки "Sign up"
            sign_up_locators = [
                (AppiumBy.ID, "login_signup_button"),
                (AppiumBy.XPATH, '//android.widget.TextView[@resource-id="login_signup_button"]'),
                (AppiumBy.XPATH, '//android.widget.TextView[@text="Sign up"]'),
                (AppiumBy.ACCESSIBILITY_ID, "Sign up"),
                (AppiumBy.XPATH, '//*[contains(@text, "Sign up")]')
            ]

            for locator in sign_up_locators:
                try:
                    sign_up_btn = self.wait.until(
                        EC.presence_of_element_located(locator)
                    )
                    if sign_up_btn.is_enabled() and sign_up_btn.is_displayed():
                        sign_up_btn.click()
                        log(f"[UI] Clicked 'Sign up' button using {locator}")
                        return True
                    else:
                        log(f"[DEBUG] Button found but not clickable: {locator}")
                except Exception as e:
                    log(f"[DEBUG] Failed to find or click 'Sign up' button with {locator}: {str(e)}")
                    continue

            # Последний вариант - нажатие по координатам
            log("[WARNING] Falling back to coordinate-based tap")
            window_size = self.driver.get_window_size()
            x = int((696 + 839) / 2)  # Средняя координата X из bounds
            y = int((1808 + 1865) / 2)  # Средняя координата Y из bounds
            self.driver.tap([(x, y)], 100)
            log("[UI] Performed coordinate-based tap for 'Sign up'")
            return True

        except Exception as e:
            log(f"[ERROR] Failed to click 'Sign up' button: {str(e)}")
            return False

    def _go_directly_to_email_flow(self):
        """Alternative flow when sign up button isn't found"""
        try:
            log("[STEP] Attempting direct email flow")
            
            # Click "Continue with email"
            self._click_continue_with_email()
            
            # Handle account selection if it appears
            self._handle_account_selection()
            
            return True
        except Exception as e:
            log(f"[ERROR] Direct email flow failed: {str(e)}")
            return False

    def _click_continue_with_email(self):
        """Clicks the 'Continue with email' button"""
        try:
            locators = [
                (AppiumBy.ACCESSIBILITY_ID, "Continue with email"),
                (AppiumBy.ID, "continue_with_email"),
                (AppiumBy.XPATH, '//android.widget.Button[@content-desc="Continue with email"]'),
                (AppiumBy.XPATH, '//android.widget.Button[contains(@resource-id, "continue_with_email")]')
            ]

            for locator in locators:
                try:
                    button = wait_for_element(self.driver, locator)
                    if button.is_enabled() and button.is_displayed():
                        button.click()
                        log(f"[UI] Clicked 'Continue with email' button using {locator}")
                        return True
                    else:
                        log(f"[DEBUG] Button found but not clickable: {locator}")
                except Exception as e:
                    log(f"[DEBUG] Failed to find or click 'Continue with email' button with {locator}: {str(e)}")
                    continue

            # Последний вариант - нажатие по координатам
            log("[WARNING] Falling back to coordinate-based tap")
            x = int((48 + 1032) / 2)  # Средняя координата X из bounds
            y = int((927 + 1083) / 2)  # Средняя координата Y из bounds
            self.driver.tap([(x, y)], 100)
            log("[UI] Performed coordinate-based tap for 'Continue with email'")
            return True

        except Exception as e:
            log(f"[ERROR] Failed to click 'Continue with email': {str(e)}")
            raise

    def _handle_account_selection(self):
        """Handles account selection screen if it appears"""
        try:
            # Wait for account selection screen
            account_picker = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, "com.reddit.frontpage:id/account_picker_accounts")
                )
            )
            log("[UI] Account selection screen detected")
            
            # Click "Add account" (second ViewGroup)
            add_account = self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.view.ViewGroup[2]'))
            )
            add_account.click()
            log("[UI] Clicked 'Add account'")
            
        except Exception as e:
            log(f"[DEBUG] Account selection not detected: {str(e)}")

    def enter_email_credentials(self, email, password):
        """Handles email entry screen"""
        try:
            log("[STEP] Entering email credentials")
            
            # Find email field with multiple strategies
            email_field = None
            email_locators = [
                (AppiumBy.XPATH, '//android.widget.EditText[@text="Email"]'),
                (AppiumBy.XPATH, '//android.widget.EditText[contains(@hint, "Email")]'),
                (AppiumBy.CLASS_NAME, "android.widget.EditText"),
                (AppiumBy.ID, "com.reddit.frontpage:id/email")
            ]
            
            for locator in email_locators:
                try:
                    email_field = self.wait.until(
                        EC.presence_of_element_located(locator))
                    break
                except:
                    continue
            
            if not email_field:
                # Last resort - get first EditText
                all_edit = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                if all_edit:
                    email_field = all_edit[0]
                else:
                    raise Exception("Email field not found")

            email_field.clear()
            email_field.send_keys(email)
            log(f"[UI] Entered email: {email}")

            # Uncheck promotional emails if exists
            try:
                checkbox = self.driver.find_element(AppiumBy.CLASS_NAME, "android.widget.CheckBox")
                if checkbox.is_selected():
                    checkbox.click()
                    log("[UI] Unchecked promotional emails")
            except:
                log("[DEBUG] Promotional checkbox not found")

            # Click continue button
            continue_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')))
            continue_btn.click()
            log("[UI] Clicked continue button")
            
            return True
            
        except Exception as e:
            log(f"[ERROR] Email entry failed: {str(e)}")
            return False

    # [Rest of your existing methods...]
    def enter_verification_code(self, code: str):
        """Enters verification code"""
        try:
            code_field = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.CLASS_NAME, "android.widget.EditText"))
            )
            code_field.send_keys(code)
            log("[UI] Entered verification code")
            time.sleep(2)
            return True
        except Exception as e:
            log(f"[ERROR] Verification code entry failed: {str(e)}")
            return False

    def handle_username_screen(self):
        """Handles username creation"""
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//*[contains(@text, "username")]'))
            )

            username = f"user_{random.randint(100000, 999999)}"
            username_field = self.driver.find_element(
                AppiumBy.XPATH, '//android.widget.EditText[@text="Username"]')
            username_field.clear()
            username_field.send_keys(username)

            continue_btn = self.driver.find_element(
                AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')
            continue_btn.click()

            log(f"[UI] Created username: {username}")
            return username

        except Exception as e:
            log(f"[ERROR] Username creation failed: {str(e)}")
            raise

    def _handle_account_selection(self):
        """Handles the account selection screen if it appears"""
        try:
            # Wait for account selection screen to appear
            account_picker = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, "com.reddit.frontpage:id/account_picker_accounts")
                )
            )
            log("[UI] Account selection screen detected")
            
            # Click the "Add account" option (second ViewGroup)
            add_account = self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.view.ViewGroup[2]'))
            )
            add_account.click()
            log("[UI] Clicked 'Add account'")
            
        except Exception as e:
            # This screen might not always appear
            log(f"[DEBUG] Account selection screen not detected: {str(e)}")

    def enter_email_credentials(self, email, password):
        """Enters email and handles the email submission screen"""
        try:
            log("[STEP] Entering email credentials")
            
            # Wait for email field - trying multiple strategies
            email_locators = [
                (AppiumBy.XPATH, '//android.widget.EditText[@text="Email"]'),
                (AppiumBy.XPATH, '//android.widget.EditText[contains(@hint, "Email")]'),
                (AppiumBy.CLASS_NAME, "android.widget.EditText"),
                (AppiumBy.XPATH, '//android.widget.EditText')
            ]
            
            email_field = None
            for locator in email_locators:
                try:
                    email_field = self.wait.until(
                        EC.presence_of_element_located(locator)
                    )
                    break
                except:
                    continue
            
            if not email_field:
                # Fallback - get all EditText fields and use the first one
                all_edit_texts = self.driver.find_elements(
                    AppiumBy.CLASS_NAME, "android.widget.EditText")
                if all_edit_texts:
                    email_field = all_edit_texts[0]
            
            if not email_field:
                raise Exception("Could not find email field")

            email_field.clear()
            email_field.send_keys(email)
            log(f"[UI] Entered email: {email}")

            # Handle promotional emails checkbox if present
            try:
                checkbox = self.wait.until(
                    EC.presence_of_element_located(
                        (AppiumBy.XPATH, '//android.widget.CheckBox'))
                )
                if checkbox.is_selected():
                    checkbox.click()
                    log("[UI] Unchecked promotional emails")
            except:
                log("[DEBUG] Promotional checkbox not found")

            # Find and click continue button
            continue_buttons = [
                (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]'),
                (AppiumBy.ID, "com.reddit.frontpage:id/continue_button"),
                (AppiumBy.ACCESSIBILITY_ID, "Continue")
            ]
            
            for locator in continue_buttons:
                try:
                    continue_btn = self.wait.until(
                        EC.element_to_be_clickable(locator)
                    )
                    continue_btn.click()
                    log("[UI] Clicked continue button")
                    return True
                except:
                    continue
            
            raise Exception("Could not find continue button")

        except Exception as e:
            log(f"[ERROR] Failed to enter email: {str(e)}")
            return False

    # [Rest of the methods remain unchanged...]

    def enter_verification_code(self, code: str):
        """Enters the verification code from email"""
        try:
            log("[STEP] Entering verification code")
            
            code_field = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.EditText')
                )
            )
            code_field.send_keys(code)
            log("[UI] Entered verification code")
            return True

        except Exception as e:
            log(f"[ERROR] Failed to input verification code: {str(e)}")
            return False

    def handle_username_screen(self):
        """Generates random username and proceeds"""
        try:
            log("[STEP] Handling username screen")
            
            self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//*[contains(@text, "username")]')
                )
            )

            username = f"user_{random.randint(100000, 999999)}"
            username_field = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.EditText')
                )
            )
            username_field.clear()
            username_field.send_keys(username)
            log(f"[UI] Generated username: {username}")

            self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')
                )
            ).click()
            log("[UI] Submitted username")
            return username

        except Exception as e:
            log(f"[ERROR] Failed to generate username: {str(e)}")
            raise

    # [Rest of the methods remain unchanged...]
    def set_password(self, password: str):
        """Sets and confirms password"""
        try:
            log("[STEP] Setting password")
            
            password_fields = self.wait.until(
                EC.presence_of_all_elements_located(
                    (AppiumBy.XPATH, '//android.widget.EditText')
                )
            )
            password_fields[0].send_keys(password)
            
            if len(password_fields) > 1:
                password_fields[1].send_keys(password)
                log("[UI] Confirmed password")

            self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')
                )
            ).click()
            log("[UI] Submitted password")
            return True

        except Exception as e:
            log(f"[ERROR] Failed to input password: {str(e)}")
            return False

    def select_gender(self):
        """Randomly selects gender"""
        try:
            choices = ["Man", "Woman"]
            choice = random.choice(choices)
            
            self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, f'//android.widget.Button[@text="{choice}"]')
                )
            ).click()
            log(f"[UI] Selected gender: {choice}")
            return True

        except Exception as e:
            log(f"[ERROR] Gender selection failed: {str(e)}")
            return False

    def select_avatar(self):
        """Randomly selects avatar"""
        try:
            log("[STEP] Selecting avatar")
            
            for _ in range(random.randint(1, 5)):
                window_size = self.driver.get_window_size()
                start_x = window_size['width'] * 0.8
                end_x = window_size['width'] * 0.2
                y = window_size['height'] * 0.5
                self.driver.swipe(start_x, y, end_x, y, 400)
                time.sleep(0.5)

            self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')
                )
            ).click()
            log("[UI] Selected avatar")
            return True

        except Exception as e:
            log(f"[ERROR] Avatar selection failed: {str(e)}")
            return False

    def select_interests(self):
        """Selects random interests"""
        try:
            log("[STEP] Selecting interests")
            
            interests = self.wait.until(
                EC.presence_of_all_elements_located(
                    (AppiumBy.XPATH, '//android.widget.TextView[contains(@resource-id, "interest")]')
                )
            )
            selected = 0

            for interest in random.sample(interests, min(len(interests), random.randint(5, 10))):
                try:
                    interest.click()
                    selected += 1
                    time.sleep(0.2)
                except:
                    continue

            log(f"[UI] Selected {selected} interests")

            self.wait.until(
                EC.element_to_be_clickable(
                    (AppiumBy.XPATH, '//android.widget.Button[@text="Continue"]')
                )
            ).click()
            log("[UI] Submitted interests")
            return True

        except Exception as e:
            log(f"[ERROR] Interest selection failed: {str(e)}")
            return False