from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui

# 使用Selenium開啟瀏覽器並自動登入
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))

# 設置 Chrome WebDriver 的選項
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 可選，設置為無頭模式，不顯示瀏覽器視窗

# 前往目標網站
driver.get("https://tip.railway.gov.tw/tra-tip-web/tip/tip001/tip125/query")

# 等待開始訂票按鈕出現
wait = WebDriverWait(driver, 10)
start_button = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'btn-basic')]")))

# 等待3秒
time.sleep(3)

# 按下開始訂票按鈕
start_button.click()

# 等待Radio元素出現
try:
    input_element = driver.find_element(By.ID, "pid")
except TimeoutException:
    print("找不到input_element元素，程式結束")
    driver.quit()
    exit()

# 等待3秒 //MUST
time.sleep(3)

# 點擊Radio元素
# radio_element.click()

# 找到 class 為 pid 的元素並填入指定訊息
input_element = driver.find_element(By.ID, "pid")
input_element.send_keys("A123456789")
# input_element.send_keys(Keys.RETURN)

input_element = driver.find_element(By.ID, "startStation1")
input_element.send_keys("1000-臺北")
# input_element.send_keys(Keys.RETURN)

input_element = driver.find_element(By.ID, "endStation1")
input_element.send_keys("7000-花蓮")
# input_element.send_keys(Keys.RETURN)

input_element = driver.find_element(By.ID, "trainNoList1")
input_element.send_keys("434")
# input_element.send_keys(Keys.RETURN)

# <input type="text" data-plugin="datepicker" class="rideDate" placeholder="YYYY/MM/DD" id="rideDate1" data-date-start-date="+0d" name="ticketOrderParamList[0].rideDate" value="2023/06/13" maxlength="10" aria-required="true" aria-invalid="false">
input_element = driver.find_element(By.ID, "rideDate1")
# 找到日期輸入框元素
input_element = driver.find_element(By.ID, "rideDate1")
# 清空輸入框中的內容
input_element.clear()
# 輸入日期
input_element.send_keys("2023")
input_element.send_keys("06")
# input_element.send_keys(Keys.DELETE)
input_element.send_keys("29")
# 你也可以按下 Enter 鍵以模擬輸入完成
input_element.send_keys(Keys.RETURN)

# time.sleep(10)
# <div class="recaptcha-checkbox-border" role="presentation"></div>
# 等待目標元素出現
wait = WebDriverWait(driver, 10)
# target_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'recaptcha')]")))
# target_element = driver.find_element(By.ID, "recaptcha")
# <div class="recaptcha-checkbox-border" role="presentation"></div>
# <div id="rc-anchor-container" class="rc-anchor rc-anchor-normal rc-anchor-light"><div id="recaptcha-accessible-status" class="rc-anchor-aria-status" aria-hidden="true">reCAPTCHA 要求驗證. </div><div class="rc-anchor-error-msg-container" style="display:none"><span class="rc-anchor-error-msg" aria-hidden="true"></span></div><div class="rc-anchor-content"><div class="rc-inline-block"><div class="rc-anchor-center-container"><div class="rc-anchor-center-item rc-anchor-checkbox-holder"><span class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox" role="checkbox" aria-checked="false" id="recaptcha-anchor" tabindex="0" dir="ltr" aria-labelledby="recaptcha-anchor-label"><div class="recaptcha-checkbox-border" role="presentation"></div><div class="recaptcha-checkbox-borderAnimation" role="presentation"></div><div class="recaptcha-checkbox-spinner" role="presentation"><div class="recaptcha-checkbox-spinner-overlay"></div></div><div class="recaptcha-checkbox-checkmark" role="presentation"></div></span></div></div></div><div class="rc-inline-block"><div class="rc-anchor-center-container"><label class="rc-anchor-center-item rc-anchor-checkbox-label" aria-hidden="true" role="presentation" id="recaptcha-anchor-label"><span aria-live="polite" aria-labelledby="recaptcha-accessible-status"></span>我不是機器人</label></div></div></div><div class="rc-anchor-normal-footer"><div class="rc-anchor-logo-portrait" aria-hidden="true" role="presentation"><div class="rc-anchor-logo-img rc-anchor-logo-img-portrait"></div><div class="rc-anchor-logo-text">reCAPTCHA</div></div><div class="rc-anchor-pt"><a href="https://www.google.com/intl/zh-TW/policies/privacy/" target="_blank">隱私權</a><span aria-hidden="true" role="presentation"> - </span><a href="https://www.google.com/intl/zh-TW/policies/terms/" target="_blank">條款</a></div></div></div>
# <button type="button" id="goBack" class="btn btn-3d-liner" title="上一步">上一步</button>
try:
    target_element = wait.until(EC.visibility_of_element_located((By.ID, "goBack")))
    # target_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@id, 'goBack')]")))
    # 如果找到目標元素，執行相應的操作
    # 使用 ActionChains 將滑鼠移到目標元素上方並停留三秒後點擊
    actions = ActionChains(driver)
    if target_element:
        # 取得目標元素的座標
        location = target_element.location
        print("目標元素座標:", location)
        x = location['x']
        y = location['y']
        
        # 捲動網頁到目標元素可見的區域
        driver.execute_script("window.scrollTo(0, arguments[0]);", y - 200)  # 往上捲動 200 個像素
        
        # 移動滑鼠到目標元素的位置
        # actions.move_to_element(target_element).perform()
        # time.sleep(3)
        # actions.click().perform()

        # 取得瀏覽器視窗的座標
        window_position = driver.get_window_position()
        window_x = window_position['x']
        window_y = window_position['y']

        # 計算滑鼠相對於瀏覽器視窗的座標
        mouse_x = window_x + x
        mouse_y = window_y + y

        # 移動滑鼠到目標元素的位置
        pyautogui.moveTo(mouse_x, mouse_y, duration=0.5)
        time.sleep(3)

        # 點擊滑鼠
        pyautogui.click()
    else:
        print("找不到目標元素1")

except TimeoutException:
    print("TimeoutException 找不到目標元素2")
    # 在這裡可以執行錯誤處理的程式碼，或者結束程式的適當操作




# 等待 20 秒
time.sleep(20000)

# 關閉瀏覽器視窗
driver.quit()
