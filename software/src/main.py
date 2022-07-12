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
from PIL import Image

from . import PI, INSTALL_DIR, RES_DIR
from .tetris import runTetrisGame
from .snake import runSnakeGame

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
LED_BRIGHTNESS = 0.6


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


BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS = (BLUE, GREEN, RED, YELLOW, CYAN, MAGENTA, ORANGE)
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

CONTROLLER = {
    'JKEY_X': 3,
    'JKEY_Y': 2,
    'JKEY_A': 1,
    'JKEY_B': 0,
    'JKEY_R': 10,
    'JKEY_L': 9,
    'JKEY_SEL': 4,
    'JKEY_START': 6,
}

mykeys = {
    pygame.K_1: CONTROLLER['JKEY_A'],
    pygame.K_2: CONTROLLER['JKEY_B'],
    pygame.K_3: CONTROLLER['JKEY_Y'],
    pygame.K_4: CONTROLLER['JKEY_X'],
    pygame.K_x: CONTROLLER['JKEY_SEL'],
    pygame.K_s: CONTROLLER['JKEY_START'],
}

mask = bytearray([1, 2, 4, 8, 16, 32, 64, 128])


def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT
    global a1_counter, RUNNING
    a1_counter = 0
    RUNNING = True
    joystick_detected = False
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
        time.sleep(2)
    else:
        DEVICE.contrast(200)
        pygame.init()
        drawImage(f'{RES_DIR}/pi.bmp')
        pygame.joystick.init()
        while not joystick_detected:
            # scroll_text("Waiting for controller...")
            pygame.joystick.quit()
            pygame.joystick.init()
            try:
                joystick = pygame.joystick.Joystick(
                    0)  # create a joystick instance
                joystick.init()  # init instance
                # print("Initialized joystick: {}".format(joystick.get_name()))
                joystick_detected = True
            except pygame.error:
                print("no joystick found.")
                joystick_detected = False

    clearScreen()

    drawClock(1)
    if PI:
        scroll_text("Let's play")

    menu_selected = 0
    while True:
        # select one of the three menu entries (Tetris, Snake, Clock)
        clearScreen()
        # drawSymbols()
        drawImage(f'{RES_DIR}/menu{menu_selected}.bmp')
        updateScreen()
        if not PI:
            checkForQuit()

        # check if joystick is still connected
        if PI:
            if joystick_cnt == 50:
                joystick_cnt = 0
                pygame.joystick.quit()
                pygame.joystick.init()
                try:
                    # create a joystick instance
                    joystick = pygame.joystick.Joystick(0)
                    joystick.init()  # init instance
                    # print("Initialized joystick: {}".format(joystick.get_name()))
                    joystick_detected = True
                except pygame.error:
                    print("no joystick found.")
                    joystick_detected = False
            else:
                joystick_cnt += 1

        pygame.event.pump()
        for event in pygame.event.get():
            # print("event detected {}".format(event))
            if event.type == pygame.JOYBUTTONDOWN:
                print(event.button)
                print(pygame.CONTROLLER_BUTTON_DPAD_DOWN)
                if (event.button == pygame.CONTROLLER_BUTTON_DPAD_DOWN):
                    menu_selected = (menu_selected + 1) % 3
                if (event.button == pygame.CONTROLLER_BUTTON_DPAD_UP):
                    menu_selected = (menu_selected - 1) % 3
                if (event.button == pygame.CONTROLLER_BUTTON_START):
                    if menu_selected == 0:
                        runTetrisGame()
                    if menu_selected == 1:
                        runSnakeGame()
                    if menu_selected == 2:
                        drawClock(0)
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
            # print("event detected {}".format(event))
            # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                # print("Joystick button pressed: {}".format(event.button))
                if (myevent == CONTROLLER['JKEY_START']):
                    # print("exiting clock")
                    clearScreen()
                    updateScreen()
                    return
                if (myevent == CONTROLLER['JKEY_A']
                        or myevent == CONTROLLER['JKEY_B']
                        or myevent == CONTROLLER['JKEY_X']
                        or myevent == CONTROLLER['JKEY_Y']):
                    color = color + 1
                    if (color > (len(COLORS) - 1)):
                        color = 0

            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present

        # check if joystick is still connected
        if PI:
            if joystick_cnt == 25:
                joystick_cnt = 0
                pygame.joystick.quit()
                pygame.joystick.init()
                try:
                    joystick = pygame.joystick.Joystick(
                        0)  # create a joystick instance
                    joystick.init()  # init instance
                    # print("Initialized joystick: {}".format(joystick.get_name()))
                    # joystick_detected = True
                except pygame.error:
                    print("no joystick found.")
                    # joystick_detected = False
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
        scroll_text("Press Select to shutdown!")
    else:
        drawImage(f'{RES_DIR}/shutdown.bmp')

    while True:

        pygame.event.pump()
        for event in pygame.event.get():  # User did something
            # print("event detected {}".format(event))
            # Possible joystick actions:
            # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                # print("Joystick button pressed: {}".format(event.button))
                if (myevent != CONTROLLER['JKEY_SEL']):
                    # print("exiting clock")
                    clearScreen()
                    updateScreen()
                    return
                else:
                    if not PI:
                        terminate()
                    else:
                        clearScreen()
                        updateScreen()
                        scroll_text("Shutdown...")
                        subprocess.Popen(['shutdown', '-h', 'now'])
                        # call("sudo nohup shutdown -h now", shell=True)
                        terminate()
            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present

        updateScreen()
        time.sleep(.2)


def drawImage(filename):
    im = Image.open(filename)
    for row in range(0, BOARDHEIGHT):
        for col in range(0, BOARDWIDTH):
            r, g, b = im.getpixel((col, row))
            drawPixelRgb(col, row, r, g, b)
    updateScreen()


def drawHalfImage(filename, offset):
    im = Image.open(filename)
    if offset > 10:
        offset = 10
    for row in range(0, 10):
        for col in range(0, 10):
            r, g, b = im.getpixel((col, row))
            drawPixelRgb(col, row+offset, r, g, b)

# drawing #


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
        except:
            print(str(x) + ' --- ' + str(y))
    else:
        pygame.draw.rect(
            DISPLAYSURF, COLORS[color], (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))


def drawDarkPixel(x, y, color):

    if color == BLANK:
        return

    darkcolor = COLORS[color]
    print(darkcolor)
    darkcolor = [int(darkcolor[0] * 0.1), int(darkcolor[1]
                                               * 0.1), int(darkcolor[2] * 0.1)]
    print(darkcolor)
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
