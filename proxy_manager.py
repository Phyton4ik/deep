import requests
import time
from config.settings import PROXY_ROTATE_URL
from utils.logger import log

def rotate_ip(max_retries=3, delay=5):
    """
    Triggers a proxy IP rotation by sending a GET request to the proxy reset URL.
    Retries up to `max_retries` times if the request fails.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            log(f"[INFO] Rotating IP attempt {attempt + 1}...")
            response = requests.get(PROXY_ROTATE_URL, timeout=10)

            if response.status_code == 200:
                log("[SUCCESS] Proxy IP rotated successfully.")
                time.sleep(delay)  # Give time for proxy rotation to complete
                return True
            else:
                log(f"[WARNING] Failed to rotate IP. Status code: {response.status_code}")

        except Exception as e:
            log(f"[ERROR] Exception occurred during IP rotation: {str(e)}")

        attempt += 1
        time.sleep(delay)  # Wait before retrying

    log("[FAILURE] Maximum IP rotation attempts reached. Skipping this login.")
    return False
