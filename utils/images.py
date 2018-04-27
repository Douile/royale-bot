import math

def radial_gradient(draw,width,height,color_inner,color_outer): # will overite everything in image
    """Creates a radial gradient on an image. Might be slow"""
    alpha = False
    if len(color_inner) == 4 and len(color_outer) == 4:
        alpha = True
    for x in range(width):
        for y in range(height):
            dToE = math.sqrt((x -width/2) ** 2 + (y - height/2) ** 2)
            dToE = float(dToE) / (math.sqrt(2) * width/2)
            r = round(color_inner[0] * dToE + color_outer[0] * (1-dToE))
            g = round(color_inner[1] * dToE + color_outer[1] * (1-dToE))
            b = round(color_inner[2] * dToE + color_outer[2] * (1-dToE))
            if alpha:
                a = round(color_inner[3] * dToE + color_outer[3] * (1-dToE))
                color = (r,g,b,a)
            else:
                color = (r,g,b)
            draw.point((x,y),fill=color)
def darken(color,alpha):
    """Darkens a color to specified alpha"""
    return (color[0],color[1],color[2],alpha)
