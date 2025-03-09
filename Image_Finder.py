# This will be a web scraper that is used to find some 
# sample images to train our data and allow use to easliy
# categorize our data

# libaries that will be used to find our images
import os
import requests
from bs4 import BeautifulSoup



def Image_Finder(query, num_of_images_downloaded):
    
    # url (using bing/mozilla to skip website automation)
    url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    #image

    #folder where images are going to be saved

    #format of images 

    #dowlaoding my images to my save folder 

    #some sort of dowload statment 


#Sample call at the end 


