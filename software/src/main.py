# WS2812 LED Matrix Gamecontrol (Tetris, Snake, Pong)
# by M Oehler
# https://hackaday.io/project/11064-raspberry-pi-retro-gaming-led-display
# ported from
# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import pygame
import time
import os
import subprocess
from PIL import Image, ImageFont, ImageDraw
from pygame.display import update
from pygame.draw import circle

from . import PI, INSTALL_DIR, RES_DIR
from .tetris import runTetrisGame
from .snake import runSnakeGame
from . import clock

# If Pi = False the script runs in simulation mode using pygame lib
if PI:
    # dummy display for pygame joystick usage
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import board
    import neopixel
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi, noop
    from luma.core.render import canvas
    from luma.core.virtual import viewport
    from luma.core.legacy import text, show_message
    from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

# only modify this two values for size adaption!
PIXEL_X = 10
PIXEL_Y = 20

SIZE = 20
FPS = 15
BOXSIZE = 20
WINDOWWIDTH = BOXSIZE * PIXEL_X
WINDOWHEIGHT = BOXSIZE * PIXEL_Y
BOARDWIDTH = PIXEL_X
BOARDHEIGHT = PIXEL_Y
BLANK = '.'
LED_BRIGHTNESS = 1

# Small Font used for the 8x8 dot matrix display
PIXELFONT = ImageFont.truetype(f"{RES_DIR}/font/arriva-7x3.ttf", 8)


#               R    G    B
WHITE = (255, 255, 255)
GRAY = (185, 185, 185)
BLACK = (0,   0,   0)
RED = (255,   0,   0)
DARKRED = (128, 0, 0)
LIGHTRED = (175,  20,  20)
GREEN = (0, 255,   0)
DARKGREEN = (0, 128,   0)
LIGHTGREEN = (20, 175,  20)
BLUE = (0,   0, 255)
DARKBLUE = (0,   0, 128)
LIGHTBLUE = (20,  20, 175)
YELLOW = (255, 255,   0)
DARKYELLOW = (128, 128,   0)
LIGHTYELLOW = (175, 175,  20)
CYAN = (0, 255, 255)
DARKCYAN = (0, 128, 128)
MAGENTA = (255,   0, 255)
DARKMAGENTA = (128,   0, 128)
ORANGE = (255, 100,   0)
DARKORANGE = (128, 50,   0)
LIGHTGREY = (128, 128, 128)


BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS = (BLUE, GREEN, RED, YELLOW, CYAN, MAGENTA, ORANGE, LIGHTGREY)
DARKCOLORS = (DARKBLUE, DARKGREEN, DARKRED, DARKYELLOW,
              DARKCYAN, DARKMAGENTA, DARKORANGE)
LIGHTCOLORS = (LIGHTBLUE, LIGHTGREEN, LIGHTRED, LIGHTYELLOW)
# assert len(COLORS) == len(LIGHTCOLORS) # each color must have light color


# font clock #

clock_font = [
    0x1F, 0x11, 0x1F,
    0x00, 0x00, 0x1F,
    0x1D, 0x15, 0x17,
    0x15, 0x15, 0x1F,
    0x07, 0x04, 0x1F,
    0x17, 0x15, 0x1D,
    0x1F, 0x15, 0x1D,
    0x01, 0x01, 0x1F,
    0x1F, 0x15, 0x1F,
    0x17, 0x15, 0x1F]

theTetrisFont = [
    0x78, 0x78, 0x1E, 0x1E,  # S
    0x1E, 0x1E, 0x78, 0x78,  # Z
    0x00, 0xFF, 0xFF, 0x00,  # I
    0x06, 0x06, 0x7E, 0x7E,  # J
    0x7E, 0x7E, 0x06, 0x06,  # L
    0x3C, 0x3C, 0x3C, 0x3C,  # O
    0x7E, 0x7E, 0x18, 0x18,  # T
]

DEVICE = None
PIXELS = None

if PI:
    serial = spi(port=0, device=0, gpio=noop())
    DEVICE = max7219(serial, cascaded=4,
                     blocks_arranged_in_reverse_order=False)
    pixel_pin = board.D18
    # The number of NeoPixels
    num_pixels = PIXEL_X*PIXEL_Y
    order = neopixel.GRB
    PIXELS = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=LED_BRIGHTNESS,
        auto_write=False, pixel_order=order)

# key server for controller #

QKEYDOWN = 0
QKEYUP = 1

