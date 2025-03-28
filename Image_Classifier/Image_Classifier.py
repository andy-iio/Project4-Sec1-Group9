#Creating a deep learning pipeline (Creating my own CNN)

#Set Up and Laod Data
#Installing and setting up dependicies

#what libaries I am using 
import tensorflow as tf
import os
import cv2
import imghdr
from matplotlib import pyplot as plt

#Setting a GPU Memeory Consumption Growth (limit memory)
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu,True)

#removing weird images (corruption)
    data_dir = 'Data' #this variable is the path to my image directory
    image_extensions = ['jpeg', 'jpg', 'bmp', 'png'] #types of images (list)

    for image_class in os.listdir(data_dir): #lopping thorugh folders in data directory
        for image in os.listdir(os.path.join(data_dir, image_class)): #print images in the subdirecotry
            image_path = os.path.join(data_dir,image_class,image) # grabbing the images (single images)
            try:
                img = cv2.imread(image_path) #checking that image can be loaded in open cv
                tip = imghdr.what(image_path) #checking that loaded image matches one of the paths
                if tip not in image_extensions:
                    print("Image not in list".format(image_path))
                    os.remove(image_path)
            except Exception as e:
                print("Issue with image".format(image_path))




    

