

class Circle:
    def __init__(self, x, y, radius, vx, vy):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = vx
        self.vy = vy  
    
    def __eq__(self, other):
        return (self.x == other.x) and (self.y == other.y) and (self.z == other.z) and (self.radius == other.radius)
    
    def __sub__(self, other):
        return self.x - other.x, self.y - other.y, self.vx - other.vx, self.vy - other.vy 
    
    



