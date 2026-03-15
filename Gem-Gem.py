"""A simple match-3 style gem-swapping game.

This script is a self-contained game that uses Pygame to draw colorful gems
on the screen. The player swaps gems to make matches of 3 or more identical
gems in a row or column. Matched gems disappear and new gems drop down from
above.

The game demonstrates several common game programming concepts, such as:
- A 2D grid-based board stored in a list of lists (board[x][y]).
- Event-based input handling (mouse clicks and key presses).
- Simple animation by redrawing frames at a fixed rate.
- Checking for matching patterns and applying game rules.

This version of the game has been heavily commented to help absolute beginners
understand what each part of the code does.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
# Import the modules we need for this game.
# Each import provides a set of useful tools.

import random  # for choosing random gem types and random sounds
import time    # for tracking time and making things happen at intervals
import pygame  # the game library used to draw graphics and play sounds
import sys     # for exiting the program cleanly
import copy    # to make deep copies of the board (so we can modify copies safely)
import os      # for file path operations (used in resource_path function)

# Import all useful constants from pygame.locals (such as QUIT, MOUSEBUTTONUP).
# This allows us to write QUIT instead of pygame.QUIT.
from pygame.locals import *

# ---------------------------------------------------------------------------
# Game constants (configuration values)
# ---------------------------------------------------------------------------
# Constants are values that are set once and do not change during the game.
# By convention, constants are written in ALL_CAPS.

# How many times per second we redraw the screen.
FPS = 30  # frames per second

# Size of the game window in pixels.
WINDOWWIDTH = 600  # width of the program's window in pixels
WINDOWHEIGHT = 600 # height of the program's window in pixels

# How many columns and rows are on the game board.
BOARDWIDTH = 8  # number of columns in the board
BOARDHEIGHT = 8 # number of rows in the board

# Each gem is displayed using a square image. This is the pixel size of each gem.
GEMIMAGESIZE = 64  # width & height of each gem image in pixels

# The number of different gem image files (gem1.png through gemN.png).
# If you want more gem types, drop more gem images into the folder and increase this.
NUMGEMIMAGES = 7
assert NUMGEMIMAGES >= 5  # game needs at least 5 types of gems to work

# The number of different match sound files (match0.wav through matchN.wav).
NUMMATCHSOUNDS = 6

# How quickly animated gem swaps move. 1 = slow, 100 = fast.
MOVERATE = 25  # higher means faster animation

# How often the player's score is reduced while playing.
# Every DEDUCTSPEED seconds, the score is reduced by 1 point.
DEDUCTSPEED = 0.8

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
# Colors in Pygame are represented as tuples of (red, green, blue)
# where each value is between 0 and 255.

PURPLE    = (255,   0, 255)
LIGHTBLUE = (170, 190, 255)
BLUE      = (  0,   0, 255)
RED       = (255, 100, 100)
BLACK     = (  0,   0,   0)
BROWN     = ( 85,  65,   0)

# Used for UI elements.
HIGHLIGHTCOLOR = PURPLE        # color for the border around the selected gem
BGCOLOR = LIGHTBLUE            # background color for the game window
GRIDCOLOR = BLUE               # color of the grid lines between gems
GAMEOVERCOLOR = RED            # color of the "Game over" text
GAMEOVERBGCOLOR = BLACK        # background color behind the "Game over" text
SCORECOLOR = BROWN             # color of the score text

# ---------------------------------------------------------------------------
# Derived constants (calculated from the above constants)
# ---------------------------------------------------------------------------
# The board is centered in the window. These margins determine how much
# space is on each side of the board.
XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * BOARDHEIGHT) / 2)

# ---------------------------------------------------------------------------
# Direction constants (used to animate gem movement)
# ---------------------------------------------------------------------------
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

# ---------------------------------------------------------------------------
# Special values stored in the board
# ---------------------------------------------------------------------------
# EMPTY_SPACE is used to represent a board space that has no gem.
EMPTY_SPACE = -1  # an arbitrary nonpositive value

# ROWABOVEBOARD is a special y-value used for gems that are just above the top
# of the board (before they drop into place).
ROWABOVEBOARD = 'row above board'  # an arbitrary, noninteger value


def resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    
    This function is used to find files like images, even when the game is packaged into an executable.
    When running as a script, it uses the current directory.
    When packaged with PyInstaller, it uses the temporary directory where files are extracted.
    
    Parameters:
    relative_path (str): The relative path to the resource file (e.g., 'image.png').
    
    Returns:
    str: The absolute path to the resource file.
    """
    
    # Try to get the path from PyInstaller's temporary directory.
    try:
        base_path = sys._MEIPASS
    
    # If not packaged, use the current working directory.
    except Exception:
        base_path = os.path.abspath(".")
    
    # Join the base path with the relative path to get the full path.
    return os.path.join(base_path, relative_path)


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main():
    """Initialize the game and start the main game loop.

    This function sets up Pygame, loads all assets (images and sounds),
    and then repeatedly starts games until the player quits.
    """

    # Declare global variables that we will use in many functions.
    # These variables are defined once here and then used in many places.
    global FPSCLOCK, DISPLAYSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS

    # Initialize all of Pygame. This must be called before using other Pygame
    # functions like creating surfaces or playing sounds.
    pygame.init()

    # Create a clock object to manage how fast the game updates.
    FPSCLOCK = pygame.time.Clock()

    # Create the main window where everything will be drawn.
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

    # Set the title that appears in the window's title bar.
    pygame.display.set_caption('Gem-Gem')

    # Load a font for rendering text on the screen.
    BASICFONT = pygame.font.Font('freesansbold.ttf', 36)

    # -----------------------------------------------------------------------
    # Load gem images
    # -----------------------------------------------------------------------
    # GEMIMAGES will be a list where each entry is a Pygame Surface for a gem.
    GEMIMAGES = []

    # Load each image file (gem1.png, gem2.png, ...).
    # The index in GEMIMAGES corresponds to the 'imageNum' stored in the gem data.
    for i in range(1, NUMGEMIMAGES + 1):
        gemImage = pygame.image.load(resource_path('gem%s.png' % i))

        # If the loaded image is not the size we expect, scale it to fit.
        if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
            gemImage = pygame.transform.smoothscale(gemImage, (GEMIMAGESIZE, GEMIMAGESIZE))

        GEMIMAGES.append(gemImage)

    # -----------------------------------------------------------------------
    # Load sounds
    # -----------------------------------------------------------------------
    # Store sounds in a dictionary so we can reference them by name.
    GAMESOUNDS = {}

    # Sound to play when a swap does not create a match.
    GAMESOUNDS['bad swap'] = pygame.mixer.Sound(resource_path('badswap.wav'))

    # There are multiple match sounds; play a random one when a match happens.
    GAMESOUNDS['match'] = []
    for i in range(NUMMATCHSOUNDS):
        GAMESOUNDS['match'].append(pygame.mixer.Sound(resource_path('match%s.wav' % i)))

    # -----------------------------------------------------------------------
    # Create a list of pygame.Rect objects for each board cell
    # -----------------------------------------------------------------------
    # BOARDRECTS[x][y] will be a pygame.Rect specifying where that cell is
    # located on the screen. This helps convert between board positions (x,y)
    # and pixel locations.
    BOARDRECTS = []

    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDHEIGHT):
            r = pygame.Rect(
                (XMARGIN + (x * GEMIMAGESIZE),
                 YMARGIN + (y * GEMIMAGESIZE),
                 GEMIMAGESIZE,
                 GEMIMAGESIZE)
            )
            BOARDRECTS[x].append(r)

    # -----------------------------------------------------------------------
    # Start the first game loop.
    # -----------------------------------------------------------------------
    while True:
        runGame()


