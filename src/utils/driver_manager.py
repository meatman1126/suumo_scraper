from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

class DriverManager:
    """Selenium WebDriverの管理クラス"""
    
    def __init__(self):
        """WebDriverの初期化"""
        self.driver = self._setup_driver()
        self.driver.implicitly_wait(10)
    
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Chrome WebDriverの設定を行う
        
        Returns:
            webdriver.Chrome: 設定済みのChrome WebDriverインスタンス
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        service = Service('/opt/homebrew/bin/chromedriver')
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def wait_for_page_load(self, timeout: int = 30) -> None:
        """
        ページの読み込み完了を待機する
        
        Args:
            timeout (int): タイムアウト時間（秒）
        """
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
    
    def wait_for_element(self, by: By, value: str, timeout: int = 30) -> None:
        """
        要素の出現を待機する
        
        Args:
            by (By): 要素の検索方法
            value (str): 検索条件
            timeout (int): タイムアウト時間（秒）
        """
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def close(self) -> None:
        """WebDriverを終了する"""
        self.driver.quit() 