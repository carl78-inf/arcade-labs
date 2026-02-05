import arcade

WIDTH = 600
HEIGHT = 600

arcade.open_window(WIDTH, HEIGHT, "Example")

arcade.start_render()
arcade.draw_text("Hello, world", 350, 300, arcade.color.BLUE_SAPPHIRE)
arcade.finish_render()

arcade.run()
