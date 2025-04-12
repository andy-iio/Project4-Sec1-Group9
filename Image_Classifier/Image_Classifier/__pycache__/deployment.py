import tensorflow as tf
from tensorflow.keras.utils import load_img, img_to_array
from tensorflow.keras.models import load_model
import numpy as np

# loading the h5 model for juypter 
model_path = './Image_Classifier/Image_Classifier/imageclassifierHS_Updated.h5'

# function definition
def load_and_predict(model_path, img_path, target_size=(256, 256)): #images are 256, 256
    model = load_model(model_path)  # loading model

    img = load_img(img_path, target_size=target_size)  # loading image
    img_array = img_to_array(img)  # converting image  to array
    
    # Normalizing the image (scaling pixel values so that they are between zero and one) 
    img_array = img_array / 255.0

    img_array = np.expand_dims(img_array, axis=0)  # adding value to batch

    predictions = model.predict(img_array)  # using array to make prediction

    # Apply sigmoid if the vlaue passed in is not between 0 and one 
    #it has to be for this classification 
    predicted_class_prob = tf.sigmoid(predictions[0][0]).numpy()  # Apply sigmoid to get proper vlaue (0-1)
    rounded_prob = round(predicted_class_prob, 1) #rounded probability for class classifiaction 

    # Converting probability to classes for easier understanding 
    if rounded_prob > 0.50: 
        predicted_class = "Prepper Tips"
    else:
        predicted_class = "Meal Prep"
    
    # printing result
    print(f"Predicted Class: {predicted_class}")
    return predicted_class

