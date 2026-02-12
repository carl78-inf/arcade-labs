import arcade

WIDTH = 800
HEIGHT = 600

arcade.open_window(WIDTH, HEIGHT, "Example")
arcade.set_background_color(arcade.color.SKY_BLUE)
arcade.start_render()

# --- Draw the barn ---

# Barn cement base
arcade.draw_lrbt_rectangle_filled(30, 350, 170, 210, arcade.color.BISQUE)

# Bottom half
arcade.draw_lrbt_rectangle_filled(30, 350, 210, 350, arcade.color.BROWN)

# Left-bottom window
arcade.draw_rect_filled(arcade.XYWH(70, 260, 30, 40), arcade.color.BONE)
arcade.draw_rect_filled(arcade.XYWH(70, 260, 20, 30), arcade.color.BLACK)

# Right-bottom window
arcade.draw_rect_filled(arcade.XYWH(310, 260, 30, 40), arcade.color.BONE)
arcade.draw_rect_filled(arcade.XYWH(310, 260, 20, 30), arcade.color.BLACK)

# Barn door
arcade.draw_rect_filled(arcade.XYWH(190, 230, 100, 100), arcade.color.BLACK_BEAN)

# Rail above the door
arcade.draw_rect_filled(arcade.XYWH(190, 280, 180, 5), arcade.color.BONE)

# Draw second level of barn
arcade.draw_polygon_filled([[20, 350],
                            [100, 470],
                            [280, 470],
                            [360, 340]],
                            arcade.color.BROWN)

# Draw loft of barn
arcade.draw_triangle_filled(100, 470, 280, 470, 190, 500, arcade.color.BROWN)

# Left-top window
arcade.draw_rect_filled(arcade.XYWH(130, 440, 30, 40), arcade.color.BONE)
arcade.draw_rect_filled(arcade.XYWH(130, 440, 20, 30), arcade.color.BLACK)

# Right-top window
arcade.draw_rect_filled(arcade.XYWH(250, 440, 30, 40), arcade.color.BONE)
arcade.draw_rect_filled(arcade.XYWH(250, 440, 20, 30), arcade.color.BLACK)

# Draw 2nd level door
arcade.draw_rect_outline(arcade.XYWH(190, 310, 30, 60), arcade.color.BONE, 5)
#---------------------------------------------------------------------------------------------------------
"""
arcade.draw_lbwh_rectangle_filled(left=0, bottom=0, width=800, height=200, color=arcade.color.GREEN)
arcade.draw_circle_filled(center_x=400, center_y=300, radius=100, color=arcade.color.WHITE)
arcade.draw_circle_outline(center_x=400, center_y=300, radius=100, color=arcade.color.BLACK, border_width=10)

arcade.draw_lbwh_rectangle_filled(left=340, bottom=195, width=30, height=50, color=arcade.color.WHITE)
arcade.draw_lbwh_rectangle_outline(left=340, bottom=195, width=30, height=50, color=arcade.color.BLACK, border_width=10)

arcade.draw_lbwh_rectangle_filled(left=430, bottom=195, width=30, height=50, color=arcade.color.WHITE)
arcade.draw_lbwh_rectangle_outline(left=430, bottom=195, width=30, height=50, color=arcade.color.BLACK, border_width=10)

#Manchas
arcade.draw_circle_filled(center_x=327, center_y=330, radius=20, color=arcade.color.BLACK)
arcade.draw_circle_filled(center_x=478, center_y=270, radius=15, color=arcade.color.BLACK)

arcade.draw_ellipse_filled(center_x=365, center_y=345, width=50, height=30, color=arcade.color.WHITE, tilt_angle=35)
arcade.draw_ellipse_outline(center_x=365, center_y=345, width=50, height=30, color=arcade.color.BLACK, tilt_angle=35, border_width=10)

arcade.draw_ellipse_filled(center_x=435, center_y=345, width=50, height=30, color=arcade.color.WHITE, tilt_angle=-35)
arcade.draw_ellipse_outline(center_x=435, center_y=345, width=50, height=30, color=arcade.color.BLACK, tilt_angle=-35, border_width=10)

#Cara
arcade.draw_arc_filled(center_x=400, center_y=280, width=100, height=140, color=arcade.color.WHITE, start_angle=0, end_angle=180)
arcade.draw_arc_outline(center_x=400, center_y=280, width=100, height=140, color=arcade.color.BLACK, start_angle=0, end_angle=180, border_width=20)
#Boca
arcade.draw_ellipse_filled(center_x=400, center_y=280, width=130, height=50, color=arcade.color.PINK)
arcade.draw_ellipse_outline(center_x=400, center_y=280, width=130, height=50, color=arcade.color.BLACK, border_width=10)

arcade.draw_circle_filled(center_x=385, center_y=320, radius=6, color=arcade.color.BLACK)
arcade.draw_circle_filled(center_x=415, center_y=320, radius=6, color=arcade.color.BLACK)

arcade.draw_circle_outline(center_x=425, center_y=280, radius=10, color=arcade.color.BLACK, border_width=5)
arcade.draw_circle_outline(center_x=375, center_y=280, radius=10, color=arcade.color.BLACK, border_width=5)"""

