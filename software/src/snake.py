import random
import pickle
import os
import time
import pygame

from . import main
from . import PI, INSTALL_DIR

# snake constants #
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0  # syntactic sugar: index of the worm's head


# gaming main routines #
def runSnakeGame():

    # Set a random start point.
    startx = random.randint(2, main.BOARDWIDTH - 2)
    starty = random.randint(2, main.BOARDHEIGHT - 2)
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
        main.scroll_text(f"Snake Highscore: {str(highscore)}")

    # Start the apple in a random place.
    apple = getRandomLocation(wormCoords)

    while True:  # main game loop
        olddirection = direction
        pygame.event.pump()
        for event in pygame.event.get():
            action = main.get_action(event)
            if (olddirection == direction):   # only one direction change per step
                if action == 'LEFT':
                    if direction != RIGHT:
                        direction = LEFT
                if action == 'RIGHT':
                    if direction != LEFT:
                        direction = RIGHT
                if action == 'DOWN':
                    if direction != UP:
                        direction = DOWN
                if action == 'UP':
                    if direction != DOWN:
                        direction = UP
                if action == 'START':
                    exit_game = pause_game()
                    if exit_game:
                        return

        # check if the worm has hit itself or the edge
        if (wormCoords[HEAD]['x'] == -1
                or wormCoords[HEAD]['x'] == main.BOARDWIDTH
                or wormCoords[HEAD]['y'] == -1
                or wormCoords[HEAD]['y'] == main.BOARDHEIGHT):
            time.sleep(1.5)
            if score > highscore:
                highscore = score
                if PI:
                    pickle.dump(highscore, open(
                        f"{INSTALL_DIR}/hs_snake.p", "wb"))
                    main.scroll_text("New Highscore !!!")
            return  # game over
        for wormBody in wormCoords[1:]:
            if wormBody['x'] == wormCoords[HEAD]['x'] and wormBody['y'] == wormCoords[HEAD]['y']:
                time.sleep(1.5)
                if score > highscore:
                    highscore = score
                    if PI:
                        pickle.dump(highscore, open(
                            f"{INSTALL_DIR}/hs_snake.p", "wb"))
                        main.scroll_text("New Highscore !!!")
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
                newHead = {'x': wormCoords[HEAD]['x'], 'y': main.BOARDHEIGHT-1}
            else:
                newHead = {'x': wormCoords[HEAD]['x'],
                           'y': wormCoords[HEAD]['y'] - 1}
        elif direction == DOWN:
            if wormCoords[HEAD]['y'] == main.BOARDHEIGHT-1:
                newHead = {'x': wormCoords[HEAD]['x'], 'y': 0}
            else:
                newHead = {'x': wormCoords[HEAD]['x'],
                           'y': wormCoords[HEAD]['y'] + 1}
        elif direction == LEFT:
            if wormCoords[HEAD]['x'] == 0:
                newHead = {'x': main.BOARDWIDTH -
                           1, 'y': wormCoords[HEAD]['y']}
            else:
                newHead = {'x': wormCoords[HEAD]
                           ['x'] - 1, 'y': wormCoords[HEAD]['y']}
        elif direction == RIGHT:
            if wormCoords[HEAD]['x'] == main.BOARDWIDTH-1:
                newHead = {'x': 0, 'y': wormCoords[HEAD]['y']}
            else:
                newHead = {'x': wormCoords[HEAD]
                           ['x'] + 1, 'y': wormCoords[HEAD]['y']}
        if not PI:
            main.checkForQuit()
        wormCoords.insert(0, newHead)
        main.clearScreen()
        drawWorm(wormCoords)
        drawApple(apple)
        main.scoreText(score)
        main.updateScreen()
        time.sleep(.15)


# snake subroutines #

def getRandomLocation(wormCoords):
    while True:
        x = random.randint(0, main.BOARDWIDTH - 1)
        y = random.randint(0, main.BOARDHEIGHT - 1)
        if {'x': x, 'y': y} in wormCoords:
            print('no apples on worm')
        else:
            break
    return {'x': x, 'y': y}


def drawWorm(wormCoords):
    for coord in wormCoords:
        x = coord['x']
        y = coord['y']
        main.drawPixel(x, y, 1)


def drawApple(coord):
    x = coord['x']
    y = coord['y']
    main.drawPixel(x, y, 2)


def pause_game():
    main.scroll_text("PAUSE")
    while True:
        pygame.event.pump()
        for event in pygame.event.get():
            action = main.get_action(event)
            # Keep Playing
            if action == 'START':
                return False
            # End Game
            elif action == 'SELECT':
                return True