# ---------------------------------------------------------------------------
# runGame()
# ---------------------------------------------------------------------------

def runGame():
    """Play through a single game until the player loses or exits.

    This function contains the main game loop that handles input,
    updates the board state, checks for matches, updates score, and draws
    everything to the screen.
    """

    # Create a new empty board and fill it with initial gems.
    gameBoard = getBlankBoard()
    score = 0

    # Fill the board with gems and animate them dropping into place.
    fillBoardAndAnimate(gameBoard, [], score)

    # Variables used to track player input and game state.
    firstSelectedGem = None      # The first gem that the player clicked
    lastMouseDownX = None        # Mouse x position at the start of click/drag
    lastMouseDownY = None        # Mouse y position at the start of click/drag
    gameIsOver = False           # Becomes True when no moves are left
    lastScoreDeduction = time.time()  # Track when the score was last reduced
    clickContinueTextSurf = None # Cache for the "click to continue" text surface

    # Main game loop (runs until we return)
    while True:
        clickedSpace = None

        # Handle all pending Pygame events (mouse, keyboard, etc.).
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                # User closed the window or pressed ESC: quit the program.
                pygame.quit()
                sys.exit()

            elif event.type == KEYUP and event.key == K_BACKSPACE:
                # Pressing Backspace restarts the game immediately.
                return  # return to main() which starts a new game

            elif event.type == MOUSEBUTTONUP:
                # The player released the mouse button.
                if gameIsOver:
                    # If the game is over, clicking restarts a new game.
                    return

                # If the mouse-up position equals the mouse-down position,
                # then this was a click (not a drag).
                if event.pos == (lastMouseDownX, lastMouseDownY):
                    clickedSpace = checkForGemClick(event.pos)
                else:
                    # This was a drag (mouse moved while button held down).
                    firstSelectedGem = checkForGemClick((lastMouseDownX, lastMouseDownY))
                    clickedSpace = checkForGemClick(event.pos)

                    # If either end of the drag is not on a gem, ignore it.
                    if not firstSelectedGem or not clickedSpace:
                        firstSelectedGem = None
                        clickedSpace = None

            elif event.type == MOUSEBUTTONDOWN:
                # Record where the mouse button was first pressed.
                lastMouseDownX, lastMouseDownY = event.pos

        # If the player clicked on a space and we don't have a first gem yet,
        # select it as the first gem to swap.
        if clickedSpace and not firstSelectedGem:
            firstSelectedGem = clickedSpace

        # If the player clicks a second space after selecting the first gem,
        # attempt to swap the two gems.
        elif clickedSpace and firstSelectedGem:
            firstSwappingGem, secondSwappingGem = getSwappingGems(gameBoard, firstSelectedGem, clickedSpace)

            # If the gems are not next to each other, the swap is invalid.
            if firstSwappingGem is None and secondSwappingGem is None:
                firstSelectedGem = None  # deselect the first gem
                continue

            # Animate the swap on the screen.
            boardCopy = getBoardCopyMinusGems(gameBoard, (firstSwappingGem, secondSwappingGem))
            animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)

            # Swap the gem values in the board data structure.
            gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = secondSwappingGem['imageNum']
            gameBoard[secondSwappingGem['x']][secondSwappingGem['y']] = firstSwappingGem['imageNum']

            # Check if this swap created any matches.
            matchedGems = findMatchingGems(gameBoard)

            if matchedGems == []:
                # No matches were created by this swap: swap back and play a sound.
                GAMESOUNDS['bad swap'].play()
                animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [], score)

                # Swap back in the game board.
                gameBoard[firstSwappingGem['x']][firstSwappingGem['y']] = firstSwappingGem['imageNum']
                gameBoard[secondSwappingGem['x']][secondSwappingGem['y']] = secondSwappingGem['imageNum']
            else:
                # A match was made. Remove the matched gems and update the score.
                scoreAdd = 0

                # Keep finding matches until no more exist after dropping new gems.
                while matchedGems != []:
                    # 'points' is used to display the score gained from this match.
                    points = []

                    for gemSet in matchedGems:
                        # Each matched set gives more points the larger it is.
                        scoreAdd += (10 + (len(gemSet) - 3) * 10)

                        # Remove the matched gems from the board.
                        for gem in gemSet:
                            gameBoard[gem[0]][gem[1]] = EMPTY_SPACE

                        # Prepare a little score popup text for this match.
                        points.append({
                            'points': scoreAdd,
                            'x': gem[0] * GEMIMAGESIZE + XMARGIN,
                            'y': gem[1] * GEMIMAGESIZE + YMARGIN,
                        })

                    # Play a random match sound.
                    random.choice(GAMESOUNDS['match']).play()
                    score += scoreAdd

                    # Drop new gems into the holes and animate the movement.
                    fillBoardAndAnimate(gameBoard, points, score)

                    # Look for any new matches created by the dropped gems.
                    matchedGems = findMatchingGems(gameBoard)

            # Reset selection so the player can start a new swap.
            firstSelectedGem = None

            # If there are no possible moves left, the game ends.
            if not canMakeMove(gameBoard):
                gameIsOver = True

        # Draw the game state to the screen.
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(gameBoard)

        # If a gem is currently selected, draw its highlight.
        if firstSelectedGem is not None:
            highlightSpace(firstSelectedGem['x'], firstSelectedGem['y'])

        # If the game is over, show the "click to continue" message.
        if gameIsOver:
            if clickContinueTextSurf is None:
                # Create the text surface once, then reuse it.
                clickContinueTextSurf = BASICFONT.render(
                    'Final Score: %s (Click to continue)' % (score),
                    1,
                    GAMEOVERCOLOR,
                    GAMEOVERBGCOLOR,
                )
                clickContinueTextRect = clickContinueTextSurf.get_rect()
                clickContinueTextRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))

            DISPLAYSURF.blit(clickContinueTextSurf, clickContinueTextRect)

        # Reduce score over time while the game is still running.
        elif score > 0 and time.time() - lastScoreDeduction > DEDUCTSPEED:
            score -= 1
            lastScoreDeduction = time.time()

        # Draw the player's score.
        drawScore(score)

        # Update the display and wait for the next frame.
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def getSwappingGems(board, firstXY, secondXY):
    """Return two gem dictionaries if they are adjacent and swappable.

    The game uses dictionaries to represent gems. Each gem dictionary has
    the keys:
      - 'x', 'y': board coordinates
      - 'imageNum': which gem image to draw
      - 'direction': where it is moving (UP/DOWN/LEFT/RIGHT)

    If the two selected spaces are not adjacent (up/down/left/right),
    this function returns (None, None).

    Parameters:
      board: The current game board.
      firstXY: {'x': int, 'y': int} for the first selected gem.
      secondXY: {'x': int, 'y': int} for the second selected gem.

    Returns:
      (firstGem, secondGem) if adjacent, otherwise (None, None).
    """

    firstGem = {
        'imageNum': board[firstXY['x']][firstXY['y']],
        'x': firstXY['x'],
        'y': firstXY['y'],
    }

    secondGem = {
        'imageNum': board[secondXY['x']][secondXY['y']],
        'x': secondXY['x'],
        'y': secondXY['y'],
    }

    # Determine if the gems are adjacent and set their movement direction.
    if firstGem['x'] == secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
        # First gem is to the right of the second gem.
        firstGem['direction'] = LEFT
        secondGem['direction'] = RIGHT

    elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['y']:
        # First gem is to the left of the second gem.
        firstGem['direction'] = RIGHT
        secondGem['direction'] = LEFT

    elif firstGem['y'] == secondGem['y'] + 1 and firstGem['x'] == secondGem['x']:
        # First gem is below the second gem.
        firstGem['direction'] = UP
        secondGem['direction'] = DOWN

    elif firstGem['y'] == secondGem['y'] - 1 and firstGem['x'] == secondGem['x']:
        # First gem is above the second gem.
        firstGem['direction'] = DOWN
        secondGem['direction'] = UP

    else:
        # Not adjacent: cannot swap.
        return None, None

    return firstGem, secondGem



