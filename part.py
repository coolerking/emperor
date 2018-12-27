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
            image2 = dk.util.img.binary_to_img(image)
            image3 = dk.util.img.img_to_arr(image2)
            print('*** image3')
            print(image3)
            print(type(image3))
            print(image == image3)

        print('************************')