CONTROLLER = {}
if PI:
    # 8-Bitdo Controller Input Keycodes
    CONTROLLER = {
        11: 'UP',
        12: 'DOWN',
        13: 'LEFT',
        14: 'RIGHT',
        3: 'X',
        2: 'Y',
        1: 'A',
        0: 'B',
        4: 'SELECT',
        6: 'START',
        # 10: 'R',
        # 9: 'L',
    }

else:
    # Keyboard Controlls based on scancode
    # Arrow Keys + 1234 (ABXY) + <ENTER> (Start) + <RETURN> (Select)
    CONTROLLER = {
        82: 'UP',
        81: 'DOWN',
        80: 'LEFT',
        79: 'RIGHT',
        30: 'A',
        31: 'B',
        32: 'X',
        33: 'Y',
        40: 'START',
        42: 'SELECT',
    }


mask = bytearray([1, 2, 4, 8, 16, 32, 64, 128])


def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT
    global a1_counter, RUNNING
    a1_counter = 0
    RUNNING = True
    joystick_cnt = 0

    if not PI:
        pygame.init()
        FPSCLOCK = pygame.time.Clock()
        DISPLAYSURF = pygame.display.set_mode((PIXEL_X*SIZE, PIXEL_Y*SIZE))
        BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
        BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
        pygame.display.set_caption('Pi Games')
        DISPLAYSURF.fill(BGCOLOR)
        pygame.display.update()
        drawImage(f'{RES_DIR}/pi.bmp')
        updateScreen()
        time.sleep(2)
    else:
        print("PI SETUP")
        DEVICE.contrast(200)
        pygame.init()
        drawImage(f'{RES_DIR}/pi.bmp')
        updateScreen()
        pygame.joystick.init()
        joystick_detected = False
        while not joystick_detected:
            # scroll_text("Waiting for controller...")
            pygame.joystick.quit()
            pygame.joystick.init()
            try:
                joystick = pygame.joystick.Joystick(
                    0)  # create a joystick instance
                joystick.init()  # init instance
                print("Initialized joystick: {}".format(joystick.get_name()))
                joystick_detected = True
            except pygame.error:
                print("no joystick found.")
                joystick_detected = False

    clearScreen()

    drawClock(1)

    # Check for joystick in the first loop
    joystick_cnt = 45
    menu_selected = 0
    while True:
        # select one of the three menu entries (Tetris, Snake, Clock)
        clearScreen()
        # drawSymbols()
        drawImage(f'{RES_DIR}/menu{menu_selected}.bmp')
        # draw color if clock menu is selected
        if menu_selected == 2:
            clock.binary_clock_overlay(True)
        else:
            clock.binary_clock_overlay()
        updateScreen()
        if not PI:
            checkForQuit()

        # check if joystick is still connected
        if PI:
            if joystick_cnt >= 45:
                # print("CHECK FOR JOYSTICK")
                joystick = check_joystick()
                joystick_cnt = 0
            else:
                joystick_cnt += 1

        pygame.event.pump()
        for event in pygame.event.get():

            # Translate event to "action" string based on Controller / Keyboard
            action = get_action(event)

            if action == 'DOWN':
                joystick_cnt = - 50
                menu_selected = (menu_selected + 1) % 3
            elif action == 'UP':
                joystick_cnt = - 50
                menu_selected = (menu_selected - 1) % 3
            elif action == 'START':
                if menu_selected == 0:
                    print("Starting Tetris")
                    runTetrisGame()
                    joystick = check_joystick()
                    transition('circle', 26, 0.6, True)
                    transition('menu', 5, 0.05)
                if menu_selected == 1:
                    print("Starting Snake")
                    runSnakeGame()
                    joystick = check_joystick()
                    transition('circle', 26, 0.6, True)
                    transition('menu', 5, 0.05)
                if menu_selected == 2:
                    transition('menu', 5, 0.05, True)
                    print("Starting Clock")
                    drawClock(0)
                    joystick = check_joystick()

                # Remove any scores left over after a game
                matrix_clear()

            elif action == 'SELECT':
                shutdownScreen()
                matrix_clear()

            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present
        time.sleep(.1)

    terminate()


