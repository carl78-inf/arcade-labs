# Personaje
import arcade

class Player:
    def __init__(self, pos_x, pos_y, speed = 3):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.speed = speed
        self.change_x = 0
        self.change_y = 0
        self.width = 30
        self.hight = 40

    def on_draw(self):
        arcade.draw_lbwh_rectangle_outline(left=self.pos_x - (self.width / 2), bottom=self.pos_y - (self.hight / 2), \
                                           width=self.width, height=self.hight, color=arcade.color.RED, border_width= 2)

    def on_update(self):
        self.pos_x += self.change_x
        self.pos_y += self.change_y

    def move(self):
        pass

    def on_key_press(self, key):
        if key == arcade.key.LEFT:
            self.change_x = -self.speed
        elif key == arcade.key.RIGHT:
            self.change_x = self.speed
        elif key == arcade.key.UP:
            self.change_y = self.speed
        elif key == arcade.key.DOWN:
            self.change_y = -self.speed
    
    def on_key_release(self, key):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.change_y = 0