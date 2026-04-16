# Prueba cámara
"""
Platformer Game

python -m arcade.examples.platform_tutorial.14_multiple_levels
"""
import arcade
import Player2

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Platformer"

# Constants used to scale our sprites from their original size
TILE_SCALING = 2
COIN_SCALING = 0.5

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20


class GameView(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        # Call the parent class and set up the window
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.player_texture = None
        self.player_sprite = None
        # Variable to hold our Tiled Map
        self.tile_map = None
        # Replacing all of our SpriteLists with a Scene variable
        self.scene = None
        # A variable to store our camera object
        self.camera = None
        # A variable to store our gui camera object
        self.gui_camera = None
        # Where is the right edge of the map?
        self.end_of_map = 0
        # Level number to load
        self.level = 1
        self.player = Player2.Player(260, 313, 1, 0, 0, 0, 0, 190, 320, -70, 70)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        layer_options = {
            "Platforms": {
                "use_spatial_hash": True
            }
        }

        # Load our TileMap
        """self.tile_map = arcade.load_tilemap(
            f":resources:tiled_maps/map2_level_{self.level}.json",
            scaling=TILE_SCALING,
            layer_options=layer_options,
        )"""
        self.tile_map = arcade.load_tilemap(
            r"C:\Users\Carlos UAH\OneDrive - Universidad de Alcala\1ºUAH\2ºCuatrimestre\Tecnología de videojuegos\Inicio_proyecto\ps.json",
            scaling=TILE_SCALING,
            layer_options=layer_options,
        )

        # Create our Scene Based on the TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_texture = arcade.load_texture(
            ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
        )

        # Add Player Spritelist before "Foreground" layer. This will make the foreground
        # be drawn after the player, making it appear to be in front of the Player.
        # Setting before using scene.add_sprite allows us to define where the SpriteList
        # will be in the draw order. If we just use add_sprite, it will be appended to the
        # end of the order.
        #self.scene.add_sprite_list_after("Player", "Foreground")

        self.player_sprite = arcade.Sprite(self.player_texture)
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 128
        self.scene.add_sprite("Player", self.player_sprite)
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, walls=self.scene["Platforms"], gravity_constant=GRAVITY
        )

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.Camera2D()

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.Camera2D()

        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        # Calculate the right edge of the map in pixels
        self.end_of_map = (self.tile_map.width * self.tile_map.tile_width)
        self.end_of_map *= self.tile_map.scaling
        print(self.end_of_map)

    def on_draw(self):
        """Render the screen."""
        # Clear the screen to the background color
        self.clear()
        # Activate our camera before drawing
        self.camera.use()
        # Draw our Scene
        self.scene.draw()
        self.player.draw()
        # Activate our GUI camera
        self.gui_camera.use()

    def on_update(self, delta_time):
        """Movement and Game Logic"""
        # Move the player using our physics engine
        self.physics_engine.update()
        # Check if the player got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            self.setup()
        self.camera.position = self.player_sprite.position

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.ESCAPE:
            self.setup()

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0


def main():
    """Main function"""
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()