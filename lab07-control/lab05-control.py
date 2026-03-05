import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

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

class Cow:
    def __init__(self, pos_x, pos_y, scale):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.scale = scale
    
    def draw(self):
        dibujar_vaca(self.pos_x, self.pos_y, self.scale)


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.cow = Cow(400, 300, 1)
        self.set_mouse_visible(False)
    
    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, 800, 0, 200, arcade.color.BITTER_LIME)
        self.cow.draw()
    
    def on_update(self, delta_time):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        self.cow.pos_x = x
        self.cow.pos_y = y
    
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.cow.scale += 0.1
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.cow.scale -= 0.1

def main():
    window = MyGame()
    arcade.run()


main()