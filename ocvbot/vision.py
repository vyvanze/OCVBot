# coding=UTF-8
"""
Module for "seeing" the client.

"""
import logging as log
import pathlib

import pyautogui as pag

from ocvbot import input, misc, startup as start


def haystack_locate(needle, haystack, grayscale=False, conf=0.95):
    """
    Finds the coordinates of a needle image within a haystack image.

    Args:
        needle (file): Filepath to the needle image.
        haystack (file): Filepath to the haystack image.
        grayscale (bool): Whether to use grayscale matching to increase
                          speed, default is false.
        conf (float): Similarity required to match needle to haystack,
                      expressed as a decimal <= 1, default is 0.95.

    """
    # Make sure file path is OS-agnostic.
    needle = str(pathlib.Path(needle))

    target_image = pag.locate(needle, haystack, confidence=conf, grayscale=grayscale)
    if target_image is not None:
        log.debug('Found center of %s, %s', needle, target_image)
        return target_image

    log.debug('Cannot find center of %s, conf=%s', needle, conf)
    return False


def wait_for_needle_list(loops, needle_list, sleep_range):
    """
    Works like vision.wait_for_needle(), except multiple needles can be
    searched for simultaneously.

    Args:
        loops: The number of tries to look for each needle in needle_list.
        needle_list: A list of filepaths to the needles to look for. Each
                     item in the list is a 2-tuple containing:
                     - The filepath to the needle.
                     - The region in which to search for that needle.
        sleep_range: A 2-tuple containing the minimum and maximum number
                     of miliseconds to wait after each loop.

    Returns:
        If a needle in needle_list is found, returns a 2-tuple containing
        the ltwh dimensions of the needle and the index of the needle in
        needle_list (This is so the function knows which needle was found).

        Returns false if no needles in needle_list could be found.

    """
    for _ in range(1, loops):

        for item in needle_list:
            needle, region = item

            needle_found = Vision(region=region,
                                  needle=needle,
                                  loop_num=1).wait_for_needle(get_tuple=True)
            if needle_found is True:
                return needle_found, needle_list.index(needle)

        misc.sleep_rand(sleep_range[0], sleep_range[1])

    return False


