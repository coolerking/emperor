# -*- coding: utf-8 -*-
import numpy as np
import donkeycar as dk
class ImageChecker:
    def __init__(self):
        pass
    def run(self, image):
        print('***** ImageChecker *****')
        #print(image)
        #print(type(image))
        if type(image) is np.ndarray:
            #print(image.shape)
            bin = dk.util.img.arr_to_binary(image)
            #print(bin)
            #print(type(bin))
            #print(len(bin))
            print(image.dtype)
            # PiCamera -> np.ndarray型式 (120,160,3)
            image2 = dk.util.img.binary_to_img(bin)
            print('*** image2')
            print(image2)
            print(type(image2))
            print(image == image2)

        print('************************')

