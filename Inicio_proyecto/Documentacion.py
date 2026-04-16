# Documentación para leer
"""
The main window class that all object-oriented applications should
derive from.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING

import pyglet

from arcade.utils import is_pyodide

if is_pyodide():
    pyglet.options.backend = "webgl"

import pyglet.config
import pyglet.window.mouse
from pyglet.display.base import Screen, ScreenMode
from pyglet.event import EVENT_HANDLE_STATE, EVENT_UNHANDLED
from pyglet.window import MouseCursor

import arcade
from arcade.clock import GLOBAL_CLOCK, GLOBAL_FIXED_CLOCK, _setup_clock, _setup_fixed_clock
from arcade.color import BLACK
from arcade.context import ArcadeContext
from arcade.gl.provider import get_arcade_context, set_provider
from arcade.types import LBWH, Color, Rect, RGBANormalized, RGBOrA255
from arcade.utils import is_raspberry_pi
from arcade.window_commands import get_display_size, set_window

if TYPE_CHECKING:
    from arcade.camera import Projector
    from arcade.camera.default import DefaultProjector
    from arcade.start_finish_data import StartFinishRenderData

LOG = logging.getLogger(__name__)

MOUSE_BUTTON_LEFT = 1
MOUSE_BUTTON_MIDDLE = 2
MOUSE_BUTTON_RIGHT = 4

_window: Window

__all__ = [
    "get_screens",
    "NoOpenGLException",
    "Window",
    "open_window",
    "View",
    "MOUSE_BUTTON_LEFT",
    "MOUSE_BUTTON_MIDDLE",
    "MOUSE_BUTTON_RIGHT",
]


def get_screens() -> list[Screen]:
    """
    Return a list of screens. So for a two-monitor setup, this should return
    a list of two screens. Can be used with :class:`arcade.Window` to select which
    window we full-screen on.

    Returns:
        List of screens, one for each monitor.
    """
    display = pyglet.display.get_display()
    return display.get_screens()


class NoOpenGLException(Exception):
    """Exception when we can't get an OpenGL 3.3+ context"""

    pass


