# -*- coding: utf-8 -*-
import numpy as np
import donkeycar as dk
class ImageChecker:
    def __init__(self):
        pass
    def run(self, image):
        print('***** ImageChecker *****')
        print('*** image original')
        #print(image)
        print(type(image))
        if type(image) is np.ndarray:
            print(image.shape)
            print(image.dtype)
            bin = dk.util.img.arr_to_binary(image)
            print('*** bin')
            #print(bin)
            print(type(bin))
            #print(len(bin))
            # PiCamera -> np.ndarray型式 (120,160,3)
            print('*** img')
            img = dk.util.img.binary_to_img(bin)
            print(type(img))
            arr = dk.util.img.img_to_arr(img)
            print('*** arr')
            print(type(arr))
            print(arr.shape)
            print(arr.dtype)
            print(image == arr)
        print('************************')

