import math
import pygame

def point_line_dist(px,py,x1,y1,x2,y2):
    A=px-x1
    B=py-y1
    C=x2-x1
    D=y2-y1
    dot=A*C+B*D
    len_sq=C*C+D*D
    param=-1
    if len_sq!=0:
        param=dot/len_sq
    if param<0:
        xx,yy=x1,y1
    elif param>1:
        xx,yy=x2,y2
    else:
        xx=x1+param*C
        yy=y1+param*D
    dx=px-xx
    dy=py-yy
    return math.hypot(dx,dy)

def draw_arrow(screen,x1,y1,x2,y2,color,width=2):
    pygame.draw.line(screen,color,(x1,y1),(x2,y2),width)
    angle=math.atan2(y2-y1,x2-x1)
    arr_size=10+width
    ang_l=angle+math.pi*0.75
    ang_r=angle-math.pi*0.75
    lx=x2+arr_size*math.cos(ang_l)
    ly=y2+arr_size*math.sin(ang_l)
    rx=x2+arr_size*math.cos(ang_r)
    ry=y2+arr_size*math.sin(ang_r)
    pygame.draw.polygon(screen,color,[(x2,y2),(lx,ly),(rx,ry)])

def draw_city_background(screen, width, height):
    # 먼저 기존처럼 그라디언트를 깔고,
    top_color=(150,200,255)
    bottom_color=(230,230,255)
    for y in range(height):
        alpha=y/float(height)
        r=int(top_color[0]*(1-alpha)+bottom_color[0]*alpha)
        g=int(top_color[1]*(1-alpha)+bottom_color[1]*alpha)
        b=int(top_color[2]*(1-alpha)+bottom_color[2]*alpha)
        pygame.draw.line(screen,(r,g,b),(0,y),(width,y))