class Window(pyglet.window.Window):
    """
    A window that will appear on your desktop.

    This class is a subclass of Pyglet's Window class with many
    Arcade-specific features added.

    .. note::

        Arcade currently cannot easily support multiple windows. If you need
        multiple windows, consider using multiple views or divide the window
        into sections.

    .. _pyglet_pg_window_size_position: https://pyglet.readthedocs.io/en/latest/programming_guide/windowing.html#size-and-position
    .. _pyglet_pg_window_style: https://pyglet.readthedocs.io/en/latest/programming_guide/windowing.html#window-style

    Args:
        width:
            Window width. Defaults to 1280.
        height:
            Window height. Defaults to 720.
        title:
            The title/caption of the window
        fullscreen:
            Should this be full screen?
        resizable:
            Can the user resize the window?
        update_rate:
            How frequently to run the on_update event.
        draw_rate:
            How frequently to run the on_draw event. (this is the FPS limit)
        fixed_rate:
            How frequently should the fixed_updates run,
            fixed updates will always run at this rate.
        fixed_frame_cap:
            The maximum number of fixed updates that can occur in one update loop.
            defaults to infinite. If large lag spikes cause your game to freeze,
            try setting this to a smaller number. This may cause your physics to
            lag behind temporarily.
        antialiasing:
            Use multisampling framebuffer (antialiasing)
        samples: Number of samples used in antialiasing (default 4).
            Usually this is 2, 4, 8 or 16.
        gl_version: What OpenGL version to request.
            This is ``(3, 3)`` by default and can be overridden when using more
            advanced OpenGL features.
        screen: Pass a pyglet :py:class:`~pyglet.display.Screen` to
            request the window be placed on it. See `pyglet's window size &
            position guide <pyglet_pg_window_size_position_>`_ to learn more.
        style: Request a non-default window style, such as borderless.
            Some styles only work in certain situations. See `pyglet's guide
            to window style <pyglet_pg_window_style_>`_ to learn more.
        visible:
            Should the window be visible immediately
        vsync:
            Wait for vertical screen refresh before swapping buffer
            This can make animations and movement look smoother.
        gc_mode: Decides how OpenGL objects should be garbage collected
            ("context_gc" (default) or "auto")
        center_window:
            If true, will center the window.
        enable_polling:
            Enabled input polling capability.
            This makes the :py:attr:`keyboard` and :py:attr:`mouse` attributes available for use.
        file_drops:
            Should the window listen for file drops? If True, the window will dispatch
            ``on_file_drop`` events when files are dropped onto the window.
        **kwargs:
            Further keyword arguments are passed to the pyglet window constructor.
            This can be used to set advanced options that aren't explicitly handled by Arcade.

    Raises:
        NoOpenGLException: If the system does not support OpenGL requested OpenGL version.
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        title: str | None = "Arcade Window",
        fullscreen: bool = False,
        resizable: bool = False,
        update_rate: float = 1 / 60,
        antialiasing: bool = True,
        gl_version: tuple[int, int] = (3, 3),
        screen: Screen | None = None,
        style: str | None = pyglet.window.Window.WINDOW_STYLE_DEFAULT,
        visible: bool = True,
        vsync: bool = False,
        gc_mode: str = "context_gc",
        center_window: bool = False,
        samples: int = 4,
        enable_polling: bool = True,
        gl_api: str = "opengl",
        draw_rate: float = 1 / 60,
        fixed_rate: float = 1.0 / 60.0,
        fixed_frame_cap: int | None = None,
        file_drops: bool = False,
        **kwargs,
    ) -> None:
        # In certain environments we can't have antialiasing/MSAA enabled.
        # Detect replit environment
        if os.environ.get("REPL_ID"):
            antialiasing = False

        desired_gl_provider = "opengl"
        if is_pyodide():
            gl_api = "webgl"

        if gl_api == "webgl":
            pyglet.options.backend = "webgl"
            desired_gl_provider = "webgl"

        # Detect Raspberry Pi and switch to OpenGL ES 3.1
        if is_raspberry_pi():
            gl_version = 3, 1
            gl_api = "opengles"

        self.closed = False
        """Indicates if the window was closed"""
        self.headless: bool = arcade.headless
        """If True, the window is running in headless mode."""

        config = None
        # Attempt to make window with antialiasing
        if gl_api == "opengl" or gl_api == "opengles":
            if antialiasing:
                try:
                    config = pyglet.config.OpenGLConfig(
                        major_version=gl_version[0],
                        minor_version=gl_version[1],
                        opengl_api=gl_api.replace("open", ""),  # type: ignore  # pending: upstream fix
                        double_buffer=True,
                        sample_buffers=1,
                        samples=samples,
                        depth_size=24,
                        stencil_size=8,
                        red_size=8,
                        green_size=8,
                        blue_size=8,
                        alpha_size=8,
                    )
                except RuntimeError:
                    LOG.warning("Skipping antialiasing due missing hardware/driver support")
                    config = None
                    antialiasing = False
            # If we still don't have a config
            if not config:
                config = pyglet.config.OpenGLConfig(
                    major_version=gl_version[0],
                    minor_version=gl_version[1],
                    opengl_api=gl_api.replace("open", ""),  # type: ignore  # pending: upstream fix
                    double_buffer=True,
                    depth_size=24,
                    stencil_size=8,
                    red_size=8,
                    green_size=8,
                    blue_size=8,
                    alpha_size=8,
                )
        try:
            # This type ignore is here because somehow Pyright thinks this is an Emscripten window
            super().__init__(
                width=width,
                height=height,
                caption=title,
                resizable=resizable,
                config=config,  # type: ignore
                vsync=vsync,
                visible=visible,
                style=style,
                file_drops=file_drops,
                **kwargs,
            )
            # pending: weird import tricks resolved
            self.register_event_type("on_update")
            self.register_event_type("on_action")
            self.register_event_type("on_fixed_update")
        except pyglet.window.NoSuchConfigException:
            raise NoOpenGLException(
                "Unable to create an OpenGL 3.3+ context. "
                "Check to make sure your system supports OpenGL 3.3 or higher."
            )
        if gl_api == "opengl" or gl_api == "opengles":
            if antialiasing:
                import pyglet.graphics.api.gl as gl
                import pyglet.graphics.api.gl.lib as gllib

                try:
                    gl.glEnable(gl.GL_MULTISAMPLE_ARB)
                except gllib.GLException:
                    LOG.warning("Warning: Anti-aliasing not supported on this computer.")

        _setup_clock()
        _setup_fixed_clock(fixed_rate)

        # We don't call the set_draw_rate function here because unlike the updates,
        # the draw scheduling is initially set in the call to pyglet.app.run()
        # that is done by the run() function. run() will pull this draw rate from
        # the Window and use it. Calls to set_draw_rate only need
        # to be done if changing it after the application has been started.

        # To ensure that draws are never de-synced from updates and wasted the draw rate
        # is forced to be slower than or equal to the update rate.
        # This works because pyglet ensures that a scheduled event takes as long or longer than the
        # call rate, but never less.
        assert update_rate <= draw_rate, (
            "An arcade window's draw rate cannot be faster than its update rate"
        )
        self._draw_rate = max(update_rate, draw_rate)
        self._accumulated_draw_time: float = 0.0

        # Fixed rate cannot be changed post initialization as this throws off physics sims.
        # If more time resolution is needed in fixed updates, devs can do 'sub-stepping'.
        self._fixed_rate = fixed_rate
        self._fixed_frame_cap = fixed_frame_cap
        self.set_update_rate(update_rate)

        self.set_vsync(vsync)

        if fullscreen is True:
            super().set_fullscreen(True, screen)

        set_window(self)

        self.push_handlers(on_resize=self._on_resize)

        set_provider(desired_gl_provider)
        self._ctx: ArcadeContext = get_arcade_context(self, gc_mode=gc_mode, gl_api=gl_api)
        # self._ctx: ArcadeContext = ArcadeContext(self, gc_mode=gc_mode, gl_api=gl_api)
        self._background_color: Color = BLACK

        self._current_view: View | None = None

        # See if we should center the window
        if center_window:
            self.center_window()

        self.keyboard: pyglet.window.key.KeyStateHandler | None = None
        """
        A pyglet KeyStateHandler that can be used to poll the state of the keyboard.

            Example::

                    if self.window.keyboard[key.SPACE]:
                        print("The space key is currently being held down.")
        """
        self.mouse: pyglet.window.mouse.MouseStateHandler | None = None
        """
        A pyglet MouseStateHandler that can be used to poll the state of the mouse.

            Example::

                if self.window.mouse.LEFT:
                    print("The left mouse button is currently being held down.")
                print(
                    "The mouse is at position "
                    f"{self.window.mouse["x"]}, {self.window.mouse["y"]}"
                )
        """

        if enable_polling:
            self.keyboard = pyglet.window.key.KeyStateHandler()

            if arcade.headless:
                self.push_handlers(self.keyboard)

            else:
                self.mouse = pyglet.window.mouse.MouseStateHandler()
                self.push_handlers(self.keyboard)
                self.push_handlers(self.mouse)
        else:
            self.keyboard = None
            self.mouse = None

        # Framebuffer for drawing content into when start_render is called.
        # These are typically functions just at module level wrapped in
        # start_render and finish_render calls. The framebuffer is repeatedly
        # rendered to the window when the event loop starts.
        self._start_finish_render_data: StartFinishRenderData | None = None

    @property
    def current_view(self) -> View | None:
        """
        The currently active view.

        To set a different view, call :py:meth:`~arcade.Window.show_view`.
        """
        return self._current_view

    # TODO: This is overriding the ctx function from Pyglet's BaseWindow which returns the
    # SurfaceContext class from pyglet. We should probably rename this.
    @property
    def ctx(self) -> ArcadeContext:  # type: ignore
        """
        The OpenGL context for this window.

        This context instance provides access to a powerful set of
        features for lower level OpenGL programming. It is also used
        internally by Arcade to manage OpenGL resources.
        """
        return self._ctx

    def clear(  # type: ignore # not sure what to do here, BaseWindow.clear is static
        self,
        color: RGBOrA255 | None = None,
        color_normalized: RGBANormalized | None = None,
        viewport: tuple[int, int, int, int] | None = None,
    ) -> None:
        """
        Clears the window with the configured background color
        set through :py:attr:`~arcade.Window.background_color`.

        Args:
            color:
                Override the current background color with one of the following:

                1. A :py:class:`~arcade.types.Color` instance
                2. A 3 or 4-length RGB/RGBA :py:class:`tuple` of byte values (0 to 255)

            color_normalized:
                override the current background color using normalized values (0.0 to 1.0).
                For example, (1.0, 0.0, 0.0, 1.0) making the window contents red.

            viewport:
                The area of the window to clear. By default, the entire window is cleared.
                The viewport format is ``(x, y, width, height)``.
        """
        # Use the configured background color if none is provided
        if color is None and color_normalized is None:
            color = self.background_color
        self.ctx.screen.clear(color=color, color_normalized=color_normalized, viewport=viewport)

    @property
    def background_color(self) -> Color:
        """
        Get or set the background color for this window.
        This affects what color the window will contain when
        :py:meth:`~arcade.Window.clear` is called.

        Examples::

            # Use Arcade's built in Color values
            window.background_color = arcade.color.AMAZON

            # Set the background color with a custom Color instance
            MY_RED = arcade.types.Color(255, 0, 0)
            window.background_color = MY_RED

            # Set the background color directly from an RGBA tuple
            window.background_color = 255, 0, 0, 255

            # Set the background color directly from an RGB tuple
            # RGB tuples will assume 255 as the opacity / alpha value
            window.background_color = 255, 0, 0
        """
        return self._background_color

    @background_color.setter
    def background_color(self, value: RGBOrA255) -> None:
        self._background_color = Color.from_iterable(value)

    @property
    def rect(self) -> Rect:
        """Return a Rect describing the size of the window."""
        return LBWH(0, 0, self.width, self.height)

    def run(self, view: View | None = None) -> None:
        """
        Run the event loop. Optionally start with a specified view.

        After the window has been set up, and the event hooks are in place, this
        is usually one of the last commands on the main program. This is a blocking
        function starting pyglet's event loop meaning it will start to dispatch
        events such as ``on_draw`` and ``on_update``.

        Args:
            view: The view to display when starting the run. Defaults to None.
        """
        if view is not None:
            self.show_view(view)
        arcade.run()

    def close(self) -> None:
        """Close the Window."""
        self.closed = True
        super().close()
        # Make sure we don't reference the window any more
        set_window(None)
        pyglet.clock.unschedule(self._dispatch_updates)

    def set_fullscreen(
        self,
        fullscreen: bool = True,
        screen=None,
        mode: ScreenMode | None = None,
        width: float | None = None,
        height: float | None = None,
    ) -> None:
        """
        Change the fullscreen status of the window.

        In most cases you simply want::

            # Enter fullscreen mode
            window.set_fullscreen(True)
            # Leave fullscreen mode
            window.set_fullscreen(False)

        When entering fullscreen mode the window will resize to the screen's
        resolution. When leaving fullscreen mode the window will resize back
        to the size it was before entering fullscreen mode.

        Args:
            fullscreen:
                Should we enter or leave fullscreen mode?
            screen:
                Which screen should we display on? See :func:`get_screens`
            mode:
                The screen will be switched to the given mode.  The mode must
                have been obtained by enumerating `Screen.get_modes`.  If
                None, an appropriate mode will be selected from the given
                `width` and `height`.
            width:
                Override the width of the window. Will be rounded to :py:class:`int`.
            height:
                Override the height of the window. Will be rounded to :py:class:`int`.
        """
        # fmt: off
        super().set_fullscreen(
            fullscreen, screen, mode,
            # TODO: resolve the upstream int / float screen coord issue
            None if width is None else int(width),
            None if height is None else int(height))
        # fmt: on

    def center_window(self) -> None:
        """Center the window on your desktop."""
        # Get the display screen using pyglet
        screen_width, screen_height = get_display_size()

        window_width, window_height = self.get_framebuffer_size()
        # Center the window
        self.set_location((screen_width - window_width) // 2, (screen_height - window_height) // 2)

    def on_update(self, delta_time: float) -> bool | None:
        """
        This method can be implemented and is reserved for game logic.
        Move sprites. Perform collision checks and other game logic.
        This method is called every frame before :meth:`on_draw`.

        The ``delta_time`` can be used to make sure the game runs at the same
        speed, no matter the frame rate.

        Args:
            delta_time: Time interval since the last time the function was
                called in seconds.
        """
        pass

    def on_fixed_update(self, delta_time: float):
        """
        Called for each fixed update. This is useful for physics engines
        and other systems that should update at a constant rate.

        Args:
            delta_time: Time interval since the last time the function was
                called in seconds.
        """
        pass

    def _dispatch_frame(self, delta_time: float) -> None:
        """
        To handle the de-syncing of on_draw and on_update that can occur when the events aren't
        linked. Dispatch frame keeps them in sync by always ensuring on_draw happens along-side
        an on_update. This requires that the draw frequencies is less than or equal to the update
        frequency.

        This only works because pyglet will only dispatch events after the call rate, or longer.
        This means if the update rate and draw rate are equal they will both always be called.
        The modulus on the accumulated draw time means that when the update rate is greater
        than the draw rate no time is lost.

        Args:
            delta_time: The amount of time since the last update.
        """
        self._dispatch_updates(delta_time)
        self._accumulated_draw_time += delta_time

        if self._draw_rate <= self._accumulated_draw_time:
            # Because we only ever dispatch one draw event per loop
            # we only need the modulus to keep time, if we didn't care
            # it could be set to zero instead.
            # ! This should maybe be fixed at 'self._draw_rate', discuss.

            # In case the window close in on_update, on_fixed_update or input callbacks
            if not self.closed:
                self.draw(self._accumulated_draw_time)
            self._accumulated_draw_time %= self._draw_rate

    def _dispatch_updates(self, delta_time: float) -> None:
        """
        Internal function that is scheduled with Pyglet's clock, this function gets
        run by the clock, and dispatches the on_update events.

        It also accumulates time and runs fixed updates until the Fixed Clock catches
        up to the global clock

        Args:
            delta_time: Time interval since the last time the function was
                called in seconds.
        """
        GLOBAL_CLOCK.tick(delta_time)
        fixed_count = 0
        while GLOBAL_FIXED_CLOCK.accumulated >= self._fixed_rate and (
            self._fixed_frame_cap is None or fixed_count <= self._fixed_frame_cap
        ):
            GLOBAL_FIXED_CLOCK.tick(self._fixed_rate)
            self.dispatch_event("on_fixed_update", self._fixed_rate)
            fixed_count += 1
        self.dispatch_event("on_update", GLOBAL_CLOCK.delta_time)

    def flip(self) -> None:
        """
        Present the rendered content to the screen.

        This is not necessary to call when using the standard standard
        event loop. The event loop will automatically call this method
        after ``on_draw`` has been called.

        Window framebuffers normally have a back and front buffer meaning
        they are "double buffered". Content is always drawn into the back
        buffer while the front buffer contains the previous frame.
        Swapping the buffers makes the back buffer visible and hides the
        front buffer. This is done to prevent flickering and tearing.

        This method also garbage collects OpenGL resources if there are
        any dead resources to collect. If you override this method, make
        sure to call the super method to ensure that the garbage collection
        is done.
        """
        # Garbage collect OpenGL resources
        num_collected = self.ctx.gc()  # noqa: F841
        # LOG.debug("Garbage collected %s OpenGL resource(s)", num_collected)

        super().flip()  # type: ignore # Window typed at runtime

    def set_update_rate(self, rate: float) -> None:
        """
        Set how often the on_update function should be dispatched.
        For example::

            # Set the update rate to 60 times per second.
            self.set_update_rate(1 / 60)

        Args:
            rate: Update frequency in seconds
        """
        self._update_rate = rate
        pyglet.clock.unschedule(self._dispatch_frame)
        pyglet.clock.schedule_interval(self._dispatch_frame, rate)

    def set_draw_rate(self, rate: float) -> None:
        """
        Set how often the on_draw function should be run.
        The draw rate cannot currently be faster than the update rate.

        For example::

            # Set the draw rate to 60 frames per second.
            set.set_draw_rate(1 / 60)
        """
        assert self._update_rate <= rate, (
            "An arcade window's draw rate cannot be faster than its update rate"
        )
        self._draw_rate = max(self._update_rate, rate)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        """
        Called repeatedly while the mouse is moving in the window area.

        Override this function to respond to changes in mouse position.

        Args:
            x: x position of mouse within the window in pixels
            y: y position of mouse within the window in pixels
            dx: Change in x since the last time this method was called
            dy: Change in y since the last time this method was called
        """
        pass

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        """
        Called once whenever a mouse button gets pressed down.

        Override this function to handle mouse clicks. For an example of
        how to do this, see Arcade's built-in :ref:`aiming and shooting
        bullets <sprite_bullets_aimed>` demo.

        Args:
            x:
                x position of the mouse
            y:
                y position of the mouse
            button:
                What button was pressed. This will always be one of the following:

                - ``arcade.MOUSE_BUTTON_LEFT``
                - ``arcade.MOUSE_BUTTON_RIGHT``
                - ``arcade.MOUSE_BUTTON_MIDDLE``

            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        pass

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int
    ) -> EVENT_HANDLE_STATE:
        """
        Called repeatedly while the mouse moves with a button down.

        Override this function to handle dragging.

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            dx:
                Change in x since the last time this method was called
            dy:
                Change in y since the last time this method was called
            buttons:
                Which button is pressed
            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        """
        Called once whenever a mouse button gets released.

        Override this function to respond to mouse button releases. This
        may be useful when you want to use the duration of a mouse click
        to affect gameplay.

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            button:
                What button was hit. One of:

                - ``arcade.MOUSE_BUTTON_LEFT``
                - ``arcade.MOUSE_BUTTON_RIGHT``
                - ``arcade.MOUSE_BUTTON_MIDDLE``
            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return EVENT_UNHANDLED

    def on_mouse_scroll(
        self, x: int, y: int, scroll_x: float, scroll_y: float
    ) -> EVENT_HANDLE_STATE:
        """
        Called repeatedly while a mouse scroll wheel moves.

        Override this function to respond to scroll events. The scroll
        arguments may be positive or negative to indicate direction, but
        the units are unstandardized. How many scroll steps you receive
        may vary wildly between computers depending a number of factors,
        including system settings and the input devices used (i.e. mouse
        scrollwheel, touch pad, etc).

        .. warning:: Not all users can scroll easily!

                 Only some input devices support horizontal
                 scrolling. Standard vertical scrolling is common,
                 but some laptop touch pads are hard to use.

                 This means you should be careful about how you use
                 scrolling. Consider making it optional
                 to maximize the number of people who can play your
                 game!

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            scroll_x:
                Number of steps scrolled horizontally since the last call of this function
            scroll_y:
                Number of steps scrolled vertically since the last call of this function
        """
        return EVENT_UNHANDLED

    def set_mouse_cursor_visible(self, visible: bool = True) -> None:
        """
        Set whether to show the system's cursor while over the window

        By default, the system mouse cursor is visible whenever the
        mouse is over the window. To hide the cursor, pass ``False`` to
        this function. Pass ``True`` to make the cursor visible again.

        The window will continue receiving mouse events while the cursor
        is hidden, including movements and clicks. This means that
        functions like :meth:`~.Window.on_mouse_motion` and
        t':meth:`~.Window.on_mouse_press` will continue to work normally.

        You can use this behavior to visually replace the system mouse
        cursor with whatever you want. One example is :ref:`a game
        character that is always at the most recent mouse position in
        the window<sprite_collect_coins>`.

        .. note:: Advanced users can try using system cursor state icons

                 It may be possible to use system icons representing
                 cursor interaction states such as hourglasses or resize
                 arrows by using features :class:``~arcade.Window`` inherits
                 from the underlying pyglet window class. See the
                 `pyglet overview on cursors
                 <https://pyglet.readthedocs.io/en/master/programming_guide/mouse.html#changing-the-mouse-cursor>`_
                 for more information.

        Args:
            visible: Whether to hide the system mouse cursor
        """
        super().set_mouse_cursor_visible(visible)

    def on_action(self, action_name: str, state) -> None:
        """
        Called when an action is dispatched.
        This is related to the input manager / controller support.

        Args:
            action_name:
                The name of the action
            state:
                The state of the action
        """
        pass

    def on_key_press(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        """
        Called once when a key gets pushed down.

        Override this function to add key press functionality.

        .. tip:: If you want the length of key presses to affect
                 gameplay, you also need to override
                 :meth:`~.Window.on_key_release`.

        Args:
            symbol:
                Key that was just pushed down
            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return EVENT_UNHANDLED

    def on_key_release(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        """
        Called once when a key gets released.

        Override this function to add key release functionality.

        Situations that require handling key releases include:

        * Rhythm games where a note must be held for a certain
          amount of time
        * 'Charging up' actions that change strength depending on
          how long a key was pressed
        * Showing which keys are currently pressed down

        Args:
            symbol (int): Key that was released
            modifiers (int): Bitwise 'and' of all modifiers (shift,
                      ctrl, num lock) active during this event.
                      See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return EVENT_UNHANDLED

    def before_draw(self) -> None:
        """
        New event in base pyglet window. This is current unused in Arcade.
        """
        pass

    def on_draw(self) -> EVENT_HANDLE_STATE:
        """
        Override this function to add your custom drawing code.

        This method is usually called 60 times a second unless
        another update rate has been set. Should be called after
        :meth:`~arcade.Window.on_update`.

        This function should normally start with a call to
        :meth:`~arcade.Window.clear` to clear the screen.
        """
        if self._start_finish_render_data:
            self.clear()
            self._start_finish_render_data.draw()
            return True

        return EVENT_UNHANDLED

    def _on_resize(self, width: int, height: int) -> EVENT_HANDLE_STATE:
        """
        The internal method called when the window is resized.

        The purpose of this method is mainly setting the viewport
        to the new size of the window. Users should override
        :meth:`~arcade.Window.on_resize` instead. This method is
        called first.

        Args:
            width: New width of the window
            height: New height of the window
        """
        # Retain viewport
        self.viewport = (0, 0, width, height)

        return EVENT_UNHANDLED

    def on_resize(self, width: int, height: int) -> EVENT_HANDLE_STATE:
        """
        Override this method to add custom actions when the window is resized.

        An internal ``_on_resize`` is called first adjusting the viewport
        to the new size of the window so there is no need to call
        ```super().on_resize(width, height)```.

        Args:
            width: New width of the window
            height: New height of the window
        """
        pass

    def set_minimum_size(self, width: int, height: int) -> None:
        """
        Set the minimum size of the window.

        This will limit how small the window can be resized.

        Args:
            width: Minimum width
            height: Minimum height
        """
        super().set_minimum_size(width, height)

    def set_maximum_size(self, width: int, height: int) -> None:
        """
        Sets the maximum size of the window.

        This will limit how large the window can be resized.

        Args:
            width: Maximum width
            height: Maximum height
        """
        super().set_maximum_size(width, height)

    def set_size(self, width: int, height: int) -> None:
        """
        Resize the window.

        Args:
            width: New width of the window
            height: New height of the window
        """
        super().set_size(width, height)

    def get_size(self) -> tuple[int, int]:
        """Get the size of the window."""
        return super().get_size()

    def get_location(self) -> tuple[int, int]:
        """Get the current X/Y coordinates of the window."""
        return super().get_location()  # type: ignore # Window typed at runtime

    def set_visible(self, visible: bool = True):
        """
        Set if the window should be visible or not.

        Args:
            visible (bool): Should the window be visible?
        """
        super().set_visible(visible)

    def use(self) -> None:
        """Make the window the target for drawing.

        The window will always be the target for drawing unless
        offscreen framebuffers are used in the application.

        This simply binds the window's framebuffer.
        """
        self.ctx.screen.use()

    @property
    def default_camera(self) -> DefaultProjector:
        """
        The default camera for the window.

        This is an extremely simple camera simply responsible for
        maintaining the default projection and viewport.
        """
        return self._ctx._default_camera

    @property
    def current_camera(self) -> Projector:
        """
        Get or set the current camera.

        This represents the projector currently being used to define
        the projection and view matrices.
        """
        return self._ctx.current_camera

    @current_camera.setter
    def current_camera(self, next_camera):
        self._ctx.current_camera = next_camera

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """
        Get/set the viewport of the window.

        This will define what area of the window is rendered into.
        The values are ``x, y, width, height``. The value will normally
        be ``(0, 0, screen width, screen height)``.

        In most case you don't want to change this value manually
        and instead rely on the cameras.
        """
        return self._ctx.screen.viewport

    @viewport.setter
    def viewport(self, new_viewport: tuple[int, int, int, int]):
        if self._ctx.screen == self._ctx.active_framebuffer:
            self._ctx.viewport = new_viewport
        else:
            self._ctx.screen.viewport = new_viewport

    def test(self, frames: int = 10) -> None:
        """
        Used by unit test cases. Runs the event loop a few times and stops.

        Args:
            frames: How many frames to run the event loop for.
        """
        start_time = time.time()
        for _ in range(frames):
            self.switch_to()
            self.dispatch_events()
            self.dispatch_event("on_draw")
            self.flip()
            current_time = time.time()
            elapsed_time = current_time - start_time
            start_time = current_time
            if elapsed_time < 1.0 / 60.0:
                sleep_time = (1.0 / 60.0) - elapsed_time
                time.sleep(sleep_time)
            self._dispatch_updates(1 / 60)

    def show_view(self, new_view: View) -> None:
        """
        Set the currently active view.

        This will hide the current view
        and show the new view in the next frame.

        This is not a blocking call. It will simply point to the new view
        and return immediately.

        Calling this function is the same as setting the
        :py:attr:`arcade.Window.current_view` attribute.

        Args:
            new_view: The view to activate.
        """
        if not isinstance(new_view, View):
            raise TypeError(
                f"Window.show_view() takes an arcade.View, but it got a {type(new_view)}."
            )

        self._ctx.screen.use()
        self.viewport = (0, 0, self.width, self.height)

        # Store the Window that is showing the "new_view" View.
        if new_view.window is None:
            new_view.window = self
        # NOTE: This is not likely to happen and is creating issues for the test suite.
        # elif new_view.window != self:
        #     raise RuntimeError((
        #         "You are attempting to pass the same view "
        #         "object between multiple windows. A single "
        #         "view object can only be used in one window. "
        #         f"{self} != {new_view.window}"
        #     ))

        # remove previously shown view's handlers
        if self._current_view is not None:
            self._current_view.on_hide_view()
            self.remove_handlers(self._current_view)

        # push new view's handlers
        self._current_view = new_view

        # Note: Excluding on_show because this even can trigger multiple times.
        #       It should only be called once when the view is shown.
        view_handlers = {
            event_type: getattr(new_view, event_type, None)
            for event_type in self.event_types
            if event_type != "on_show" and hasattr(new_view, event_type)
        }
        if view_handlers:
            self.push_handlers(**view_handlers)
        self._current_view.on_show_view()

        # Note: After the View has been pushed onto pyglet's stack of event handlers
        # (via push_handlers()), pyglet
        # will still call the Window's event handlers.
        # (See pyglet's EventDispatcher.dispatch_event() implementation for details)

    def hide_view(self) -> None:
        """
        Hide the currently active view (if any).

        This is only necessary if you don't want an active view
        falling back to the window's event handlers. It's not
        necessary to call when changing the active view.
        """
        if self._current_view is None:
            return

        self._current_view.on_hide_view()
        self.remove_handlers(self._current_view)
        self._current_view = None

    def switch_to(self) -> None:
        """Switch the this window context.

        This is normally only used in multi-window applications.
        """
        super().switch_to()  # type: ignore # Window typed at runtime

    def set_caption(self, caption) -> None:
        """Set the caption/title of the window."""
        super().set_caption(caption)  # type: ignore # Window typed at runtime

    def set_location(self, x, y) -> None:
        """Set location of the window."""
        super().set_location(x, y)  # type: ignore # Window typed at runtime

    def activate(self) -> None:
        """Activate this window."""
        super().activate()  # type: ignore # Window typed at runtime

    def minimize(self) -> None:
        """Minimize the window."""
        super().minimize()  # type: ignore # Window typed at runtime

    def maximize(self) -> None:
        """Maximize  the window."""
        super().maximize()  # type: ignore # Window typed at runtime

    def set_vsync(self, vsync: bool) -> None:
        """Set if we sync our draws to the monitors vertical sync rate."""
        super().set_vsync(vsync)

    def set_mouse_cursor_platform_visible(self, platform_visible=None) -> None:
        """
        .. warning:: You are probably looking for
                     :meth:`~.Window.set_mouse_cursor_visible`!

        This is a lower level function inherited from the pyglet window.

        For more information on what this means, see the documentation
        for :py:meth:`pyglet.window.Window.set_mouse_cursor_platform_visible`.
        """
        super().set_mouse_cursor_platform_visible(platform_visible)

    def set_exclusive_mouse(self, exclusive=True) -> None:
        """Capture the mouse."""
        super().set_exclusive_mouse(exclusive)

    def set_exclusive_keyboard(self, exclusive=True) -> None:
        """Capture all keyboard input."""
        super().set_exclusive_keyboard(exclusive)

    def get_system_mouse_cursor(self, name) -> MouseCursor:
        """Get the system mouse cursor"""
        return super().get_system_mouse_cursor(name)

    def dispatch_events(self) -> None:
        """Dispatch events"""
        super().dispatch_events()  # type: ignore # Window typed at runtime

    def on_mouse_enter(self, x: int, y: int) -> EVENT_HANDLE_STATE:
        """
        Called once whenever the mouse enters the window area on screen.

        This event will not be triggered if the mouse is currently being
        dragged.

        Args:
            x: The x position the mouse entered the window
            y: The y position the mouse entered the window
        """
        pass

    def on_mouse_leave(self, x: int, y: int) -> EVENT_HANDLE_STATE:
        """
        Called once whenever the mouse leaves the window area on screen.

        This event will not be triggered if the mouse is currently being
        dragged. Note that the coordinates of the mouse pointer will be
        outside of the window rectangle.

        Args:
            x: The x position the mouse entered the window
            y: The y position the mouse entered the window
        """
        pass

    @property
    def center(self) -> tuple[float, float]:
        """
        Returns center coordinates of the window

        Equivalent to ``(self.width / 2, self.height / 2)``.
        """
        return (self.width / 2, self.height / 2)

    @property
    def center_x(self) -> float:
        """
        Returns the center x-coordinate of the window.

        Equivalent to ``self.width / 2``.
        """
        return self.width / 2

    @property
    def center_y(self) -> float:
        """
        Returns the center y-coordinate of the window.

        Equivalent to ``self.height / 2``.
        """
        return self.height / 2

    # --- CLOCK ALIASES ---
    @property
    def time(self) -> float:
        """
        Shortcut to the global clock's time.

        This is the time in seconds since the application started.
        """
        return GLOBAL_CLOCK.time

    @property
    def fixed_time(self) -> float:
        """
        Shortcut to the fixed clock's time.

        This is the time in seconds since the application started
        but updated at a fixed rate.
        """
        return GLOBAL_FIXED_CLOCK.time

    @property
    def delta_time(self) -> float:
        """Shortcut for the global clock's delta_time."""
        return GLOBAL_CLOCK.delta_time

    @property
    def fixed_delta_time(self) -> float:
        """The configured fixed update rate"""
        return self._fixed_rate

    # required because pyglet marks the method as abstract methods,
    # but resolves class during runtime
    def _create(self) -> None:
        """Internal method to create the window."""
        super()._create()  # type: ignore

    def _recreate(self, changes: Sequence[str]) -> None:
        super()._recreate(changes)  # type: ignore


def open_window(
    width: int,
    height: int,
    window_title: str | None = None,
    resizable: bool = False,
    antialiasing: bool = True,
    **kwargs,
) -> Window:
    """
    Shortcut for opening/creating a window with less options.

    For a full set of window options, create a :py:class:`~arcade.Window`
    instance directly.

    Args:
        width:
            Width of the window.
        height:
            Height of the window.
        window_title:
            Title/caption of the window.
        resizable:
            Whether the user can resize the window.
        antialiasing:
            Whether to use antialiasing
        **kwargs:
            Additional keyword arguments to pass to the window constructor.
    """
    global _window
    _window = Window(
        width, height, window_title, resizable=resizable, antialiasing=antialiasing, **kwargs
    )
    _window.invalid = False
    return _window

#-------------------------------------------------------------------------------------------------------------#
class View:

    """
    A view is a way to separate drawing and logic from the window itself.
    Subclassing the window is very inflexible since you can't easily switch
    your update and draw logic.

    A view is a way to encapsulate that logic, so you can easily switch between
    different parts of your game. Maybe you have a title screen, a game screen,
    and a game over screen. Each of these could be a different view.

    Args:
        window:
            The window this view is associated with. If None, the current
            window is used. (Normally you don't need to provide this).
    """

    def __init__(
        self, window: Window | None = None, background_color: RGBOrA255 | None = None
    ) -> None:
        self.window = arcade.get_window() if window is None else window
        self._background_color: Color | None = background_color and Color.from_iterable(
            background_color
        )

    def clear(
        self,
        color: RGBOrA255 | None = None,
        color_normalized: RGBANormalized | None = None,
        viewport: tuple[int, int, int, int] | None = None,
    ) -> None:
        """
        Clears the window with the configured background color
        set through :py:attr:`arcade.View.background_color`.

        Args:
            color:
                override the current background color with one of the following:

                1. A :py:class:`~arcade.types.Color` instance
                2. A 3 or 4-length RGB/RGBA :py:class:`tuple` of byte values (0 to 255)
            color_normalized:
                Override the current background color using normalized values (0.0 to 1.0).
                For example, (1.0, 0.0, 0.0, 1.0) making the window contents red.
            viewport:
                The viewport range to clear
        """
        if color is None and color_normalized is None:
            color = self.background_color
        self.window.clear(color=color, color_normalized=color_normalized, viewport=viewport)

    def on_update(self, delta_time: float) -> bool | None:
        """
        This method can be implemented and is reserved for game logic.
        Move sprites. Perform collision checks and other game logic.
        This method is called every frame before :meth:`on_draw`.

        The ``delta_time`` can be used to make sure the game runs at the same
        speed, no matter the frame rate.

        Args:
            delta_time:
                Time interval since the last time the function was called in seconds.
        """
        pass

    def on_fixed_update(self, delta_time: float):
        """
        Called for each fixed update. This is useful for physics engines
        and other systems that should update at a constant rate.

        Args:
            delta_time:
                Time interval since the last time the function was called in seconds.
        """
        pass

    def on_draw(self) -> bool | None:
        """
        Override this function to add your custom drawing code.

        This method is usually called 60 times a second unless
        another update rate has been set. Should be called after
        :meth:`~arcade.Window.on_update`.

        This function should normally start with a call to
        :meth:`~arcade.Window.clear` to clear the screen.
        """
        pass

    def on_show_view(self) -> None:
        """Called once when the view is shown.

        .. seealso:: :py:meth:`~arcade.View.on_hide_view`
        """
        pass

    def on_hide_view(self) -> None:
        """Called once when this view is hidden."""
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        """
        Called repeatedly while the mouse is moving in the window area.

        Override this function to respond to changes in mouse position.

        Args:
            x: x position of mouse within the window in pixels
            y: y position of mouse within the window in pixels
            dx: Change in x since the last time this method was called
            dy: Change in y since the last time this method was called
        """
        pass

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        """
        Called once whenever a mouse button gets pressed down.

        Override this function to handle mouse clicks. For an example of
        how to do this, see Arcade's built-in :ref:`aiming and shooting
        bullets <sprite_bullets_aimed>` demo.

        Args:
            x:
                x position of the mouse
            y:
                y position of the mouse
            button:
                What button was pressed. This will always be one of the following:

                - ``arcade.MOUSE_BUTTON_LEFT``
                - ``arcade.MOUSE_BUTTON_RIGHT``
                - ``arcade.MOUSE_BUTTON_MIDDLE``

            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        pass

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, _buttons: int, _modifiers: int
    ) -> bool | None:
        """
        Called repeatedly while the mouse moves with a button down.

        Override this function to handle dragging.

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            dx:
                Change in x since the last time this method was called
            dy:
                Change in y since the last time this method was called
            _buttons:
                Which button is pressed
            _modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        self.on_mouse_motion(x, y, dx, dy)
        return False

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        """
        Called once whenever a mouse button gets released.

        Override this function to respond to mouse button releases. This
        may be useful when you want to use the duration of a mouse click
        to affect gameplay.

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            button:
                What button was hit. One of:

                - ``arcade.MOUSE_BUTTON_LEFT``
                - ``arcade.MOUSE_BUTTON_RIGHT``
                - ``arcade.MOUSE_BUTTON_MIDDLE``

            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock)
                active during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        pass

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
        """
        Called repeatedly while a mouse scroll wheel moves.

        Override this function to respond to scroll events. The scroll
        arguments may be positive or negative to indicate direction, but
        the units are unstandardized. How many scroll steps you receive
        may vary wildly between computers depending a number of factors,
        including system settings and the input devices used (i.e. mouse
        scrollwheel, touch pad, etc).

        .. warning:: Not all users can scroll easily!

            Only some input devices support horizontal
            scrolling. Standard vertical scrolling is common,
            but some laptop touch pads are hard to use.

            This means you should be careful about how you use
            scrolling. Consider making it optional
            to maximize the number of people who can play your
            game!

        Args:
            x:
                x position of mouse
            y:
                y position of mouse
            scroll_x:
                number of steps scrolled horizontally
                since the last call of this function
            scroll_y:
                number of steps scrolled vertically since
                the last call of this function
        """
        pass

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """
        Called once when a key gets pushed down.

        Override this function to add key press functionality.

        .. tip:: If you want the length of key presses to affect
                 gameplay, you also need to override
                 :meth:`~.Window.on_key_release`.

        Args:
            symbol:
                Key that was just pushed down
            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock) active
                during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return False

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """
        Called once when a key gets released.

        Override this function to add key release functionality.

        Situations that require handling key releases include:

        * Rhythm games where a note must be held for a certain
          amount of time
        * 'Charging up' actions that change strength depending on
          how long a key was pressed
        * Showing which keys are currently pressed down

        Args:
            symbol:
                Key that was released
            modifiers:
                Bitwise 'and' of all modifiers (shift, ctrl, num lock) active
                during this event. See :ref:`pg_simple_input_keyboard_modifiers`.
        """
        return False

    def on_resize(self, width: int, height: int) -> bool | None:
        """
        Override this method to add custom actions when the window is resized.

        An internal ``_on_resize`` is called first adjusting the viewport
        to the new size of the window so there is no need to call
        ```super().on_resize(width, height)```.

        Args:
            width: New width of the window
            height: New height of the window
        """
        pass

    def on_mouse_enter(self, x: int, y: int) -> bool | None:
        """
        Called once whenever the mouse enters the window area on screen.

        This event will not be triggered if the mouse is currently being
        dragged.

        Args:
            x: The x position the mouse entered the window
            y: The y position the mouse entered the window
        """
        pass

    def on_mouse_leave(self, x: int, y: int) -> bool | None:
        """
        Called once whenever the mouse leaves the window area on screen.

        This event will not be triggered if the mouse is currently being
        dragged. Note that the coordinates of the mouse pointer will be
        outside of the window rectangle.

        Args:
            x: The x position the mouse entered the window
            y: The y position the mouse entered the window
        """
        pass

    @property
    def size(self) -> tuple[float, float]:
        """
        An alias for `arcade.Window.size`
        """
        return self.window.size

    @property
    def width(self) -> float:
        """
        An alias for `arcade.Window.width`
        """
        return self.window.width

    @property
    def height(self) -> float:
        """
        An alias for `arcade.Window.height`
        """
        return self.window.height

    @property
    def center(self) -> tuple[float, float]:
        """
        An alias for `arcade.Window.center`
        """
        return self.window.center

    @property
    def center_x(self) -> float:
        """
        An alias for `arcade.Window.center_x`
        """
        return self.window.center_x

    @property
    def center_y(self) -> float:
        """
        An alias for `arcade.Window.center_y`
        """
        return self.window.center_y

    @property
    def background_color(self) -> Color | None:
        """
        Get or set the background color for this view.
        This affects what color the window will contain when
        :py:meth:`~arcade.View.clear` is called.

        Examples::

            # Use Arcade's built in Color values
            view.background_color = arcade.color.AMAZON

            # Set the background color with a custom Color instance
            MY_RED = arcade.types.Color(255, 0, 0)
            view.background_color = MY_RED

            # Set the background color directly from an RGBA tuple
            view.background_color = 255, 0, 0, 255

            # Set the background color directly from an RGB tuple
            # RGB tuples will assume 255 as the opacity / alpha value
            view.background_color = 255, 0, 0
        """
        return self._background_color

    @background_color.setter
    def background_color(self, value: RGBOrA255) -> None:

        self._background_color = Color.from_iterable(value)






