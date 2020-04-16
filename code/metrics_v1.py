import keras.backend as K
import numpy as np
layer = 0
beta = 0.001
def custom_loss(layer):
    def euclidean_loss(y_true, y_pred):
        return K.sqrt(K.sum(K.square(y_pred[:3] - y_true[:3]))) + beta * K.sqrt(K.sum(K.square(y_pred[3:] - y_true[3:])))
    return euclidean_loss

def euclidean_dist(y_true, y_pred):
  return K.sqrt(K.mean(K.square(y_pred[:,:3] - y_true[:,:3]), axis=1))

def x_error(y_true, y_pred):
  return K.mean(K.abs(y_pred[:,0] - y_true[:,0]))

def y_error(y_true, y_pred):
  return K.mean(K.abs(y_pred[:,1] - y_true[:,1]))

def z_error(y_true, y_pred):
  return K.mean(K.abs(y_pred[:,2] - y_true[:,2]))
