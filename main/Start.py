import json
import logging
import time
import sys

from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ReuseChrome import *

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))  # 重点


sys.excepthook = handle_exception  # 重点


class Start():

    def __init__(self):
        # 使用ReuseChrome()复用上次的session
        configs = None
        with open('./static/chromedriver/config.txt', 'r') as f:
            configs = f.readlines()
        self.driver = ReuseChrome(command_executor=configs[0].replace('\n', ''),
                                  session_id=configs[1].replace('\n', ''))

    def wait(self, xpath):
        """
        显性等待
        :param xpath:
        :return:
        """
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

    def wait_by_type(self, type, xpath):
        """
        显性等待
        :param xpath:
        :return:
        """
        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((type, xpath))
        )

    def close(self):
        """
        关闭
        :return:
        """
        self.driver.quit()

    def click_check(self, xpath):
        '''
        校验点击
        :param xpath:xpath参数
        :return:
        '''
        self.wait(xpath)
        self.driver.find_element_by_xpath(xpath).click()

    def click_check_by_css(self, xpath):
        '''
        校验点击
        :param xpath:xpath参数
        :return:
        '''
        self.wait_by_type(By.CSS_SELECTOR, xpath)
        self.driver.find_element_by_css_selector(xpath).click()

    def input(self, xpath, value):
        self.wait(xpath)
        self.driver.find_element_by_xpath(xpath).send_keys(value)

    def inputByCssSelector(self, xpath, value):
        """
        根据jq选择器设置值
        :param xpath:
        :param value:
        :return:
        """
        self.wait_by_type(By.CSS_SELECTOR, xpath)
        self.driver.find_element_by_css_selector(xpath).send_keys(value)

    def exec_js(self, js):
        """
        执行js
        :param js:
        :return:
        """
        # 定位“立即注册”位置，修改target属性值为空，让新打开的链接显示在同一个窗口
        return self.driver.execute_script(js)  # 执行js语句

    def set_referrer_policy(self):
        """
        设置 referrer policy
        :return:
        """
        value = '\'<meta name="referrer" content="strict-origin-when-cross-origin">\''
        self.exec_js(
            'document.querySelector("head").innerHTML=document.querySelector("head").innerHTML+' + value + '')

    def click_for_csv(self, name, count=0):
        """
        根据csv文件执行js
        :param name:
        :return:
        """
        with open('./static/chromedriver/exex_js.csv', 'r') as f:
            for texts in f:
                arr = texts.split(',')
                if arr[0].__eq__(name):
                    js = self.exec_js("$('%s').click()" % arr[1])

    def format_data(self, value):
        return value.replace('\n', '').replace(' ', '')

    def get_data(self):
        """
        获取实时数据
        :return:
        """
        logging.info('开始抓取')
        self.driver.get('https://www.huobi.be/zh-cn/markets/?tab=exchange')
        list_xpath = '//dl[@class="table-wrap"]/dd[@class="market-exchange-item"]'
        self.wait(list_xpath)
        count = 1
        tmp_data = {}
        refresh_count = 0
        start_time = time.time()
        while True:
            # 每十分钟刷新一次
            if time.time() - start_time >= 60 * 8:
                logging.info('第%s次刷新', refresh_count)
                self.driver.get('https://www.huobi.be/zh-cn/markets/?tab=exchange')
                self.wait(list_xpath)
                start_time = time.time()
                refresh_count += 1
            logging.info('第%s次抓取' % count)
            html = etree.HTML(self.driver.page_source)
            result_list = html.xpath(list_xpath)
            for result in result_list:
                currency_info = {}
                currency_info['name'] = self.format_data(
                    '|'.join(result.xpath('div[@class="item-wrap"]/span[1]/em/text()')))
                currency_info['new_price'] = self.format_data(result.xpath('div[@class="item-wrap"]/span[2]/text()')[0])
                currency_info['increase'] = self.format_data(result.xpath('div[@class="item-wrap"]/span[3]/text()')[0])
                currency_info['max_price'] = self.format_data(result.xpath('div[@class="item-wrap"]/span[4]/text()')[0])
                currency_info['min_price'] = self.format_data(result.xpath('div[@class="item-wrap"]/span[5]/text()')[0])
                currency_info['amount_24'] = self.format_data(result.xpath('div[@class="item-wrap"]/span[6]/text()')[0])
                currency_info['transaction_24'] = self.format_data(
                    result.xpath('div[@class="item-wrap"]/span[7]/text()')[0])
                currency_info['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                # 价格不变跳过
                try:
                    if tmp_data[currency_info['name']] == currency_info['new_price']:
                        continue
                except:
                    pass
                tmp_data[currency_info['name']] = currency_info['new_price']
                insert_data = json.dumps(currency_info, ensure_ascii=False)
                with open('static/data/%s.txt' % currency_info['name'], 'a') as f:
                    f.write(insert_data + '\n')
                logging.info(insert_data)
            count += 1
            time.sleep(1)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()

    # 开启Proxy
    # options.add_argument('--proxy-server={0}'.format('127.0.0.1:8888'))
    # 解决 您的连接不是私密连接问题
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-urlfetcher-cert-requests')
    prefs = {"profile.managed_default_content_settings.images": 2}  # 设置无图模式
    options.add_experimental_option("prefs", prefs)  # 加载无图模式设置
    # prefs = {"profile.default_content_setting_values.cookies": 2}  # 设置禁用cookie
    # options.add_experimental_option("prefs", prefs)  # 加载禁用cookie设置
    # options.add_argument('--incognito')  # 隐身模式（无痕模式）
    # 手机模式
    # options.add_argument("--user-agent=iphone 6 plus")
    '''禁用 w3c'''
    options.add_experimental_option('w3c', False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 以键值对的形式加入参数
    options.add_argument('disable-infobars')  # 去掉提示：Chrome正收到自动测试软件的控制
    options.add_argument("--auto-open-devtools-for-tabs")  # 打开开发者模式
    # options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    options.add_argument('--no-sandbox')  # root用户不加这条会无法运行
    options.add_argument('--headless')  # 无界面模式
    # options.add_extension('./static/chromedriver/plugin/xpath.crx')  # 安装插件
    # options.add_extension('./static/plugin/Proxy.crx')
    start = Start()
    try:
        Start().close()
    except:
        pass
    driver = webdriver.Chrome(executable_path="./static/chromedriver/chromedriver", options=options)
    # driver = webdriver.Chrome(options=options)
    # 过检测
    # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #     "source": """
    #                    Object.defineProperty(navigator, 'webdriver', {
    #                      get: () => undefined
    #                    })
    #                  """
    # })
    driver.maximize_window()
    executor_url = driver.command_executor._url
    session_id = driver.session_id
    with open('./static/chromedriver/config.txt', 'w') as f:
        f.write(executor_url + '\n')
        f.write(session_id + '\n')
    Start().get_data()
