import arcade
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3

class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y):
        self.list = arcade.SpriteList()
        self.sprite = arcade.Sprite(":resources:images/animated_characters/male_adventurer/maleAdventurer_walk4.png", scale)
        self.score = 0
        self.sprite.center_x = pos_x
        self.sprite.center_y = pos_y
        self.list.append(self.sprite)
        self.change_x = change_x
        self.change_y = change_y
    
    def draw(self):
        self.list.draw()
    
    def on_update(self):
        self.sprite.center_y += self.change_y
        self.sprite.center_x += self.change_x

        if self.sprite.center_x  > SCREEN_WIDTH:
            self.sprite.center_x = SCREEN_WIDTH
            self.change_x *= -1

        if self.sprite.center_y > SCREEN_HEIGHT:
            self.sprite.center_y = SCREEN_HEIGHT
            self.change_y *= -1
        
        if self.sprite.center_x < 0:
            self.sprite.center_x = 0
            self.change_x *= -1

        if self.sprite.center_y < 0:
            self.sprite.center_y = 0
            self.change_y *= -1

class Coin:
    def __init__(self, scale, change_x, change_y):
        self.list = arcade.SpriteList()
        self.sprite = arcade.Sprite(":resources:images/items/coinGold.png", scale)
        self.score = 0
        self.sprite.center_x = random.randrange(SCREEN_WIDTH)
        self.sprite.center_y = random.randrange(SCREEN_HEIGHT)
        self.list.append(self.sprite)
        self.change_x = change_x
        self.change_y = change_y
    
    def draw(self):
        self.list.draw()
    
    def on_update(self):
        self.sprite.center_y += self.change_y
        self.sprite.center_x += self.change_x

        if self.sprite.center_x  > SCREEN_WIDTH:
            self.sprite.center_x = SCREEN_WIDTH
            self.change_x *= -1

        if self.sprite.center_y > SCREEN_HEIGHT:
            self.sprite.center_y = SCREEN_HEIGHT
            self.change_y *= -1
        
        if self.sprite.center_x < 0:
            self.sprite.center_x = 0
            self.change_x *= -1

        if self.sprite.center_y < 0:
            self.sprite.center_y = 0
            self.change_y *= -1


class MyGame(arcade.Window):
    def __init__(self, mouse = False):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.player = Player(400, 300, 1, 0, 0)
        self.coin = Coin(400, 300, 1, 3, 3)
    
    def on_draw(self):
        self.clear()
        self.player.draw()
        self.coin.draw()
    
    def on_update(self, delta_time):
        self.player.on_update()
        self.coin.on_update()
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.player.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player.change_x = MOVEMENT_SPEED
        elif key == arcade.key.UP:
            self.player.change_y = MOVEMENT_SPEED
        elif key == arcade.key.DOWN:
            self.player.change_y = -MOVEMENT_SPEED
    
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player.change_y = 0

def main():
    window = MyGame()
    arcade.run()


main()