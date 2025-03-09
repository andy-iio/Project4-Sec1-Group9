from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import io
from PIL import Image
import time

# Set up Chrome options
chrome_options = Options()


# Set up Chrome service using WebDriver Manager for dowloading 
service = Service(ChromeDriverManager().install())

# Initialize the WebDriver with options and service
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open Google (chosen platform for images)
driver.get("https://www.google.com")

#function defnetion 
def find_images(driver, delay, max_images):
    # scroll down function that allows for scrolling down to bottom of screen
    def scroll_down(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

    #traget url (can be chnaged accordingly)
    url = "https://www.google.com/search?q=meal+prepping+old+pictures&sca_esv=fecf88b048ffc4bd&udm=2&biw=1033&bih=851&sxsrf=AHTn8zrBI7szyBCDIqPNjWJrJ9AYKfyGaw%3A1741505270284&ei=9kLNZ-yHEc7cptQP846RKA&ved=0ahUKEwjs2onYvPyLAxVOrokEHXNHBAUQ4dUDCBE&uact=5&oq=meal+prepping+old+pictures&gs_lp=EgNpbWciGm1lYWwgcHJlcHBpbmcgb2xkIHBpY3R1cmVzSOmAAlCM2gFY6v8BcAN4AJABAJgBRqABsAeqAQIxNbgBA8gBAPgBAZgCBKACjAHCAgcQIxgnGMkCwgIKEAAYgAQYQxiKBcICBhAAGAcYHsICBRAAGIAEmAMAiAYBkgcBNKAHuxI&sclient=img"
    driver.get(url) #webdriver goes to url 

    image_urls = set() # stores all urls of images found 
    skips = 0

    # while we havent found max_images .... keep scrolling 
    while len(image_urls) + skips < max_images:
        scroll_down(driver)

        # find images with this class name (google inspection class name)
        thumbnails = driver.find_elements(By.CLASS_NAME, "sFlh5c FyHeAf")

        #loop thorugh all images thsat have not been seen yet 
        for img in thumbnails[len(image_urls) + skips: max_images]:
            #clicking on the images 
            try:
                img.click()
                time.sleep(delay)
            except:
                continue
            
            #looking for the real image (pop up window)
            images = driver.find_elements(By.CLASS_NAME,"sFlh5c FyHeAf iPVvYb")
            for image in images:
                if image.get_attributes('src') in image_urls:
                    max_images += 1
                    skips += 1
                    break
                
                
                if image.get_attribute('src') and 'http' in image.get_attribute('src'):
                    image_urls.add(image.get_attribute('src'))
                    print(f"Found{len(image_urls)}")
    
    #return the image urls thst have been found in accordance to the category 
    return image_urls

def download_images(download_path, url, file_name):
    try:
        image_content = requests.get(url).content
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file)
        file_path = download_path + file_name
        
        with open(file_path, "wb") as f:
            image.save(f, "JPEG")
        
        print("Success")
    except Exception as e:
        print("Failed - ", e)

urls = find_images(driver,1, 5)

for i, url in enumerate(urls):
    download_images("Meal_Prepping/", url, str(i) + ".jpg")

driver.quit()