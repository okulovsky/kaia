import subprocess
import time
import webbrowser
from pathlib import Path
from threading import Thread
import requests
from brainbox.framework import ApiUtils
import os
import signal

class BrowserInstance:
    def __init__(self, disable_mic_at_startup: bool = True, port: int = 5179):
        self.port = port
        self.disable_mic_at_startup = disable_mic_at_startup

    def __enter__(self):
        url = f'http://localhost:{self.port}'
        ApiUtils.wait_for_reply(url, 5)

        from selenium import webdriver
        from selenium.webdriver.firefox.service import Service as FirefoxService
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from webdriver_manager.firefox import GeckoDriverManager

        # Setup Firefox options
        options = FirefoxOptions()
        options.add_argument("--new-tab")  # Open in new tab if possible
        options.set_preference("permissions.default.microphone", 2 if self.disable_mic_at_startup else 0)
        options.set_preference("media.autoplay.default", 0)  # 0 = allow all autoplay

        try:
            self.driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()),
                options=options
            )
            self.driver.get(url)
        except Exception as e:
            print("Failed to launch browser:", e)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.close()  # closes current tab
            # self.driver.quit()  # if you want to close the entire browser


class Frontend:
    def __init__(self,
                 npm_version: str,
                 frontend_folder: Path,
                 ):
        self.npm_version = npm_version
        self.frontend_folder = frontend_folder



    BrowserInstance = BrowserInstance

    def __enter__(self):
        cmd = f'''
source ~/.nvm/nvm.sh && \
nvm use {self.npm_version} && \
npx vite --config vite.autotest.config.ts
'''
        self.process = subprocess.Popen(['/bin/bash', '-c', cmd], cwd=self.frontend_folder,  preexec_fn=os.setsid )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.process.wait()



