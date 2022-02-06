# ############################### #
#       Image Reader              #
# ############################### #

import numpy as np
import pandas as pd
from os import path, makedirs, getcwd, listdir
from natsort import natsorted 
from PIL import Image, ImageFilter 
from datetime import date
import argparse
import sys
from PIL.ImageFilter import (SMOOTH)

class ImageReader:
    """
    generating input information from stack of images, 
    or collection of image files
    """
    def __init__(self, stack_array, file_path):
        self.stack_array = stack_array
        save_dir = path.join(file_path, 'PoreNet_Inputs_' + date.today().strftime('%Y-%m-%d'))
        if not path.exists(save_dir):
            self.save_dir = makedirs(save_dir) 
        else:
            self.save_dir = save_dir
    
    @staticmethod 
    def _trim_image_size(stack_array, min, max):
        return stack_array[min:max, min:max, :]
    
    @staticmethod 
    def _trim_stack_size(stack_array, min, max):
        return stack_array[:,:,min:max]
    
    def trim_images(self, direction = 'plane', min = None, max = None):
        self.stack_array = {'plane': ImageReader._trim_image_size, 
                                'stack': ImageReader._trim_stack_size}[direction](self.stack_array, min, max)
    
    @staticmethod 
    def _to_df(slice_array):
        slice_df = pd.DataFrame(columns = ['x','y'])
        index = np.where(slice_array == 1)
        slice_df['x'] = index[0]
        slice_df['y'] = index[1]
        return slice_df 

    def slice_to_csv(self, direction = 'z', sep =' '):
        width, height, stack = self.stack_array.shape
        axs_max = {'x': width, 'y': height, 'z': stack}[direction]
        axs_lin = np.arange(0, axs_max)

        for count, ax_lim in enumerate(zip(axs_lin[:-1], axs_lin[1:])):
            axs_slice = {'z':(slice(0, width), slice(0, height), slice(ax_lim[0], ax_lim[1])) ,
                            'x':(slice(ax_lim[0], ax_lim[1]), slice(0, height), slice(0, stack)) ,
                                'y':(slice(0, width), slice(ax_lim[0], ax_lim[1]), slice(0, stack))}[direction]
            slice_df = ImageReader._to_df(np.squeeze(self.stack_array[axs_slice]))
            columns = [col for col in ['x','y','z'] if col != direction]
            slice_df.columns = columns 
            slice_df.to_csv(path.join(self.save_dir, 'input_image_' + str(count) + '.csv'), sep=sep, header=True, index = False, float_format = '%d')
            
    @classmethod 
    def from_image_stack(cls, stack_path = None, stack_name = None):
        stack = Image.open(path.join(stack_path, stack_name))
        w, h,_ = np.shape(stack)
        stack_array = np.zeros((w, h, stack.n_frames))
        for frame in range(stack.n_frames):
            stack.seek(frame)
            stack.filter(ImageFilter.MaxFilter(5))
            r,_,_ = stack.split()
            stack_array[:,:,frame] = np.array(r)
        index = np.where(stack_array > 0)
        stack_array[index] = 1
        return cls(stack_array, stack_path)

    @classmethod 
    def from_image_files(cls, file_path = None, stem_name = None):
        image_files = natsorted([_file for _file in listdir(file_path) if stem_name in _file], key = lambda y: y.lower())
        image_array = []
        for _img in image_files:
            image = Image.open(path.join(file_path, _img))
            img,_,_ = image.split()
            image_array.append(np.array(img))
        image_array = np.array(image_array)
        image_array = np.swapaxes(image_array, 0, 2)
        index = np.where(image_array > 0)
        image_array[index] = 1
        return cls(image_array, file_path)