#-----------------------------------------------------------------------------------------------------------------
def dibujar_vaca(x: int, y: int, escala: float)->None:
    arcade.draw_circle_filled(center_x=x, center_y=y, radius=100*escala, color=arcade.color.WHITE)
    arcade.draw_circle_outline(center_x=x, center_y=y, radius=100*escala, color=arcade.color.BLACK, border_width=10*escala)

    arcade.draw_lbwh_rectangle_filled(left=x-60*escala, bottom=y-105*escala, width=30*escala, height=50*escala, color=arcade.color.WHITE)
    arcade.draw_lbwh_rectangle_outline(left=x-60*escala, bottom=y-105*escala, width=30*escala, height=50*escala, color=arcade.color.BLACK, border_width=10*escala)

    arcade.draw_lbwh_rectangle_filled(left=x+30*escala, bottom=y-105*escala, width=30*escala, height=50*escala, color=arcade.color.WHITE)
    arcade.draw_lbwh_rectangle_outline(left=x+30*escala, bottom=y-105*escala, width=30*escala, height=50*escala, color=arcade.color.BLACK, border_width=10*escala)
    
    arcade.draw_circle_filled(center_x=x-73*escala, center_y=y+30*escala, radius=20*escala, color=arcade.color.BLACK)
    arcade.draw_circle_filled(center_x=x+78*escala, center_y=y-30*escala, radius=15*escala, color=arcade.color.BLACK)

    arcade.draw_ellipse_filled(center_x=x-35*escala, center_y=y+45*escala, width=50*escala, height=30*escala, color=arcade.color.WHITE, tilt_angle=35)
    arcade.draw_ellipse_outline(center_x=x-35*escala, center_y=y+45*escala, width=50*escala, height=30*escala, color=arcade.color.BLACK, tilt_angle=35, border_width=10*escala)

    arcade.draw_ellipse_filled(center_x=x+35*escala, center_y=y+45*escala, width=50*escala, height=30*escala, color=arcade.color.WHITE, tilt_angle=-35)
    arcade.draw_ellipse_outline(center_x=x+35*escala, center_y=y+45*escala, width=50*escala, height=30*escala, color=arcade.color.BLACK, tilt_angle=-35, border_width=10*escala)

    arcade.draw_arc_filled(center_x=x, center_y=y-20*escala, width=100*escala, height=140*escala, color=arcade.color.WHITE, start_angle=0, end_angle=180)
    arcade.draw_arc_outline(center_x=x, center_y=y-20*escala, width=100*escala, height=140*escala, color=arcade.color.BLACK, start_angle=0, end_angle=180, border_width=20*escala)

    arcade.draw_ellipse_filled(center_x=x, center_y=y-20*escala, width=130*escala, height=50*escala, color=arcade.color.PINK)
    arcade.draw_ellipse_outline(center_x=x, center_y=y-20*escala, width=130*escala, height=50*escala, color=arcade.color.BLACK, border_width=10*escala)

    arcade.draw_circle_filled(center_x=x-15*escala, center_y=y+20*escala, radius=6*escala, color=arcade.color.BLACK)
    arcade.draw_circle_filled(center_x=x+15*escala, center_y=y+20*escala, radius=6*escala, color=arcade.color.BLACK)

    arcade.draw_circle_outline(center_x=x+25*escala, center_y=y-20*escala, radius=10*escala, color=arcade.color.BLACK, border_width=5*escala)
    arcade.draw_circle_outline(center_x=x-25*escala, center_y=y-20*escala, radius=10*escala, color=arcade.color.BLACK, border_width=5*escala)


dibujar_vaca(500,200,0.5)

#-----------------------------------------------------------------------------------------------------------------





arcade.finish_render()

arcade.run()
