"""
价格获取模块 - 从两个交易所获取BTC价格
"""
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceFetcher:
    def __init__(self):
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # 使用新的无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-web-resources')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--enable-automation')
            chrome_options.add_argument('--password-store=basic')
            chrome_options.add_argument('--use-mock-keychain')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 尝试使用chromium-browser
            import os
            chromium_paths = [
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/usr/bin/google-chrome',
            ]
            chromium_binary = None
            for path in chromium_paths:
                if os.path.exists(path):
                    chromium_binary = path
                    break
            
            if chromium_binary:
                chrome_options.binary_location = chromium_binary
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("WebDriver初始化成功")
        except Exception as e:
            logger.error(f"WebDriver初始化失败: {e}")
            self.driver = None
    
    def get_backpack_price(self):
        """
        从Backpack交易所获取BTC价格
        https://backpack.exchange/trade/BTC_USD_PERP
        """
        import re
        
        # 首先尝试API方式
        try:
            # 尝试Backpack的公共API
            api_urls = [
                "https://api.backpack.exchange/api/v1/ticker",
                "https://backpack.exchange/api/v1/ticker",
            ]
            
            for api_url in api_urls:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # 查找BTC相关的ticker
                        if isinstance(data, list):
                            for ticker in data:
                                if 'BTC' in str(ticker.get('symbol', '')).upper():
                                    price = float(ticker.get('lastPrice', 0))
                                    if 20000 < price < 200000:
                                        logger.info(f"Backpack价格获取成功(API): ${price}")
                                        return price
                        elif isinstance(data, dict):
                            if 'lastPrice' in data:
                                price = float(data['lastPrice'])
                                if 20000 < price < 200000:
                                    logger.info(f"Backpack价格获取成功(API): ${price}")
                                    return price
                except:
                    continue
        except Exception as e:
            logger.debug(f"API方式获取失败，尝试网页抓取: {e}")
        
        # 如果API失败，使用Selenium抓取网页
        try:
            if not self.driver:
                self._init_driver()
            
            if not self.driver:
                logger.error("WebDriver未初始化")
                return None
            
            url = "https://backpack.exchange/trade/BTC_USD_PERP"
            self.driver.get(url)
            time.sleep(8)  # 增加等待时间，确保页面完全加载
            
            # 尝试多种选择器来找到价格
            price_selectors = [
                "//span[contains(@class, 'price')]",
                "//div[contains(@class, 'last-price')]",
                "//div[contains(@class, 'lastPrice')]",
                "//span[contains(text(), '$')]",
                "[data-testid='price']",
                ".price",
                "#price",
                "//*[contains(@class, 'ticker')]//*[contains(text(), '$')]",
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    if selector.startswith("//"):
                        element = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    text = element.text.strip()
                    # 提取价格数字
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', text.replace(',', ''))
                    if price_match:
                        price_val = float(price_match.group(1))
                        if 20000 < price_val < 200000:
                            price = price_val
                            logger.info(f"Backpack价格获取成功(选择器): ${price}")
                            return price
                except:
                    continue
            
            # 如果选择器都失败，尝试从页面源码中提取
            page_source = self.driver.page_source
            
            # 查找包含价格的文本
            price_patterns = [
                r'"lastPrice":\s*"?([\d,]+\.?\d{2,})"?',
                r'"price":\s*"?([\d,]+\.?\d{2,})"?',
                r'\$([\d,]+\.?\d{2,})',
                r'BTC.*?(\d{4,6}\.?\d{0,2})',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    for match in matches:
                        try:
                            price_val = float(str(match).replace(',', ''))
                            if 20000 < price_val < 200000:
                                logger.info(f"Backpack价格获取成功(正则): ${price_val}")
                                return price_val
                        except:
                            continue
            
            logger.warning("无法从Backpack获取价格")
            return None
            
        except Exception as e:
            logger.error(f"获取Backpack价格时出错: {e}")
            return None
    
    def get_lighter_price(self):
        """
        从Lighter交易所获取BTC价格
        https://app.lighter.xyz/trade/BTC
        """
        import re
        
        # 首先尝试API方式
        try:
            # 尝试Lighter的公共API
            api_urls = [
                "https://api.lighter.xyz/v1/ticker",
                "https://app.lighter.xyz/api/v1/ticker",
            ]
            
            for api_url in api_urls:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # 查找BTC相关的ticker
                        if isinstance(data, list):
                            for ticker in data:
                                if 'BTC' in str(ticker.get('symbol', '')).upper():
                                    price = float(ticker.get('lastPrice', ticker.get('price', 0)))
                                    if 20000 < price < 200000:
                                        logger.info(f"Lighter价格获取成功(API): ${price}")
                                        return price
                        elif isinstance(data, dict):
                            if 'lastPrice' in data or 'price' in data:
                                price = float(data.get('lastPrice', data.get('price', 0)))
                                if 20000 < price < 200000:
                                    logger.info(f"Lighter价格获取成功(API): ${price}")
                                    return price
                except:
                    continue
        except Exception as e:
            logger.debug(f"API方式获取失败，尝试网页抓取: {e}")
        
        # 如果API失败，使用Selenium抓取网页
        try:
            if not self.driver:
                self._init_driver()
            
            if not self.driver:
                logger.error("WebDriver未初始化")
                return None
            
            url = "https://app.lighter.xyz/trade/BTC"
            self.driver.get(url)
            time.sleep(8)  # 增加等待时间，确保页面完全加载
            
            # 尝试多种选择器来找到价格
            price_selectors = [
                "//span[contains(@class, 'price')]",
                "//div[contains(@class, 'last-price')]",
                "//div[contains(@class, 'lastPrice')]",
                "//span[contains(text(), '$')]",
                "[data-testid='price']",
                ".price",
                "#price",
                "//*[contains(@class, 'ticker')]//*[contains(text(), '$')]",
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    if selector.startswith("//"):
                        element = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 8).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    text = element.text.strip()
                    # 提取价格数字
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', text.replace(',', ''))
                    if price_match:
                        price_val = float(price_match.group(1))
                        if 20000 < price_val < 200000:
                            price = price_val
                            logger.info(f"Lighter价格获取成功(选择器): ${price}")
                            return price
                except:
                    continue
            
            # 如果选择器都失败，尝试从页面源码中提取
            page_source = self.driver.page_source
            
            # 查找包含价格的文本
            price_patterns = [
                r'"lastPrice":\s*"?([\d,]+\.?\d{2,})"?',
                r'"price":\s*"?([\d,]+\.?\d{2,})"?',
                r'\$([\d,]+\.?\d{2,})',
                r'BTC.*?(\d{4,6}\.?\d{0,2})',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    for match in matches:
                        try:
                            price_val = float(str(match).replace(',', ''))
                            if 20000 < price_val < 200000:
                                logger.info(f"Lighter价格获取成功(正则): ${price_val}")
                                return price_val
                        except:
                            continue
            
            logger.warning("无法从Lighter获取价格")
            return None
            
        except Exception as e:
            logger.error(f"获取Lighter价格时出错: {e}")
            return None
    
    def get_prices(self):
        """获取两个交易所的价格"""
        backpack_price = self.get_backpack_price()
        lighter_price = self.get_lighter_price()
        
        return {
            'backpack': backpack_price,
            'lighter': lighter_price,
            'difference': backpack_price - lighter_price if (backpack_price and lighter_price) else None,
            'difference_percent': ((backpack_price - lighter_price) / lighter_price * 100) if (backpack_price and lighter_price and lighter_price != 0) else None
        }
    
    def close(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
