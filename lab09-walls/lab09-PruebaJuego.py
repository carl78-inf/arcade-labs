# Prueba del juego
import arcade
from Player import Player

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.player = Player(400, 300)
    
    def on_draw(self):
        self.clear()
        self.player.on_draw()
    
    def on_update(self, delta_time):
        self.player.on_update()
    
    def on_key_press(self, key, modifiers):
        self.player.on_key_press(key)

    def on_key_release(self, key, modifiers):
        self.player.on_key_release(key)

def main():
    window = MyGame()
    arcade.run()


main()