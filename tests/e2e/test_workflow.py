import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_end_to_end_workflow(driver):
    # Login
    driver.get("http://localhost:3000/login")
    driver.find_element(By.NAME, "email").send_keys("test@example.com")
    driver.find_element(By.NAME, "password").send_keys("testpass123")
    driver.find_element(By.ID, "login-button").click()
    
    # Check dashboard loaded
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dashboard"))
    )
    
    # Navigate to insights
    driver.find_element(By.ID, "insights-nav").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "insights-page"))
    )
    
    # Check data visualization
    charts = driver.find_elements(By.CLASS_NAME, "chart-container")
    assert len(charts) > 0
    
    # Test filtering
    filter_button = driver.find_element(By.ID, "filter-button")
    filter_button.click()
    
    date_picker = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "date-picker"))
    )
    date_picker.click()
    
    # Apply filter
    driver.find_element(By.ID, "apply-filter").click()
    
    # Verify filtered results
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "filtered-results"))
    )
