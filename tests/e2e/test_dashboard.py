import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

def test_dashboard_loading(driver):
    driver.get("http://localhost:3000/dashboard")
    
    # Check main components
    assert driver.find_element(By.ID, "insights-panel")
    assert driver.find_element(By.ID, "productivity-chart")
    assert driver.find_element(By.ID, "activity-feed")

def test_insight_interaction(driver):
    driver.get("http://localhost:3000/dashboard")
    
    # Click first insight
    insight = driver.find_element(By.CLASS_NAME, "insight-card")
    insight.click()
    
    # Check detail view
    detail = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "insight-detail"))
    )
    assert detail.is_displayed()