class Camera2D:
    """
    A simple orthographic camera.

    It provides properties to access every important variable for controlling the camera.
    3D properties such as pos, and up are constrained to a 2D plane. There is no access to the
    forward vector (as a property).

    There are also ease of use methods for matching the viewport and projector to the window size.

    Provides many helpful values:
        * The position and rotation or the camera
        * 8 positions along the edge of the camera's viewable area
        * the bounding box of the area the camera sees
        * Viewport, and Scissor box for controlling where to draw to

    .. warning:: Do not replace the ``camera_data`` and ``projection_data``
                 instances after initialization!

    Replacing the camera data and projection data may break controllers. Their
    contents are exposed via properties rather than directly to prevent this.

    Args:
        viewport:
            A ``Rect`` which defines the pixel bounds which the camera fits its image to.
            If the viewport is not 1:1 with the projection then positions in world space
            won't match pixels on screen.
        position:
            The 2D position of the camera.

            This is in world space, so the same as :py:class:`Sprite` and draw commands.
            The default projection is a :py:func:`XYWH` rect positioned at (0, 0) so the
            position of the camera is the center of the viewport.
        up:
            A 2D vector which describes which direction is up
            (defines the +Y-axis of the camera space).
        zoom:
            A scalar value which is inversely proportional to the size of the
            camera projection. i.e. a zoom of 2.0 halves the size of the projection,
            doubling the perceived size of objects.
        projection:
            A ``Rect`` which defines the world space
            bounds which the camera projects to the viewport.
        near:
            The near clipping plane of the camera.
        far:
            The far clipping plane of the camera.
        aspect: The ratio between width and height that the viewport should
            be constrained to. If unset then the viewport just matches the given
            size. The aspect ratio describes how much larger the width should be
            compared to the height. i.e. for an aspect ratio of ``4:3`` you should
            input ``4.0/3.0`` or ``1.33333...``. Cannot be equal to zero.
        scissor:
            A ``Rect`` which will crop the camera's output to this area on screen.
            Unlike the viewport this has no influence on the visuals rendered with
            the camera only the area shown.
        render_target:
            The FrameBuffer that the camera may use. Warning if the target isn't the screen
            it won't automatically show up on screen.
        window:
            The Arcade Window to bind the camera to. Defaults to the currently active window.
    """

    def __init__(
        self,
        viewport: Rect | None = None,
        position: Point2 | None = None,
        up: tuple[float, float] = (0.0, 1.0),
        zoom: float = 1.0,
        projection: Rect | None = None,
        near: float = DEFAULT_NEAR_ORTHO,
        far: float = DEFAULT_FAR,
        *,
        aspect: float | None = None,
        scissor: Rect | None = None,
        render_target: Framebuffer | None = None,
        window: Window | None = None,
    ):
        self._window: Window = window or get_window()
        self.render_target: Framebuffer | None = render_target
        """
        An optional framebuffer to activate at the same time as
        the projection data, could be the screen, or an offscreen texture
        """

        # We don't want to force people to use a render target,
        # but we need to have some form of default size.
        render_target = render_target or self._window.ctx.screen
        viewport = viewport or LBWH(*render_target.viewport)

        if not isinstance(viewport, Rect):
            raise TypeError("viewport must be a Rect type,use arcade.LBWH or arcade.types.Viewport")

        if aspect is None:
            width, height = viewport.size
        elif aspect == 0.0:
            raise ZeroProjectionDimension(
                "aspect ratio is 0 which will cause invalid viewport dimensions."
            )
        elif viewport.height * aspect < viewport.width:
            width = viewport.height * aspect
            height = viewport.height
        else:
            width = viewport.width
            height = viewport.width / aspect
        viewport = XYWH(viewport.x, viewport.y, width, height)

        half_width = width / 2
        half_height = height / 2

        # Unpack projection, but only validate when it's given directly
        left, right, bottom, top = (
            (-half_width, half_width, -half_height, half_height)
            if projection is None
            else projection.lrbt
        )

        if projection is not None:
            if left == right:
                raise ZeroProjectionDimension(
                    f"projection width is 0 due to equal {left=} and {right=} values"
                )
            if bottom == top:
                raise ZeroProjectionDimension(
                    f"projection height is 0 due to equal {bottom=} and {top=}"
                )
        if near == far:
            raise ZeroProjectionDimension(
                f"projection depth is 0 due to equal {near=} and {far=} values"
            )

        # By using -left and -bottom this ensures that (0.0, 0.0) is always
        # in the bottom left corner of the viewport
        pos_x = position[0] if position is not None else -left
        pos_y = position[1] if position is not None else -bottom
        self._camera_data = CameraData(
            position=(pos_x, pos_y, 0.0),
            up=(up[0], up[1], 0.0),
            forward=(0.0, 0.0, -1.0),
            zoom=zoom,
        )
        self._projection_data: OrthographicProjectionData = OrthographicProjectionData(
            left=left, right=right, top=top, bottom=bottom, near=near, far=far
        )

        self.viewport = viewport

        """
        A rect which describes how the final projection should be mapped
        from unit-space. defaults to the size of the render_target or window
        """

        self.scissor: Rect | None = scissor
        """
        An optional rect which describes what pixels of the active render
        target should be drawn to when undefined the viewport rect is used.
        """

    @classmethod
    def from_camera_data(
        cls,
        *,
        camera_data: CameraData | None = None,
        projection_data: OrthographicProjectionData | None = None,
        render_target: Framebuffer | None = None,
        viewport: Rect | None = None,
        scissor: Rect | None = None,
        window: Window | None = None,
    ) -> Self:
        """
        Make a ``Camera2D`` directly from data objects.

        This :py:class:`classmethod` allows advanced users to:

        #. skip or replace the default validation
        #. share ``camera_data`` or ``projection_data`` between cameras

        .. warning:: Be careful when sharing data objects!
                    **Any** action on a camera which changes a shared
                    object changes it for **every** camera which uses
                    the same object.

        .. list-table::
          :header-rows: 1

          * - Shared Value
            - Example Use(s)
          * - ``camera_data``
            - Mini-maps, reflection, and ghosting effects.
          * - ``projection_data``
            - Simplified rendering configuration
          * - ``render_target``
            - Complex rendering setups

        Args:
            camera_data:
                A :py:class:`~arcade.camera.CameraData`
                describing the position, up, forward and zoom.
            projection_data:
                A :py:class:`~arcade.camera.OrthographicProjectionData`
                which describes the left, right, top, bottom, far, near
                planes and the viewport for an orthographic projection.
            render_target:
                A non-screen :py:class:`~arcade.gl.framebuffer.Framebuffer` for this
                camera to draw into. When specified,

                * nothing will draw directly to the screen
                * the buffer's internal viewport will be ignored

            viewport:
                A viewport as a :py:class:`~arcade.types.rect.Rect`.
                This overrides any viewport the ``render_target`` may have.
            scissor:
                The OpenGL scissor box to use when drawing.
            window: The Arcade Window to bind the camera to.
                Defaults to the currently active window.
        """

        if projection_data:
            left, right = projection_data.left, projection_data.right
            if projection_data.left == projection_data.right:
                raise ZeroProjectionDimension(
                    f"projection width is 0 due to equal {left=}and {right=} values"
                )
            bottom, top = projection_data.bottom, projection_data.top
            if bottom == top:
                raise ZeroProjectionDimension(
                    f"projection height is 0 due to equal {bottom=}and {top=}"
                )
            near, far = projection_data.near, projection_data.far
            if near == far:
                raise ZeroProjectionDimension(
                    f"projection depth is 0 due to equal {near=}and {far=} values"
                )

        # build a new camera with defaults and then apply the provided camera objects.
        new_camera = cls(
            render_target=render_target, window=window, viewport=viewport, scissor=scissor
        )

        if camera_data is not None:
            new_camera._camera_data = camera_data
        if projection_data is not None:
            new_camera._projection_data = projection_data

        return new_camera

    def use(self) -> None:
        """
        Set internal projector as window projector,
        and set the projection and view matrix.
        call every time you want to 'look through' this camera.

        If you want to use a 'with' block use activate() instead.
        """
        if self.render_target is not None:
            self.render_target.use()
        self._window.current_camera = self

        _projection = generate_orthographic_matrix(self.projection_data, self.zoom)
        _view = generate_view_matrix(self.view_data)

        self._window.ctx.viewport = self._viewport.lbwh_int
        self._window.ctx.scissor = None if not self.scissor else self.scissor.lbwh_int
        self._window.projection = _projection
        self._window.view = _view

    @contextmanager
    def activate(self) -> Generator[Self, None, None]:
        """
        Set internal projector as window projector,
        and set the projection and view matrix.

        This method works with 'with' blocks.
        After using this method it automatically resets
        the projector to the one previously in use.
        """
        previous_projection = self._window.current_camera
        previous_framebuffer = self._window.ctx.active_framebuffer
        try:
            self.use()
            yield self
        finally:
            previous_framebuffer.use()
            previous_projection.use()

    def project(self, world_coordinate: Point) -> Vec2:
        """
        Take a Vec2 or Vec3 of coordinates and return the related screen coordinate
        """
        _projection = generate_orthographic_matrix(self.projection_data, self.zoom)
        _view = generate_view_matrix(self.view_data)

        return project_orthographic(
            world_coordinate,
            self._viewport.lbwh_int,
            _view,
            _projection,
        )

    def unproject(self, screen_coordinate: Point) -> Vec3:
        """
        Take in a pixel coordinate from within
        the range of the window size and returns
        the world space coordinates.

        Essentially reverses the effects of the projector.

        Args:
            screen_coordinate: A 2D or 3D position in pixels from the bottom left of the screen.
        Returns:
            A 3D vector in world space (same as sprites).
            perfect for finding if the mouse overlaps with a sprite or ui element irrespective
            of the camera.
        """

        _projection = generate_orthographic_matrix(self.projection_data, self.zoom)
        _view = generate_view_matrix(self.view_data)
        return unproject_orthographic(
            screen_coordinate, self._viewport.lbwh_int, _view, _projection
        )

    def equalize(self) -> None:
        """
        Forces the projection to match the size of the viewport.
        When matching the projection to the viewport the method keeps
        the projections center in the same relative place.
        """
        x, y = self._projection_data.rect.x, self._projection_data.rect.y
        self._projection_data.rect = XYWH(x, y, self.viewport_width, self.viewport_height)

    def match_window(
        self,
        viewport: bool = True,
        projection: bool = True,
        scissor: bool = True,
        position: bool = False,
        aspect: float | None = None,
    ) -> None:
        """
        Sets the viewport to the size of the window.
        Should be called when the window is resized.

        Args:
            viewport: Flag whether to equalise the viewport to the value.
            projection: Flag whether to also equalize the projection to the viewport.
                On by default
            scissor: Flag whether to also equalize the scissor box to the viewport.
                On by default
            position: Flag whether to position the camera so that (0.0, 0.0) is in
                the bottom-left of the viewport
            aspect: The ratio between width and height that the viewport should
                be constrained to. If unset then the viewport just matches the window
                size. The aspect ratio describes how much larger the width should be
                compared to the height. i.e. for an aspect ratio of ``4:3`` you should
                input ``4.0/3.0`` or ``1.33333...``. Cannot be equal to zero.
        """
        self.update_values(
            self._window.rect,
            viewport=viewport,
            projection=projection,
            scissor=scissor,
            position=position,
            aspect=aspect,
        )

    def match_target(
        self,
        viewport: bool = True,
        projection: bool = True,
        scissor: bool = True,
        position: bool = False,
        aspect: float | None = None,
    ) -> None:
        """
        Sets the viewport to the size of the Camera2D's render target.

        Args:
            viewport: Flag whether to equalize the viewport to the area of the render target
            projection: Flag whether to equalize the size of the projection to
                match the render target.
                The projection center stays fixed, and the new projection matches only in size.
            scissor: Flag whether to update the scissor value.
            position: Flag whether to position the camera so that (0.0, 0.0) is in
                the bottom-left of the viewport
            aspect: The ratio between width and height that the value should
                be constrained to. i.e. for an aspect ratio of ``4:3`` you should
                input ``4.0/3.0`` or ``1.33333...``. Cannot be equal to zero.
                If unset then the value will not be updated.
        Raises:
            ValueError: Will be raised if the Camera2D was has no render target.
        """
        if self.render_target is None:
            raise ValueError(
                "Tried to match a non-exsistant render target. Please use `match_window` instead"
            )

        self.update_values(
            LRBT(*self.render_target.viewport),
            viewport,
            projection,
            scissor,
            position,
            aspect=aspect,
        )

    def update_values(
        self,
        value: Rect,
        viewport: bool = True,
        projection: bool = True,
        scissor: bool = True,
        position: bool = False,
        aspect: float | None = None,
    ):
        """
        Convenience method for updating the viewport, projection, position
        and a few others with the same value.

        Args:
            value: The rect that the values will be derived from.
            viewport: Flag whether to equalize the viewport to the value.
            projection: Flag whether to equalize the size of the projection to match the value.
                The projection center stays fixed, and the new projection matches only in size.
            scissor: Flag whether to update the scissor value.
            position: Flag whether to position the camera so that (0.0, 0.0) is in
                the bottom-left of the viewport
            aspect: The ratio between width and height that the value should
                be constrained to. i.e. for an aspect ratio of ``4:3`` you should
                input ``4.0/3.0`` or ``1.33333...``. Cannot be equal to zero.
                If unset then the value will not be updated.
        """
        if aspect is not None:
            if aspect == 0.0:
                raise ZeroProjectionDimension(
                    "aspect ratio is 0 which will cause invalid viewport dimensions."
                )
            elif value.height * aspect < value.width:
                w = value.height * aspect
                h = value.height
            else:
                w = value.width
                h = value.width / aspect
            value = XYWH(value.x, value.y, w, h)

        self.viewport = value

        if projection:
            x, y = self._projection_data.rect.x, self._projection_data.rect.y
            self._projection_data.rect = XYWH(x, y, value.width, value.height)

        if scissor and self.scissor:
            self.scissor = value

        if position:
            self._camera_data.position = (
                -self._projection_data.left,
                -self._projection_data.bottom,
                self._camera_data.position[2],
            )

    def aabb(self) -> Rect:
        """
        Retrieve the axis-aligned bounds box of the camera's view area.

        If the camera isn't rotated , this will be precisely the view area,
        but it will cover a larger area when it is rotated. Useful for CPU culling
        """
        up = self._camera_data.up
        ux, uy, *_ = up
        rx, ry = uy, -ux  # up x Z'

        l, r, b, t = self._viewport.lrbt
        x, y = self.position

        x_points = (
            x + ux * t + rx * l,  # top left
            x + ux * t + rx * r,  # top right
            x + ux * b + rx * l,  # bottom left
            x + ux * b + rx * r,  # bottom right
        )
        y_points = (
            y + uy * t + ry * l,  # top left
            y + uy * t + ry * r,  # top right
            y + uy * b + ry * l,  # bottom left
            y + uy * b + ry * r,  # bottom right
        )

        left = min(x_points)
        right = max(x_points)
        bottom = min(y_points)
        top = max(y_points)
        return LRBT(left=left, right=right, bottom=bottom, top=top)

    def point_in_view(self, point: Point2) -> bool:
        # TODO test
        """
        Take a 2D point in the world, and return whether the point is inside the
        visible area of the camera.
        """
        # This is unwrapped from standard Vec2 operations,
        # The construction and garbage collection of the vectors would
        # increase this method's cost by ~4x

        pos = self.position
        diff = point[0] - pos[0], point[1] - pos[1]

        up = self._camera_data.up

        h_width = self.width / 2.0
        h_height = self.height / 2.0

        dot_x = up[1] * diff[0] - up[0] * diff[1]
        dot_y = up[0] * diff[0] + up[1] * diff[1]

        return abs(dot_x) <= h_width and abs(dot_y) <= h_height

    def move_to(self, position: Point2, *, duration: float | None = None) -> Point2:
        """
        Move the camera to the provided position.
        If duration is None this is the same as setting camera.position.
        duration makes it easy to move the camera smoothly over time.

        When duration is not None it uses :py:func:`arcade.math.smerp` method
        to smoothly move to the target position. This means duration does NOT
        equal the fraction to move. To make the motion frame rate independant
        use ``duration = dt * T`` where ``T`` is the number of seconds to move
        half the distance to the target position.

        Args:
            position: x, y position in world space to move too
            duration: The number of frames it takes to approximately move half-way
                to the target position

        Returns:
            The actual position the camera was set too.
        """
        if duration is None:
            x, y = position
            self._camera_data.position = (x, y, self._camera_data.position[2])
            return position

        x1, y1, z1 = self._camera_data.position
        x2, y2 = position
        d = pow(2, -duration)
        x = x1 + (x2 - x1) * d
        y = y1 + (y2 - y1) * d

        self._camera_data.position = (x, y, z1)
        return x, y

    def move_by(self, change: Point2) -> Point2:
        """
        Move the camera in world space along the XY axes by the provided change.
        If you want to drag the camera with a mouse :py:func:`camera2D.drag_by`
        is the method to use.

        Args:
            change: amount to move XY position in world space

        Returns:
            final XY position of the camera
        """
        pos = self._camera_data.position
        new = pos[0] + change[0], pos[1] + change[1]
        self._camera_data.position = new[0], new[1], pos[2]
        return new

    def drag_by(self, change: Point2) -> Point2:
        """
        Move the camera in world space by an amount in screen space.
        This is a utility method to make it easy to drag the camera correctly.
        normally zooming in/out, rotating the camera, and using a non 1:1 projection
        causes the mouse dragging to desync with the camera motion. It automatically
        negates the change so the change represents the amount the camera appears
        to move. This is because moving the camera left makes everything appear to
        move right. So a user moving the mouse right expects the camera to move
        left.

        The simplest use case is with the Window/View's :py:func:`on_mouse_drag`
        .. code-block:: python

            def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
                    self.camera.drag_by((dx, dy))

        .. warning:: This method is more expensive than :py:func:`Camera2D.move_by` so
                    use only when needed. If your camera is 1:1 with the screen and you
                    only zoom in and out you can get away with
                    ``camera2D.move_by(-change / camera.zoom)``.

        .. warning:: This method must assume that viewport has the same pixel scale as the
                    window. If you are doing some form of upscaling you will have to scale
                    the mouse dx and dy by the difference in pixel scale.

        Args:
            change: The number of pixels to move the camera by

        Returns:
            The final position of the camera.
        """

        # Early exit to avoid expensive matrix generation
        if change[0] == 0.0 and change[1] == 0.0:
            return self._camera_data.position[0], self._camera_data.position[1]

        x0, y0, _ = self.unproject((0, 0))
        xc, yc, _ = self.unproject(change)

        dx, dy = xc - x0, yc - y0
        pos = self._camera_data.position
        new = pos[0] - dx, pos[1] - dy
        self._camera_data.position = new[0], new[1], pos[2]
        return new

    @property
    def view_data(self) -> CameraData:
        """The view data for the camera.

        This includes:

        * the position
        * forward vector
        * up direction
        * zoom.

        Camera controllers use this property.
        """
        return self._camera_data

    @property
    def projection_data(self) -> OrthographicProjectionData:
        """The projection data for the camera.

        This is an Orthographic projection. with a
        right, left, top, bottom, near, and far value.

        An easy way to understand the use of the projection is
        that the right value of the projection tells the
        camera what value will be at the right most
        pixel in the viewport.

        Due to the view data having a zoom component
        most use cases will only change the projection
        on screen resize.
        """
        return self._projection_data

    @property
    def position(self) -> Vec2:
        """
        The 2D position of the camera.

        This is in world space, so the same as :py:class:`Sprite` and draw commands.
        The default projection is a :py:func:`XYWH` rect positioned at (0, 0) so the
        position of the camera is the center of the viewport.
        """
        return Vec2(self._camera_data.position[0], self._camera_data.position[1])

    # Setter with different signature will cause mypy issues
    # https://github.com/python/mypy/issues/3004
    @position.setter
    def position(self, pos: Point) -> None:
        x, y, *_z = pos
        z = self._camera_data.position[2] if not _z else _z[0]
        self._camera_data.position = (x, y, z)

    @property
    def x(self) -> float:
        """The 2D world position of the camera along the X axis"""
        return self._camera_data.position[0]

    @x.setter
    def x(self, x: float) -> None:
        pos = self._camera_data.position
        self._camera_data.position = (x, pos[1], pos[2])

    @property
    def y(self) -> float:
        """The 2D world position of the camera along the Y axis"""
        return self._camera_data.position[1]

    @y.setter
    def y(self, y: float) -> None:
        pos = self._camera_data.position
        self._camera_data.position = (pos[0], y, pos[2])

    @property
    def projection(self) -> Rect:
        """Get/set the left, right, bottom, and top projection values.

        These are world space values which control how the camera
        projects the world onto the pixel space of the current
        viewport area.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data

        .. warning:: The axis values cannot be equal!

                     * ``left`` cannot equal ``right``
                     * ``bottom`` cannot equal ``top``

        This property raises a :py:class:`~arcade.camera.data_types.ZeroProjectionDimension`
        exception if any axis pairs are equal. You can handle this
        exception as a :py:class:`ValueError`.
        """

        return self._projection_data.rect / self._camera_data.zoom

    @projection.setter
    def projection(self, value: Rect) -> None:
        # Unpack and validate
        if not value:
            raise ZeroProjectionDimension(f"Projection area is 0, {value.lrbt}")

        _z = self._camera_data.zoom

        # Modify the projection data itself.
        self._projection_data.rect = value * _z

    @property
    def width(self) -> float:
        """
        The width of the projection from left to right.
        This is in world space coordinates not pixel coordinates.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return (self._projection_data.right - self._projection_data.left) / self._camera_data.zoom

    @width.setter
    def width(self, new_width: float) -> None:
        w = self.width
        l = self.left / w  # Normalised Projection left
        r = self.right / w  # Normalised Projection Right

        self.left = l * new_width
        self.right = r * new_width

    @property
    def height(self) -> float:
        """
        The height of the projection from bottom to top.
        This is in world space coordinates not pixel coordinates.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return (self._projection_data.top - self._projection_data.bottom) / self._camera_data.zoom

    @height.setter
    def height(self, new_height: float) -> None:
        h = self.height
        b = self.bottom / h  # Normalised Projection Bottom
        t = self.top / h  # Normalised Projection Top

        self.bottom = b * new_height
        self.top = t * new_height

    @property
    def left(self) -> float:
        """
        The left edge of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return self._projection_data.left / self._camera_data.zoom

    @left.setter
    def left(self, new_left: float) -> None:
        self._projection_data.left = new_left * self._camera_data.zoom

    @property
    def right(self) -> float:
        """
        The right edge of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return self._projection_data.right / self._camera_data.zoom

    @right.setter
    def right(self, new_right: float) -> None:
        self._projection_data.right = new_right * self._camera_data.zoom

    @property
    def bottom(self) -> float:
        """
        The bottom edge of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return self._projection_data.bottom / self._camera_data.zoom

    @bottom.setter
    def bottom(self, new_bottom: float) -> None:
        self._projection_data.bottom = new_bottom * self._camera_data.zoom

    @property
    def top(self) -> float:
        """
        The top edge of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS scaled by zoom.
                  If this isn't what you want,
                  you have to calculate the value manually from projection_data
        """
        return self._projection_data.top / self._camera_data.zoom

    @top.setter
    def top(self, new_top: float) -> None:
        self._projection_data.top = new_top * self._camera_data.zoom

    @property
    def projection_near(self) -> float:
        """
        The near plane of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS NOT scaled by zoom.
        """
        return self._projection_data.near

    @projection_near.setter
    def projection_near(self, new_near: float) -> None:
        self._projection_data.near = new_near

    @property
    def projection_far(self) -> float:
        """
        The far plane of the projection in world space.
        This is not adjusted with the camera position.

        .. note:: this IS NOT scaled by zoom.
        """
        return self._projection_data.far

    @projection_far.setter
    def projection_far(self, new_far: float) -> None:
        self._projection_data.far = new_far

    @property
    def viewport(self) -> Rect:
        return self._viewport

    @viewport.setter
    def viewport(self, viewport: Rect) -> None:
        if not isinstance(viewport, Rect):
            raise TypeError("viewport must be a Rect type,use arcade.LBWH or arcade.types.Viewport")

        self._viewport = viewport

    @property
    def viewport_width(self) -> int:
        """
        The width of the viewport.
        Defines the number of pixels drawn too horizontally.
        """
        return int(self._viewport.width)

    @viewport_width.setter
    def viewport_width(self, new_width: int) -> None:
        self._viewport = self._viewport.resize(new_width, anchor=Vec2(0.0, 0.0))

    @property
    def viewport_height(self) -> int:
        """
        The height of the viewport.
        Defines the number of pixels drawn too vertically.
        """
        return int(self._viewport.height)

    @viewport_height.setter
    def viewport_height(self, new_height: int) -> None:
        self._viewport = self._viewport.resize(height=new_height, anchor=Vec2(0.0, 0.0))

    @property
    def viewport_left(self) -> int:
        """
        The left most pixel drawn to on the X axis.
        """
        return int(self._viewport.left)

    @viewport_left.setter
    def viewport_left(self, new_left: int) -> None:
        """
        Set the left most pixel drawn to.
        This moves the position of the viewport, and does not change the size.
        """
        self._viewport = self._viewport.align_left(new_left)

    @property
    def viewport_right(self) -> int:
        """
        The right most pixel drawn to on the X axis.
        """
        return int(self._viewport.right)

    @viewport_right.setter
    def viewport_right(self, new_right: int) -> None:
        """
        Set the right most pixel drawn to.
        This moves the position of the viewport, and does not change the size.
        """
        self._viewport = self._viewport.align_right(new_right)

    @property
    def viewport_bottom(self) -> int:
        """
        The bottom most pixel drawn to on the Y axis.
        """
        return int(self._viewport.bottom)

    @viewport_bottom.setter
    def viewport_bottom(self, new_bottom: int) -> None:
        """
        Set the bottom most pixel drawn to.
        This moves the position of the viewport, and does not change the size.
        """
        self._viewport = self._viewport.align_bottom(new_bottom)

    @property
    def viewport_top(self) -> int:
        """
        The top most pixel drawn to on the Y axis.
        """
        return int(self._viewport.top)

    @viewport_top.setter
    def viewport_top(self, new_top: int) -> None:
        """
        Set the top most pixel drawn to.
        This moves the position of the viewport, and does not change the size.
        """
        self._viewport = self._viewport.align_top(new_top)

    @property
    def up(self) -> Vec2:
        """
        A 2D vector which describes what is mapped
        to the +Y direction on screen.
        This is equivalent to rotating the screen.
        The base vector is 3D, but this
        camera only provides a 2D view.
        """
        return Vec2(self._camera_data.up[0], self._camera_data.up[1])

    @up.setter
    def up(self, _up: Point2) -> None:
        """
        Set the 2D vector which describes what is
        mapped to the +Y direction on screen.
        This is equivalent to rotating the screen.
        The base vector is 3D, but this
        camera only provides a 2D view.

        .. warning:: This is assumed to be normalized (length 1.0)
        """
        x, y = _up
        self._camera_data.up = (x, y, 0.0)

    @property
    def angle(self) -> float:
        """
        An angle representation of the 2D UP vector.
        This starts with 0 degrees as [0, 1] rotating
        clock-wise.
        """
        # We rotate counter clockwise by 90 degrees because we want 0 deg to be directly up
        angle = degrees(atan2(self._camera_data.up[1], self._camera_data.up[0])) - 90.0
        if angle <= 0.0:
            angle += 360.0
        return 360 - angle

    @angle.setter
    def angle(self, value: float) -> None:
        """
        Set the 2D UP vector using an angle.
        This starts with 0 degrees as [0, 1]
        rotating clock-wise.
        """
        _r = radians(90.0 - value)
        # Note that this is flipped as we want 0 degrees to be vert.
        self._camera_data.up = (cos(_r), sin(_r), 0.0)

    @property
    def zoom(self) -> float:
        """
        A scalar value which describes
        how much the projection should
        be scaled towards from its center.

        A value of 2.0 causes the projection
        to be half its original size.
        This causes sprites to appear 2.0x larger.
        """
        return self._camera_data.zoom

    @zoom.setter
    def zoom(self, _zoom: float) -> None:
        """
        Set the scalar value which describes
        how much the projection should
        be scaled towards from its center.

        A value of 2.0 causes the projection
        to be half its original size.
        This causes sprites to appear 2.0x larger.
        """
        self._camera_data.zoom = _zoom

    # top_left
    @property
    def top_left(self) -> Vec2:
        """Get the top left most corner the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        top = self.top
        left = self.left

        return Vec2(pos.x + ux * top + rx * left, pos.y + uy * top + ry * left)

    @top_left.setter
    def top_left(self, new_corner: Point2):
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        top = self.top
        left = self.left

        x, y = new_corner
        self.position = (x - ux * top - rx * left, y - uy * top - ry * left)  # type: ignore

    # top_center
    @property
    def top_center(self) -> Vec2:
        """Get the top most position the camera can see"""
        pos = self.position

        ux, uy, *_ = self._camera_data.up
        top = self.top
        return Vec2(pos.x + ux * top, pos.y + uy * top)

    @top_center.setter
    def top_center(self, new_top: Point2):
        ux, uy, *_ = self._camera_data.up
        top = self.top

        x, y = new_top
        self.position = x - ux * top, y - uy * top  # type: ignore

    # top_right
    @property
    def top_right(self) -> Vec2:
        """Get the top right most corner the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        top = self.top
        right = self.right

        return Vec2(pos.x + ux * top + rx * right, pos.y + uy * top + ry * right)

    @top_right.setter
    def top_right(self, new_corner: Point2):
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        top = self.top
        right = self.right

        x, y = new_corner
        self.position = (x - ux * top - rx * right, y - uy * top - ry * right)  # type: ignore

    # center_right
    @property
    def center_right(self) -> Vec2:
        """Get the right most point the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        right = self.right
        return Vec2(pos.x + uy * right, pos.y - ux * right)

    @center_right.setter
    def center_right(self, new_right: Point2):
        ux, uy, *_ = self._camera_data.up
        right = self.right

        x, y = new_right
        self.position = x - uy * right, y + ux * right  # type: ignore

    # bottom_right
    @property
    def bottom_right(self) -> Vec2:
        """Get the bottom right most corner the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        bottom = self.bottom
        right = self.right
        return Vec2(pos.x + ux * bottom + rx * right, pos.y + uy * bottom + ry * right)

    @bottom_right.setter
    def bottom_right(self, new_corner: Point2):
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        bottom = self.bottom
        right = self.right

        x, y = new_corner
        self.position = (
            x - ux * bottom - rx * right,
            y - uy * bottom - ry * right,
        )  # type: ignore

    # bottom_center
    @property
    def bottom_center(self) -> Vec2:
        """Get the bottom most position the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        bottom = self.bottom

        return Vec2(pos.x + ux * bottom, pos.y + uy * bottom)

    @bottom_center.setter
    def bottom_center(self, new_bottom: Point2):
        ux, uy, *_ = self._camera_data.up
        bottom = self.bottom

        x, y = new_bottom
        self.position = x - ux * bottom, y - uy * bottom  # type: ignore

    # bottom_left
    @property
    def bottom_left(self) -> Vec2:
        """Get the bottom left most corner the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        bottom = self.bottom
        left = self.left

        return Vec2(pos.x + ux * bottom + rx * left, pos.y + uy * bottom + ry * left)

    @bottom_left.setter
    def bottom_left(self, new_corner: Point2):
        ux, uy, *_ = self._camera_data.up
        rx, ry = uy, -ux

        bottom = self.bottom
        left = self.left

        x, y = new_corner
        self.position = x - ux * bottom - rx * left, y - uy * bottom - ry * left  # type: ignore

    # center_left
    @property
    def center_left(self) -> Vec2:
        """Get the left most point the camera can see"""
        pos = self.position
        ux, uy, *_ = self._camera_data.up
        left = self.left
        return Vec2(pos.x + uy * left, pos.y - ux * left)

    @center_left.setter
    def center_left(self, new_left: Point2):
        ux, uy, *_ = self._camera_data.up
        left = self.left

        x, y = new_left
        self.position = Vec2(x - uy * left, y + ux * left)



class Sprite(BasicSprite, PymunkMixin):
    """
    Sprites are used to render image data to the screen & perform collisions.

    Most games center around sprites. They are most frequently used as follows:

    1. Create ``Sprite`` instances from image data
    2. Add the sprites to a :py:class:`~arcade.SpriteList` instance
    3. Call :py:meth:`SpriteList.draw() <arcade.SpriteList.draw>` on the
       instance inside your ``on_draw`` method.

    For runnable examples of how to do this, please see Arcade's
    :ref:`built-in Sprite examples <sprites>`.

    .. tip:: Advanced users should see :py:class:`~arcade.BasicSprite`

        It uses fewer resources at the cost of having fewer features.

    Args:
        path_or_texture:
            Path to an image file, or a texture object.
        center_x:
            Location of the sprite in pixels.
        center_y:
            Location of the sprite in pixels.
        scale:
            Show the image at this many times its original size.
        angle:
            The initial rotation of the sprite in degrees
    """

    __slots__ = (
        "_velocity",
        "change_angle",
        "_properties",
        "boundary_left",
        "boundary_right",
        "boundary_top",
        "boundary_bottom",
        "textures",
        "cur_texture_index",
        "_hit_box",
        "physics_engines",
        "guid",
        "force",
    )

    def __init__(
        self,
        path_or_texture: PathOrTexture | None = None,
        scale: float | Point2 = 1.0,
        center_x: float = 0.0,
        center_y: float = 0.0,
        angle: float = 0.0,
        **kwargs: Any,
    ) -> None:
        if isinstance(path_or_texture, Texture):
            _texture = path_or_texture
            _textures = [_texture]
        elif isinstance(path_or_texture, str | Path):
            _texture = arcade.texture.default_texture_cache.load_or_get_texture(path_or_texture)
            _textures = [_texture]
        else:
            _texture = get_default_texture()
            # Backwards compatibility:
            # When applying default texture we don't want
            # it part of the animating ones
            _textures = []
        super().__init__(
            _texture,
            scale=scale,
            center_x=center_x,
            center_y=center_y,
            **kwargs,
        )
        PymunkMixin.__init__(self)

        self._angle = angle
        # Movement
        self._velocity = 0.0, 0.0
        self.change_angle: float = 0.0
        """Change in angle per 1/60th of a second."""

        # Custom sprite properties
        self._properties: dict[str, Any] | None = None

        # Boundaries for moving platforms in tilemaps
        self.boundary_left: float | None = None
        """
        :py:class:`~arcade.physics_engines.PhysicsEnginePlatformer`
        uses this as the left boundary for moving
        :py:attr:`~arcade.physics_engines.PhysicsEnginePlatformer.platforms`.
        """

        self.boundary_right: float | None = None
        """
        :py:class:`~arcade.physics_engines.PhysicsEnginePlatformer`
        uses this as the right boundary for moving
        :py:attr:`~arcade.physics_engines.PhysicsEnginePlatformer.platforms`.
        """

        self.boundary_top: float | None = None
        """
        :py:class:`~arcade.physics_engines.PhysicsEnginePlatformer`
        uses this as the top boundary for moving
        :py:attr:`~arcade.physics_engines.PhysicsEnginePlatformer.platforms`.
        """

        self.boundary_bottom: float | None = None
        """
        :py:class:`~arcade.physics_engines.PhysicsEnginePlatformer`
        uses this as the top boundary for moving
        :py:attr:`~arcade.physics_engines.PhysicsEnginePlatformer.platforms`.
        """

        self.cur_texture_index: int = 0
        """Current texture index for sprite animation."""
        self.textures: list[Texture] = _textures
        """List of textures stored in the sprite."""

        self.physics_engines: list[Any] = []
        """List of physics engines that have registered this sprite."""

        # Debug properties
        self.guid: str | None = None
        """A unique id for debugging purposes."""

        self._hit_box: RotatableHitBox = self._hit_box.create_rotatable(angle=self._angle)

        self._width = self._texture.width * self._scale[0]
        self._height = self._texture.height * self._scale[1]

    # --- Properties ---

    @property
    def angle(self) -> float:
        """
        Get or set the rotation or the sprite.

        The value is in degrees and is clockwise.
        """
        return self._angle

    @angle.setter
    def angle(self, new_value: float) -> None:
        if new_value == self._angle:
            return

        self._angle = new_value
        self._hit_box.angle = new_value

        for sprite_list in self.sprite_lists:
            sprite_list._update_angle(self)

        self.update_spatial_hash()

    @property
    def radians(self) -> float:
        """
        Get or set the rotation of the sprite in radians.

        The value is in radians and is clockwise.
        """
        return self._angle / 180.0 * math.pi

    @radians.setter
    def radians(self, new_value: float) -> None:
        self.angle = new_value * 180.0 / math.pi

    @property
    def velocity(self) -> Point2:
        """
        Get or set the velocity of the sprite.

        The x and y velocity can also be set separately using the
        ``sprite.change_x`` and ``sprite.change_y`` properties.

        Example::

            sprite.velocity = 1.0, 0.0
        """
        return self._velocity

    @velocity.setter
    def velocity(self, new_value: Point2) -> None:
        self._velocity = new_value

    @property
    def change_x(self) -> float:
        """Get or set the velocity in the x plane of the sprite."""
        return self.velocity[0]

    @change_x.setter
    def change_x(self, new_value: float) -> None:
        self._velocity = new_value, self._velocity[1]

    @property
    def change_y(self) -> float:
        """Get or set the velocity in the y plane of the sprite."""
        return self.velocity[1]

    @change_y.setter
    def change_y(self, new_value: float) -> None:
        self._velocity = self._velocity[0], new_value

    @property
    def hit_box(self) -> HitBox:
        """Get or set the hit box for this sprite."""
        return self._hit_box

    @hit_box.setter
    def hit_box(self, hit_box: HitBox | RotatableHitBox) -> None:
        if type(hit_box) is HitBox:
            self._hit_box = hit_box.create_rotatable(self.angle)
        else:
            # Mypy doesn't seem to understand the type check above
            # It still thinks hit_box can be a union here
            self._hit_box = hit_box  # type: ignore

    @property
    def texture(self) -> Texture:
        """Get or set the active texture for this sprite"""
        return self._texture

    @texture.setter
    def texture(self, texture: Texture) -> None:
        if texture == self._texture:
            return

        if __debug__ and not isinstance(texture, Texture):
            raise TypeError(
                f"The 'texture' parameter must be an instance of arcade.Texture,"
                f" but is an instance of '{type(texture)}'."
            )

        # If sprite is using default texture, update the hit box
        if self._texture is get_default_texture():
            self.hit_box = RotatableHitBox(
                texture.hit_box_points,
                position=self._position,
                angle=self.angle,
                scale=self._scale,
            )

        self._texture = texture
        self._width = texture.width * self._scale[0]
        self._height = texture.height * self._scale[1]
        self.update_spatial_hash()
        for sprite_list in self.sprite_lists:
            sprite_list._update_texture(self)

    @property
    def properties(self) -> dict[str, Any]:
        """Get or set custom sprite properties."""
        if self._properties is None:
            self._properties = {}
        return self._properties

    @properties.setter
    def properties(self, value: dict[str, Any]) -> None:
        self._properties = value

    # --- Movement methods -----

    def forward(self, speed: float = 1.0) -> None:
        """
        Adjusts a Sprites forward.

        Args:
            speed: The speed at which the sprite moves.
        """
        angle_rad = math.radians(self.angle)
        self.center_x += math.sin(angle_rad) * speed
        self.center_y += math.cos(angle_rad) * speed

    def reverse(self, speed: float = 1.0) -> None:
        """
        Adjusts a Sprite backwards.

        Args:
            speed: The speed at which the sprite moves.
        """
        self.forward(-speed)

    def strafe(self, speed: float = 1.0) -> None:
        """
        Adjusts a Sprite sideways.

        Args:
            speed: The speed at which the sprite moves.
        """
        angle_rad = math.radians(self.angle + 90)
        self.center_x += math.sin(angle_rad) * speed
        self.center_y += math.cos(angle_rad) * speed

    def turn_right(self, theta: float = 90.0) -> None:
        """
        Rotate the sprite right by the passed number of degrees.

        Args:
            theta: Change in angle, in degrees
        """
        self.angle = self._angle + theta

    def turn_left(self, theta: float = 90.0) -> None:
        """
        Rotate the sprite left by the passed number of degrees.

        Args:
            theta: Change in angle, in degrees
        """
        self.angle = self._angle - theta

    def stop(self) -> None:
        """
        Stop the Sprite's motion by setting the velocity and angle change to 0.
        """
        self.velocity = 0, 0
        self.change_angle = 0.0

    # ----Update Methods ----

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        """
        The default update method for a Sprite. Can be overridden by a subclass.

        This method moves the sprite based on its velocity and angle change.

        Args:
            delta_time: Time since last update in seconds
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        # NOTE: change_x and change_y (or velocity) are historically defined as
        # the change in position per frame. To convert to change in position per
        # second, we multiply by 60 (frames per second).
        # Users can define these values in any unit they want, but this breaks
        # compatibility with physics engines. Consider changing this in the future.
        delta_time *= 60
        self.position = (
            self._position[0] + self.change_x * delta_time,
            self._position[1] + self.change_y * delta_time,
        )
        self.angle += self.change_angle * delta_time

    # ----Utility Methods----

    def update_spatial_hash(self) -> None:
        """
        Update the sprites location in the spatial hash.
        """
        # self._hit_box._adjusted_cache_dirty = True
        # super().update_spatial_hash()
        for sprite_list in self.sprite_lists:
            if sprite_list.spatial_hash is not None:
                sprite_list.spatial_hash.move(self)

    def append_texture(self, texture: Texture) -> None:
        """
        Appends a new texture to the list of textures that can be
        applied to this sprite.

        Args:
            texture: Texture to add to the list of available textures
        """
        self.textures.append(texture)

    def set_texture(self, texture_no: int) -> None:
        """
        Set the current texture by texture number.
        The number is the index into ``self.textures``.

        Args:
            texture_no: Index into ``self.textures``
        """
        texture = self.textures[texture_no]
        self.texture = texture

    def remove_from_sprite_lists(self) -> None:
        """
        Remove this sprite from all sprite lists it is in
        including registered physics engines.
        """
        super().remove_from_sprite_lists()
        for engine in self.physics_engines:
            engine.remove_sprite(self)

        self.physics_engines.clear()

    def register_physics_engine(self, physics_engine: Any) -> None:
        """
        Register a physics engine on the sprite.
        This is only needed if you actually need a reference
        to your physics engine in the sprite itself.
        It has no other purposes.

        The registered physics engines can be accessed
        through the ``physics_engines`` attribute.

        It can for example be the pymunk physics engine
        or a custom one you made.

        Args:
            physics_engine: The physics engine to register
        """
        self.physics_engines.append(physics_engine)

    def sync_hit_box_to_texture(self) -> None:
        """
        Update the sprite's hit box to match the current texture's hit box.
        """
        self.hit_box = RotatableHitBox(
            self.texture.hit_box_points,
            position=self._position,
            angle=self.angle,
            scale=self._scale,
        )


