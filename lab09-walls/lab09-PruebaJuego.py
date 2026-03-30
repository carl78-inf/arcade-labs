# Prueba del juego
import arcade
from Player import Player
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SPRITE_SCALING_BOX = 0.5
SPRITE_SCALING_PLAYER = 0.5
MOVEMENT_SPEED = 3

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        self.player = Player(400, 300, SPRITE_SCALING_PLAYER, MOVEMENT_SPEED)
    
    def setup(self):

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        # Reset the score
        self.score = 0

        # Manually create and position a box at 300, 200
        wall = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", SPRITE_SCALING_BOX)
        wall.center_x = 300
        wall.center_y = 200
        self.wall_list.append(wall)

        # Manually create and position a box at 364, 200
        """wall = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", SPRITE_SCALING_BOX)
        wall.center_x = 364
        wall.center_y = 200
        self.wall_list.append(wall)"""

    
    def on_draw(self):
        self.clear()
        self.player.on_draw()
        self.wall_list.draw()
        self.player_list.draw()
    
    def on_update(self, delta_time):
        self.player.on_update()
        """for wall in self.wall_list:
            if self.player.pos_y - wall.center_x <= 32:
                self.player.pos_y = wall.center_x + 32"""
        if math.fabs(self.player.pos_y - 200) <= 64 and math.fabs(self.player.pos_x -300) <= 64:
            self.player.change_y = 0
            self.player.change_x = 0

    
    def on_key_press(self, key, modifiers):
        self.player.on_key_press(key)

    def on_key_release(self, key, modifiers):
        self.player.on_key_release(key)

def main():
    window = MyGame()
    window.setup()
    arcade.run()


main()