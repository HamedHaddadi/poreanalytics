
import numpy as np
import pandas as pd 
from os import path, makedirs, stat
from .. utils.tools import list_files, generate_RGB, GroupDict
from itertools import permutations
from functools import wraps 
from datetime import date 
import matplotlib 
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection 
import sys 

class PoreNetwork2D:
    """
    Processing pore networks for 2D planar data
        so plane_num is an important parameter here
    """
    def __init__(self, file_path = None, **kwargs):
        self.connection_groups = {}
        self.max_balls = []
        self.pores = [pd.read_csv(path.join(file_path, file_name), header=0, sep=',') for file_name in list_files(file_path, 'pores')]
        if len(self.pores) == 0:
            print('no pore file found, exit!')
            sys.exit(-1)
        self.connections = [np.loadtxt(path.join(file_path, file_name)) for file_name in list_files(file_path, 'connections') if stat(path.join(file_path, file_name)).st_size != 0]
        if len(self.connections) == 0:
            print('connection files are empty; exit')
            sys.exit(-1)
        self.max_balls.extend([pd.read_csv(path.join(file_path, file_), header=0, sep=',') for file_ in list_files(file_path, 'maxball')])
        print('the length of max balls is = ', len(self.max_balls))

        self.save_dir = path.join(file_path, 'Post_Processed_Data' + date.today().strftime('%b-%d-%Y'))
        if not path.isdir(self.save_dir):
            self.save_dir = makedirs(self.save_dir)
    
    @property
    def is_connection_group(self):
        if len(self.connection_groups.keys()) > 0:
            return True
        else:
            return False 
    
    def _generate_connection_groups(self, plane_num):
        connection_group = GroupDict()
        for count, ind in enumerate(permutations(range(self.connections[plane_num].shape[0]), 2)):
            if self.connections[plane_num][ind] == 1:
                connection_group[count] = set(ind)
        self.connection_groups[plane_num] = connection_group 
        
    def plot_pore_groups(self, plane_num = 0, figure = None, alpha = 0.5, maxballs = True):

        if self.is_connection_group or plane_num not in self.connection_groups.keys():
            self._generate_connection_groups(plane_num)
        
        group_colors = generate_RGB(len(self.connection_groups[plane_num].keys()))
        edge_group_colors = generate_RGB(len(self.connection_groups[plane_num].keys())) 
        connected_patches = [PatchCollection([Circle((self.pores[plane_num].loc[pore, 'x'], self.pores[plane_num].loc[pore, 'y']), radius = self.pores[plane_num].loc[pore, 'radius']) for pore in group], facecolor=group_colors[count], edgecolor=edge_group_colors[count], alpha = alpha, linewidth = 3) for count, group in \
            enumerate(self.connection_groups[plane_num])]
        
        connected_ids = []
        for group in self.connection_groups[plane_num]:
            connected_ids.extend([_id for _id in group])
        connected_ids = set(connected_ids)

        unconnected_ids = [_id for _id in self.pores[plane_num]['id'].tolist() if _id not in connected_ids]
        group_colors = generate_RGB(len(unconnected_ids))
        edge_group_colors = generate_RGB(len(unconnected_ids))
        unconnected_patches = [PatchCollection([Circle((self.pores[plane_num].loc[pore, 'x'], self.pores[plane_num].loc[pore, 'y']), radius = self.pores[plane_num].loc[pore, 'radius'])],
                        facecolor = group_colors[count], edgecolor = edge_group_colors[count], alpha = alpha, linewidth = 3) for count, pore in enumerate(unconnected_ids)]
        
        if figure is None:
            fig, axs = plt.subplots(figsize=(6,6))
        else:
            fig, axs = figure
        
        axs.set_xlim(self.pores[plane_num]['x'].min(), self.pores[plane_num]['x'].max())
        axs.set_ylim(self.pores[plane_num]['y'].min(), self.pores[plane_num]['y'].max())
        axs.set_xlabel('x')
        axs.set_ylabel('y')
        
        if maxballs:
            fig, axs = self.plot_maxballs(plane_num, figure = (fig, axs))

        for patch in connected_patches:
            axs.add_collection(patch)
        for patch in unconnected_patches:
            axs.add_collection(patch)

        return fig, axs

    # ### Plot pores without connection based grouping ### #
    def plot_pores(self, plane_num = 0, figure = None, alpha = 0.3, maxballs = False):
        
        return_fig = True
        if figure is None:
            fig, axs = plt.subplots(figsize=(6,6))
            return_fig = False
        else:
            fig, axs = figure 
        
        # correct using patch collections 
        patches = PatchCollection([Circle((self.pores[plane_num].loc[rank, 'x'], self.pores[plane_num].loc[rank, 'y']),\
             radius = self.pores[plane_num].loc[rank, 'radius']) for rank in self.pores[plane_num]['id'].tolist()], facecolor = 'r' , edgecolor = 'r',\
                  alpha = alpha, linewidth = 3)
        
        
        axs.set_xlim(self.pores[plane_num]['x'].min(), self.pores[plane_num]['x'].max())
        axs.set_ylim(self.pores[plane_num]['y'].min(), self.pores[plane_num]['y'].max())
        axs.set_xlabel('x')
        axs.set_ylabel('y')       

        axs.add_collection(patches)
        if maxballs:
            fig, axs = self.plot_maxballs(plane_num = plane_num, figure = (fig, axs))
        if return_fig:
            return fig, axs 
    
    # ### plot the maximal balls ### #
    def plot_maxballs(self, plane_num = 0, figure = None, colorby = 'radius', markersize = 50, return_fig = True, screen_by = None):
        """
        screen_by: radius or rank:
        input format: <key>_<value>
        """
        return_fig = True
        if figure is None:
            fig, axs = plt.subplots(figsize = (6,6))
            return_fig = False
        else:
            fig, axs = figure 
        
        if screen_by is not None:
            screen  = screen_by.split('_')
            screen_key, screen_val = screen[0], float(screen[1])
            maxballs = self.max_balls[plane_num][self.max_balls[plane_num][screen_key] <= screen_val]
        else:
            maxballs = self.max_balls[plane_num]
                
        cm = axs.scatter(maxballs['x'], maxballs['y'],
                        c = maxballs[colorby], s = markersize, cmap = 'jet')
        axs.set_xlim(maxballs['x'].min(), maxballs['x'].max())
        axs.set_ylim(maxballs['y'].min(), maxballs['y'].max())
        cm.set_clim(maxballs[colorby].min(), maxballs[colorby].max())
        plt.colorbar(cm)

        if return_fig:
            return fig, axs 
