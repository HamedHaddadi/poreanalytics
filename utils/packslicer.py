
# ###################### #
# Author: Hamed Haddadi  #
# ##################### #

import numpy as np
import pandas as pd
from os import path, makedirs, getcwd
import argparse
import sys

class PackSlicer:
    """
    Utility class to read sphere packs => sphere packs are artificially generated
        either by Lattice or by LubaStilin   
    
    => to run with default arguments from a linux terminal:
        python3 packslicer.py -filename <pack filename> 
    => to run using the 'ini' file: 
        python3 packslice.py <input>.ini
        use the instructions in the ini file to change inputs
    => stores the image stacks in a directory with a same file name + 'PoreNet_Inputs'
    """ 

    def __init__(self, filename = None, filepath = None,  voxel = None, call_args = None):
        
        if filename == None:
            print('enter a filename; ...')
            sys.exit(0)

        self.output_name = filename.split('.')[0]
        self.save_path = path.join(filepath, self.output_name + '_PoreNet_Inputs')
        print('the save path is ', self.save_path)
        if not path.isdir(self.save_path):
            makedirs(self.save_path)
        self.voxel = voxel
        data_file = path.join(filepath, filename)
        file_info = open(data_file).read().splitlines()[0:2]
        self.voxel_size = float(file_info[0].split(' ')[1])
        self.x, self.y, self.z = tuple([int(val) for val in file_info[1].split(' ')[1:]])
        self.all_data = np.loadtxt(data_file, dtype=int, skiprows = 2).reshape(self.x, self.y, self.z)
        if call_args:
            self.call_args = call_args
        else:
            self.call_args = {}
    
    _get_tuple = staticmethod(lambda line: tuple([elem for elem in line.split('=')[1].split(' ')]))
    _get_val = staticmethod(lambda line: line.split('=')[1])

    @classmethod
    def from_ini_file(cls, filename, filepath = None):
        input_file = open(path.join(filepath, filename)).read().splitlines()
        input_args = {'filename':None, 'filepath':getcwd(), 'voxel':'solid', 'output':'OutPuts'}
        call_args = {'domain_begin': None, 'domain_range':None,
             'slice':'plane', 'direction':'x', 'num_slice': None}
        for line in input_file:
            if '#' in line and line.strip() !='': continue
            else:
                key = line.split('=')[0]
                if key in input_args.keys():
                    input_args[key] = line.split('=')[1]
                elif key in call_args.keys():
                    print(key)
                    call_args[key] = {'domain_begin':PackSlicer._get_tuple,
                                        'domain_range':PackSlicer._get_tuple,
                                        'direction':PackSlicer._get_val, 
                                        'slice':PackSlicer._get_val, 
                                         'num_slice':PackSlicer._get_val}[key](line)       
        input_args.update(call_args)
        return cls(**input_args)

    def trim_data(self, domain_begin = None, domain_range = None):
        
        if domain_begin is None and domain_range is None:
            self.grid_x, self.grid_y, self.grid_z = self.x, self.y, self.z
            self.domain = self.all_data
        else:
            bx, by, bz = tuple(domain_begin)
            self.grid_x, self.grid_y, self.grid_z = tuple(domain_range)
            self.domain = self.all_data[bx:bx + self.grid_x, by: by + self.grid_y, bz:bz + self.grid_z]
    
    @staticmethod
    def _generate_from_numpy_array(domain, voxel):
        domain_frame = pd.DataFrame(columns = ['x','y','z'])
        index = {'solid':1, 'void': 0}[voxel]
        domain = np.where(domain == index)
        domain_frame['x'] = domain[0]
        domain_frame['y'] = domain[1]
        domain_frame['z'] = domain[2]
        return domain_frame
    
    @staticmethod
    def _to_csv(frame, outname, sep = ' ', voxel_size= 1):
        outname += '.csv'
        frame *= voxel_size
        frame.to_csv(outname, sep = sep, header=True, index=False, float_format = '%.9f')
    
    def plane_slice(self, thickness = 1, direction =  'x', dimension = 'voxel', output = 'csv', sep= ' '):
        ax = {'x':self.grid_x, 'y':self.grid_y, 'z':self.grid_z}[direction]
        ax_lin = np.arange(0, ax, thickness)
        voxel_size = {'voxel':1, 'real': self.voxel_size}[dimension]

        for count, ax_lim in enumerate(zip(ax_lin[:-1], ax_lin[1:])):
            ax_slice = {'x':(slice(ax_lim[0], ax_lim[1]), slice(0, self.grid_y), slice(0, self.grid_z)), 
                        'y': (slice(0, self.grid_x), slice(ax_lim[0], ax_lim[1]), slice(0, self.grid_z)),  
                        'z': (slice(0, self.grid_x), slice(0, self.grid_z), slice(ax_lim[0], ax_lim[1]))}[direction]
            out_columns = [col for col in ['x','y','z'] if direction not in col]
            slice_frame = PackSlicer._generate_from_numpy_array(self.all_data[ax_slice], self.voxel)[out_columns]
            if not slice_frame.empty:
                out_name = path.join(self.save_path, 'Slice_in_' + direction + '_' + str(count))
                {'csv': PackSlicer._to_csv}[output](slice_frame, out_name, sep = sep, voxel_size= voxel_size)


    def volume_slice(self, num_slice = 4, output='csv', dimension = 'voxel', sep=' '):
        voxel_size = {'voxel': 1, 'real': self.voxel_size}[dimension]
        x_lin = np.arange(0, self.grid_x, self.grid_x//num_slice)
        y_lin = np.arange(0, self.grid_y, self.grid_y//num_slice)
        z_lin = np.arange(0, self.grid_z, self.grid_z//num_slice)
        counter = 0
        for x_min, x_max in zip(x_lin[:-1], x_lin[1:]):
            for y_min, y_max in zip(y_lin[:-1], y_lin[1:]):
                for z_min, z_max in zip(z_lin[:-1], z_lin[1:]):
                    out_name = path.join(self.save_path, 'Volume_Slice_' + str(counter))
                    slice_frame = PackSlicer._generate_from_numpy_array(self.all_data[x_min:x_max, y_min:y_max, z_min:z_max], voxel_size)
                    {'csv': PackSlicer._to_csv}[output](slice_frame, out_name, sep = sep, voxel_size = voxel_size)
                    counter += 1
    
    def __call__(self, slice = 'plane', domain_begin = None, domain_range = None,
     direction = None, num_slice = None):

        if direction is None:
            direction = self.call_args.get('direction')
        if num_slice is None:
            num_slice = self.call_args.get('num_slice')


        domain_begin = self.call_args.get('domain_begin')
        domain_range = self.call_args.get('domain_range')
        direction = self.call_args.get('direction')
        num_slice = self.call_args.get('num_slice')

        self.trim_data(domain_begin, domain_range)
        if slice == 'plane':
            self.plane_slice(direction = direction)
        elif slice == 'volume':
            self.volume_slice(num_slice = num_slice)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'parse inputs from command line')
    parser.add_argument('-filename', nargs = '?', type=str, help='name of the input file', required = True)
    parser.add_argument('--filepath', nargs = '?', type=str, default='./', help='path to the input file')
    parser.add_argument('--voxel', nargs = '?', type=str, default='solid', help='voxel type: solid/void')
    parser.add_argument('--slice', nargs = '?', type=str, default = 'plane', help = 'type of data slicing')
    parser.add_argument('--direction', nargs = '?', type=str, help='direction of plane slicing')
    parser.add_argument('--num_slice', nargs = '?', type=int, default = 4,  help='number of volumetric or plane slice')
    parser.add_argument('--domain', nargs = '*', default = 'none')

    args = vars(parser.parse_args())
    if args['filename'][-4:] == '.ini':
        print('reading inputs from .ini file')
        reader = PackSlicer.from_ini_file(args['filename'], filepath = args.get('filepath'))
        reader()
    
    else:
        inputs = {key:val for key,val in args.items() if key not in ['slice', 'domain', 'direction', 'num_slice']}
        call_inputs = {}
        if args['domain'] == 'none':
            call_inputs.update({'domain_begin': None, 'domain_range': None,
                'slice':args['slice']})
        elif len(args['domain']) == 6:
            call_inputs.update({'domain_begin':args['domain'][:3],
                'domain_range':args['domain'][3:], 'slice':args['slice']})
        else:
            print('domain information must be a len = 6 list or none')
            sys.exit(-1)
    
        if args.get('direction') != None:
            call_inputs['direction'] = args['direction']
        if 'num_slice' in args.keys():
            call_inputs['num_slice'] = args['num_slice']
        reader = PackSlicer(call_args = call_inputs, **inputs)
        reader()




     
        