class Vision:
    """
    Contains methods for locating images on the display.
    All coordinates are relative to the top left corner of the display.
    All coordinates are in a (left, top, width, height) format.

    Args:
        region (tuple): A 4-tuple containing the Left, Top, Width, and
                      Height of the region in which to look for the
                      needle.
        needle (file): The image to search within the (ltwh) coordinates
                       for. Must be a filepath.
        loctype (str): Whether to return the needle's (ltwh) coordinates
                       or its (X, Y) center.
            regular = Returns the needle's left, top, width, and height
                      as a 4-tuple.
            center = Returns the (X, Y) coordinates of the needle's
                     center as a 2-tuple (relative to the display's
                     dimensions).
        conf (float): The confidence value required to match the needle
                      successfully, expressed as a decimal <= 1. This is
                      used by PyAutoGUI, default is 0.95.
        loop_num (int): The number of times wait_for_image() will search
                        the given coordinates for the needle, default is
                        10.
        loop_sleep_range (tuple): A 2-tuple containing the minimum and
                                  maximum number of miliseconds to wait
                                  between image-search loops. Used by
                                  the wait_for_image() method, default
                                  is (0, 100).
        grayscale (bool): Converts the haystack to grayscale before
                          searching within it. Speeds up searching by
                          about 30%, default is false.

    """

    def __init__(self, region, needle, loctype='regular', conf=0.95,
                 loop_num=10, loop_sleep_range=(0, 100), grayscale=False):
        self.grayscale = grayscale
        self.region = region
        self.needle = needle
        self.loctype = loctype
        self.conf = conf
        self.loop_num = loop_num
        self.loop_sleep_range = loop_sleep_range

    def find_needle(self):
        """
        Searches within the self.ltwh coordinates for self.needle.

        Returns:
            If the needle is found and self.loctype is 'regular', returns
            the needle's left/top/width/height dimensions as a 4-tuple.

            If the needle is found and self.loctype is 'center', returns
            coordinates of the needle's (X, Y) center as a 2-tuple.

            If the needle is not found, returns False.

        """
        # Make sure file path is OS-agnostic.
        needle = str(pathlib.Path(self.needle))

        if self.loctype == 'regular':
            needle_coords = pag.locateOnScreen(needle,
                                               confidence=self.conf,
                                               grayscale=self.grayscale,
                                               region=self.region)
            if needle_coords is not None:
                log.debug('Found regular image %s, %s', needle, needle_coords)
                return needle_coords
            else:
                log.debug('Cannot find regular image %s, conf=%s', needle, self.conf)
                return False

        elif self.loctype == 'center':
            needle_coords = pag.locateCenterOnScreen(needle,
                                                     confidence=self.conf,
                                                     grayscale=self.grayscale,
                                                     region=self.region)
            if needle_coords is not None:
                log.debug('Found center of image %s, %s', needle, needle_coords)
                return needle_coords
            else:
                log.debug('Cannot find center of image %s, conf=%s', needle, self.conf)
                return False

        raise RuntimeError('Incorrect mlocate function parameters!')

    def wait_for_needle(self, get_tuple=False):
        """
        Repeatedly searches within the self.ltwh coordinates for the needle.

        Args:
            get_tuple (bool): Whether to return a tuple containing the
                              needle's coordinates, default is False.

        Returns:
            If get_tuple is False, returns True if needle was found.

            If get_tuple is true and self.loctype is 'regular', returns
            a 4-tuple containing the (left, top, width, height) coordinates
            of the needle. If self.loctype is 'center', returns a 2-tuple
            containing the (X, Y) center of the needle.

            Returns False if needle was not found.

        """
        # log.debug('Looking for %s', + self.needle)

        # Add 1 to self.loop_num because if loop_num=1, it won't loop at
        #   all.
        for tries in range(1, (self.loop_num + 1)):

            needle_coords = Vision.find_needle(self)

            if isinstance(needle_coords, tuple) is True:
                log.debug('Found %s after trying %s times.', self.needle, tries)
                if get_tuple is True:
                    return needle_coords
                else:
                    return True
            else:
                log.debug('Cannot find %s, tried %s times.', self.needle, tries)
                misc.sleep_rand(self.loop_sleep_range[0], self.loop_sleep_range[1])

        log.debug('Timed out looking for %s', self.needle)
        return False

    def click_needle(self, sleep_range=(50, 200, 50, 200),
                     move_duration_range=(50, 1500),
                     button='left', move_away=False):
        """
        Moves the mouse to the provided needle image and clicks on
        it.

        Args:
            sleep_range (tuple): Passed to the Mouse class in input.py,
                                 see its docstring for more info.
            move_duration_range (tuple): Passed to the Mouse class in
                                         input.py, see its docstring for
                                         more info.
            button (str): The mouse button to use when clicking on the
                          needle, default is 'left'.
            move_away (bool): Whether to move the mouse out of the way
                              after clicking on the needle. Useful when
                              mlocate() needs to determine the status
                              of a button that the mouse just clicked.

        Returns:
            Returns True if the needle was clicked on successfully,
            returns False otherwise.

        """
        log.debug('Looking for %s to click on.', self.needle)

        needle_coords = self.wait_for_needle(get_tuple=True)

        if isinstance(needle_coords, tuple) is True:
            # Randomize the location the mouse cursor will move to using
            #   the dimensions of needle image.
            # The mouse will click anywhere within the needle image.
            input.Mouse(region=needle_coords,
                        sleep_range=sleep_range,
                        move_duration_range=move_duration_range,
                        button=button).click_coord()

            log.debug('Clicking on %s', self.needle)

            if move_away is True:
                input.Mouse(region=(25, 25, 100, 100), move_duration_range=(50, 200)).moverel()
            return True

        else:
            return False


def orient(region=(0, 0, start.DISPLAY_WIDTH, start.DISPLAY_HEIGHT),
           launch_client=False):
    """
    Looks for an icon to orient the client. If it's found, use its
    location within the game client to determine the coordinates of the
    game client relative to the display's coordinates.

    This function is also used to determine if the client is logged out.
    This is generally one of the first functions that is run upon script
    startup.

    Args:
        region (tuple): A 4-tuple containing the left, top, width, and
                      height of the coordinate space to search within,
                      relative to the display's coordinates. By default
                      uses the entire display.

    Raises:
       Raises an exception if the client cannot be found, or if the
       function can't determine if the client is logged in or logged
       out.

    Returns:
         If client is logged in, returns a 2-tuple containing a string
         with the text "logged_in" and a 2-tuple of the center (X, Y)
         coordinates of the orient needle.

         If client is logged out, returns a 2-tuple containing a string
         with the text "logged_out" and a 2-tuple of the center (X, Y)
         coordinates of the orient-logged-out needle.

    """
    logged_in = Vision(region=region, needle='needles/minimap/orient.png',
                       loctype='center', loop_num=1,
                       conf=0.8).wait_for_needle(get_tuple=True)
    if isinstance(logged_in, tuple) is True:
        return 'logged_in', logged_in

    # If the client is not logged in, check if it's logged out.
    logged_out = Vision(region=region, needle='needles/login-menu/orient-logged-out.png',
                        loctype='center', loop_num=1,
                        conf=0.8).wait_for_needle(get_tuple=True)
    if isinstance(logged_out, tuple) is True:
        return 'logged_out', logged_out

    if launch_client is True:
        # TODO: Write start_client()
        #start_client()
        # Try 10 times to find the login screen after launching the client.
        for _ in range(1, 10):
            misc.sleep_rand(8000, 15000)
            orient(region=region, launch_client=False)
        log.critical('Could not find client! %s', launch_client)
        raise Exception('Could not find client!')

    else:
        raise Exception('Could not find client!')


