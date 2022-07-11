# WS2812 LED Matrix Gamecontrol (Tetris, Snake, Pong)
# by M Oehler
# https://hackaday.io/project/11064-raspberry-pi-retro-gaming-led-display
# ported from
# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import pygame
import random
import time
import os
import pickle
import subprocess
from PIL import Image

from . import PI, INSTALL_DIR, RES_DIR
from .tetris import runTetrisGame

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
LIGHTRED = (175,  20,  20)
GREEN = (0, 255,   0)
LIGHTGREEN = (20, 175,  20)
BLUE = (0,   0, 255)
LIGHTBLUE = (20,  20, 175)
YELLOW = (255, 255,   0)
LIGHTYELLOW = (175, 175,  20)
CYAN = (0, 255, 255)
MAGENTA = (255,   0, 255)
ORANGE = (255, 100,   0)


BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS = (BLUE, GREEN, RED, YELLOW, CYAN, MAGENTA, ORANGE)
LIGHTCOLORS = (LIGHTBLUE, LIGHTGREEN, LIGHTRED, LIGHTYELLOW)
# assert len(COLORS) == len(LIGHTCOLORS) # each color must have light color


# snake constants #
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0  # syntactic sugar: index of the worm's head

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
            scroll_text("Waiting for controller...")
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

    while True:
        clearScreen()
        # drawSymbols()
        drawImage(f'{RES_DIR}/select.bmp')
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
                    joystick = pygame.joystick.Joystick(
                        0)  # create a joystick instance
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
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                if (myevent == CONTROLLER['JKEY_B']):
                    drawClock(1)
                if (myevent == CONTROLLER['JKEY_A']):
                    runPongGame()
                if (myevent == CONTROLLER['JKEY_X']):
                    runTetrisGame()
                if (myevent == CONTROLLER['JKEY_Y']):
                    runSnakeGame()
                if (myevent == CONTROLLER['JKEY_SEL']):
                    shutdownScreen()

            if event.type == pygame.QUIT:  # get all the QUIT events
                terminate()  # terminate if any QUIT events are present

        time.sleep(.1)

    terminate()


