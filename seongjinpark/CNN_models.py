"""
Seongjin Park (seongjinpark@email.arizona.edu)
Contains function that defines model's archtecture
Modified CNN sturucture of Kim 2014 paper
flatten data: created by Yiyun Zhao
"""
import numpy as np
import os
import os.path
import pickle

from keras.models import load_model
from keras.layers.core import Dense, Dropout, SpatialDropout1D, Masking
from keras.layers import Input, MaxPooling1D, Flatten, Convolution1D
from keras.layers.merge import Concatenate
from keras.layers.convolutional import Conv1D
from keras.layers.embeddings import Embedding
from keras.layers.pooling import GlobalMaxPooling1D
from keras.models import Sequential, Model
from keras.utils import np_utils
from keras import optimizers
from keras import regularizers


# CNN model 
def CNN_model_stance(x_train, y_train, x_test, y_answer):
    """
    x_train: training data  (5217, 314)
    y_train: training label (5217, )
    x_test : test data      (1485, 314)
    y_test : test label     (1485, )
    """

    # hyperparameters 
    num_cnn_layer = 128 
    filter_sizes = [314]
    num_dense_layers = 2 
    num_dense_units = 256 
    num_epochs = 100 
    learn_rate = 0.001 
    mb_size = 32 
    l2reg = 1e-4 
    
    num_features = 1 
    sequence_len = np.shape(x_train)[1]
    dropout_prob = 0.7

    # reshape data for CNN
    x_train = np.reshape(x_train, (np.shape(x_train)[0], np.shape(x_train)[1], 1))
    x_test = np.reshape(x_test, (np.shape(x_test)[0], np.shape(x_test)[1], 1))

    # if there is a pre-existing model, use it
    if (os.path.exists('CNN_model.h5')):
        model = load_model('CNN_model.h5')
        model.summary()

    else:
        # define model input
        model_input = Input(shape = (sequence_len, num_features))
    
        # create an array to save results from different filter sizes
        convolutional_blocks = []
        for fsz in filter_sizes:
            conv = Conv1D(filters=num_cnn_layer,
                                 kernel_size = fsz,
                                 padding="valid",
                                 activation="relu",
                                 strides=1)(model_input)
            conv = MaxPooling1D(pool_size=1)(conv)
            conv = Flatten()(conv)
            convolutional_blocks.append(conv)
        if len(convolutional_blocks) > 1:
            dense_input = Concatenate()(convolutional_blocks)
        else:
            dense_input = convolutional_blocks[0]

        # add dropout layers 
        dense_input = Dropout(dropout_prob)(dense_input)

        # add fully-connected dense layer
        for ndl in range(num_dense_layers):
            dense_output = Dense(num_dense_units, activation = "relu")(dense_input)
        # add final softmax layer 
        model_output = Dense(4, activation="softmax")(dense_output)

        model = Model(model_input, model_output)

        # use adam optimizer
        adam = optimizers.Adam(lr = learn_rate, beta_1 = 0.9, beta_2 = 0.999,
                epsilon = 1e-08, decay = 0.0)
        
        # compile the model
        model.compile(optimizer=adam, loss="categorical_crossentropy", metrics=["accuracy"])

        # print the model architecture
        model.summary()

        # train the model 
        model.fit(x_train, y_train, 
            batch_size = mb_size,
            epochs = num_epochs,
            shuffle = False, 
            class_weight = None)

        # save the model 
        model.save('CNN_model_v2.h5')

    # make a prediction
    pred_probabilities = model.predict(x_test, batch_size=mb_size)
    confidence = np.max(pred_probabilities, axis=1)
    Y_pred = pred_probabilities.argmax(axis = 1)

    
    return Y_pred, confidence

## Main Script
# Load data
x_train = np.load(os.path.join('flatten_data',
                               'flat_train_x.npy'))
y_train = np.load(os.path.join('flatten_data',
                               'flat_train_y.npy'))
x_dev = np.load(os.path.join('flatten_data',
                               'flat_dev_x.npy'))
y_dev = np.load(os.path.join('flatten_data',
                               'flat_dev_y.npy'))

# Make a prediction 
y_pred, confidence = CNN_model_stance(x_train, y_train,
                                       x_dev, y_dev)

# Print the result of performance evaluations
from sklearn.metrics import classification_report, f1_score

y_dev_max = y_dev.argmax(axis = 1)
print(classification_report(y_dev_max, y_pred, labels=None, target_names=None, sample_weight=None, digits=3))
print("Micro F1: ", f1_score(y_pred, y_dev_max, average = 'micro'))
print("Macro F1: ", f1_score(y_pred, y_dev_max, average = 'macro'))