def getBlankBoard():
    """Create and return an empty game board.

    The board is represented as a list of columns, where each column is a list
    of rows. board[x][y] is the gem at column x and row y. An empty space is
    represented by EMPTY_SPACE.

    Returns:
      list: a new board filled with EMPTY_SPACE.
    """

    board = []
    for x in range(BOARDWIDTH):
        # Create a full column of EMPTY_SPACE values.
        board.append([EMPTY_SPACE] * BOARDHEIGHT)

    return board



def canMakeMove(board):
    """Return True if there is a valid move available on the board.

    The game ends when the player cannot make any move that will create a
    match of 3 or more gems. This function looks for specific patterns where a
    single swap would create a match.
    """

    # These patterns describe gem arrangements that are one swap away from
    # forming a match of three identical gems. Each tuple contains three
    # relative offsets from the current position.
    oneOffPatterns = (
        ((0, 1), (1, 0), (2, 0)),
        ((0, 1), (1, 1), (2, 0)),
        ((0, 0), (1, 1), (2, 0)),
        ((0, 1), (1, 0), (2, 1)),
        ((0, 0), (1, 0), (2, 1)),
        ((0, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 2), (0, 3)),
        ((0, 0), (0, 1), (0, 3)),
    )

    # Loop through every board position.
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            for pat in oneOffPatterns:
                # For each pattern, check both orientations (original and swapped).
                if (
                    getGemAt(board, x + pat[0][0], y + pat[0][1])
                    == getGemAt(board, x + pat[1][0], y + pat[1][1])
                    == getGemAt(board, x + pat[2][0], y + pat[2][1])
                    != None
                ) or (
                    getGemAt(board, x + pat[0][1], y + pat[0][0])
                    == getGemAt(board, x + pat[1][1], y + pat[1][0])
                    == getGemAt(board, x + pat[2][1], y + pat[2][0])
                    != None
                ):
                    return True

    # No pattern found that indicates a possible match.
    return False



