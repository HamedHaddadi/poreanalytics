
from libc.stdlib cimport rand
from math import sqrt 
from libc.limits cimport INT_MAX
from libc.float cimport FLT_MAX   
# ############################ #
# . List of useful objects     #
# ############################ #

#. Circle object
cdef class Circle:
    
    cdef:
        public float x, y, radius, vx, vy, h 
        public int event_flag 
        tuple _attrs
    
    def __cinit__(self, float x, float y , float vx, float vy, float radius, float h):
        """
        inflation h is the inflation factor
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = vx
        self.vy = vy
        self.event_flag = 0
        self.h = h 
        self._attrs = ()
    
    property attrs:
        def __get__(self):
            self._attrs = (self.x, self.y, self.radius, self.vx, self.vy, self.event_flag)
            return self._attrs
    
    def __sub__(C1, C2):
        if isinstance(C1, Circle) and isinstance(C2, Circle):
            return (<Circle> C1).x - (<Circle> C2).x, (<Circle> C1).y - (<Circle> C2).y,\
             (<Circle> C1).vx - (<Circle> C2).vx, (<Circle> C1).vy - (<Circle> C2).vy
    
    def update_circle(self, float dt):
        self.x += self.vx*dt 
        self.y += self.vy*dt 
        self.radius += self.h*dt  


# ############################ #
# . Packing Algorithms         #
# ############################ #

#. Lubachevsky-Stillinger in 2D
cdef class LubaStill2D:
    """
    Event-driven Lubachevsly-Stillinger random pack 
    generator 
    """
    cdef:
        int max_events
        int num_objects
        int num_seeds
        int box
        float _max_x, _max_y, _min_x, _min_y 
        public float radius_i, h, tol
        list _objects

    def __cinit__(self, int max_events, int num_seeds, int box, float h, float radius_i):
        self.max_events = max_events 
        self.num_seeds = num_seeds 
        self.box = box 
        self.h = h 
        self.radius_i = radius_i
        self.tol = 0.01
        self._objects = []
    
    property objects:
        def __get__(self):
            return self._objects

    property max_x:
        def __get__(self):
            cdef list _x = [object.x for object in self._objects]
            self._max_x = max(_x)
            return self._max_x 

    property min_x:
        def __get__(self):
            cdef list _x = [object.x for object in self._objects]
            self._min_x = min(_x)
            return self._min_x 

    property min_y:
        def __get__(self):
            cdef list _y = [object.y for object in self._objects]
            self._min_y = min(_y)
            return self._min_y

    property max_y:
        def __get__(self):
            cdef list _y = [object.y for object in self._objects]
            self._max_y = max(_y)
            return self._max_y  

    cpdef dispense(self):
        
        cdef float dl 
        cdef float x, y, vx, vy
        cdef int count
        cdef int i,j 
        cdef float num 
        self._objects.clear()

        dl = <float> self.box / sqrt(self.num_seeds)
        for i in range(<int> sqrt(self.num_seeds)):
            x = 2*self.radius_i + i*dl + 0.05*(-1 + 2*(<float> rand()/ <float> INT_MAX))
            for j in range(<int> sqrt(self.num_seeds)):
                vx = -1 + 2*(<float> rand()/ <float> INT_MAX)
                vy = -1 + 2*(<float> rand()/ <float> INT_MAX)
                y = 2*self.radius_i + j*dl + 0.05*(-1 + 2*(<float> rand()/ <float> INT_MAX))
                self._objects.append(Circle(x, y, vx, vy, self.radius_i, self.h)) 
        self.num_objects = len(self._objects)
    
    # #### Main loop and associated methods #### #
    cdef particle_collision_time(self):
        cdef:
            float rx, ry, vrx, vry
            int obj1, obj2 
            float a, b, c
            float t_col, tp_col 
            bint break_flag = False 

        tp_col = FLT_MAX
        for obj1 in range(self.num_objects - 1):
            for obj2 in range(obj1 + 1, self.num_objects):    
                rx, ry, vrx, vry = self._objects[obj2] - self._objects[obj1]
                a = vrx*vrx + vry*vry - 4.0*self.h*self.h 
                b = 2*rx*vrx + 2*ry*vry - 8*self.h*self._objects[obj1].radius 
                c = rx*rx + ry*ry - (2*self._objects[obj1].radius)*(2*self._objects[obj1].radius)
                
                if (b*b - 4*a*c >= 0.0) and (b <= 0.0):
                    t_col = (-1*b - sqrt(b*b - 4*a*c))/(2*a)
                elif ((b*b - 4*a*c < 0) and (b > 0.0)):
                    t_col = FLT_MAX 
                elif ((c < 0.0) and (abs(c) >= self.tol)):
                    break_flag = True 
                if break_flag: break 

                if t_col < tp_col:
                    tp_col = t_col 
        return tp_col, break_flag, obj1, obj2 
    
    # useful methods
    def right_wall(self, int n_obj):
        cdef float r = self.box - self._objects[n_obj].x 
        cdef float v = -self._objects[n_obj].vx
        return r, v 

    def left_wall(self, int n_obj):
        cdef float r = -self._objects[n_obj].x  
        cdef float v = -self._objects[n_obj].vx 
        return r, v 
    
    def top_wall(self, int n_obj):
        cdef float r = self.box - self._objects[n_obj].y  
        cdef float v = -self._objects[n_obj].vy 
        return r, v 
    
    def bottom_wall(self, int n_obj):
        cdef float r = -self._objects[n_obj].y 
        cdef float v = -self._objects[n_obj].vy 
        return r, v
    
    cdef wall_collision_time(self):

        cdef:
            float rx, ry, vrx, vry
            float a, b, c 
            # max collision time
            float tw_col = FLT_MAX
            # the object id which collides with the wall 
            int obj_id
            str wall_id 
            int n_obj, count
            str wall_key
            dict wall_tcol = {}
            tuple wall_collision             
            dict wall_map = {'top': self.top_wall, 
                                'bottom': self.bottom_wall,  
                                    'left': self.left_wall, 
                                     'right': self.right_wall}
 
        for n_obj in range(self.num_objects): 
            wall_tcol = {key:FLT_MAX for key in wall_map.keys()}
            for wall_key in wall_map.keys():
                r, vr = wall_map[wall_key](n_obj)
                a = vr*vr - self.h*self.h 
                b = 2*r*vr - 2.0*self.h*(self._objects[n_obj].radius + self.tol)
                c = r*r - (self._objects[n_obj].radius + self.tol)*(self._objects[n_obj].radius + self.tol)
                if (c > 0.0) and (b*b - 4.0*a*c >= 0.0) and (b <= 0):
                    wall_tcol[wall_key] = (-b - sqrt(b*b - 4.0*a*c))/2*a 
            wall_tcol = {key:val for key, val in sorted(wall_tcol.items(), key = lambda item: item[1])}
            wall_collision = list(wall_tcol.items())[0]
            if wall_collision[1] < tw_col:
                tw_col = wall_collision[1]
            obj_id = n_obj 
            wall_id = wall_collision[0]                

        return tw_col, wall_id, obj_id

    # evolve the particles for delta_t   
    cdef evolve(self, delta_t):
        cdef int n_obj
        for n_obj in range(self.num_objects):
            self._objects[n_obj].x += self._objects[n_obj].vx*delta_t 
            self._objects[n_obj].y += self._objects[n_obj].vy*delta_t 
            self._objects[n_obj].radius += self.h*delta_t 
    
    # collisions: wall or particle
    def collide_particle(self, int obj1, int obj2):
        print('collision with particles')
        cdef float rx, ry, rd, vrx, vry, prx, pry, vr
        rx, ry, vrx, vry = self._objects[obj2] - self._objects[obj1]
        rd = sqrt(rx*rx + ry*ry)
        vr = vrx*rx/rd + vry*ry/rd 
        prx = vr*rx/rd + 2.0*self.h*rx/rd 
        pry = vr*ry/rd + 2.0*self.h*ry/rd 
        self._objects[obj1].vx -= prx 
        self._objects[obj1].vy -= pry 
        self._objects[obj2].vx += prx 
        self._objects[obj2].vy += pry 
    
    # wall collision
    def collide_top(self, int obj_id):
        self._objects[obj_id].vy = -1*(self._objects[obj_id].vy)
    def collide_bottom(self, int obj_id):
        self._objects[obj_id].vy = -1*(self._objects[obj_id].vy)
    def collide_left(self, int obj_id):
        self._objects[obj_id].vx = -1*(self._objects[obj_id].vx)
    def collide_right(self, int obj_id):
        self._objects[obj_id].vx = -1*(self._objects[obj_id].vx)
    
    def collide_wall(self, str wall_id, int obj_id):
        print('collision with walls ')
        {'top': self.collide_top, 
            'bottom': self.collide_bottom, 
                'left': self.collide_left, 
                    'right': self.collide_right}[wall_id](obj_id)
        
    # ## main callable ## #
    def __call__(self):
        cdef:
            int n_event
            int obj1, obj2, obj_id 
            float delta_t, tp_col, tw_col 
            str wall_id 
            bint wall_collision = False
            bint break_flag = False  
        
        self.dispense()
             
        # for total number of events ...
        for n_event in range(self.max_events):
            wall_collision = False
            print('running ', n_event, 'of ', self.max_events)
            print('now the radius is = ', self._objects[0].radius)
            # loop over all pairs
            t_col = FLT_MAX 
            tp_col, break_flag, obj1, obj2 = self.particle_collision_time()
            # overlap error break 
          #  print('break_flag is ', break_flag)
            # if break_flag: break 
            tw_col, wall_id, obj_id = self.wall_collision_time()

            if (tp_col < tw_col):
                delta_t = tp_col 
                print('PARTICLE-PARTICLE colliding objects are ', obj1, obj2)
                print('velocity of PP colliding objects BEFORE is ', self._objects[obj1].vx, self._objects[obj2].vx, 
                        self._objects[obj1].vy, self._objects[obj2].vy)
            else:
                delta_t = tw_col 
                print('WALL colliding object id is = ', obj_id)
                print('velocity of wall colliding object BEFORE is ', self._objects[obj_id].vx, self._objects[obj_id].vy)

                wall_collision = True 
            
            self.evolve(delta_t)
            
            if wall_collision:
                self.collide_wall(wall_id, obj_id)
                print('velocity of wall colliding object AFTER is ', self._objects[obj_id].vx, self._objects[obj_id].vy)
            else:
                self.collide_particle(obj1, obj2)
                print('velocity of PP colliding objects AFTER is ', self._objects[obj1].vx, self._objects[obj2].vx, 
                        self._objects[obj1].vy, self._objects[obj2].vy)                

                  
        