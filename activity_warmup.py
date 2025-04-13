from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
import time
import random

class RedditActivityWarmup:
    def __init__(self, driver, duration_minutes=3):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        self.actions = TouchAction(driver)
        self.session_time = duration_minutes * 60

    def _safe_click(self, xpath):
        try:
            element = self.wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, xpath)))
            self.actions.tap(element).perform()
            log(f"[ACTION] Clicked: {xpath}")
            time.sleep(random.uniform(1, 2))
            return True
        except Exception as e:
            log(f"[WARNING] Click failed on {xpath}: {str(e)}")
            return False

    def _scroll_screen(self, direction='up'):
        try:
            size = self.driver.get_window_size()
            x = size['width'] // 2
            y_start = size['height'] * (0.8 if direction == 'up' else 0.2)
            y_end = size['height'] * (0.2 if direction == 'up' else 0.8)
            self.driver.swipe(x, int(y_start), x, int(y_end), 600)
            time.sleep(random.uniform(1, 2))
            return True
        except Exception as e:
            log(f"[WARNING] Scroll failed: {str(e)}")
            return False

    def _interact_with_post(self):
        actions = [
            ('//*[contains(@resource-id, "upvote")]', "upvote"),
            ('//*[contains(@resource-id, "downvote")]', "downvote"),
            ('//*[contains(@text, "Comment")]', "comment"),
            ('//*[contains(@text, "Share")]', "share"),
            ('//*[contains(@text, "Save")]', "save")
        ]
        random.shuffle(actions)
        for xpath, _ in actions[:2]:
            self._safe_click(xpath)
            time.sleep(random.uniform(1, 2))
            self._safe_click('//android.widget.ImageButton[@content-desc="Back"]')

    def _visit_sections(self):
        sections = [
            '//*[contains(@text, "Home")]',
            '//*[contains(@text, "Popular")]',
            '//*[contains(@text, "News")]',
            '//*[contains(@text, "Gaming")]'
        ]
        for xpath in random.sample(sections, 2):
            self._safe_click(xpath)
            time.sleep(random.uniform(2, 3))

    def _relaunch_app(self):
        log("[INFO] Relaunching Reddit...")
        self.driver.press_keycode(3)  # Home
        time.sleep(1)
        self.driver.activate_app("com.reddit.frontpage")
        time.sleep(3)

    def _join_random_community(self):
        self._safe_click('//*[contains(@content-desc, "Communities")]')
        for _ in range(random.randint(1, 2)):
            self._scroll_screen()
        buttons = self.driver.find_elements(AppiumBy.XPATH, '//*[contains(@text, "Join")]')
        if buttons:
            random.choice(buttons).click()
            log("[ACTION] Joined a community")
        self._safe_click('//*[contains(@content-desc, "Home")]')

    def warmup_session(self):
        start = time.time()
        log(f"[WARMUP] Started for {self.session_time} seconds")
        while time.time() - start < self.session_time:
            self._scroll_screen()
            self._interact_with_post()
            if random.choice([True, False]):
                self._visit_sections()
            if random.randint(1, 3) == 1:
                self._join_random_community()
            if random.randint(1, 4) == 1:
                self._relaunch_app()
            time.sleep(random.uniform(2, 5))
        log("[WARMUP] Session completed")
        return True

def warmup_reddit_activity(driver, duration_minutes=3):
    warmup = RedditActivityWarmup(driver, duration_minutes)
    return warmup.warmup_session()
