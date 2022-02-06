
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from collections import namedtuple
import argparse

Sphere = namedtuple('Sphere', ['x','y','z','radius'])

class Lattice:
    def __init__(self, bounds = [], radius = None, clearance = None):
        self.spheres = []
        self.res_x, self.res_y, self.res_z = tuple(bounds)
        self.radius = radius
        self.clear = clearance
        self.x_coords = np.arange(0, self.res_x, 2*self.radius)
        self.y_coords = np.arange(0, self.res_y, 2*self.radius)
        self.z_coords = np.arange(0, self.res_z, 2*self.radius)

        self.xx, self.yy, self.zz = np.meshgrid(np.linspace(0, self.res_x, self.res_x), np.linspace(0, self.res_y, self.res_y),
             np.linspace(0, self.res_z, self.res_z), indexing = 'ij')
        self.domain = np.zeros_like(self.xx)
        self.save_name = 'Lattice_Test_Pack_Res_' + str(self.res_x) + '_' + str(self.res_y) 
    
    def _dispense(self):
        self.spheres = [Sphere(x = x, y = y, z = z, radius = self.radius) for x in self.x_coords for y in self.y_coords for z in self.z_coords]
    
    def define_domain(self, clearance = None):
        if not clearance:
            clearance = self.clear
        self.save_name += '_Clearance_' + str(clearance) + '.txt'
        for sphere in self.spheres:
            solid_index = np.where(((self.xx - sphere.x)**2 + (self.yy - sphere.y)**2 + (self.zz - sphere.z)**2)**0.5 <= sphere.radius - clearance)
            self.domain[solid_index] = 1
    
    def print_domain(self):
        header = '1e-6 \n' + str(self.res_x) + ' ' + str(self.res_y) + ' ' +str(self.res_z)
        np.savetxt(self.save_name, self.domain.flatten(), delimiter =' ', fmt = '%d', header=header) 
    
    def plot_domain(self, domain = 0):
        """
        domain: 0 for void
                1 for solid
        """
        solid_index = np.where(self.domain == domain)
        fig = plt.figure(figsize=(8,8))
        axs = fig.add_subplot(111, projection = '3d')
        axs.scatter(self.xx[solid_index], self.yy[solid_index], self.zz[solid_index], c= self.domain[solid_index], cmap='jet')
        return fig, axs
    
    def __call__(self, output = 'print', domain = 1):
        self._dispense()
        self.define_domain()
        if 'plot' in output:
            self.plot_domain(domain)
        elif 'print' in output:
            self.print_domain()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='parse inputs for the lattice generator')
    parser.add_argument('-pack', nargs = '?', type = str, required = True, help='pack type: Lattice/LubaStilin')
    parser.add_argument('--radius', type=float, nargs = '?', help='radius of spheres for lattice pack')
    parser.add_argument('--clearance', type=float, nargs = '?', help = 'clearance between spheres for lattice pack')
    parser.add_argument('--output', nargs = '?', type=str, default='print', help='type of output')
    parser.add_argument('--domain', type=int, nargs = '?', default = 1, help = 'domain type: 0 for void; 1 for solid')
    parser.add_argument('-bounds', nargs = '+', type=int, required = True, help='three integers for domain size')
    args = parser.parse_args()

    print('requested a ', args.pack, 'sphere pack with radius ', args.radius, ' and ', args.clearance, 
        ' distance between particles in a ', args.domain, ' domain')

    if args.pack == 'Lattice':
        pack = Lattice(bounds = args.bounds, radius = args.radius, clearance = args.clearance)
        pack(output = args.output, domain = args.domain)
    else:
        raise NotImplementedError




    
        
    




