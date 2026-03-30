"""
Platformer Game

python -m arcade.examples.platform_tutorial.14_multiple_levels
"""
import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3

class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y, change_z, max_left, max_right):
        self.list = arcade.SpriteList()
        self.sprite = arcade.Sprite(":resources:images/animated_characters/male_adventurer/maleAdventurer_walk4.png", scale)
        self.sprite.scale = scale
        self.score = 0
        self.sprite.center_x = pos_x
        self.sprite.center_y = pos_y
        self.list.append(self.sprite)
        self.change_x = change_x
        self.change_y = change_y
        self.change_z = change_z
        self.max_left = max_left
        self.max_right = max_right
    
    def draw(self):
        self.list.draw()

    def on_update(self):
        height = self.sprite.height
        self.sprite.scale = list(self.sprite.scale)[0] + self.change_z
        """if(0.3 <= list(self.sprite.scale)[0] <= 1):
        #if(self.change_z != 0): self.change_y += list(self.sprite.scale)[0]*self.sprite.height*(-1) // (list(self.sprite.scale)[0]*(self.sprite.height/2)*(-1))*self.change_z
            self.sprite.center_y += -(1/2)*height + (1/2)*self.sprite.height
        elif(list(self.sprite.scale)[0] < 0.3):
            self.sprite.scale = 0.3
        elif(list(self.sprite.scale)[0] > 1):
            self.sprite.scale = 1"""
        self.sprite.center_y += -(1/2)*height + (1/2)*self.sprite.height
        self.sprite.center_x += self.change_x
        #print(f'X = {self.sprite.center_x} Y = {self.sprite.center_y}, Scale = {self.sprite.scale}')

        if self.sprite.center_x  > self.max_right:
            self.sprite.center_x = self.max_right
            #self.change_x *= -1

        if self.sprite.center_y > SCREEN_HEIGHT:
            self.sprite.center_y = SCREEN_HEIGHT
            self.change_y *= -1
        
        if self.sprite.center_x < self.max_left:
            self.sprite.center_x = self.max_left
            #self.change_x *= -1

        if self.sprite.center_y < 0:
            self.sprite.center_y = 0
            self.change_y *= -1

class MyGame(arcade.Window):
    def __init__(self, mouse = False):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.player = Player(260, 313, 1, 0, 0, 0, 190, 320)
        self.player2 = Player(540, 313, 1, 0, 0, 0, 470, 610)
        self.contador = 0
        self.tiempo = 0
    
    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, 800, 0, 250, arcade.color.BITTER_LIME)
        arcade.draw_lrbt_rectangle_filled(190, 320, 210, 250, arcade.color.RED_BROWN)
        arcade.draw_lrbt_rectangle_filled(470, 610, 210, 250, arcade.color.RED_BROWN)
        self.player.draw()
        self.player2.draw()
        #arcade.draw_text(text= self.contador, x = 50, y = 50, color= arcade.color.BLACK)
        arcade.draw_text(text= (self.player.sprite.center_x, self.player.sprite.center_y), x = 50, y = 50, color= arcade.color.BLACK)
        arcade.draw_text(text= (self.player.sprite.scale, self.player.sprite.height), x = 50, y = 70, color= arcade.color.BLACK)
    
    def on_update(self, delta_time):
        self.tiempo += 1
        self.player.on_update()
        self.player2.on_update()
        if(self.player.sprite.change_x > 320): self.player.sprite.change_x = 320 
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.player.change_x = -MOVEMENT_SPEED
            self.player2.change_z = -0.01
        elif key == arcade.key.RIGHT:
            self.player.change_x = MOVEMENT_SPEED
            self.player2.change_z = 0.01
        elif key == arcade.key.UP:
            self.player.change_z = -0.01
            self.player2.change_x = MOVEMENT_SPEED
        elif key == arcade.key.DOWN:
            self.player.change_z = 0.01
            self.player2.change_x = -MOVEMENT_SPEED
    
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0
            self.player2.change_z = 0
            self.player2.change_y = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player.change_z = 0
            self.player.change_y = 0
            self.player2.change_x = 0
            

def main():
    window = MyGame()
    arcade.run()


main()