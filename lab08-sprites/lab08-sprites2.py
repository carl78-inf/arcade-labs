import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

tex_name = ":resources:images/items/coinGold.png"
sprite1 = arcade.Sprite(tex_name)

class MyGame(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Sprite Example")
        arcade.set_background_color(arcade.color.ASH_GREY)

    def on_draw(self):
        self.clear()
        sprite1.draw()


def main():
    window = MyGame()
    arcade.run()





if __name__ == "__main__":
    main()


S