def drawMovingGem(gem, progress):
    """Draw a gem while it is moving.

    The gem slides smoothly from its start position to its end position
    based on the progress parameter.

    Parameters:
      gem (dict): A gem dictionary with keys 'x', 'y', 'imageNum', 'direction'.
      progress (float): A number between 0 and 100 representing how far along
                        the animation is.
    """

    movex = 0
    movey = 0

    # Convert progress from 0-100 to 0.0-1.0.
    progress *= 0.01

    # Determine how far the gem should move in pixels.
    if gem['direction'] == UP:
        movey = -int(progress * GEMIMAGESIZE)
    elif gem['direction'] == DOWN:
        movey = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == RIGHT:
        movex = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == LEFT:
        movex = -int(progress * GEMIMAGESIZE)

    basex = gem['x']
    basey = gem['y']

    # Special handling for gems above the board.
    if basey == ROWABOVEBOARD:
        basey = -1

    # Convert board coordinates to pixel coordinates.
    pixelx = XMARGIN + (basex * GEMIMAGESIZE)
    pixely = YMARGIN + (basey * GEMIMAGESIZE)

    # Create a rectangle for where the gem should be drawn.
    r = pygame.Rect((pixelx + movex, pixely + movey, GEMIMAGESIZE, GEMIMAGESIZE))

    # Draw the gem image onto the screen.
    DISPLAYSURF.blit(GEMIMAGES[gem['imageNum']], r)



