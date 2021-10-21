from pypasser import reCaptchaV2

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service

# Create an instace of webdriver
service = Service("./msedgedriver.exe")
driver = webdriver.Edge(service=service)

# Open target
driver.get('https://www.google.com/recaptcha/api2/demo')

# Solve reCaptcha v2 via PyPasser
is_checked = reCaptchaV2(driver=driver, play=False)

if is_checked:
    # Click submit button
    driver.find_element(By.CSS_SELECTOR, '#recaptcha-demo-submit').click()
    if 'Verification Success' in driver.page_source:
        print('SUCCESS')
        
else:
    print('FAIL')
