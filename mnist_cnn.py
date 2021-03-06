'''Trains a simple convnet on the MNIST dataset.
Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''
from __future__ import print_function
import keras
import xlsxwriter
import time
import pandas as pd
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
import datetime
#============ Multi-GPU ==========
from multi_gpu import to_multi_gpu

num_classes = 10

# input image dimensions
img_rows, img_cols = 28, 28

batches = [1000,2000,3000,4000,5000]

epochs = [10,20,30,40,50,60,70,80,90,100]

# the data, shuffled and split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

#============ Multi-GPU ============
model = to_multi_gpu(model,n_gpus=2)
#===================================
model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adadelta(),
              metrics=['accuracy'])

tiemposIniciales = []
tiemposFinales = []
lotes = []
errores = []
epocas = []
precisiones = []
segunderos = []

for x in batches:
	for y in epochs:
		
		horaInicio = time.strftime("%H:%M:%S")
		fechaInicio = time.strftime("%d-%m-%Y")
		horaInicial = datetime.datetime.now()
		model.fit(x_train, y_train,
        	  batch_size=x,
         	  epochs=y,
                  verbose=1,
                  validation_data=(x_test, y_test))
	        
		score = model.evaluate(x_test, y_test, verbose=0)

		horaFin = time.strftime("%H:%M:%S")
		fechaFin = time.strftime("%d-%m-%Y")		
		horaFinal = datetime.datetime.now()
		diferencia = horaFinal - horaInicial
		aux = pd.Timedelta(diferencia)
		segundosDiferencia = aux.total_seconds() 
		segunderos.append(segundosDiferencia)
		print("total segundos",segundosDiferencia)
		lotes.append(x)
		epocas.append(y)
		tiemposIniciales.append(fechaInicio+" "+horaInicio)
		tiemposFinales.append(fechaFin+" "+horaFin)
		errores.append(score[0])
		precisiones.append(score[1])		                
 
          	print("Inicio: ", fechaInicio," ", horaInicio, " termino: ",fechaFin, " ", horaFin)
	        print('Test loss:', score[0])
	        print('Test accuracy:', score[1])


df = pd.DataFrame({ 'Epocas'        : epocas,
		    'Batche Size'   : lotes,
		    'segundos'      : segunderos,			
		    'Tiempo Inicial': tiemposIniciales,
		    'Tiempos Final' : tiemposFinales,
		    'error'         : errores,
		    'precisionn'    : precisiones } )

writer = pd.ExcelWriter('CPU.xlsx', engine='xlsxwriter')

df.to_excel(writer, sheet_name='entrenamiento')

workbook = writer.book
worksheet = writer.sheets['entrenamiento']

writer.save()