def pullDownAllGems(board):
    """Apply gravity so that gems fall down into empty spaces.

    After removing matched gems, there are empty spots in the board. This
    function makes all gems fall to the bottom of their column, leaving
    EMPTY_SPACE values at the top.
    """

    for x in range(BOARDWIDTH):
        gemsInColumn = []
        for y in range(BOARDHEIGHT):
            if board[x][y] != EMPTY_SPACE:
                # Collect only the gems that exist (skip empty spaces).
                gemsInColumn.append(board[x][y])

        # The bottom of the column gets the gems, the top gets empty spaces.
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn



def getGemAt(board, x, y):
    """Return the gem at position (x, y) or None if out of bounds."""

    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        # Coordinates outside the board are treated as None.
        return None
    else:
        return board[x][y]



def getDropSlots(board):
    """Compute which new gems should drop into each column.

    This function returns a list of lists called dropSlots, where each
    inner list contains the gem types that should drop down into that
    column (from top to bottom) to fill any empty spaces.

    It attempts to avoid creating immediate matches by choosing a gem type
    that is different from its neighbors.

    Parameters:
      board: The current game board.

    Returns:
      list[list[int]]: A list of drop slot lists, one per column.
    """

    # Work on a copy so we don't change the original board while computing.
    boardCopy = copy.deepcopy(board)

    # Apply gravity so that existing gems are already at the bottom.
    pullDownAllGems(boardCopy)

    # Prepare an empty list for each column.
    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    # Look for empty spaces from the bottom up.
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 1, -1, -1):  # start from bottom row
            if boardCopy[x][y] == EMPTY_SPACE:
                # The space is empty, so we need to decide which gem will drop here.
                possibleGems = list(range(len(GEMIMAGES)))

                # Avoid choosing a gem that would immediately match with neighbors.
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    neighborGem = getGemAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborGem is not None and neighborGem in possibleGems:
                        possibleGems.remove(neighborGem)

                # Choose one of the remaining gem types at random.
                newGem = random.choice(possibleGems)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)

    return dropSlots



