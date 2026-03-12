import random
import arcade

# --- Constants --- #
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_COIN = 0.2
COIN_COUNT = 50

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.scale = scale
        self.change_x = change_x
        self.change_y = change_y
        self.texture = arcade.Sprite(":resources:images/items/coinGold.png")
    
    def draw(self):
        self.texture.
    
    def on_update(self):
        self.pos_y += self.change_y
        self.pos_x += self.change_x

        if self.pos_x > SCREEN_WIDTH:
            self.pos_x = SCREEN_WIDTH
            self.change_x *= -1

        if self.pos_y > SCREEN_HEIGHT:
            self.pos_y = SCREEN_HEIGHT
            self.change_y *= -1
        
        if self.pos_x < 0:
            self.pos_x = 0
            self.change_x *= -1

        if self.pos_y < 0:
            self.pos_y = 0
            self.change_y *= -1

class MyGame(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Sprite Example")
        arcade.set_background_color(arcade.color.ASH_GREY)

    def on_draw(self):
        self.clear()


def main():
    window = MyGame()
    arcade.run()





if __name__ == "__main__":
    main()
