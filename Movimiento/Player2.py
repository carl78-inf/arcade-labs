import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MOVEMENT_SPEED = 3

class Player:
    def __init__(self, pos_x, pos_y, scale, change_x, change_y, change_z, change_scale, max_left, max_right, max_far, max_near):
        self.list = arcade.SpriteList()
        self.sprite = arcade.Sprite(":resources:images/animated_characters/male_adventurer/maleAdventurer_walk4.png", scale)
        self.sprite.scale = scale
        self.score = 0
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos_z = 0
        self.sprite.center_x = pos_x
        self.sprite.center_y = pos_y
        self.list.append(self.sprite)
        self.change_x = change_x
        self.change_y = change_y
        self.change_z = change_z
        self.change_scale = change_scale
        self.max_left = max_left
        self.max_right = max_right
        self.max_far = max_far
        self.max_near = max_near
    
    def draw(self):
        self.list.draw()

    def on_update(self):
        self.pos_z += self.change_z
        height = self.sprite.height
        self.sprite.scale = list(self.sprite.scale)[0] + self.change_scale
        if(self.max_far <= self.pos_z <= self.max_near):
        #if(self.change_z != 0): self.change_y += list(self.sprite.scale)[0]*self.sprite.height*(-1) // (list(self.sprite.scale)[0]*(self.sprite.height/2)*(-1))*self.change_z
            self.sprite.center_y += -(1/2)*height + (1/2)*self.sprite.height
        elif(self.pos_z < self.max_far):
            self.sprite.scale = list(self.sprite.scale)[0] - self.change_scale
        elif(self.pos_z > self.max_near):
            self.sprite.scale = list(self.sprite.scale)[0] - self.change_scale
        self.sprite.center_x += self.change_x
        #print(f'X = {self.sprite.center_x} Y = {self.sprite.center_y}, Scale = {self.sprite.scale}')

        """if self.sprite.center_x  > self.max_right:
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
            self.change_y *= -1"""