def findMatchingGems(board):
    """Find all sets of 3 or more matching gems on the board.

    Returns a list of gem sets, where each set is a list of (x, y) tuples
    indicating the positions of the gems to remove.
    """

    gemsToRemove = []  # list of lists of gems to remove
    boardCopy = copy.deepcopy(board)

    # Check every position for horizontal and vertical matches.
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            # Check for horizontal matches of length 3 or more.
            if (
                getGemAt(boardCopy, x, y)
                == getGemAt(boardCopy, x + 1, y)
                == getGemAt(boardCopy, x + 2, y)
                and getGemAt(boardCopy, x, y) != EMPTY_SPACE
            ):
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []

                # Keep collecting gems as long as they match.
                while getGemAt(boardCopy, x + offset, y) == targetGem:
                    removeSet.append((x + offset, y))
                    boardCopy[x + offset][y] = EMPTY_SPACE
                    offset += 1

                gemsToRemove.append(removeSet)

            # Check for vertical matches of length 3 or more.
            if (
                getGemAt(boardCopy, x, y)
                == getGemAt(boardCopy, x, y + 1)
                == getGemAt(boardCopy, x, y + 2)
                and getGemAt(boardCopy, x, y) != EMPTY_SPACE
            ):
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []

                while getGemAt(boardCopy, x, y + offset) == targetGem:
                    removeSet.append((x, y + offset))
                    boardCopy[x][y + offset] = EMPTY_SPACE
                    offset += 1

                gemsToRemove.append(removeSet)

    return gemsToRemove



def highlightSpace(x, y):
    """Draw a colored border around the board cell at (x, y)."""
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)



def getDroppingGems(board):
    """Return a list of gems that should fall down this frame.

    Any gem that has an empty space directly beneath it should fall down.
    This function returns a list of gem dictionaries describing those gems.
    """

    boardCopy = copy.deepcopy(board)
    droppingGems = []

    for x in range(BOARDWIDTH):
        # Start from the second-to-last row (since the bottom row can't fall).
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y + 1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                droppingGems.append({
                    'imageNum': boardCopy[x][y],
                    'x': x,
                    'y': y,
                    'direction': DOWN,
                })
                boardCopy[x][y] = EMPTY_SPACE

    return droppingGems



