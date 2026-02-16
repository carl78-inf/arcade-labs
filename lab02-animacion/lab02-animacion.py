import arcade
import math

contador = 0

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

class MiJuego(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Mi Juego")
        arcade.set_background_color(arcade.color.AIR_SUPERIORITY_BLUE)

        self.contador = 0

        self.pos_x = 0
        self.pos_y = 0
        self.escala = 0
    
    def on_draw(self):
        self.clear()
        if self.pos_x > 800: 
            self.pos_x = 0
        self.pos_x += 1
        self.contador += 0.2
        self.pos_y = math.sin(self.contador + 1) * 100 + 300
        self.escala = math.sin(self.contador / 10 + 1) + 1.1
        arcade.draw_lrbt_rectangle_filled(0, 800, 0, 200, arcade.color.BITTER_LIME)
        dibujar_vaca(self.pos_x,self.pos_y,self.escala)
        

if __name__ == "__main__":
    juego = MiJuego()
    contador +=5
    juego.on_draw
    arcade.run()
