import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3
DEAD_ZONE = 0.02
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_COIN = 0.2

class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y):
        self.player_list = arcade.SpriteList()
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/male_adventurer/maleAdventurer_walk4.png", scale)
        self.score = 0
        self.player_sprite.center_x = pos_x
        self.player_sprite.center_y = pos_y
        self.player_list.append(self.player_sprite)
        self.change_x = change_x
        self.change_y = change_y
    
    def draw(self):
        self.player_list.draw()
    
    def on_update(self):
        self.player_sprite.center_y += self.change_y
        self.player_sprite.center_x += self.change_x

        if self.player_sprite.center_x  > SCREEN_WIDTH:
            self.player_sprite.center_x = SCREEN_WIDTH
            self.change_x *= -1

        if self.player_sprite.center_y > SCREEN_HEIGHT:
            self.player_sprite.center_y = SCREEN_HEIGHT
            self.change_y *= -1
        
        if self.player_sprite.center_x < 0:
            self.player_sprite.center_x = 0
            self.change_x *= -1

        if self.player_sprite.center_y < 0:
            self.player_sprite.center_y = 0
            self.change_y *= -1

class MyGame(arcade.Window):
    def __init__(self, mouse = False):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.player = Player(400, 300, 1, 0, 0)
        self.set_mouse_visible(False)
        self.mouse = mouse

        """joysticks = arcade.get_joysticks()
        if joysticks:
            self.joystick = joysticks[0]
            self.joystick.open()
        else:
            print("There are no joysticks.")
            self.joystick = None"""
    
    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, 800, 0, 200, arcade.color.BITTER_LIME)
        self.player.draw()
    
    def on_update(self, delta_time):
        """if self.joystick:
            self.cow.change_x = self.joystick.x*(MOVEMENT_SPEED+1)
            self.cow.change_y = -self.joystick.y*(MOVEMENT_SPEED+1)"""

        self.player.on_update()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse:
            self.player.player_sprite.center_x = x
            self.player.player_sprite.center_y  = y
    
    """def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse:
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.cow.scale += 0.1
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self.cow.scale -= 0.1"""
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.player.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.player.change_x = MOVEMENT_SPEED
        elif key == arcade.key.W or key == arcade.key.UP:
            self.player.change_y = MOVEMENT_SPEED
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.player.change_y = -MOVEMENT_SPEED
    
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.player.change_y = 0

def main():
    window = MyGame(mouse=True)
    arcade.run()


main()