# -*- coding: utf-8 -*-

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x

import tensorflow as tf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from utils import StandardScaler

tf.__version__

device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  print('GPU device not found')
else:
  print('Found GPU at: {}'.format(device_name))

path = "training_data.csv"
df_demand = pd.read_csv(path)
df_demand.columns = ["timebin", "cell", "count"]

timebins = pd.unique(df_demand['timebin'])
stations = pd.unique(df_demand['cell'])
num_timebins, num_cells, num_counts = df_demand.nunique(axis=0)

# data = pd.pivot(df_demand, index='timebin', columns='start_station_id', values='count')
demand_count = df_demand['count'].values.reshape((num_cells, num_timebins)).T
df_demand_count = pd.DataFrame(demand_count, columns=stations).add_prefix('station_')

datebins = pd.to_datetime(timebins, unit='s', utc=True, infer_datetime_format=True).tz_convert(tz='US/Eastern')

onehot = True
if onehot:
    df_month = pd.get_dummies(datebins.month, prefix='month')
    df_hour = pd.get_dummies(datebins.hour, prefix='hour')
    df_dayofweek = pd.get_dummies(datebins.dayofweek, prefix='dayofweek')
    df_weekend = pd.get_dummies(np.in1d(datebins.dayofweek, [5,6]), prefix='weekend')
else:
    df_month = pd.DataFrame(datebins.month, columns=['month'])
    df_hour = pd.DataFrame(datebins.hour, columns=['hour'])
    df_dayofweek = pd.DataFrame(datebins.dayofweek, columns=['dayofweek'])
    df_weekend = pd.DataFrame(np.in1d(datebins.dayofweek, [5,6]), columns=['weekend'])

df = pd.concat([df_demand_count, df_month, df_hour, df_dayofweek, df_weekend], axis=1)
names_stations = df_demand_count.columns.tolist()
names_month = df_month.columns.tolist()
names_hour = df_hour.columns.tolist()
names_dayofweek = df_dayofweek.columns.tolist()
names_weekend = df_weekend.columns.tolist()
names_all = df.columns.tolist()

train_filter = (datebins >= '2018-01-01') & (datebins < '2019-09-30')
val_filter = (datebins >= '2019-10-01') & (datebins < '2019-12-31')
test_filter = (datebins >= '2019-10-01') & (datebins < '2019-12-31')

df_train = df[train_filter]
df_val = df[val_filter]
df_test = df[test_filter]

df.head(), df.shape

num_input = df.shape[1]
# num_input = num_cells
num_output = num_cells
num_output = df.shape[1]

def get_dataset_XY(df, batch_size=None, batch_index=0, num_feature=24, num_horizon=1, num_input = num_input, num_output=num_output):
    x_offsets = np.sort(np.concatenate((np.arange(-num_feature+1, 1, 1),)))
    y_offsets = np.sort(np.arange(1, 1+ num_horizon, 1))

    min_t = abs(min(x_offsets))
    max_t = abs(df.shape[0] - abs(max(y_offsets)))  # Exclusive

    X, Y = [], []
    if batch_size is None:
        batch_size = max_t - min_t + 1
        batch_index = 0
    count = 0
    for t in range(min_t, max_t):
        t = t + batch_size * batch_index
        xt = df.iloc[t + x_offsets, 0:num_input].values.flatten('F')
        yt = df.iloc[t + y_offsets, 0:num_output].values.flatten('F')
        X.append(xt)
        Y.append(yt)

        count += 1
        if count == batch_size:
            break

    X = np.stack(X).reshape([-1, num_input, num_feature])
    Y = np.stack(Y)#.reshape([-1, num_input, num_feature])

    return X, Y

batch_size = 100
num_feature = 24
num_horizon = 1

X_train, Y_train = get_dataset_XY(df_train, batch_size, 0, num_feature, num_horizon)
X_train.shape, Y_train.shape

X_val, Y_val = get_dataset_XY(df_val, None, 0, num_feature, num_horizon)
# # X_test, Y_test = get_dataset_XY(df_test)
X_test, Y_test = X_val, Y_val

X_train.shape, Y_train.shape, X_val.shape, Y_val.shape

scaler = StandardScaler(mean=X_train.mean(), std=X_train.std())

import gcn
import importlib
importlib.reload(gcn)

# Hyperparameters
learning_rate = 3e-4 # learning rate
decay = 0.9
batchsize = 100 # batch size 

hidden_num_layer = [10, 20, 20] # determine the number of hidden layers and the vector length at each node of each hidden layer
reg_weight = [0, 0, 0] # regularization weights for adjacency matrices L1 loss

keep = 1 # drop out probability

early_stop_th = 200 # early stopping threshold, if validation RMSE not dropping in continuous 20 steps, break
training_epochs = 10 # total training epochs

# Training
start_time = datetime.datetime.now()

val_error, predic_res, test_Y, test_error, bestWeightA = gcn.gcnn_ddgf(
    hidden_num_layer, reg_weight, 
    num_input, num_output, num_feature, num_horizon, 
    learning_rate, decay, batchsize, 
    keep, early_stop_th, training_epochs, 
    get_dataset_XY, df_train, 
    X_val, Y_val, 
    X_test, Y_test, 
    scaler, 'RMSE')

end_time = datetime.datetime.now()
val_error
print('Total training time: ', end_time-start_time)