def drawClock(color):
    joystick_cnt = 0

    if PI:
        DEVICE.clear()
        DEVICE.show()

    hour = time.localtime().tm_hour
    minute = time.localtime().tm_min
    second = time.localtime().tm_sec

    while True:

        pygame.event.pump()
        for event in pygame.event.get():  # User did something
            action = get_action(event)
            if action == 'START':
                # print("exiting clock")
                clearScreen()
                updateScreen()
                transition('circle', 26, 0.6)
                transition('menu', 5, 0.05)
                return
            if action in ['A', 'B', 'X', 'Y']:
                color = color + 1
                if (color > (len(COLORS) - 1)):
                    color = 0

            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present

        # check if joystick is still connected
        if PI:
            if joystick_cnt == 15:
                joystick_cnt = 0
                joystick = check_joystick()
            else:
                joystick_cnt += 1

        ltime = time.localtime()
        hour = ltime.tm_hour
        minute = ltime.tm_min
        second = ltime.tm_sec
        clearScreen()

        drawnumber(int(hour/10), 2, 1, color)
        drawnumber(int(hour % 10), 6, 1, color)
        drawnumber(int(minute/10), 2, 8, color)
        drawnumber(int(minute % 10), 6, 8, color)
        drawnumber(int(second/10), 2, 15, color)
        drawnumber(int(second % 10), 6, 15, color)

        updateScreen()
        time.sleep(.2)


def shutdownScreen():

    if PI:
        DEVICE.clear()
        DEVICE.show()
        drawImage(f'{RES_DIR}/shutdown.bmp')
        updateScreen()
    else:
        drawImage(f'{RES_DIR}/shutdown.bmp')
        updateScreen()

    matrix_image("select_to")
    counter = 0
    while True:

        # Blinking "PAUSE"
        if counter == 8:
            matrix_image("shutdown")
        if counter == 16:
            matrix_image("select_to")
            counter = 0

        pygame.event.pump()
        for event in pygame.event.get():  # User did something

            action = get_action(event)
            if action == 'START':
                clearScreen()
                updateScreen()
                return
            elif action == 'SELECT':
                if not PI:
                    terminate()
                else:
                    clearScreen()
                    updateScreen()
                    matrix_image("shutdown")
                    subprocess.Popen(['shutdown', '-h', 'now'])
                    # call("sudo nohup shutdown -h now", shell=True)
                    terminate()

            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present

        updateScreen()
        counter += 1
        time.sleep(.2)


def transition(name, image_count, animation_time, reverse=False):

    print(f"ANIMATION: {name}")

    if animation_time <= 0:
        sleep_time = 0.02
    else:
        sleep_time = animation_time / image_count
    for i in range(0, image_count - 1):
        if reverse:
            drawImage(f'{RES_DIR}/animations/{name}/{image_count-1-i}.bmp')
        else:
            drawImage(f'{RES_DIR}/animations/{name}/{i}.bmp')
        updateScreen()
        time.sleep(sleep_time)


def drawImage(filename):
    im = Image.open(filename)
    for row in range(0, BOARDHEIGHT):
        for col in range(0, BOARDWIDTH):
            r, g, b = im.getpixel((col, row))
            drawPixelRgb(col, row, r, g, b)


def drawHalfImage(filename, offset):
    im = Image.open(filename)
    if offset > 10:
        offset = 10
    for row in range(0, 10):
        for col in range(0, 10):
            r, g, b = im.getpixel((col, row))
            drawPixelRgb(col, row+offset, r, g, b)

# drawing #


def matrix_text(text, offset=(0, 0)):
    with canvas(DEVICE) as draw:
        draw.text(offset, text, font=PIXELFONT, fill="white")


def matrix_image(image):
    bitmap = Image.open(f"{RES_DIR}/dotmatrix/{image}.bmp")
    with canvas(DEVICE)as draw:
        draw.bitmap((0, 0), bitmap, fill='white')


def matrix_clear():
    with canvas(DEVICE) as draw:
        draw.rectangle((0, 0, 32, 8))


def clearScreen():
    if PI:
        PIXELS.fill((0, 0, 0))
    else:
        DISPLAYSURF.fill(BGCOLOR)


def updateScreen():
    if PI:
        PIXELS.show()
    else:
        pygame.display.update()


def drawPixel(x, y, color):
    if color == BLANK:
        return
    if PI:
        try:
            if (x >= 0 and y >= 0 and color >= 0):
                if x % 2 == 1:
                    PIXELS[x*PIXEL_Y+y] = COLORS[color]
                else:
                    PIXELS[x*PIXEL_Y+(PIXEL_Y-1-y)] = COLORS[color]
        except Exception as e:
            print(e)
            print(str(x) + ' --- ' + str(y))
    else:
        pygame.draw.rect(
            DISPLAYSURF, COLORS[color], (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))


