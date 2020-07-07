import bpy
import math
import numpy as np

def get_grease_pencil(gpencil_obj_name='GPencil') -> bpy.types.GreasePencil:
    """
    Return the grease-pencil object with the given name. Initialize one if not already present.
    :param gpencil_obj_name: name/key of the grease pencil object in the scene
    """

    # If not present already, create grease pencil object
    if gpencil_obj_name not in bpy.context.scene.objects:
        bpy.ops.object.gpencil_add(location=(0, 0, 0), type='EMPTY')
        # rename grease pencil
        bpy.context.scene.objects[-1].name = gpencil_obj_name

    # Get grease pencil object
    gpencil = bpy.context.scene.objects[gpencil_obj_name]

    return gpencil


def get_grease_pencil_layer(gpencil: bpy.types.GreasePencil, gpencil_layer_name='GP_Layer',
                            clear_layer=False) -> bpy.types.GPencilLayer:
    """
    Return the grease-pencil layer with the given name. Create one if not already present.
    :param gpencil: grease-pencil object for the layer data
    :param gpencil_layer_name: name/key of the grease pencil layer
    :param clear_layer: whether to clear all previous layer data
    """

    # Get grease pencil layer or create one if none exists
    if gpencil.data.layers and gpencil_layer_name in gpencil.data.layers:
        gpencil_layer = gpencil.data.layers[gpencil_layer_name]
    else:
        gpencil_layer = gpencil.data.layers.new(gpencil_layer_name, set_active=True)

    if clear_layer:
        gpencil_layer.clear()  # clear all previous layer data

    # bpy.ops.gpencil.paintmode_toggle()  # need to trigger otherwise there is no frame

    return gpencil_layer


# Util for default behavior merging previous two methods
def init_grease_pencil(gpencil_obj_name='GPencil', gpencil_layer_name='GP_Layer',
                       clear_layer=True) -> bpy.types.GPencilLayer:
    gpencil = get_grease_pencil(gpencil_obj_name)
    gpencil_layer = get_grease_pencil_layer(gpencil, gpencil_layer_name, clear_layer=clear_layer)
    return gpencil_layer

def draw_line(gp_frame, p0: tuple, p1: tuple):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing

    # Define stroke geometry
    gp_stroke.points.add(count=2)
    gp_stroke.points[0].co = p0
    gp_stroke.points[1].co = p1
    return gp_stroke

def draw_circle(gp_frame, center: tuple, radius: float, segments: int):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    gp_stroke.draw_cyclic = True        # closes the stroke
    
    #gp_stroke.line_width = 100
    #gp_stroke.material_index = 1

    # Define stroke geometry
    angle = 2*math.pi/segments  # angle in radians
    gp_stroke.points.add(count=segments)
    for i in range(segments):
        x = center[0] + radius*math.cos(angle*i)
        y = center[1] + radius*math.sin(angle*i)
        z = center[2]
        gp_stroke.points[i].co = (x, y, z)

    return gp_stroke

def rotate_stroke(stroke, angle, axis='z'):
    # Define rotation matrix based on axis
    if axis.lower() == 'x':
        transform_matrix = np.array([[1, 0, 0],
                                     [0, math.cos(angle), -math.sin(angle)],
                                     [0, math.sin(angle), math.cos(angle)]])
    elif axis.lower() == 'y':
        transform_matrix = np.array([[math.cos(angle), 0, -math.sin(angle)],
                                     [0, 1, 0],
                                     [math.sin(angle), 0, math.cos(angle)]])
    # default on z
    else:
        transform_matrix = np.array([[cos(angle), -math.sin(angle), 0],
                                     [sin(angle), math.cos(angle), 0],
                                     [0, 0, 1]])

    # Apply rotation matrix to each point
    for i, p in enumerate(stroke.points):
        p.co = transform_matrix @ np.array(p.co).reshape(3, 1)

def draw_sphere(gp_frame, center: tuple, radius: int, circles: int):
    angle = math.pi / circles
    for i in range(circles):
        circle = draw_circle(gp_frame, center, radius, 32)
        rotate_stroke(circle, angle*i, 'x')
        print(angle * i)

gp_layer = init_grease_pencil()

sigma = 10
beta = 8/3
ro = 28
#init coords
x = 1 
y = 1
z = 1
dt = 0.01
prevpos = [(x,y,z),]



def lorrentz(x,y,z,dt):
    dx = (sigma*(y-x))*dt
    dy = (x*(ro - z) - y)*dt
    dz = (x*y - beta*z)*dt
    return (dx,dy,dz)

for frama in range(0,1000):
    gp_frame = gp_layer.frames.new(frama)
    dxyz = lorrentz(x,y,z,dt)
    newcoords = (x+dxyz[0],y+dxyz[1],z+dxyz[2])
    if(np.linalg.norm(np.array((x,y,z)) - np.array(newcoords)) < 0.1):
        pass
    else:
        prevpos.append(newcoords)
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    gp_stroke.line_width = 200
    gp_stroke.material_index = 1
    
    for cpos in range(1,len(prevpos)-1):
        draw_line(gp_frame,prevpos[cpos-1],prevpos[cpos])
        
    x+=dxyz[0]
    y+=dxyz[1]
    z+=dxyz[2]
    