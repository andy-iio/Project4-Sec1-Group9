from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time

# Set up Chrome options
chrome_options = Options()

# Set up Chrome service using WebDriver Manager for downloading 
service = Service(ChromeDriverManager().install())

# Initialize the WebDriver with options and service
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open Google Images (chosen platform for images)
driver.get("https://www.google.com/imghp")

# Function definition to click on random images
def click_random_images(driver, delay, max_images):
    # Target URL for search (you can change the search query)
    url = 
    driver.get(url)

    # Wait for images to load using WebDriverWait
    WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.XPATH, "//img[contains(@class, 'YQ4gaf')]"))
    )

    # Find all image thumbnails using their class name
    thumbnails = driver.find_elements(By.XPATH, "//img[contains(@class, 'YQ4gaf')]")
    print(f"Found {len(thumbnails)} thumbnails.")  # For debugging
    
    image_count = 0

    # While we haven't clicked on enough images, keep clicking random ones
    while image_count < max_images and len(thumbnails) > 0:
        # Choose a random thumbnail image
        random_image = random.choice(thumbnails)
        
        # Click on the random image
        try:
            random_image.click()
            time.sleep(delay)  # Wait for the image to open
            image_count += 1
            print(f"Clicked on image {image_count}")
        except Exception as e:
            print(f"Error clicking image: {e}")
            continue

    # Return the number of images clicked
    return image_count

# Click on random images
click_random_images(driver, 3, 6)  # Change the max_images as needed

# Quit the driver
driver.quit()