def drawDarkPixel(x, y, color):

    if color == BLANK:
        return

    darkcolor = COLORS[color]
    darkcolor = [int(darkcolor[0] * 0.1), int(darkcolor[1]
                                              * 0.1), int(darkcolor[2] * 0.1)]
    if PI:
        try:
            if (x >= 0 and y >= 0 and color >= 0):
                if x % 2 == 1:
                    PIXELS[x*PIXEL_Y+y] = darkcolor
                else:
                    PIXELS[x*PIXEL_Y+(PIXEL_Y-1-y)] = darkcolor
        except:
            print(str(x) + ' --- ' + str(y))
    else:
        pygame.draw.rect(
            DISPLAYSURF, darkcolor, (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))


def drawPixelRgb(x, y, r, g, b):
    if PI:
        if (x >= 0 and y >= 0):
            if x % 2 == 1:
                PIXELS[x*PIXEL_Y+y] = (r, g, b)
            else:
                PIXELS[x*PIXEL_Y+(PIXEL_Y-1-y)] = (r, g, b)
    else:
        pygame.draw.rect(DISPLAYSURF, (r, g, b),
                         (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))


def drawnumber(number, offsetx, offsety, color):
    for x in range(0, 3):
        for y in range(0, 5):
            if clock_font[3*number + x] & mask[y]:
                drawPixel(offsetx+x, offsety+y, color)


def draw_bin_number_main_menu(bin_number, offsetx, offsety, color):
    for x in range(0, 2):
        for y in range(0, 4):
            if bin_number[x][y] == 1:
                drawPixel(offsetx+x, offsety+y, color)


def drawnumberMAX7219(number, offsetx, offsety, draw1):
    for x in range(0, 3):
        for y in range(0, 5):
            if clock_font[3*number+2 - x] & mask[y]:
                drawScorePixel(offsetx+x, offsety+y, 1, draw1)
            elif clock_font[3*number+2 - x] & mask[y]:
                drawScorePixel(offsetx+x, offsety+y, 0, draw1)


def drawTetrisMAX7219(piece, offsetx, offsety, draw1):
    for x in range(0, 4):
        for y in range(0, 8):
            if theTetrisFont[4*piece + x] & mask[y]:
                drawScorePixel(offsetx+x, offsety+y, 1, draw1)
            elif theTetrisFont[4*piece + x] & mask[y]:
                drawScorePixel(offsetx+x, offsety+y, 0, draw1)


def drawScorePixel(x, y, on, draw):
    if PI:
        draw.point((31-x, y), fill="white")
        # time.sleep(.01)
    else:
        pygame.draw.rect(DISPLAYSURF, COLORS[2], (64-2*x, 410+2*y, 2, 2))


def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()


def scroll_text(text):
    if PI:
        show_message(DEVICE, text, fill="white", font=proportional(CP437_FONT))
    else:
        titleSurf, titleRect = makeTextObjs(str(text), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3,
                            int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)


def scoreText(score):
    _score = score
    if _score > 999:
        _score = 999
    if PI:
        with canvas(DEVICE) as draw:
            for i in range(0, 3):
                text(draw, ((3-i)*8, 0), str(_score % 10), fill="white")
                _score //= 10
    else:
        titleSurf, titleRect = makeTextObjs(str(_score), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3,
                            int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

# program flow #


def get_action(event):
    if event.type == pygame.JOYBUTTONDOWN and event.button in CONTROLLER:
        return CONTROLLER[event.button]
    elif event.type == pygame.KEYDOWN and event.scancode in CONTROLLER:
        return CONTROLLER[event.scancode]
    else:
        return ""


def check_joystick():
    pygame.joystick.quit()
    pygame.joystick.init()
    try:
        # create a joystick instance
        joystick = pygame.joystick.Joystick(0)
        joystick.init()  # init instance
        # print("Initialized joystick: {}".format(joystick.get_name()))
        return joystick
    except pygame.error:
        print("no joystick found.")
        return None


def terminate():
    RUNNING = False
    pygame.quit()
    exit()


def checkForQuit():
    for event in pygame.event.get(pygame.QUIT):  # get all the QUIT events
        terminate()  # terminate if any QUIT events are present
    for event in pygame.event.get(pygame.KEYUP):  # get all the KEYUP events
        if event.key == pygame.K_ESCAPE:
            terminate()  # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event)  # put the other KEYUP event objects back


if __name__ == '__main__':
    main()
