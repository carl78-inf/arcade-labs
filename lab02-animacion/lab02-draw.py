import arcade

WIDTH = 800
HEIGHT = 600

arcade.open_window(WIDTH, HEIGHT, "Example")
arcade.set_background_color(arcade.color.SKY_BLUE)
arcade.start_render()



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
arcade.draw_circle_outline(center_x=375, center_y=280, radius=10, color=arcade.color.BLACK, border_width=5)

arcade.finish_render()

arcade.run()
