# Player
import arcade

class Player: 

    def __init__(self, pos_x, pos_y, scale, change_x, change_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.scale = scale
        self.change_x = change_x
        self.change_y = change_y

        self.player_texture = arcade.load_texture(
            ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
        )
        self.player_sprite = arcade.Sprite(self.player_texture)

    def on_draw(self):
        self.player_sprite