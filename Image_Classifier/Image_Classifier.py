#Creating a deep learning pipeline (Creating my own CNN)

#Set Up and Laod Data
#Installing and setting up dependicies

#what libaries I am using 
import tensorflow as tf
import os

#Setting a GPU Memeory Consumption Growth (limit memory)
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu,True)


    