# gaming main routines #
def runSnakeGame():

    # Set a random start point.
    startx = random.randint(2, BOARDWIDTH - 2)
    starty = random.randint(2, BOARDHEIGHT - 2)
    wormCoords = [{'x': startx,     'y': starty},
                  {'x': startx - 1, 'y': starty},
                  {'x': startx - 2, 'y': starty}]
    direction = RIGHT
    score = 0

    if os.path.isfile(f'{INSTALL_DIR}/hs_snake.p'):
        try:
            highscore = pickle.load(open(f"{INSTALL_DIR}/hs_snake.p", "rb"))
        except EOFError:
            highscore = 0
    else:
        highscore = 0
    if PI:
        scroll_text(f"Snake Highscore: {str(highscore)}")

    # Start the apple in a random place.
    apple = getRandomLocation(wormCoords)

    while True:  # main game loop
        olddirection = direction
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                if (olddirection == direction):   # only one direction change per step
                    axis = event.axis
                    val = round(event.value)
                    if (axis == 0 and val == -1):
                        if direction != RIGHT:
                            direction = LEFT
                    if (axis == 0 and val == 1):
                        if direction != LEFT:
                            direction = RIGHT
                    if (axis == 1 and val == 1):
                        if direction != UP:
                            direction = DOWN
                    if (axis == 1 and val == -1):
                        if direction != DOWN:
                            direction = UP

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_LEFT):
                    if direction != RIGHT:
                        direction = LEFT
                if (event.key == pygame.K_RIGHT):
                    if direction != LEFT:
                        direction = RIGHT
                if (event.key == pygame.K_DOWN):
                    if direction != UP:
                        direction = DOWN
                if (event.key == pygame.K_UP):
                    if direction != DOWN:
                        direction = UP
                if (event.key == CONTROLLER['JKEY_SEL']):
                    # quit game
                    return

            if event.type == pygame.JOYBUTTONDOWN:
                if (event.button == CONTROLLER['JKEY_SEL']):
                    # quit game
                    return

        # check if the worm has hit itself or the edge
        if (wormCoords[HEAD]['x'] == -1
                or wormCoords[HEAD]['x'] == BOARDWIDTH
                or wormCoords[HEAD]['y'] == -1
                or wormCoords[HEAD]['y'] == BOARDHEIGHT):
            time.sleep(1.5)
            if score > highscore:
                highscore = score
                if PI:
                    pickle.dump(highscore, open(
                        f"{INSTALL_DIR}/hs_snake.p", "wb"))
                    scroll_text("New Highscore !!!")
            return  # game over
        for wormBody in wormCoords[1:]:
            if wormBody['x'] == wormCoords[HEAD]['x'] and wormBody['y'] == wormCoords[HEAD]['y']:
                time.sleep(1.5)
                if score > highscore:
                    highscore = score
                    if PI:
                        pickle.dump(highscore, open(
                            f"{INSTALL_DIR}/hs_snake.p", "wb"))
                        scroll_text("New Highscore !!!")
                return  # game over

        # check if worm has eaten an apple
        if wormCoords[HEAD]['x'] == apple['x'] and wormCoords[HEAD]['y'] == apple['y']:
            # don't remove worm's tail segment
            score += 1
            apple = getRandomLocation(wormCoords)  # set a new apple somewhere
        else:
            del wormCoords[-1]  # remove worm's tail segment

        # move the worm by adding a segment in the direction it is moving
        if direction == UP:
            if wormCoords[HEAD]['y'] == 0:
                newHead = {'x': wormCoords[HEAD]['x'], 'y': BOARDHEIGHT-1}
            else:
                newHead = {'x': wormCoords[HEAD]['x'],
                           'y': wormCoords[HEAD]['y'] - 1}
        elif direction == DOWN:
            if wormCoords[HEAD]['y'] == BOARDHEIGHT-1:
                newHead = {'x': wormCoords[HEAD]['x'], 'y': 0}
            else:
                newHead = {'x': wormCoords[HEAD]['x'],
                           'y': wormCoords[HEAD]['y'] + 1}
        elif direction == LEFT:
            if wormCoords[HEAD]['x'] == 0:
                newHead = {'x': BOARDWIDTH - 1, 'y': wormCoords[HEAD]['y']}
            else:
                newHead = {'x': wormCoords[HEAD]
                           ['x'] - 1, 'y': wormCoords[HEAD]['y']}
        elif direction == RIGHT:
            if wormCoords[HEAD]['x'] == BOARDWIDTH-1:
                newHead = {'x': 0, 'y': wormCoords[HEAD]['y']}
            else:
                newHead = {'x': wormCoords[HEAD]
                           ['x'] + 1, 'y': wormCoords[HEAD]['y']}
        if not PI:
            checkForQuit()
        wormCoords.insert(0, newHead)
        clearScreen()
        drawWorm(wormCoords)
        drawApple(apple)
        scoreText(score)
        updateScreen()
        time.sleep(.15)


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


def twoscoreText(score1, score2):
    _score1 = score1
    _score2 = score2
    if _score1 > 9:
        _score1 = 9
    if _score2 > 9:
        _score2 = 9
    if PI:
        with canvas(DEVICE) as draw:
            text(draw, (0, 0), str(_score1), fill="white")
            text(draw, (8, 0), ":", fill="white")
            text(draw, (16, 0), str(_score2), fill="white")
            text(draw, (24, 0), " ", fill="white")
    else:
        titleSurf, titleRect = makeTextObjs(
            str(_score1)+':'+str(_score2), BASICFONT, TEXTCOLOR)
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


# snake subroutines #


def getRandomLocation(wormCoords):
    while True:
        x = random.randint(0, BOARDWIDTH - 1)
        y = random.randint(0, BOARDHEIGHT - 1)
        if {'x': x, 'y': y} in wormCoords:
            print('no apples on worm')
        else:
            break
    return {'x': x, 'y': y}


def drawWorm(wormCoords):
    for coord in wormCoords:
        x = coord['x']
        y = coord['y']
        drawPixel(x, y, 1)


def drawApple(coord):
    x = coord['x']
    y = coord['y']
    drawPixel(x, y, 2)


if __name__ == '__main__':
    main()
