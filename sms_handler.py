# services/sms_handler.py

import time
import requests
from config.settings import FIVE_SIM_API_KEY, FIVE_SIM_COUNTRY, FIVE_SIM_OPERATOR
from utils.logger import log  # Предположим, что логгер уже есть

class FiveSimHandler:
    BASE_URL = "https://5sim.net/v1/user"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {FIVE_SIM_API_KEY}"
        }
        self.number_id = None

    def buy_number(self):
        url = f"{self.BASE_URL}/buy/activation/any/{FIVE_SIM_COUNTRY}/{FIVE_SIM_OPERATOR}/reddit"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            self.number_id = data['id']
            log(f"[5sim] Purchased number: {data['phone']} (ID: {self.number_id})")
            return data['phone']
        except requests.RequestException as e:
            log(f"[5sim] Failed to buy number: {e}")
            raise

    def wait_for_sms(self, timeout=120):
        start_time = time.time()
        log(f"[5sim] Waiting for SMS... (timeout: {timeout}s)")
        while time.time() - start_time < timeout:
            try:
                url = f"{self.BASE_URL}/check/{self.number_id}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()

                if data.get('sms'):
                    code = data['sms'][0]['code']
                    log(f"[5sim] Received SMS code: {code}")
                    return code

                time.sleep(5)
            except requests.RequestException as e:
                log(f"[5sim] Error while waiting for SMS: {e}")

        raise TimeoutError("SMS not received within timeout")

    def cancel_number(self):
        if self.number_id:
            try:
                url = f"{self.BASE_URL}/cancel/{self.number_id}"
                requests.get(url, headers=self.headers)
                log(f"[5sim] Number ID {self.number_id} cancelled.")
            except requests.RequestException as e:
                log(f"[5sim] Failed to cancel number: {e}")
                
def get_phone_number_and_sms(api_key=None, country=None, operator=None):
    """
    Wrapper function to get phone number and SMS code using FiveSimHandler.
    """
    handler = FiveSimHandler()
    try:
        phone_number = handler.buy_number()
        code = handler.wait_for_sms()
        return {
            "number": phone_number,
            "code": code
        }
    except Exception as e:
        log(f"[ERROR] get_phone_number_and_sms failed: {e}")
        handler.cancel_number()
        return None