# ----------------------------------------------------------------------
# Setup the necessary region tuples for the Vision class and orient the client.
# ----------------------------------------------------------------------

display = (0, 0, start.DISPLAY_WIDTH, start.DISPLAY_HEIGHT)
(client_status, anchor) = orient(region=display)
(client_left, client_top) = anchor

if client_status == 'logged_in':
    client_left -= 735
    client_top -= 21
elif client_status == 'logged_out':
    client_left -= 183
    client_top -= 59

# Each of these tuples contains coordinates for the "region" parameter
#   of PyAutoGUI's Locate() functions. These tuples are used by methods
#   in the Vision class to look for needles within the specified set of
#   coordinates, rather than within the entire display's coordinates,
#   which is much faster.

# All coordinates are in a (left, top, width, height) format, to match
#   PyAutoGUI.

# The fixed-width Java game client.
client = (client_left, client_top,
          start.CLIENT_WIDTH, start.CLIENT_HEIGHT)

# The player's inventory.
inv_left = client_left + 548
inv_top = client_top + 205
inv = (inv_left, inv_top,
       start.INV_WIDTH, start.INV_HEIGHT)

# Bottom half of the player's inventory.
inv_bottom_left = inv_left
inv_bottom_top = inv_top + start.INV_HALF_HEIGHT
inv_bottom = (inv_bottom_left, inv_bottom_top,
              start.INV_WIDTH, start.INV_HALF_HEIGHT)

# Right half of the player's inventory.
inv_right_half_left = (inv_left + start.INV_HALF_WIDTH) - 5
inv_right_half_top = inv_top
inv_right_half = (inv_right_half_left, inv_right_half_top,
                  start.INV_HALF_WIDTH, start.INV_HEIGHT)

# Left half of the player's inventory.
inv_left_half_left = inv_left
inv_left_half_top = inv_top
inv_left_half = (inv_left_half_left, inv_left_half_top,
                 start.INV_HALF_WIDTH, start.INV_HEIGHT)

# Gameplay screen.
game_screen_left = client_left + 4
game_screen_top = client_top + 4
game_screen = (game_screen_left, game_screen_top,
               start.GAME_SCREEN_WIDTH, start.GAME_SCREEN_HEIGHT)

# The player's inventory, plus the top and bottom "side stone" tabs that
#   open all the different menus.
side_stones_left = client_left + 516
side_stones_top = client_top + 166
side_stones = (side_stones_left, side_stones_top,
               start.SIDE_STONES_WIDTH, start.SIDE_STONES_HEIGHT)

# Chat menu.
chat_menu_left = client_left + 7
chat_menu_top = client_top + 345
chat_menu = (chat_menu_left, chat_menu_top,
             start.CHAT_MENU_WIDTH, start.CHAT_MENU_HEIGHT)

# The most recent chat message.
chat_menu_recent_left = chat_menu_left - 3
chat_menu_recent_top = chat_menu_top + 98
chat_menu_recent = (chat_menu_recent_left, chat_menu_recent_top,
                    start.CHAT_MENU_RECENT_WIDTH, start.CHAT_MENU_RECENT_HEIGHT)

# The text input fields on the login menu.
login_field_left = client_left + 273
login_field_top = client_top + 242
login_field = (login_field_left, login_field_top,
               start.LOGIN_FIELD_WIDTH, start.LOGIN_FIELD_HEIGHT)

pass_field_left = client_left + 275
pass_field_top = client_top + 258
pass_field = (pass_field_left, pass_field_top,
              start.LOGIN_FIELD_WIDTH, start.LOGIN_FIELD_HEIGHT)

# The entire minimap.
minimap_left = client_left + 571
minimap_top = client_top + 11
minimap = (minimap_left, minimap_top,
           start.MINIMAP_WIDTH, start.MINIMAP_HEIGHT)

# The current minimap "slice" for locating the player on the world map.
minimap_slice_left = client_left + 590
minimap_slice_top = client_top + 51
minimap_slice = (minimap_slice_left, minimap_slice_top,
                 start.MINIMAP_SLICE_WIDTH, start.MINIMAP_SLICE_HEIGHT)