def animateMovingGems(board, gems, pointsText, score):
    """Animate gems moving (swapping or falling) along with score popups."""

    # progress goes from 0 (start) to 100 (finish) for the animation.
    progress = 0

    while progress < 100:
        DISPLAYSURF.fill(BGCOLOR)

        # Draw the board state without the moving gems.
        drawBoard(board)

        # Draw each moving gem at its current animation position.
        for gem in gems:
            drawMovingGem(gem, progress)

        # Draw the current score.
        drawScore(score)

        # Draw any floating point text (for scoring) on the screen.
        for pointText in pointsText:
            pointsSurf = BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
            pointsRect = pointsSurf.get_rect()
            pointsRect.center = (pointText['x'], pointText['y'])
            DISPLAYSURF.blit(pointsSurf, pointsRect)

        pygame.display.update()
        FPSCLOCK.tick(FPS)

        # Move the animation forward a little.
        progress += MOVERATE



def moveGems(board, movingGems):
    """Update the board data by moving gems one cell in their direction."""

    for gem in movingGems:
        if gem['y'] != ROWABOVEBOARD:
            # Clear the gem's old position.
            board[gem['x']][gem['y']] = EMPTY_SPACE

            movex = 0
            movey = 0
            if gem['direction'] == LEFT:
                movex = -1
            elif gem['direction'] == RIGHT:
                movex = 1
            elif gem['direction'] == DOWN:
                movey = 1
            elif gem['direction'] == UP:
                movey = -1

            # Place the gem in its new location.
            board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
        else:
            # Gems with y == ROWABOVEBOARD are above the board and should
            # be moved into the top row.
            board[gem['x']][0] = gem['imageNum']



def fillBoardAndAnimate(board, points, score):
    """Fill empty spaces on the board with new gems, animating the drop."""

    # Get the list of gems that need to drop into each column.
    dropSlots = getDropSlots(board)

    # While there are still gems waiting to drop.
    while dropSlots != [[]] * BOARDWIDTH:
        # Find all gems that should move down one cell.
        movingGems = getDroppingGems(board)

        # Add a new gem from the drop slots at the top of each column.
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                movingGems.append({
                    'imageNum': dropSlots[x][0],
                    'x': x,
                    'y': ROWABOVEBOARD,
                    'direction': DOWN,
                })

        # Draw the board with the moving gems and any score text.
        boardCopy = getBoardCopyMinusGems(board, movingGems)
        animateMovingGems(boardCopy, movingGems, points, score)

        # Update the board data to reflect the movement.
        moveGems(board, movingGems)

        # Remove gems that have been dropped from the drop slots so the next
        # gem in the slot can fall in the next loop iteration.
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]



def checkForGemClick(pos):
    """Return the board coordinates of a click, or None if not on the board."""

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0], pos[1]):
                return {'x': x, 'y': y}

    return None  # Click was not on the board.



def drawBoard(board):
    """Draw the entire board and all gems on the screen."""

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            # Draw the grid cell border.
            pygame.draw.rect(DISPLAYSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)

            gemToDraw = board[x][y]
            if gemToDraw != EMPTY_SPACE:
                # If there is a gem in this cell, draw its image.
                DISPLAYSURF.blit(GEMIMAGES[gemToDraw], BOARDRECTS[x][y])



def getBoardCopyMinusGems(board, gems):
    """Return a copy of the board with some gems removed.

    This is used during animation so that the moving gems are drawn on top
    of a board that doesn't show their original positions.

    Parameters:
      board: The original board.
      gems: A list of gem dictionaries to remove from the copy.

    Returns:
      A new board copy with the specified gems replaced by EMPTY_SPACE.
    """

    boardCopy = copy.deepcopy(board)

    for gem in gems:
        if gem['y'] != ROWABOVEBOARD:
            boardCopy[gem['x']][gem['y']] = EMPTY_SPACE

    return boardCopy



def drawScore(score):
    """Draw the current score in the bottom-left corner."""

    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR)
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 6)
    DISPLAYSURF.blit(scoreImg, scoreRect)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    main()
