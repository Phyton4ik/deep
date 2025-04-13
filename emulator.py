import subprocess
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
import time
from appium import webdriver


class LDPlayerManager:
    def __init__(self, instance_name="LDPlayer-9"):
        """Initialize LDPlayerManager with default instance name and paths."""
        self.ldplayer_path = "C:\\LDPlayer\\LDPlayer9\\"  # Path to LDPlayer installation
        self.instance_name = instance_name  # Name of the emulator instance
        self.adb_port = 5555  # Default ADB port for LDPlayer

    def start_emulator(self):
        """Start the emulator and wait for it to fully initialize."""
        try:
            log("[INIT] Starting LDPlayer emulator...")
            # Launch the emulator process
            process = subprocess.Popen(
                [f"{self.ldplayer_path}dnplayer.exe", "launch", "--name", self.instance_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for the emulator to fully initialize (max 60 seconds)
            for _ in range(12):  # 12 attempts, 5 seconds each
                time.sleep(5)
                if self.is_emulator_online():
                    log("[STATUS] LDPlayer fully initialized")
                    return True
                if process.poll() is not None:  # Process terminated
                    break

            # Check for errors if the process terminated unexpectedly
            if process.returncode is not None and process.returncode != 0:
                err = process.stderr.read()
                log(f"[EMULATOR ERROR] Exit code {process.returncode}: {err}")
            else:
                log("[ERROR] Emulator process terminated unexpectedly")
            return False
        except Exception as e:
            log(f"[EMULATOR CRASH] {str(e)}")
            return False

    def adb_connect(self):
        """Connect to the emulator via ADB"""
        try:
            # Проверяем доступные устройства
            result = subprocess.run(
                [f"{self.ldplayer_path}adb.exe", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
        
            # Ищем наш эмулятор
            devices = [line.split('\t')[0] for line in result.stdout.splitlines() 
                    if '\tdevice' in line]
        
            if f"127.0.0.1:{self.adb_port}" in devices:
                log(f"[ADB] Already connected to {self.adb_port}")
                return True
            
            # Пробуем подключиться
            connect_result = subprocess.run(
                [f"{self.ldplayer_path}adb.exe", "connect", f"127.0.0.1:{self.adb_port}"],
                capture_output=True,
                text=True
            )
        
            if "connected" in connect_result.stdout:
                log(f"[ADB] Successfully connected to port {self.adb_port}")
                return True
            
            log(f"[ADB ERROR] Connection failed: {connect_result.stdout.strip()}")
            return False
        
        except Exception as e:
            log(f"[ADB FATAL] {str(e)}")
            return False

    def is_emulator_online(self):
        """Check if the emulator is online and ready."""
        try:
            result = subprocess.run(
                [f"{self.ldplayer_path}adb.exe", "devices"],
                capture_output=True,
                text=True
            )
            if "127.0.0.1:5555" in result.stdout or "emulator" in result.stdout:
                log("[STATUS] Emulator is online")
                return True
            else:
                log("[STATUS] Emulator is not online")
                return False
        except Exception as e:
            log(f"[ADB CHECK ERROR] {str(e)}")
            return False

    def prepare_reddit(self, driver):
        """Prepare the Reddit app for use by launching it via ADB or Appium."""
        try:
            log("[INIT] Launching Reddit app...")
            driver.start_activity(
                "com.reddit.frontpage",
                "com.reddit.frontpage.StartActivity"
            )
            log("[SUCCESS] Reddit app launched")
            return True
        except Exception as e:
            log(f"[REDDIT PREP ERROR] Failed to launch Reddit app via Appium: {str(e)}")
            log("[INIT] Attempting to launch Reddit app via ADB...")
            try:
                subprocess.run(
                    ["adb", "-s", "emulator-5554", "shell", "am", "start", "-n", "com.reddit.frontpage/com.reddit.frontpage.StartActivity"],
                    check=True
                )
                log("[SUCCESS] Reddit app launched via ADB")
                return True
            except Exception as adb_error:
                log(f"[ADB ERROR] Failed to launch Reddit app via ADB: {str(adb_error)}")
                return False

def init_driver(adb_port):
    """Initialize Appium driver with W3C-compatible capabilities."""
    desired_caps = {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": f"emulator-{adb_port}",
        "appium:appPackage": "com.reddit.frontpage",
        "appium:appActivity": "com.reddit.frontpage.StartActivity",
        "appium:noReset": True,
        "appium:newCommandTimeout": 300
    }

    try:
        log("[INIT] Starting Appium session...")
        driver = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)
        driver.implicitly_wait(10)
        log("[SUCCESS] Driver initialized")
        return driver
    except Exception as e:
        log(f"[DRIVER ERROR] Initialization failed: {str(e)}")
        raise RuntimeError(f"Appium session creation failed: {str(e)}")