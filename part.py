# -*- coding: utf-8 -*-
import numpy as np
import donkeycar as dk
class ImageChecker:
    def __init__(self):
        pass
    def run(self, image):
        print(image)
        print(type(image))
        if type(image) is np.array:
            print(image.shape)

