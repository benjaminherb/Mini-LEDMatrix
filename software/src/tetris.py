import os
import time
import pickle
import pygame

import main
from templates_tetris import PIECES
from . import INSTALL_DIR, PI

PIECES_ORDER = {'S': 0, 'Z': 1, 'I': 2, 'J': 3, 'L': 4, 'O': 5, 'T': 6}


def runTetrisGame():
    # setup varia
    # bles for the start of the game
    # if PI:
    # device.contrast(255)
    # device.show()
    board = getBlankBoard()
    lastMoveDownTime = time.time()
    lastMoveSidewaysTime = time.time()
    lastFallTime = time.time()
    movingDown = False  # note: there is no movingUp variable
    movingLeft = False
    movingRight = False
    score = 0
    oldscore = -1
    oldpiece = 10
    lines = 0
    level, fallFreq = calculateLevelAndFallFreq(lines)
    if os.path.isfile(f'{INSTALL_DIR}/hs_tetris.p'):
        try:
            highscore = pickle.load(open(f"{INSTALL_DIR}/hs_tetris.p", "rb"))
        except EOFError:
            highscore = 0
    else:
        highscore = 0
    if PI:
        main.show_message(device, "Tetris Highscore: " + str(highscore),
                     fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)

    fallingPiece = getNewPiece()
    nextPiece = getNewPiece()

    while True:  # game loop

        if fallingPiece == None:
            # No falling piece in play, so start a new piece at the top
            fallingPiece = nextPiece
            nextPiece = getNewPiece()
            lastFallTime = time.time()  # reset lastFallTime

            if not isValidPosition(board, fallingPiece):
                time.sleep(2)
                if score > highscore:
                    highscore = score
                    if PI:
                        pickle.dump(highscore, open(
                            f"{INSTALL_DIR}/hs_tetris.p", "wb"))
                        main.show_message(device, "New Highscore !!!", fill="white", font=proportional(
                            CP437_FONT), scroll_delay=0.01)

                return  # can't fit a new piece on the board, so game over
        if not PI:
            main.checkForQuit()

        pygame.event.pump()
        for event in pygame.event.get():
            # print("event detected {}".format(event))
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                val = round(event.value)
                if (axis == 0 and val == 0):
                    # no motion or down motion
                    movingLeft = movingRight = False

                if (axis == 1 and val == 0):
                    movingDown = False

                if (axis == 0 and val == -1) and isValidPosition(board, fallingPiece, adjX=-1):
                    fallingPiece['x'] -= 1
                    movingLeft = True
                    movingRight = False
                    lastMoveSidewaysTime = time.time()

                if (axis == 0 and val == 1) and isValidPosition(board, fallingPiece, adjX=1):
                    fallingPiece['x'] += 1
                    movingLeft = False
                    movingRight = True
                    lastMoveSidewaysTime = time.time()

                if (axis == 1 and val == 1):
                    movingDown = True
                    if isValidPosition(board, fallingPiece, adjY=1):
                        fallingPiece['y'] += 1
                    lastMoveDownTime = time.time()

                if (axis == 1 and val == -1):
                    fallingPiece['rotation'] = (
                        fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (
                            fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])

            if event.type == pygame.KEYDOWN:

                if (event.key == K_LEFT) and isValidPosition(board, fallingPiece, adjX=-1):
                    fallingPiece['x'] -= 1
                    movingLeft = True
                    movingRight = False
                    lastMoveSidewaysTime = time.time()

                if (event.key == K_RIGHT) and isValidPosition(board, fallingPiece, adjX=1):
                    fallingPiece['x'] += 1
                    movingLeft = False
                    movingRight = True
                    lastMoveSidewaysTime = time.time()

                if (event.key == K_DOWN):
                    movingDown = True
                    if isValidPosition(board, fallingPiece, adjY=1):
                        fallingPiece['y'] += 1
                    lastMoveDownTime = time.time()

                if (event.key == K_4):
                    fallingPiece['rotation'] = (
                        fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (
                            fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])

                if (event.key == K_3):
                    fallingPiece['rotation'] = (
                        fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (
                            fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])

                if (event.key == K_UP):
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    score += i  # TODO: more digits on numbercounter, more scores
                    fallingPiece['y'] += i - 1

            if event.type == pygame.KEYUP:
                movingDown = False
                movingLeft = False
                movingRight = False

            if event.type == pygame.JOYBUTTONDOWN:
                # print("Joystick button pressed: {}".format(event.button))
                if (event.button == JKEY_A):
                    fallingPiece['rotation'] = (
                        fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (
                            fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                if (event.button == JKEY_Y):
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    score += i  # TODO: more digits on numbercounter, more scores
                    fallingPiece['y'] += i - 1

                #  return

        # handle moving the piece because of user input
        if (movingLeft or movingRight) and time.time() - lastMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if movingLeft and isValidPosition(board, fallingPiece, adjX=-1):
                fallingPiece['x'] -= 1
            elif movingRight and isValidPosition(board, fallingPiece, adjX=1):
                fallingPiece['x'] += 1
            lastMoveSidewaysTime = time.time()

        if movingDown and time.time() - lastMoveDownTime > MOVEDOWNFREQ and isValidPosition(board, fallingPiece, adjY=1):
            fallingPiece['y'] += 1
            lastMoveDownTime = time.time()

        # let the piece fall if it is time to fall
        if time.time() - lastFallTime > fallFreq:
            # see if the piece has landed
            if not isValidPosition(board, fallingPiece, adjY=1):
                # falling piece has landed, set it on the board
                addToBoard(board, fallingPiece)
                remLine = removeCompleteLines(board)
                # count lines for level calculation
                lines += remLine
                # more lines, more points per line
                score += SCORES[remLine]*level
                level, fallFreq = calculateLevelAndFallFreq(lines)
                fallingPiece = None
            else:
                # piece did not land, just move the piece down
                fallingPiece['y'] += 1
                lastFallTime = time.time()

        # drawing everything on the screen
        main.clearScreen()
        drawBoard(board)
        # scoreText(score)
        if score > oldscore:
            scoreTetris(score, level, PIECES_ORDER.get(nextPiece['shape']))
            oldscore = score
        if oldpiece != PIECES_ORDER.get(nextPiece['shape']):
            scoreTetris(score, level, PIECES_ORDER.get(nextPiece['shape']))
            oldpiece = PIECES_ORDER.get(nextPiece['shape'])
        # drawStatus(score, level)
        # drawNextPiece(nextPiece)
        if fallingPiece != None:
            drawPiece(fallingPiece)

        main.updateScreen()
        # FPSCLOCK.tick(FPS)
        time.sleep(.05)

# tetris subroutines #


def calculateLevelAndFallFreq(lines):
    # Based on the score, return the level the player is on and
    # how many seconds pass until a falling piece falls one space.
    level = int(lines / 10) + 1
    # limit level to 10
    if level > 10:
        level = 10
    fallFreq = FALLING_SPEED - (level * 0.05)
    if fallFreq <= 0.05:
        fallFreq = 0.05
    return level, fallFreq


def getNewPiece():
    # return a random new piece in a random rotation and color
    shape = random.choice(list(PIECES.keys()))
    newPiece = {'shape': shape,
                'rotation': random.randint(0, len(PIECES[shape]) - 1),
                'x': int(BOARDWIDTH / 2) - int(TEMPLATEWIDTH / 2),
                'y': -2,  # start it above the board (i.e. less than 0)
                'color': PIECES_ORDER.get(shape)}
    return newPiece


def addToBoard(board, piece):
    # fill in the board based on piece's location, shape, and rotation
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if PIECES[piece['shape']][piece['rotation']][y][x] != BLANK:
                board[x + piece['x']][y + piece['y']] = piece['color']


def isOnBoard(x, y):
    return x >= 0 and x < BOARDWIDTH and y < BOARDHEIGHT


def isValidPosition(board, piece, adjX=0, adjY=0):
    # Return True if the piece is within the board and not colliding
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            isAboveBoard = y + piece['y'] + adjY < 0
            if isAboveBoard or PIECES[piece['shape']][piece['rotation']][y][x] == BLANK:
                continue
            if not isOnBoard(x + piece['x'] + adjX, y + piece['y'] + adjY):
                return False
            if board[x + piece['x'] + adjX][y + piece['y'] + adjY] != BLANK:
                return False
    return True


def isCompleteLine(board, y):
    # Return True if the line filled with boxes with no gaps.
    for x in range(BOARDWIDTH):
        if board[x][y] == BLANK:
            return False
    return True


def removeCompleteLines(board):
    # Remove any completed lines on the board, move everything above them down, and return the number of complete lines.
    numLinesRemoved = 0
    y = BOARDHEIGHT - 1  # start y at the bottom of the board
    while y >= 0:
        if isCompleteLine(board, y):
            # Remove the line and pull boxes down by one line.
            for pullDownY in range(y, 0, -1):
                for x in range(BOARDWIDTH):
                    board[x][pullDownY] = board[x][pullDownY-1]
            # Set very top line to blank.
            for x in range(BOARDWIDTH):
                board[x][0] = BLANK
            numLinesRemoved += 1
            # Note on the next iteration of the loop, y is the same.
            # This is so that if the line that was pulled down is also
            # complete, it will be removed.
        else:
            y -= 1  # move on to check next row up
    return numLinesRemoved


def drawBoard(matrix):
    for i in range(0, BOARDWIDTH):
        for j in range(0, BOARDHEIGHT):
            drawPixel(i, j, matrix[i][j])


def getBlankBoard():
    # create and return a new blank board data structure
    board = []
    for i in range(BOARDWIDTH):
        board.append([BLANK] * BOARDHEIGHT)
    return board


def drawPiece(piece, pixelx=None, pixely=None):
    shapeToDraw = PIECES[piece['shape']][piece['rotation']]
    if pixelx == None and pixely == None:
        # if pixelx & pixely hasn't been specified, use the location stored in the piece data structure
        pixelx = piece['x']
        pixely = piece['y']

    # draw each of the boxes that make up the piece
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if shapeToDraw[y][x] != BLANK:
                drawPixel(pixelx + x, pixely+y, piece['color'])

def scoreTetris(score, level, nextpiece):
    # if PI:
    # device.clear()
    _score = score
    if _score > 999999:
        _score = 999999

    if PI:
        # one point per level
        with canvas(device) as draw1:
            for i in range(0, level):
                drawScorePixel(i*2, 7, 1, draw1)

            # score as 6 digit value
            for i in range(0, 6):
                drawnumberMAX7219(_score % 10, i*4, 0, draw1)
                _score //= 10

            # draw next piece
            drawTetrisMAX7219(nextpiece, 27, 0, draw1)

            if PI:
                device.show()
