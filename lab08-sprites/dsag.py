import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3
DEAD_ZONE = 0.02


class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.scale = scale
        self.change_x = change_x
        self.change_y = change_y
    
    def draw(self):
        dibujar_vaca(self.pos_x, self.pos_y, self.scale)
    
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
    def __init__(self, mouse = False):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Lab 7 - User Control")
        arcade.set_background_color(arcade.color.ASH_GREY)
        self.cow = Cow(400, 300, 1, 0, 0)
        self.set_mouse_visible(False)
        self.mouse = mouse

        joysticks = arcade.get_joysticks()
        if joysticks:
            self.joystick = joysticks[0]
            self.joystick.open()
        else:
            print("There are no joysticks.")
            self.joystick = None
    
    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, 800, 0, 200, arcade.color.BITTER_LIME)
        self.cow.draw()
    
    def on_update(self, delta_time):
        if self.joystick:
            self.cow.change_x = self.joystick.x*(MOVEMENT_SPEED+1)
            self.cow.change_y = -self.joystick.y*(MOVEMENT_SPEED+1)

        self.cow.on_update()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse:
            self.cow.pos_x = x
            self.cow.pos_y = y
    
    def on_mouse_press(self, x, y, button, modifiers):
        if self.mouse:
            if button == arcade.MOUSE_BUTTON_LEFT:
                self.cow.scale += 0.1
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                self.cow.scale -= 0.1
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.cow.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.cow.change_x = MOVEMENT_SPEED
        elif key == arcade.key.W or key == arcade.key.UP:
            self.cow.change_y = MOVEMENT_SPEED
        elif key == arcade.key.S or key == arcade.key.DOWN:
            self.cow.change_y = -MOVEMENT_SPEED
    
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.cow.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.DOWN:
            self.cow.change_y = 0

def main():
    window = MyGame(mouse=True)
    arcade.run()


main()