class SpriteList(SpriteSequence[SpriteType]):
    """
    The purpose of the spriteList is to batch draw a list of sprites.
    Drawing single sprites will not get you anywhere performance wise
    as the number of sprites in your project increases. The spritelist
    contains many low level optimizations taking advantage of your
    graphics processor. To put things into perspective, a spritelist
    can contain tens of thousands of sprites without any issues.
    Sprites outside the viewport/window will not be rendered.

    If the spritelist are going to be used for collision it's a good
    idea to enable spatial hashing. Especially if no sprites are moving.
    This will make collision checking **a lot** faster.
    In technical terms collision checking is ``O(1)`` with spatial hashing
    enabled and ``O(N)`` without. However, if you have a
    list of moving sprites the cost of updating the spatial hash
    when they are moved can be greater than what you save with
    spatial collision checks. This needs to be profiled on a
    case by case basis.

    For the advanced options check the advanced section in the
    Arcade documentation.

    Args:
        use_spatial_hash:
            If set to True, this will make creating a sprite, and moving a sprite
            in the SpriteList slower, but it will speed up collision detection
            with items in the SpriteList. Great for doing collision detection
            with static walls/platforms in large maps.
        spatial_hash_cell_size:
            The cell size of the spatial hash (default: 128)
        atlas:
            (Advanced) The texture atlas for this sprite list. If no
            atlas is supplied the global/default one will be used.
        capacity:
            (Advanced) The initial capacity of the internal buffer.
            It's a suggestion for the maximum amount of sprites this list
            can hold. Can normally be left with default value.
        lazy:
            (Advanced) ``True`` delays creating OpenGL resources
            for the sprite list until either its :py:meth:`~SpriteList.draw`
            or :py:meth:`~SpriteList.initialize` method is called. See
            :ref:`pg_spritelist_advanced_lazy_spritelists` to learn more.
        visible:
            Setting this to False will cause the SpriteList to not
            be drawn. When draw is called, the method will just return without drawing.
    """

    #: The default texture filter used when no other filter is specified.
    #: This can be used to change the global default for all spritelists
    #:
    #: Example::
    #:
    #:     from arcade import gl
    #:     # Set global default to nearest filtering (pixelated)
    #:     arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST
    #:     # Set global default to linear filtering (smooth). This is the default.
    #:     arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.NEAREST, gl.NEAREST
    DEFAULT_TEXTURE_FILTER: ClassVar[tuple[int, int]] = gl.LINEAR, gl.LINEAR

    # Declare `special_hash` as an attribute that implements the abstract
    # property from `SpriteSequence`. It needs an explicit type here because
    # it is better than the inherited type.
    # More subtle: it requires to be initialized as a *class* attribute with
    # `= None` to "delete" the abstract property definition from the class.
    # Without that trick, attempt to instantiate a SpriteList results in a
    #   TypeError: Can't instantiate abstract class SpriteList
    #   without an implementation for abstract method 'spatial_hash'
    # The abstract property is actually implemented as an attribute (for
    # efficiency), so it is OK to silence the issue like that.
    from ..sprite_list import spatial_hash as sh

    spatial_hash: sh.SpatialHash[SpriteType] | None = None

    def __init__(
        self,
        use_spatial_hash: bool = False,
        spatial_hash_cell_size: int = 128,
        atlas: TextureAtlasBase | None = None,
        capacity: int = 100,
        lazy: bool = False,
        visible: bool = True,
    ) -> None:
        self.program: Program | None = None
        self._atlas: TextureAtlasBase | None = atlas
        self._initialized = False
        self._lazy = lazy
        self._visible = visible
        self._blend = True
        self._color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)

        capacity = _align_capacity(capacity)
        # The initial capacity of the spritelist buffers (internal)
        self._buf_capacity = capacity
        # The initial capacity of the index buffer (internal)
        self._idx_capacity = capacity
        # The number of slots used in the sprite buffer
        self._sprite_buffer_slots = 0
        # Number of slots used in the index buffer
        self._sprite_index_slots = 0
        # List of free slots in the sprite buffers. These are filled when sprites are removed.
        self._sprite_buffer_free_slots: deque[int] = deque()

        # List of sprites in the sprite list
        self.sprite_list: list[SpriteType] = []
        # Buffer slots for the sprites (excluding index buffer)
        # This has nothing to do with the index in the spritelist itself
        self.sprite_slot: dict[SpriteType, int] = dict()

        # Python representation of buffer data
        # NOTE: The number of components must be 1, 2 or 4. 3 floats is not supported
        #       for most iGPUs due to alignment issues.
        self._sprite_pos_angle_data = array("f", [0] * self._buf_capacity * 4)
        self._sprite_size_data = array("f", [0] * self._buf_capacity * 2)
        self._sprite_color_data = array("B", [0] * self._buf_capacity * 4)
        self._sprite_texture_data = array("f", [0] * self._buf_capacity)
        # Index buffer
        self._sprite_index_data = array("i", [0] * self._idx_capacity)

        self._data: SpriteListData | None = None

        # Flags for signaling if a buffer needs to be written to the OpenGL buffer
        self._sprite_pos_angle_changed: bool = False
        self._sprite_size_changed: bool = False
        self._sprite_color_changed: bool = False
        self._sprite_texture_changed: bool = False
        self._sprite_index_changed: bool = False

        # Used in collision detection optimization
        from .spatial_hash import SpatialHash

        self._spatial_hash_cell_size = spatial_hash_cell_size
        self.spatial_hash = None
        if use_spatial_hash:
            self.spatial_hash = SpatialHash(cell_size=self._spatial_hash_cell_size)

        self.properties: dict[str, Any] | None = None

        # Check if the window/context is available
        try:
            get_window()
            if not self._lazy:
                self._init_deferred()
        except RuntimeError:
            pass

    def _init_deferred(self) -> None:
        """
        Since spritelist can be created before the window we need to defer initialization.

        It also makes us able to support lazy loading.
        """
        if self._initialized:
            return

        self.ctx = get_window().ctx
        if not self._atlas:
            self._atlas = self.ctx.default_atlas

        if self.ctx._gl_api == "webgl":
            self._data = SpriteListTextureData(
                self.ctx, capacity=self._buf_capacity, atlas=self._atlas
            )
        else:
            self._data = SpriteListBufferData(
                self.ctx, capacity=self._buf_capacity, atlas=self._atlas
            )

        self._initialized = True

        # Load all the textures and write texture coordinates into buffers.
        # This is important for lazy spritelists.
        for sprite in self.sprite_list:
            if sprite._texture is None:
                raise ValueError("Attempting to use a sprite without a texture")
            self._update_texture(sprite)
            if hasattr(sprite, "textures"):
                if TYPE_CHECKING:
                    assert isinstance(sprite, Sprite)
                for texture in sprite.textures or []:
                    self._atlas.add(texture)

        self._sprite_pos_angle_changed = True
        self._sprite_size_changed = True
        self._sprite_color_changed = True
        self._sprite_texture_changed = True
        self._sprite_index_changed = True

    def __len__(self) -> int:
        """Return the length of the sprite list."""
        return len(self.sprite_list)

    def __contains__(self, sprite: object) -> bool:
        """Return if the sprite list contains the given sprite"""
        return sprite in self.sprite_slot

    def __iter__(self) -> Iterator[SpriteType]:
        """Return an iterable object of sprites."""
        return iter(self.sprite_list)

    def __getitem__(self, i: int) -> SpriteType:
        return self.sprite_list[i]

    def __setitem__(self, index: int, sprite: SpriteType) -> None:
        """Replace a sprite at a specific index"""
        try:
            existing_index = self.sprite_list.index(sprite)  # raise ValueError
            if existing_index == index:
                return
            raise Exception(f"Sprite is already in the list (index {existing_index})")
        except ValueError:
            pass

        sprite_to_be_removed = self.sprite_list[index]
        sprite_to_be_removed._unregister_sprite_list(self)
        self.sprite_list[index] = sprite  # Replace sprite
        sprite.register_sprite_list(self)

        if self.spatial_hash is not None:
            self.spatial_hash.remove(sprite_to_be_removed)
            self.spatial_hash.add(sprite)

        # Steal the slot from the old sprite
        slot = self.sprite_slot[sprite_to_be_removed]
        del self.sprite_slot[sprite_to_be_removed]
        self.sprite_slot[sprite] = slot

        # Update the internal sprite buffer data
        self._update_all(sprite)

    @property
    def visible(self) -> bool:
        """
        Get or set the visible flag for this spritelist.

        If visible is ``False`` the ``draw()`` has no effect.
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    @property
    def blend(self) -> bool:
        """Enable or disable alpha blending for the spritelist."""
        return self._blend

    @blend.setter
    def blend(self, value: bool) -> None:
        self._blend = value

    @property
    def color(self) -> Color:
        """
        Get or set the multiply color for all sprites in the list RGBA integers

        This will affect all sprites in the list, and each value must be
        between 0 and 255.

        The color may be specified as any of the following:

        * an RGBA :py:class:`tuple` with each channel value between 0 and 255
        * an instance of :py:class:`~arcade.types.Color`
        * an RGB :py:class:`tuple`, in which case the color will be treated as opaque

        Each individual sprite can also be assigned a color via its
        :py:attr:`~arcade.BasicSprite.color` property.

        When :py:meth:`.SpriteList.draw` is called, each pixel will default
        to a value equivalent to the following:

        1. Convert the sampled texture, sprite, and list colors into normalized floats (0.0 to 1.0)
        2. Multiply the color channels together: ``texture_color * sprite_color * spritelist_color``
        3. Multiply the floating point values by 255 and round the result
        """
        return Color.from_normalized(self._color)

    @color.setter
    def color(self, color: RGBA255) -> None:
        self._color = Color.from_iterable(color).normalized

    @property
    def color_normalized(self) -> RGBANormalized:
        """
        Get or set the spritelist color in normalized form (0.0 -> 1.0 floats).

        This property works the same as :py:attr:`~arcade.SpriteList.color`.
        """
        return self._color

    @color_normalized.setter
    def color_normalized(self, value: RGBOrANormalized) -> None:
        try:
            r, g, b, *_a = value
            assert len(_a) <= 1
        except (ValueError, AssertionError) as e:
            raise ValueError("color_normalized must unpack as 3 or 4 float values") from e

        self._color = r, g, b, _a[0] if _a else 1.0

    @property
    def alpha(self) -> int:
        """
        Get or set the alpha/transparency of the entire spritelist.

        This is a byte value from 0 to 255 were 0 is completely
        transparent/invisible and 255 is opaque.
        """
        return int(self._color[3] * 255)

    @alpha.setter
    def alpha(self, value: int) -> None:
        self._color = self._color[0], self._color[1], self._color[2], value / 255

    @property
    def alpha_normalized(self) -> float:
        """
        Get or set the alpha/transparency of all the sprites in the list.

        This is a floating point number from 0.0 to 1.0 were 0.0 is completely
        transparent/invisible and 1.0 is opaque.

        This is a shortcut for setting the alpha value in the spritelist color.
        """
        return self._color[3]

    @alpha_normalized.setter
    def alpha_normalized(self, value: float) -> None:
        self._color = self._color[0], self._color[1], self._color[2], value

    @property
    def atlas(self) -> TextureAtlasBase | None:
        """Get the texture atlas for this sprite list"""
        return self._atlas

    @property
    def data(self) -> SpriteListData:
        """Get the sprite data for this spritelist."""
        if not self._initialized:
            self.initialize()

        return self._data  # type: ignore[return-value]

    def _next_slot(self) -> int:
        """
        Get the next available slot in sprite buffers

        :return: index slot, buffer_slot
        """
        # Reuse old slots from deleted sprites
        if self._sprite_buffer_free_slots:
            return self._sprite_buffer_free_slots.popleft()

        # Add a new slot
        buff_slot = self._sprite_buffer_slots
        self._sprite_buffer_slots += 1
        self._grow_sprite_buffers()  # We might need to increase our buffers
        return buff_slot

    def index(self, sprite: SpriteType) -> int:
        """
        Return the index of a sprite in the spritelist

        Args:
            sprite: Sprite to find and return the index of
        """
        return self.sprite_list.index(sprite)

    def clear(self, *, capacity: int | None = None, deep: bool = True) -> None:
        """
        Remove all the sprites resetting the spritelist
        to it's initial state.

        The complexity of this method is ``O(N)`` with a deep clear (default).

        If ALL the sprites in the list gets garbage collected with the list itself
        you can do an ``O(1)``` clear using ``deep=False``. **Make sure you know
        exactly what you are doing before using this option.** Any lingering sprite
        reference will cause a massive memory leak. The ``deep`` option will
        iterate all the sprites and remove their references to this spritelist.
        Sprite and SpriteList have a circular reference for performance reasons.

        Args:
            deep: Whether to do a deep clear or not. Default is ``True``.
            capacity: The size of the internal buffers used to store the sprites.
                      Defaults to preserving the current capacity.
        """
        from .spatial_hash import SpatialHash

        # Manually remove the spritelist from all sprites
        if deep:
            for sprite in self.sprite_list:
                sprite._unregister_sprite_list(self)

        self.sprite_list = []
        self.sprite_slot = dict()

        # Reset SpatialHash
        if self.spatial_hash is not None:
            self.spatial_hash = SpatialHash(cell_size=self._spatial_hash_cell_size)

        # Clear the slot_idx and slot info and other states
        capacity = _align_capacity(capacity or self._buf_capacity)

        self._buf_capacity = capacity
        self._idx_capacity = capacity
        self._sprite_buffer_slots = 0
        self._sprite_index_slots = 0
        self._sprite_buffer_free_slots = deque()

        # Reset buffers
        # Python representation of buffer data
        self._sprite_pos_angle_data = array("f", [0] * self._buf_capacity * 4)
        self._sprite_size_data = array("f", [0] * self._buf_capacity * 2)
        self._sprite_color_data = array("B", [0] * self._buf_capacity * 4)
        self._sprite_texture_data = array("f", [0] * self._buf_capacity)
        # Index buffer
        self._sprite_index_data = array("I", [0] * self._idx_capacity)

        if self._initialized:
            self._initialized = False
            self._init_deferred()

    def pop(self, index: int = -1) -> SpriteType:
        """
        Attempt to pop a sprite from the list.

        This works like :external:ref:`popping from <tut-morelists>` a
        standard Python :py:class:`list`:

        #. If the list is empty, raise an :py:class:`IndexError`
        #. If no ``index`` is passed, try to pop the last
           :py:class:`Sprite` in the list

        This is the most efficient way to remove a sprite from the list.
        The complexity of this method is ``O(1)``.

        Args:
            index:
                Index of sprite to remove (defaults to ``-1`` for the last item)
        """
        if len(self.sprite_list) == 0:
            raise IndexError("pop from empty list")

        sprite = self.sprite_list.pop(index)
        try:
            slot = self.sprite_slot[sprite]
        except KeyError:
            raise ValueError("Sprite is not in the SpriteList")

        sprite._unregister_sprite_list(self)
        del self.sprite_slot[sprite]
        self._sprite_buffer_free_slots.append(slot)

        _ = self._sprite_index_data.pop(index)
        self._sprite_index_data.append(0)
        self._sprite_index_slots -= 1
        self._sprite_index_changed = True

        if self.spatial_hash is not None:
            self.spatial_hash.remove(sprite)

        return sprite

    def append(self, sprite: SpriteType) -> None:
        """
        Add a new sprite to the list.

        Args:
            sprite: Sprite to add to the list.
        """
        if sprite in self.sprite_slot:
            raise ValueError("Sprite already in SpriteList")

        slot = self._next_slot()
        self.sprite_slot[sprite] = slot
        self.sprite_list.append(sprite)
        sprite.register_sprite_list(self)

        self._update_all(sprite)

        # Add sprite to the end of the index buffer
        idx_slot = self._sprite_index_slots
        self._sprite_index_slots += 1
        self._grow_index_buffer()
        self._sprite_index_data[idx_slot] = slot
        self._sprite_index_changed = True

        if self.spatial_hash is not None:
            self.spatial_hash.add(sprite)

        if self._initialized:
            if sprite.texture is None:
                raise ValueError("Sprite must have a texture when added to a SpriteList")
            self._atlas.add(sprite.texture)  # type: ignore

    def swap(self, index_1: int, index_2: int) -> None:
        """
        Swap two sprites by index.

        Args:
            index_1: Item index to swap
            index_2: Item index to swap
        """
        # Swap order in python spritelist
        sprite_1 = self.sprite_list[index_1]
        sprite_2 = self.sprite_list[index_2]
        self.sprite_list[index_1] = sprite_2
        self.sprite_list[index_2] = sprite_1

        # Swap order in index buffer to change rendering order
        slot_1 = self.sprite_slot[sprite_1]
        slot_2 = self.sprite_slot[sprite_2]
        i1 = self._sprite_index_data.index(slot_1)
        i2 = self._sprite_index_data.index(slot_2)
        self._sprite_index_data[i1] = slot_2
        self._sprite_index_data[i2] = slot_1

        self._sprite_index_changed = True

    def remove(self, sprite: SpriteType) -> None:
        """
        Remove a specific sprite from the list.

        Note that this method is ``O(N)`` in complexity and will have
        and increased cost the more sprites you have in the list.
        A faster option is to use :py:meth:`pop` or :py:meth:`swap`.

        Args:
            sprite: Item to remove from the list
        """
        try:
            slot = self.sprite_slot[sprite]
        except KeyError:
            raise ValueError("Sprite is not in the SpriteList")

        index = self.sprite_list.index(sprite)
        self.sprite_list.pop(index)
        sprite._unregister_sprite_list(self)
        del self.sprite_slot[sprite]

        self._sprite_buffer_free_slots.append(slot)

        self._sprite_index_data.pop(index)
        self._sprite_index_data.append(0)
        self._sprite_index_slots -= 1
        self._sprite_index_changed = True

        if self.spatial_hash is not None:
            self.spatial_hash.remove(sprite)

    def extend(self, sprites: Iterable[SpriteType]) -> None:
        """
        Extends the current list with the given iterable

        Args:
            sprites: Iterable of Sprites to add to the list
        """
        for sprite in sprites:
            self.append(sprite)

    def insert(self, index: int, sprite: SpriteType) -> None:
        """
        Inserts a sprite at a given index.

        Args:
            index: The index at which to insert
            sprite: The sprite to insert
        """
        if sprite in self.sprite_list:
            raise ValueError("Sprite is already in list")

        index = max(min(len(self.sprite_list), index), 0)

        self.sprite_list.insert(index, sprite)
        sprite.register_sprite_list(self)

        # Allocate a new slot and write the data
        slot = self._next_slot()
        self.sprite_slot[sprite] = slot
        self._update_all(sprite)

        # Allocate room in the index buffer
        # idx_slot = self._sprite_index_slots
        self._sprite_index_slots += 1
        self._grow_index_buffer()
        self._sprite_index_data.insert(index, slot)
        self._sprite_index_data.pop()

        if self.spatial_hash is not None:
            self.spatial_hash.add(sprite)

    def reverse(self) -> None:
        """Reverses the current list in-place"""
        # Reverse the sprites and index buffer
        self.sprite_list.reverse()
        # This seems to be the reasonable way to reverse a subset of an array
        reverse_data = self._sprite_index_data[0 : len(self.sprite_list)]
        reverse_data.reverse()
        self._sprite_index_data[0 : len(self.sprite_list)] = reverse_data

        self._sprite_index_changed = True

    def shuffle(self) -> None:
        """Shuffles the current list in-place"""
        # The only thing we need to do when shuffling is
        # to shuffle the sprite_list and index buffer in
        # in the same operation. We don't change the sprite buffers

        # zip index and sprite into pairs and shuffle
        pairs = list(zip(self.sprite_list, self._sprite_index_data))
        random.shuffle(pairs)

        # Reconstruct the lists again from pairs
        sprites, indices = cast(tuple[list[SpriteType], list[int]], zip(*pairs))
        self.sprite_list = list(sprites)
        self._sprite_index_data = array("I", indices)

        # Resize the index buffer to the original capacity
        if len(self._sprite_index_data) < self._idx_capacity:
            extend_by = self._idx_capacity - len(self._sprite_index_data)
            self._sprite_index_data.extend([0] * extend_by)

        self._sprite_index_changed = True

    def sort(self, *, key: Callable, reverse: bool = False) -> None:
        """
        Sort the spritelist in place using ``<`` comparison between sprites.
        This function is similar to python's :py:meth:`list.sort`.

        Example sorting sprites based on y-axis position using a lambda::

            # Normal order
            spritelist.sort(key=lambda x: x.position[1])
            # Reversed order
            spritelist.sort(key=lambda x: x.position[1], reverse=True)

        Example sorting sprites using a function::

            # More complex sorting logic can be applied, but let's just stick to y position
            def create_y_pos_comparison(sprite):
                return sprite.position[1]

            spritelist.sort(key=create_y_pos_comparison)

        Args:
            key:
                A function taking a sprite as an argument returning a comparison key
            reverse:
                If set to ``True`` the sprites will be sorted in reverse
        """
        # In-place sort the spritelist
        self.sprite_list.sort(key=key, reverse=reverse)
        # Loop over the sorted sprites and assign new values in index buffer
        for i, sprite in enumerate(self.sprite_list):
            self._sprite_index_data[i] = self.sprite_slot[sprite]

        self._sprite_index_changed = True

    def disable_spatial_hashing(self) -> None:
        """Deletes the internal spatial hash object."""
        self.spatial_hash = None

    def enable_spatial_hashing(self, spatial_hash_cell_size: int = 128) -> None:
        """
        Turn on spatial hashing unless it is already enabled with the same cell size.

        Args:
            spatial_hash_cell_size: The size of the cell in the spatial hash.
        """
        if self.spatial_hash is None or self.spatial_hash.cell_size != spatial_hash_cell_size:
            from .spatial_hash import SpatialHash

            self.spatial_hash = SpatialHash(cell_size=spatial_hash_cell_size)
            self._recalculate_spatial_hashes()

    def _recalculate_spatial_hashes(self) -> None:
        if self.spatial_hash is None:
            from .spatial_hash import SpatialHash

            self.spatial_hash = SpatialHash(cell_size=self._spatial_hash_cell_size)

        self.spatial_hash.reset()
        for sprite in self.sprite_list:
            self.spatial_hash.add(sprite)

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        for sprite in self.sprite_list:
            sprite.update(delta_time, *args, **kwargs)

    def update_animation(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        for sprite in self.sprite_list:
            sprite.update_animation(delta_time, *args, **kwargs)

    def _get_center(self) -> tuple[float, float]:
        """Get the mean center coordinates of all sprites in the list."""
        x = sum(sprite.center_x for sprite in self.sprite_list) / len(self.sprite_list)
        y = sum(sprite.center_y for sprite in self.sprite_list) / len(self.sprite_list)
        return x, y

    center = property(_get_center)

    def rescale(self, factor: float) -> None:
        """Rescale all sprites in the list relative to the spritelists center."""
        for sprite in self.sprite_list:
            sprite.rescale_relative_to_point(self.center, factor)

    def move(self, change_x: float, change_y: float) -> None:
        """
        Moves all Sprites in the list by the same amount.
        This can be a very expensive operation depending on the
        size of the sprite list.

        Args:
            change_x: Amount to change all x values by
            change_y: Amount to change all y values by
        """
        for sprite in self.sprite_list:
            sprite.center_x += change_x
            sprite.center_y += change_y

    def preload_textures(self, texture_list: Iterable[Texture]) -> None:
        """
        Preload a set of textures that will be used for sprites in this
        sprite list.

        Args:
            texture_list: List of textures.
        """
        if not self.ctx:
            raise ValueError("Cannot preload textures before the window is created")

        for texture in texture_list:
            # Ugly spacing is a fast workaround for None type checking issues
            self._atlas.add(texture)  # type: ignore

    def write_sprite_buffers_to_gpu(self) -> None:
        """
        Ensure buffers are resized and fresh sprite data is written into the internal
        sprite buffers.

        This is automatically called in :py:meth:`SpriteList.draw`, but there are
        instances when using custom shaders we need to force this to happen since
        we might have not called :py:meth:`SpriteList.draw` since the spritelist
        was modified.

        If you have added, removed, moved or changed ANY sprite property this method
        will synchronize the data on the gpu side (buffer resizing and writing in
        new data).
        """
        self._write_sprite_buffers_to_gpu()

    def _write_sprite_buffers_to_gpu(self) -> None:
        if not self._initialized:
            self._init_deferred()

        self.data.write_sprite_buffers_to_gpu(
            # Buffer data
            self._sprite_pos_angle_data,
            self._sprite_size_data,
            self._sprite_color_data,
            self._sprite_texture_data,
            self._sprite_index_data,
            # Changed flags
            self._sprite_pos_angle_changed,
            self._sprite_size_changed,
            self._sprite_color_changed,
            self._sprite_texture_changed,
            self._sprite_index_changed,
        )
        self._sprite_pos_angle_changed = False
        self._sprite_size_changed = False
        self._sprite_color_changed = False
        self._sprite_texture_changed = False
        self._sprite_index_changed = False

    def initialize(self) -> None:
        """
        Request immediate creation of OpenGL resources for this list.

        Calling this method is optional. It only has an effect for lists
        created with ``lazy=True``. If this method is not called,
        uninitialized sprite lists will automatically initialize OpenGL
        resources on their first :py:meth:`~SpriteList.draw` call instead.

        This method is useful for performance optimization, advanced
        techniques, and writing tests. Do not call it across thread
        boundaries. See :ref:`pg_spritelist_advanced_lazy_spritelists`
        to learn more.
        """
        self._init_deferred()

    def draw(
        self,
        *,
        filter: PyGLenum | OpenGlFilter | None = None,
        pixelated: bool | None = None,
        blend_function: BlendFunction | None = None,
    ) -> None:
        if len(self.sprite_list) == 0 or not self._visible or self.alpha_normalized == 0.0:
            return

        self._init_deferred()
        self._write_sprite_buffers_to_gpu()
        self.data.render(
            atlas=self._atlas,  # type: ignore
            count=self._sprite_index_slots,
            color=self._color,
            default_texture_filter=self.DEFAULT_TEXTURE_FILTER,
            filter=filter,
            pixelated=pixelated,
            blend_function=blend_function,
            blend=self._blend,
        )

    def draw_hit_boxes(
        self, color: RGBOrA255 = (0, 0, 0, 255), line_thickness: float = 1.0
    ) -> None:
        import arcade

        converted_color = Color.from_iterable(color)
        points: list[Point2] = []

        # TODO: Make this faster in the future
        # NOTE: This will be easier when/if we change to triangles
        for sprite in self.sprite_list:
            adjusted_points = sprite.hit_box.get_adjusted_points()
            for i in range(len(adjusted_points) - 1):
                points.append(adjusted_points[i])
                points.append(adjusted_points[i + 1])
            points.append(adjusted_points[-1])
            points.append(adjusted_points[0])

        arcade.draw_lines(points, color=converted_color, line_width=line_thickness)

    def get_nearby_sprites_gpu(self, pos: Point, size: Point) -> list[SpriteType]:
        """
        Get a list of sprites that are nearby the given position and size
        using the gpu. No spatial hashing is needed. This is a very fast method
        to find nearby sprites in large spritelists but is very expensive
        if the method is called many times per frame or if the sprite list
        is small.

        Args:
            pos: The position to check for nearby sprites.
            size: The size of the area to check for nearby sprites.
        Returns:
            A list of sprites nearby the given position and size.
        """
        if not self._initialized:
            self._init_deferred()

        if len(self.sprite_list) == 0:
            return []

        self._write_sprite_buffers_to_gpu()
        indices = self.data.get_nearby_sprite_indices(pos, size, len(self.sprite_list))
        return [self.sprite_list[i] for i in indices]

    def _grow_sprite_buffers(self) -> None:
        """Double the internal buffer sizes"""
        # Resize sprite buffers if needed
        if self._sprite_buffer_slots <= self._buf_capacity:
            return

        # Double the capacity
        extend_by = self._buf_capacity
        self._buf_capacity = self._buf_capacity * 2

        # Extend the buffers so we don't lose the old data
        self._sprite_pos_angle_data.extend([0] * extend_by * 4)
        self._sprite_size_data.extend([0] * extend_by * 2)
        self._sprite_color_data.extend([0] * extend_by * 4)
        self._sprite_texture_data.extend([0] * extend_by)

        if self._initialized:
            self.data.grow_sprite_buffers()

        self._sprite_pos_angle_changed = True
        self._sprite_size_changed = True
        self._sprite_color_changed = True
        self._sprite_texture_changed = True

    def _grow_index_buffer(self) -> None:
        # Extend the index buffer capacity if needed
        # TODO: We might not need this any more since index buffer is always normalized
        if self._sprite_index_slots <= self._idx_capacity:
            return

        extend_by = self._idx_capacity
        self._idx_capacity = self._idx_capacity * 2

        self._sprite_index_data.extend([0] * extend_by)
        if self._initialized:
            self.data.grow_index_buffer()

        self._sprite_index_changed = True

    def _update_all(self, sprite: SpriteType) -> None:
        """
        Update all sprite data. This is faster when adding and moving sprites.
        This duplicate code, but reduces call overhead, dict lookups etc.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        # position
        self._sprite_pos_angle_data[slot * 4] = sprite._position[0]
        self._sprite_pos_angle_data[slot * 4 + 1] = sprite._position[1]
        self._sprite_pos_angle_data[slot * 4 + 2] = sprite._depth
        self._sprite_pos_angle_data[slot * 4 + 3] = sprite._angle
        self._sprite_pos_angle_changed = True
        # size
        self._sprite_size_data[slot * 2] = sprite._width
        self._sprite_size_data[slot * 2 + 1] = sprite._height
        self._sprite_size_changed = True
        # angle
        # color
        self._sprite_color_data[slot * 4] = sprite._color[0]
        self._sprite_color_data[slot * 4 + 1] = sprite._color[1]
        self._sprite_color_data[slot * 4 + 2] = sprite._color[2]
        self._sprite_color_data[slot * 4 + 3] = sprite._color[3] * sprite._visible
        self._sprite_color_changed = True

        # Don't deal with textures if spritelist is not initialized.
        # This can often mean we don't have a context/window yet.
        if not self._initialized:
            return

        if not sprite._texture:
            return

        # Ugly syntax makes type checking pass without perf hit from cast
        tex_slot: int = self._atlas.add(sprite._texture)[0]  # type: ignore
        slot = self.sprite_slot[sprite]

        self._sprite_texture_data[slot] = tex_slot
        self._sprite_texture_changed = True

    def _update_texture(self, sprite: SpriteType) -> None:
        """
        Make sure we update the texture for this sprite for the next batch drawing.

        Args:
            sprite: Sprite to update.
        """
        # We cannot interact with texture atlases unless the context
        # is created. We defer all texture initialization for later
        if not self._initialized:
            return

        if not sprite._texture:
            return
        atlas = self._atlas
        # Ugly spacing makes type checking work with specificity
        tex_slot: int = atlas.add(sprite._texture)[0]  # type: ignore
        slot = self.sprite_slot[sprite]

        self._sprite_texture_data[slot] = tex_slot
        self._sprite_texture_changed = True

        # Update size in cas the sprite was initialized without size
        # NOTE: There should be a better way to do this
        self._sprite_size_data[slot * 2] = sprite._width
        self._sprite_size_data[slot * 2 + 1] = sprite._height
        self._sprite_size_changed = True

    def _update_position(self, sprite: SpriteType) -> None:
        """
        Called when setting initial position of a sprite when
        added or inserted into the SpriteList.

        ``update_location`` should be called to move them
        once the sprites are in the list.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_pos_angle_data[slot * 4] = sprite._position[0]
        self._sprite_pos_angle_data[slot * 4 + 1] = sprite._position[1]
        self._sprite_pos_angle_changed = True

    def _update_position_x(self, sprite: SpriteType) -> None:
        """
        Called when setting initial position of a sprite when
        added or inserted into the SpriteList.

        ``update_location`` should be called to move them
        once the sprites are in the list.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_pos_angle_data[slot * 4] = sprite._position[0]
        self._sprite_pos_angle_changed = True

    def _update_position_y(self, sprite: SpriteType) -> None:
        """
        Called when setting initial position of a sprite when
        added or inserted into the SpriteList.

        ``update_location`` should be called to move them
        once the sprites are in the list.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_pos_angle_data[slot * 4 + 1] = sprite._position[1]
        self._sprite_pos_angle_changed = True

    def _update_depth(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update the depth of the specified sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_pos_angle_data[slot * 4 + 2] = sprite._depth
        self._sprite_pos_angle_changed = True

    def _update_color(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update position, angle, size and color
        of the specified sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_color_data[slot * 4] = int(sprite._color[0])
        self._sprite_color_data[slot * 4 + 1] = int(sprite._color[1])
        self._sprite_color_data[slot * 4 + 2] = int(sprite._color[2])
        self._sprite_color_data[slot * 4 + 3] = int(sprite._color[3] * sprite._visible)
        self._sprite_color_changed = True

    def _update_size(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update the size/scale in this sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_size_data[slot * 2] = sprite._width
        self._sprite_size_data[slot * 2 + 1] = sprite._height
        self._sprite_size_changed = True

    def _update_width(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update the size/scale in this sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_size_data[slot * 2] = sprite._width
        self._sprite_size_changed = True

    def _update_height(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update the size/scale in this sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_size_data[slot * 2 + 1] = sprite._height
        self._sprite_size_changed = True

    def _update_angle(self, sprite: SpriteType) -> None:
        """
        Called by the Sprite class to update the angle in this sprite.
        Necessary for batch drawing of items.

        Args:
            sprite: Sprite to update.
        """
        slot = self.sprite_slot[sprite]
        self._sprite_pos_angle_data[slot * 4 + 3] = sprite._angle
        self._sprite_pos_angle_changed = True


from collections.abc import Iterable

from arcade.geometry import (
    are_polygons_intersecting,
    is_point_in_polygon,
)
from arcade.math import get_distance
from arcade.sprite import BasicSprite, SpriteType
from arcade.types import Point
from arcade.types.rect import Rect
from arcade.window_commands import get_window

from .sprite_list import SpriteSequence


def get_distance_between_sprites(sprite1: SpriteType, sprite2: SpriteType) -> float:
    """
    Returns the distance between the center of two given sprites

    Args:
        sprite1: Sprite one
        sprite2: Sprite two
    """
    return get_distance(*sprite1._position, *sprite2._position)


def get_closest_sprite(
    sprite: BasicSprite, sprite_list: SpriteSequence[SpriteType]
) -> tuple[SpriteType, float] | None:
    """
    Given a Sprite and SpriteList, returns the closest sprite, and its distance.

    Args:
        sprite:
            Target sprite
        sprite_list:
            List to search for closest sprite.

    Returns:
        A tuple containing the closest sprite and the minimum distance.
        If the spritelist is empty we return ``None``.
    """
    if len(sprite_list) == 0:
        return None

    min_pos = 0
    min_distance = get_distance_between_sprites(sprite, sprite_list[min_pos])
    for i in range(1, len(sprite_list)):
        distance = get_distance_between_sprites(sprite, sprite_list[i])
        if distance < min_distance:
            min_pos = i
            min_distance = distance
    return sprite_list[min_pos], min_distance


def check_for_collision(sprite1: BasicSprite, sprite2: BasicSprite) -> bool:
    """
    Check for a collision between two sprites.

    Args:
        sprite1: First sprite
        sprite2: Second sprite

    Returns:
        ``True`` or ``False`` depending if the sprites intersect.
    """
    if __debug__:
        if not isinstance(sprite1, BasicSprite):
            raise TypeError("Parameter 1 is not an instance of a Sprite class.")
        if isinstance(sprite2, SpriteSequence):
            raise TypeError(
                "Parameter 2 is a instance of the SpriteList instead of a required "
                "Sprite. See if you meant to call check_for_collision_with_list instead "
                "of check_for_collision."
            )
        elif not isinstance(sprite2, BasicSprite):
            raise TypeError("Parameter 2 is not an instance of a Sprite class.")

    return _check_for_collision(sprite1, sprite2)


def _check_for_collision(sprite1: BasicSprite, sprite2: BasicSprite) -> bool:
    """
    Check for collision between two sprites.

    Args:
        sprite1: Sprite 1
        sprite2: Sprite 2
    Returns:
        ``True`` if sprites overlap.
    """

    # NOTE: for speed because attribute look ups are slow.
    sprite1_position = sprite1._position
    sprite1_width = sprite1._width
    sprite1_height = sprite1._height
    sprite2_position = sprite2._position
    sprite2_width = sprite2._width
    sprite2_height = sprite2._height

    radius_sum = (sprite1_width if sprite1_width > sprite1_height else sprite1_height) + (
        sprite2_width if sprite2_width > sprite2_height else sprite2_height
    )

    # Multiply by half of the theoretical max diagonal length for an estimation of distance
    radius_sum *= 0.71  # 1.42 / 2
    radius_sum_sq = radius_sum * radius_sum

    diff_x = sprite1_position[0] - sprite2_position[0]
    diff_x_sq = diff_x * diff_x
    if diff_x_sq > radius_sum_sq:
        return False

    diff_y = sprite1_position[1] - sprite2_position[1]
    diff_y_sq = diff_y * diff_y
    if diff_y_sq > radius_sum_sq:
        return False

    distance = diff_x_sq + diff_y_sq
    if distance > radius_sum_sq:
        return False

    return are_polygons_intersecting(
        sprite1.hit_box.get_adjusted_points(), sprite2.hit_box.get_adjusted_points()
    )


def _get_nearby_sprites(
    sprite: BasicSprite, sprite_list: SpriteSequence[SpriteType]
) -> list[SpriteType]:
    sprite_count = len(sprite_list)
    if sprite_count == 0:
        return []
    return sprite_list.get_nearby_sprites_gpu(sprite.position, sprite.size)


def check_for_collision_with_list(
    sprite: BasicSprite,
    sprite_list: SpriteSequence[SpriteType],
    method: int = 0,
) -> list[SpriteType]:
    """
    Check for a collision between a sprite, and a list of sprites.

    Args:
        sprite:
            Sprite to check
        sprite_list:
            SpriteList to check against
        method:
            Collision check method. Defaults to 0.

            - 0: auto-select. (spatial if available, GPU if 1500+ sprites, else simple)
            - 1: Spatial Hashing if available,
            - 2: GPU based
            - 3: Simple check-everything.

            Note that while the GPU method is very fast when you cannot use spatial hashing,
            it's also very slow if you are calling this function many times per frame.
            What method is the most appropriate depends entirely on your use case.

    Returns:
        List of sprites colliding, or an empty list.
    """
    if __debug__:
        if not isinstance(sprite, BasicSprite):
            raise TypeError(
                f"Parameter 1 is not an instance of the Sprite class, "
                f"it is an instance of {type(sprite)}."
            )
        if not isinstance(sprite_list, SpriteSequence):
            raise TypeError(f"Parameter 2 is a {type(sprite_list)} instead of expected SpriteList.")

    sprites_to_check: Iterable[SpriteType]
    # Spatial
    if sprite_list.spatial_hash is not None and (method == 1 or method == 0):
        sprites_to_check = sprite_list.spatial_hash.get_sprites_near_sprite(sprite)
    elif (
        method == 3
        or (method == 0 and len(sprite_list) <= 1500)
        or get_window().ctx._gl_api == "webgl"
    ):
        sprites_to_check = sprite_list
    else:
        # GPU transform - Not on WebGL
        sprites_to_check = _get_nearby_sprites(sprite, sprite_list)

    return [
        sprite2
        for sprite2 in sprites_to_check
        if sprite is not sprite2 and _check_for_collision(sprite, sprite2)
    ]

    # collision_list = []
    # for sprite2 in sprite_list_to_check:
    #     if sprite1 is not sprite2 and sprite2 not in collision_list:
    #         if _check_for_collision(sprite1, sprite2):
    #             collision_list.append(sprite2)


def check_for_collision_with_lists(
    sprite: BasicSprite,
    sprite_lists: Iterable[SpriteSequence[SpriteType]],
    method=0,
) -> list[SpriteType]:
    """
    Check for a collision between a Sprite, and a list of SpriteLists.

    Args:
        sprite:
            Sprite to check
        sprite_lists:
            SpriteLists to check against
        method:
            Collision check method. Defaults to 0.

            - 0: auto-select. (spatial if available, GPU if 1500+ sprites, else simple)
            - 1: Spatial Hashing if available,
            - 2: GPU based
            - 3: Simple check-everything.

            Note that while the GPU method is very fast when you cannot use spatial hashing,
            it's also very slow if you are calling this function many times per frame.
            What method is the most appropriate depends entirely on your use case.

    Returns:
        List of sprites colliding, or an empty list.
    """
    if __debug__:
        if not isinstance(sprite, BasicSprite):
            raise TypeError(
                f"Parameter 1 is not an instance of the BasicSprite class, "
                f"it is an instance of {type(sprite)}."
            )

    sprites: list[SpriteType] = []
    sprites_to_check: Iterable[SpriteType]

    for sprite_list in sprite_lists:
        # Spatial
        if sprite_list.spatial_hash is not None and (method == 1 or method == 0):
            sprites_to_check = sprite_list.spatial_hash.get_sprites_near_sprite(sprite)
        elif (
            method == 3
            or (method == 0 and len(sprite_list) <= 1500)
            or get_window().ctx._gl_api == "webgl"
        ):
            sprites_to_check = sprite_list
        else:
            # GPU transform - Not on WebGL
            sprites_to_check = _get_nearby_sprites(sprite, sprite_list)

        for sprite2 in sprites_to_check:
            if sprite is not sprite2 and _check_for_collision(sprite, sprite2):
                sprites.append(sprite2)

    return sprites


def get_sprites_at_point(point: Point, sprite_list: SpriteSequence[SpriteType]) -> list[SpriteType]:
    """
    Get a list of sprites at a particular point. This function sees if any sprite overlaps
    the specified point. If a sprite has a different center_x/center_y but touches the point,
    this will return that sprite.

    Args:
        point: Point to check
        sprite_list: SpriteList to check against

    :returns: List of sprites colliding, or an empty list.
    """
    if __debug__:
        if not isinstance(sprite_list, SpriteSequence):
            raise TypeError(f"Parameter 2 is a {type(sprite_list)} instead of expected SpriteList.")

    sprites_to_check: Iterable[SpriteType]

    if sprite_list.spatial_hash is not None:
        sprites_to_check = sprite_list.spatial_hash.get_sprites_near_point(point)
    else:
        sprites_to_check = sprite_list

    return [
        s
        for s in sprites_to_check
        if is_point_in_polygon(point[0], point[1], s.hit_box.get_adjusted_points())
    ]


def get_sprites_at_exact_point(
    point: Point, sprite_list: SpriteSequence[SpriteType]
) -> list[SpriteType]:
    """
    Get a list of sprites whose center_x, center_y match the given point.
    This does NOT return sprites that overlap the point, the center has to be an exact match.

    Args:
        point: Point to check
        sprite_list: SpriteList to check against
    Returns:
        List of sprites colliding, or an empty list.
    """
    if __debug__:
        if not isinstance(sprite_list, SpriteSequence):
            raise TypeError(f"Parameter 2 is a {type(sprite_list)} instead of expected SpriteList.")

    sprites_to_check: Iterable[SpriteType]

    if sprite_list.spatial_hash is not None:
        sprites_to_check = sprite_list.spatial_hash.get_sprites_near_point(point)
        # checks_saved = len(sprite_list) - len(sprite_list_to_check)
        # print("Checks saved: ", checks_saved)
    else:
        sprites_to_check = sprite_list

    return [s for s in sprites_to_check if s.position == point]


def get_sprites_in_rect(rect: Rect, sprite_list: SpriteSequence[SpriteType]) -> list[SpriteType]:
    """
    Get a list of sprites in a particular rectangle. This function sees if any
    sprite overlaps the specified rectangle. If a sprite has a different
    center_x/center_y but touches the rectangle, this will return that sprite.

    The rectangle is specified as a tuple of (left, right, bottom, top).

    Args:
        rect: Rectangle to check
        sprite_list: SpriteList to check against

    Returns:
        List of sprites colliding, or an empty list.
    """
    if __debug__:
        if not isinstance(sprite_list, SpriteSequence):
            raise TypeError(f"Parameter 2 is a {type(sprite_list)} instead of expected SpriteList.")

    rect_points = rect.to_points()
    sprites_to_check: Iterable[SpriteType]

    if sprite_list.spatial_hash is not None:
        sprites_to_check = sprite_list.spatial_hash.get_sprites_near_rect(rect)
    else:
        sprites_to_check = sprite_list

    return [
        s
        for s in sprites_to_check
        if are_polygons_intersecting(rect_points, s.hit_box.get_adjusted_points())
    ]



class TileMap:
    """
    Class that represents a fully parsed and loaded map from Tiled.
    For examples on how to use this class, see: :ref:`platformer_part_twelve`

    Args:
        map_file:
            A JSON map file for a Tiled map to initialize from
        scaling:
            Global scaling to apply to all Sprites.
        layer_options:
            Extra parameters for each layer.
        use_spatial_hash:
            If set to True, this will make moving a sprite
            in the SpriteList slower, but it will speed up collision detection
            with items in the SpriteList. Great for doing collision detection
            with static walls/platforms.
        hit_box_algorithm:
            The hit box algorithm to use for the Sprite's in this layer.
        tiled_map:
            An already parsed pytiled-parser map object.
            Passing this means that the ``map_file`` argument will be ignored, and the pre-parsed
            map will instead be used. This can be helpful for working with Tiled World files.
        offset:
            Can be used to offset the position of all sprites and objects
            within the map. This will be applied in addition to any offsets from Tiled. This value
            can be overridden with the layer_options dict.
        texture_atlas:
            A default texture atlas to use for the SpriteLists created by this map.
            If not supplied the global default atlas will be used.
        lazy:
            SpriteLists will be created lazily.
        texture_cache_manager:
            The texture cache manager to use for loading textures.
        hex_layout:
            The hex layout to use for the map. If not supplied, the map will be
            treated as a square map. If supplied, the map will be treated as a hexagonal map.


    The ``layer_options`` parameter can be used to specify per layer arguments.
    The available options for this are:

    - ``use_spatial_hash`` - A boolean to enable spatial hashing on this layer's SpriteList.
    - ``scaling`` - A float providing layer specific Sprite scaling.
    - ``hit_box_algorithm`` - The hit box algorithm to use for the Sprite's in this layer.
    - ``offset`` - A tuple containing X and Y position offsets for the layer
    - ``custom_class`` - All objects in the layer are created from this class instead of Sprite. \
                       Must be subclass of Sprite.
    - ``custom_class_args`` - Custom arguments, passed into the constructor of the custom_class
    - ``texture_atlas`` - A texture atlas to use for the SpriteList from this layer, if none is \
        supplied then the one defined at the map level will be used.

        Example configuring layer options for a layer named "Platforms"::

            layer_options = {
                "Platforms": {
                    "use_spatial_hash": True,
                    "scaling": 2.5,
                    "offset": (-128, 64),
                    "custom_class": Platform,
                    "custom_class_args": {
                        "health": 100
                    }
                },
            }

    The keys and their values in each layer are passed to the layer processing functions
    using the `**` operator on the dictionary.
    """

    tiled_map: pytiled_parser.TiledMap
    """
    The pytiled-parser map object. This can be useful for implementing features
    that aren't supported by this class by accessing the raw map data directly.
    """

    width: float
    "The width of the map in tiles. This is the number of tiles, not pixels."

    height: float
    "The height of the map in tiles. This is the number of tiles, not pixels."

    tile_width: float
    "The width in pixels of each tile."

    tile_height: float
    "The height in pixels of each tile."

    background_color: Color | None
    "The background color of the map."

    scaling: float
    "A global scaling value to be applied to all Sprites in the map."

    sprite_lists: dict[str, SpriteList]
    """A dictionary mapping SpriteLists to their layer names. This is used
                    for all tile layers of the map."""

    object_lists: dict[str, list[TiledObject]]
    """
    A dictionary mapping TiledObjects to their layer names. This is used
    for all object layers of the map.
    """

    offset: Vec2
    "A tuple containing the X and Y position offset values."

    def __init__(
        self,
        map_file: str | Path = "",
        scaling: float = 1.0,
        layer_options: dict[str, dict[str, Any]] | None = None,
        use_spatial_hash: bool = False,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        tiled_map: pytiled_parser.TiledMap | None = None,
        offset: Vec2 = Vec2(0, 0),
        texture_atlas: TextureAtlasBase | None = None,
        lazy: bool = False,
        texture_cache_manager: arcade.TextureCacheManager | None = None,
        hex_layout: hexagon.Layout | None = None,
    ) -> None:
        if not map_file and not tiled_map:
            raise AttributeError(
                "Initialized TileMap with an empty map_file or no tiled_map argument"
            )

        if tiled_map:
            self.tiled_map = tiled_map
        else:
            # If we should pull from local resources, replace with proper path
            map_file = resolve(map_file)

            # This attribute stores the pytiled-parser map object
            self.tiled_map = pytiled_parser.parse_map(map_file)

        if self.tiled_map.infinite:
            raise AttributeError(
                "Attempted to load an infinite TileMap. Arcade currently cannot load "
                "infinite maps. Disable the infinite map property and re-save the file."
            )

        if not texture_atlas:
            try:
                texture_atlas = get_window().ctx.default_atlas
            except RuntimeError:
                pass

        self.hex_layout = hex_layout

        self._lazy = lazy
        self.texture_cache_manager = texture_cache_manager or arcade.texture.default_texture_cache

        # Set Map Attributes
        self.width = self.tiled_map.map_size.width
        self.height = self.tiled_map.map_size.height
        self.tile_width = self.tiled_map.tile_size.width
        self.tile_height = self.tiled_map.tile_size.height
        self.background_color = self.tiled_map.background_color

        # Global Layer Defaults
        self.scaling = scaling
        self.use_spatial_hash = use_spatial_hash
        self.hit_box_algorithm = hit_box_algorithm
        self.offset = offset

        # Dictionaries to store the SpriteLists for processed layers
        self.sprite_lists: dict[str, SpriteList] = OrderedDict()
        self.object_lists: dict[str, list[TiledObject]] = OrderedDict()
        self.properties = self.tiled_map.properties

        global_options = {  # type: ignore
            "scaling": self.scaling,
            "use_spatial_hash": self.use_spatial_hash,
            "hit_box_algorithm": self.hit_box_algorithm,
            "offset": self.offset,
            "custom_class": None,
            "custom_class_args": {},
            "texture_atlas": texture_atlas,
        }

        for layer in self.tiled_map.layers:
            if (layer.name in self.sprite_lists) or (layer.name in self.object_lists):
                raise AttributeError(
                    f"You have a duplicate layer name '{layer.name}' in your Tiled map. "
                    "Please use unique names for all layers and tilesets in your map."
                )
            self._process_layer(layer, global_options, layer_options)

    def _process_layer(
        self,
        layer: pytiled_parser.Layer,
        global_options: dict[str, Any],
        layer_options: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        processed: SpriteList | tuple[SpriteList | None, list[TiledObject] | None]

        options = global_options

        if layer_options:
            if layer.name in layer_options:
                new_options = {
                    key: layer_options[layer.name].get(key, global_options[key])
                    for key in global_options
                }
                options = new_options

        if isinstance(layer, pytiled_parser.TileLayer):
            processed = self._process_tile_layer(layer, **options)
            self.sprite_lists[layer.name] = processed
        elif isinstance(layer, pytiled_parser.ObjectLayer):
            processed = self._process_object_layer(layer, **options)
            if processed[0]:
                sprite_list = processed[0]
                if sprite_list:
                    self.sprite_lists[layer.name] = sprite_list
            if processed[1]:
                object_list = processed[1]
                if object_list:
                    self.object_lists[layer.name] = object_list
        elif isinstance(layer, pytiled_parser.ImageLayer):
            processed = self._process_image_layer(layer, **options)
            self.sprite_lists[layer.name] = processed
        elif isinstance(layer, pytiled_parser.LayerGroup):
            if layer.layers:
                for sub_layer in layer.layers:
                    self._process_layer(sub_layer, global_options, layer_options)

    def get_cartesian(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """
        Given a set of coordinates in pixel units, this returns the cartesian coordinates.

        This assumes the supplied coordinates are pixel coordinates, and bases the cartesian
        grid off of the Map's tile size.

        If you have a map with 128x128 pixel Tiles, and you supply coordinates 500, 250 to
        this function you'll receive back 3, 2

        Args:
            x: The X Coordinate to convert
            y: The Y Coordinate to convert
        """
        x = math.floor(x / (self.tile_width * self.scaling))
        y = math.floor(y / (self.tile_height * self.scaling))

        return x, y

    def get_tilemap_layer(self, layer_path: str) -> pytiled_parser.Layer | None:
        """
        Given a path to a layer, this will attempt to return the layer.

        Args:
            layer_path:
                A string representing the path to the layer. For example,
                "Layer Group 1/Layer Group 2/Tile Layer 1"
        """
        assert isinstance(layer_path, str)

        def _get_tilemap_layer(my_path: list[str], layers):
            layer_name = my_path.pop(0)
            for my_layer in layers:
                if my_layer.name == layer_name:
                    if isinstance(my_layer, pytiled_parser.LayerGroup) and len(my_path) != 0:
                        return _get_tilemap_layer(my_path, my_layer.layers)
                    else:
                        return my_layer
            return None

        path = layer_path.strip("/").split("/")
        layer = _get_tilemap_layer(path, self.tiled_map.layers)
        return layer

    def _get_tile_by_gid(self, tile_gid: int) -> pytiled_parser.Tile | None:
        tile_ref: pytiled_parser.Tile | None

        flipped_diagonally = False
        flipped_horizontally = False
        flipped_vertically = False

        if tile_gid & _FLIPPED_HORIZONTALLY_FLAG:
            flipped_horizontally = True
            tile_gid -= _FLIPPED_HORIZONTALLY_FLAG

        if tile_gid & _FLIPPED_DIAGONALLY_FLAG:
            flipped_diagonally = True
            tile_gid -= _FLIPPED_DIAGONALLY_FLAG

        if tile_gid & _FLIPPED_VERTICALLY_FLAG:
            flipped_vertically = True
            tile_gid -= _FLIPPED_VERTICALLY_FLAG

        for tileset_key, tileset in self.tiled_map.tilesets.items():
            if tile_gid < tileset_key:
                continue

            # No specific tile info, but there is a tile sheet
            # print(
            #     f"data {tileset_key} {tileset.tiles} {tileset.image} "
            #     f"{tileset_key} {tile_gid} {tileset.tile_count}"
            # )
            if (
                tileset.image is not None
                and tileset_key <= tile_gid < tileset_key + tileset.tile_count
            ):
                tile_id = tile_gid - tileset_key
                existing_ref = None
                if tileset.tiles is not None:
                    if (tile_gid - tileset_key) in tileset.tiles:
                        existing_ref = tileset.tiles[tile_id]
                        existing_ref.image = tileset.image

                # No specific tile info, but there is a tile sheet
                if existing_ref:
                    tile_ref = existing_ref
                else:
                    tile_ref = pytiled_parser.Tile(id=tile_id, image=tileset.image)
            elif tileset.tiles is None and tileset.image is not None:
                # Not in this tileset, move to the next
                continue
            else:
                if tileset.tiles is None:
                    return None
                tile_ref = tileset.tiles.get(tile_gid - tileset_key)

            if tile_ref:
                my_tile = copy.copy(tile_ref)
                my_tile.tileset = tileset
                my_tile.flipped_vertically = flipped_vertically
                my_tile.flipped_diagonally = flipped_diagonally
                my_tile.flipped_horizontally = flipped_horizontally
                return my_tile

        print(f"Returning NO tile for {tile_gid}.")
        return None

    def _get_tile_by_id(
        self, tileset: pytiled_parser.Tileset, tile_id: int
    ) -> pytiled_parser.Tile | None:
        for tileset_key, cur_tileset in self.tiled_map.tilesets.items():
            if cur_tileset is tileset:
                if cur_tileset.tiles:
                    for tile_key, tile in cur_tileset.tiles.items():
                        if tile_id == tile.id:
                            return tile

        return None

    def _create_sprite_from_tile(
        self,
        tile: pytiled_parser.Tile,
        scaling: float = 1.0,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
    ) -> Sprite:
        """Given a tile from the parser, try and create a Sprite from it."""

        # --- Step 1, Find a reference to an image this is going to be based off of
        map_source = self.tiled_map.map_file
        map_directory = os.path.dirname(map_source)
        image_file = _get_image_source(tile, map_directory)

        if tile.animation:
            if not custom_class:
                custom_class = TextureAnimationSprite
            elif not issubclass(custom_class, TextureAnimationSprite):
                raise RuntimeError(
                    f"""
                    Tried to use a custom class {custom_class.__name__} for animated tiles
                    that doesn't subclass TextureAnimationSprite.
                    Custom classes for animated tiles must subclass TextureAnimationSprite.
                    """
                )
            # print(custom_class.__name__)
            args = {"path_or_texture": image_file, "scale": scaling}
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore
        else:
            if not custom_class:
                custom_class = Sprite
            elif not issubclass(custom_class, Sprite):
                raise RuntimeError(
                    f"""
                    Tried to use a custom class {custom_class.__name__} for
                    a tile that doesn't subclass arcade.Sprite.
                    Custom classes for tiles must subclass arcade.Sprite.
                    """
                )

            # Can image_file be None?
            image_x, image_y, width, height = _get_image_info_from_tileset(tile)
            texture = self.texture_cache_manager.load_or_get_texture(
                image_file,  # type: ignore
                x=image_x,
                y=image_y,
                width=width,
                height=height,
                hit_box_algorithm=hit_box_algorithm,
            )
            texture = _may_be_flip(tile, texture)

            args = {
                "path_or_texture": texture,  # type: ignore
                "scale": scaling,
            }
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore

        if tile.properties is not None and len(tile.properties) > 0:
            for key, value in tile.properties.items():
                my_sprite.properties[key] = value

        if tile.class_:
            my_sprite.properties["class"] = tile.class_

        # Add tile ID to sprite properties
        my_sprite.properties["tile_id"] = tile.id

        if tile.objects is not None:
            if not isinstance(tile.objects, pytiled_parser.ObjectLayer):
                print("Warning, tile.objects is not an ObjectLayer as expected.")
                return my_sprite

            if len(tile.objects.tiled_objects) > 1:
                if tile.image:
                    print(f"Warning, only one hit box supported for tile with image {tile.image}.")
                else:
                    print("Warning, only one hit box supported for tile.")

            for hitbox in tile.objects.tiled_objects:
                points: list[Point2] = []
                if isinstance(hitbox, pytiled_parser.tiled_object.Rectangle):
                    if hitbox.size is None:
                        print(
                            "Warning: Rectangle hitbox created for without a "
                            "height or width Ignoring."
                        )
                        continue

                    sx = hitbox.coordinates.x - (my_sprite.width / (scaling * 2))
                    sy = -(hitbox.coordinates.y - (my_sprite.height / (scaling * 2)))
                    ex = (hitbox.coordinates.x + hitbox.size.width) - (
                        my_sprite.width / (scaling * 2)
                    )
                    # issue #1068
                    # fixed size of rectangular hitbox
                    ey = -(hitbox.coordinates.y + hitbox.size.height) + (
                        my_sprite.height / (scaling * 2)
                    )

                    points = [(sx, sy), (ex, sy), (ex, ey), (sx, ey)]
                elif isinstance(hitbox, pytiled_parser.tiled_object.Polygon) or isinstance(
                    hitbox, pytiled_parser.tiled_object.Polyline
                ):
                    for point in hitbox.points:
                        adj_x = point.x + hitbox.coordinates.x - my_sprite.width / (scaling * 2)
                        adj_y = -(point.y + hitbox.coordinates.y - my_sprite.height / (scaling * 2))
                        adj_point = adj_x, adj_y
                        points.append(adj_point)

                    if points[0][0] == points[-1][0] and points[0][1] == points[-1][1]:
                        points.pop()
                elif isinstance(hitbox, pytiled_parser.tiled_object.Ellipse):
                    if not hitbox.size:
                        print(
                            f"Warning: Ellipse hitbox created without a height "
                            f" or width for {tile.image}. Ignoring."
                        )
                        continue

                    hw = hitbox.size.width / 2
                    hh = hitbox.size.height / 2
                    cx = hitbox.coordinates.x + hw
                    cy = hitbox.coordinates.y + hh

                    acx = cx - (my_sprite.width / (scaling * 2))
                    acy = cy - (my_sprite.height / (scaling * 2))

                    total_steps = 8
                    angles = [step / total_steps * 2 * math.pi for step in range(total_steps)]
                    for angle in angles:
                        x = hw * math.cos(angle) + acx
                        y = -(hh * math.sin(angle) + acy)
                        points.append((x, y))
                else:
                    print(f"Warning: Hitbox type {type(hitbox)} not supported.")

                if tile.flipped_vertically:
                    points = [(point[0], -point[1]) for point in points]

                if tile.flipped_horizontally:
                    points = [(-point[0], point[1]) for point in points]

                if tile.flipped_diagonally:
                    points = [(point[1], point[0]) for point in points]

                my_sprite.hit_box = RotatableHitBox(
                    cast(list[Point2], points),
                    position=my_sprite.position,
                    angle=my_sprite.angle,
                    scale=my_sprite.scale,
                )

        if tile.animation:
            key_frame_list = []
            for frame in tile.animation:
                frame_tile = self._get_tile_by_gid(tile.tileset.firstgid + frame.tile_id)  # type: ignore
                if frame_tile:
                    image_file = _get_image_source(frame_tile, map_directory)

                    if not frame_tile.tileset.image and image_file:  # type: ignore
                        texture = self.texture_cache_manager.load_or_get_texture(
                            image_file, hit_box_algorithm=hit_box_algorithm
                        )
                    elif image_file:
                        # No image for tile, pull from tilesheet
                        (
                            image_x,
                            image_y,
                            width,
                            height,
                        ) = _get_image_info_from_tileset(frame_tile)

                        texture = self.texture_cache_manager.load_or_get_texture(
                            image_file,
                            x=image_x,
                            y=image_y,
                            width=width,
                            height=height,
                            hit_box_algorithm=hit_box_algorithm,
                        )
                    else:
                        raise RuntimeError(
                            f"Warning: failed to load image for animation frame for "
                            f"tile '{frame_tile.id}', '{image_file}'."
                        )

                    texture = _may_be_flip(tile, texture)

                    key_frame = TextureKeyframe(  # type: ignore
                        texture=texture, duration=frame.duration, tile_id=frame.tile_id
                    )
                    key_frame_list.append(key_frame)

                    if len(key_frame_list) == 1:
                        my_sprite.texture = key_frame.texture

            # type: ignore
            cast(TextureAnimationSprite, my_sprite).animation = TextureAnimation(
                keyframes=key_frame_list
            )

        return my_sprite

    def _process_image_layer(
        self,
        layer: pytiled_parser.ImageLayer,
        texture_atlas: DefaultTextureAtlas,
        scaling: float = 1.0,
        use_spatial_hash: bool = False,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
    ) -> SpriteList:
        sprite_list: SpriteList = SpriteList(
            use_spatial_hash=use_spatial_hash,
            atlas=texture_atlas,
            lazy=self._lazy,
        )

        map_source = self.tiled_map.map_file
        map_directory = os.path.dirname(map_source)
        image_file = layer.image

        if not os.path.exists(image_file) and (map_directory):
            try2 = Path(map_directory, image_file)
            if not os.path.exists(try2):
                print(f"Warning, can't find image {image_file} for Image Layer {layer.name}")
            image_file = try2

        my_texture = self.texture_cache_manager.load_or_get_texture(
            image_file,
            hit_box_algorithm=hit_box_algorithm,
        )

        if layer.transparent_color:
            # The pillow source doesn't annotate a return type for this method, but:
            # 1. The docstring does specify the returned object is sequence-like
            # 2. We convert to RGBA mode implicitly in load_or_get_texture above
            data: Sequence[RGBA255] = my_texture.image.getdata()  # type:ignore

            target = layer.transparent_color
            new_data = []
            for item in data:
                if item[0] == target[0] and item[1] == target[1] and item[2] == target[2]:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)

            my_texture.image.putdata(new_data)

        if not custom_class:
            custom_class = Sprite
        elif not issubclass(custom_class, Sprite):
            raise RuntimeError(
                f"""
                    Tried to use a custom class {custom_class.__name__} for an
                    Image Layer that doesn't subclass arcade.Sprite.
                    Custom classes for image layers must subclass arcade.Sprite.
                """
            )

        args = {
            "filename": image_file,
            "scale": scaling,
            "path_or_texture": my_texture,
            "hit_box_algorithm": hit_box_algorithm,
        }

        my_sprite = custom_class(**custom_class_args, **args)  #  type: ignore

        if layer.properties:
            sprite_list.properties = layer.properties
            for key, value in layer.properties.items():
                my_sprite.properties[key] = value

        if layer.tint_color:
            my_sprite.color = ArcadeColor.from_iterable(layer.tint_color)

        if layer.opacity:
            my_sprite.alpha = int(layer.opacity * 255)

        my_sprite.center_x = ((layer.offset[0] * scaling) + my_sprite.width / 2) + offset[0]
        my_sprite.top = (
            self.tiled_map.map_size.height * self.tiled_map.tile_size[1] - layer.offset[1]
        ) * scaling + offset[1]

        sprite_list.visible = layer.visible
        sprite_list.append(my_sprite)
        return sprite_list

    def _process_tile_layer(
        self,
        layer: pytiled_parser.TileLayer,
        texture_atlas: DefaultTextureAtlas,
        scaling: float = 1.0,
        use_spatial_hash: bool = False,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
    ) -> SpriteList:
        sprite_list: SpriteList = SpriteList(
            use_spatial_hash=use_spatial_hash,
            atlas=texture_atlas,
            lazy=self._lazy,
        )

        if self.hex_layout is None:
            map_array = layer.data
            if TYPE_CHECKING:
                # Can never be None because we already detect and reject infinite maps
                assert map_array

            # Loop through the layer and add in the list
            for row_index, row in enumerate(map_array):
                for column_index, item in enumerate(row):
                    # Check for an empty tile
                    if item == 0:
                        continue

                    tile = self._get_tile_by_gid(item)
                    if tile is None:
                        raise ValueError(
                            f"Couldn't find tile for item {item} in layer "
                            f"'{layer.name}' in file '{self.tiled_map.map_file}'"
                            f"at ({column_index}, {row_index})."
                        )

                    my_sprite = self._create_sprite_from_tile(
                        tile,
                        scaling=scaling,
                        hit_box_algorithm=hit_box_algorithm,
                        custom_class=custom_class,
                        custom_class_args=custom_class_args,
                    )

                    if my_sprite is None:
                        print(
                            f"Warning: Could not create sprite number {item} "
                            f"in layer '{layer.name}' {tile.image}"
                        )
                    else:
                        my_sprite.center_x = (
                            column_index * (self.tiled_map.tile_size[0] * scaling)
                            + my_sprite.width / 2
                        ) + offset[0]
                        my_sprite.center_y = (
                            (self.tiled_map.map_size.height - row_index - 1)
                            * (self.tiled_map.tile_size[1] * scaling)
                            + my_sprite.height / 2
                        ) + offset[1]

                        # Tint
                        if layer.tint_color:
                            my_sprite.color = ArcadeColor.from_iterable(layer.tint_color)

                        # Opacity
                        opacity = layer.opacity
                        if opacity:
                            my_sprite.alpha = int(opacity * 255)

                        sprite_list.visible = layer.visible
                        sprite_list.append(my_sprite)

                    if layer.properties:
                        sprite_list.properties = layer.properties

            return sprite_list

        # Hexagonal map
        map_array = layer.data
        if TYPE_CHECKING:
            # Can never be None because we already detect and reject infinite maps
            assert map_array

        # FIXME: get tile size from tileset

        # Loop through the layer and add in the list
        for row_index, row in enumerate(reversed(map_array)):
            for column_index, item in enumerate(row):
                # Check for an empty tile
                if item == 0:
                    continue

                tile = self._get_tile_by_gid(item)
                if tile is None:
                    msg = (
                        f"Couldn't find tile for item {item} in layer "
                        f"'{layer.name}' in file '{self.tiled_map.map_file}'"
                        f"at ({column_index}, {row_index})."
                    )
                    raise ValueError(msg)

                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scaling=scaling,
                    hit_box_algorithm=hit_box_algorithm,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )

                if my_sprite is None:
                    print(
                        f"Warning: Could not create sprite number {item} "
                        f"in layer '{layer.name}' {tile.image}"
                    )
                else:
                    # FIXME: handle map scaling
                    # Convert from odd-r offset to cube coordinates
                    offset_coord = hexagon.OffsetCoord(column_index, row_index)
                    hex_ = offset_coord.to_cube("even-r")

                    # Convert hex position to pixel position
                    pixel_pos = hex_.to_pixel(self.hex_layout)
                    # FIXME: why is the y position negative?
                    pixel_pos = hexagon.Vec2(pixel_pos.x, pixel_pos.y)
                    my_sprite.center_x = pixel_pos.x
                    my_sprite.center_y = pixel_pos.y

                    # Tint
                    if layer.tint_color:
                        my_sprite.color = ArcadeColor.from_iterable(layer.tint_color)

                    # Opacity
                    opacity = layer.opacity
                    if opacity:
                        my_sprite.alpha = int(opacity * 255)

                    sprite_list.visible = layer.visible
                    sprite_list.append(my_sprite)

                if layer.properties:
                    sprite_list.properties = layer.properties

        return sprite_list

    def _process_object_layer(
        self,
        layer: pytiled_parser.ObjectLayer,
        texture_atlas: DefaultTextureAtlas,
        scaling: float = 1.0,
        use_spatial_hash: bool = False,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
    ) -> tuple[SpriteList | None, list[TiledObject] | None]:
        if not scaling:
            scaling = self.scaling

        sprite_list: SpriteList | None = None
        objects_list: list[TiledObject] | None = []

        shape: list[Point2] | tuple[int, int, int, int] | Point2 | None = None

        for cur_object in layer.tiled_objects:
            # shape: Optional[Point | PointList | Rect] = None
            if isinstance(cur_object, pytiled_parser.tiled_object.Tile):
                if not sprite_list:
                    sprite_list = SpriteList(
                        use_spatial_hash=use_spatial_hash,
                        atlas=texture_atlas,
                        lazy=self._lazy,
                    )

                tile = self._get_tile_by_gid(cur_object.gid)
                if tile is None:
                    raise Exception(f"Tile with gid not found: {cur_object.gid}")
                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scaling=scaling,
                    hit_box_algorithm=hit_box_algorithm,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )

                x = (cur_object.coordinates.x * scaling) + offset[0]
                y = (
                    (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    )
                    * scaling
                ) + offset[1]

                my_sprite.width = width = cur_object.size[0] * scaling
                my_sprite.height = height = cur_object.size[1] * scaling
                # center_x = width / 2
                # center_y = height / 2
                if cur_object.rotation:
                    rotation = math.radians(cur_object.rotation)
                else:
                    rotation = 0

                angle_degrees = math.degrees(rotation)
                rotated_center_x, rotated_center_y = rotate_point(
                    width / 2, height / 2, 0, 0, angle_degrees
                )

                my_sprite.position = (x + rotated_center_x, y + rotated_center_y)
                my_sprite.angle = angle_degrees
                my_sprite.visible = cur_object.visible

                if layer.tint_color:
                    my_sprite.color = ArcadeColor.from_iterable(layer.tint_color)

                opacity = layer.opacity
                if opacity:
                    my_sprite.alpha = int(opacity * 255)

                if cur_object.properties and "change_x" in cur_object.properties:
                    my_sprite.change_x = prop_to_float(cur_object.properties["change_x"])

                if cur_object.properties and "change_y" in cur_object.properties:
                    my_sprite.change_y = prop_to_float(cur_object.properties["change_y"])

                if cur_object.properties and "boundary_bottom" in cur_object.properties:
                    my_sprite.boundary_bottom = prop_to_float(
                        cur_object.properties["boundary_bottom"]
                    )

                if cur_object.properties and "boundary_top" in cur_object.properties:
                    my_sprite.boundary_top = prop_to_float(cur_object.properties["boundary_top"])

                if cur_object.properties and "boundary_left" in cur_object.properties:
                    my_sprite.boundary_left = prop_to_float(cur_object.properties["boundary_left"])

                if cur_object.properties and "boundary_right" in cur_object.properties:
                    my_sprite.boundary_right = prop_to_float(
                        cur_object.properties["boundary_right"]
                    )

                if cur_object.properties:
                    my_sprite.properties.update(cur_object.properties)

                if cur_object.class_:
                    my_sprite.properties["class"] = cur_object.class_

                if cur_object.name:
                    my_sprite.properties["name"] = cur_object.name

                sprite_list.visible = layer.visible
                sprite_list.append(my_sprite)
                continue
            elif isinstance(cur_object, pytiled_parser.tiled_object.Point):
                x = cur_object.coordinates.x * scaling
                y = (
                    self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                    - cur_object.coordinates.y
                ) * scaling

                shape = (x + offset[0], y + offset[1])
            elif isinstance(cur_object, pytiled_parser.tiled_object.Rectangle):
                if cur_object.size.width == 0 and cur_object.size.height == 0:
                    print(
                        f"WARNING: Tiled object with ID {cur_object.id} is a rectangle "
                        "with a width and height of 0. Loading it as a single point."
                    )
                    x = cur_object.coordinates.x * scaling
                    y = (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    ) * scaling

                    shape = (x + offset[0], y + offset[1])
                else:
                    sx = cur_object.coordinates.x * scaling + offset[0]
                    sy = (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    ) * scaling + offset[1]

                    ex = sx + cur_object.size.width * scaling
                    ey = sy - cur_object.size.height * scaling

                    p1 = (sx, sy)
                    p2 = (ex, sy)
                    p3 = (ex, ey)
                    p4 = (sx, ey)

                    shape = [p1, p2, p3, p4]
            elif isinstance(cur_object, pytiled_parser.tiled_object.Polygon) or isinstance(
                cur_object, pytiled_parser.tiled_object.Polyline
            ):
                points: list[Point2] = []
                shape = points
                for point in cur_object.points:
                    x = point.x + cur_object.coordinates.x
                    y = (self.height * self.tile_height) - (point.y + cur_object.coordinates.y)
                    point = (x + offset[0], y + offset[1])  # type: ignore
                    points.append(point)

                # If shape is a polyline, and it is closed, we need to
                # remove the duplicate end point
                if points[0][0] == points[-1][0] and points[0][1] == points[-1][1]:
                    points.pop()
            elif isinstance(cur_object, pytiled_parser.tiled_object.Ellipse):
                hw = cur_object.size.width / 2
                hh = cur_object.size.height / 2
                cx = cur_object.coordinates.x + hw
                cy = cur_object.coordinates.y + hh

                total_steps = 8
                angles = [step / total_steps * 2 * math.pi for step in range(total_steps)]
                points = []
                shape = points
                for angle in angles:
                    x = hw * math.cos(angle) + cx
                    y = -(hh * math.sin(angle) + cy)
                    point = (x + offset[0], y + offset[1])  # type: ignore
                    points.append(point)
            elif isinstance(cur_object, pytiled_parser.tiled_object.Text):
                pass
            else:
                continue

            if shape:
                tiled_object = TiledObject(
                    shape, cur_object.properties, cur_object.name, cur_object.class_
                )

                if not objects_list:
                    objects_list = []

                objects_list.append(tiled_object)

        return sprite_list or None, objects_list or None


def load_tilemap(
    map_file: str | Path,
    scaling: float = 1.0,
    layer_options: dict[str, dict[str, Any]] | None = None,
    use_spatial_hash: bool = False,
    hit_box_algorithm: HitBoxAlgorithm | None = None,
    offset: Vec2 = Vec2(0, 0),
    texture_atlas: DefaultTextureAtlas | None = None,
    lazy: bool = False,
    hex_layout: hexagon.Layout | None = None,
) -> TileMap:
    """
    Given a .json map file, loads in and returns a `TileMap` object.

    A TileMap can be created directly using the classes `__init__` function.
    This function exists for ease of use.

    For more clarification on the layer_options key, see the `__init__` function
    of the `TileMap` class

    Args:
        map_file:
            The JSON map file.
        scaling:
            The global scaling to apply to all Sprite's within the map.
        use_spatial_hash:
            If set to True, this will make moving a sprite
            in the SpriteList slower, but it will speed up collision detection
            with items in the SpriteList. Great for doing collision detection
            with static walls/platforms.
        hit_box_algorithm:
            The hit box algorithm to use for collision detection.
        layer_options:
            Layer specific options for the map.
        offset:
            Can be used to offset the position of all sprites and objects
            within the map. This will be applied in addition to any offsets from Tiled. This value
            can be overridden with the layer_options dict.
        texture_atlas:
            A default texture atlas to use for the SpriteLists created by this map.
            If not supplied the global default atlas will be used.
        lazy:
            SpriteLists will be created lazily.
        hex_layout:
            The hex layout to use for the map. If not supplied, the map will be
            treated as a square map. If supplied, the map will be treated as a hexagonal map.
    """
    return TileMap(
        map_file=map_file,
        scaling=scaling,
        layer_options=layer_options,
        use_spatial_hash=use_spatial_hash,
        hit_box_algorithm=hit_box_algorithm,
        offset=offset,
        texture_atlas=texture_atlas,
        lazy=lazy,
        hex_layout=hex_layout,
    )