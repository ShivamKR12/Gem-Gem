"""
A simple match-3 style gem-swapping game.

This script is a self-contained game that uses Pygame to draw colorful gems
on the screen. The player swaps gems to make matches of 3 or more identical
gems in a row or column. Matched gems disappear and new gems drop down from
above.

The game demonstrates several common game programming concepts, such as:
- A 2D grid-based board stored in a list of lists (board[x][y]).
- Event-based input handling (mouse clicks and key presses).
- Simple animation by redrawing frames at a fixed rate.
- Checking for matching patterns and applying game rules.
"""

import random
import time
import pygame
import sys
import copy
import os

from pygame.locals import *

# ---------------------------------------------------------------------------
# Game constants (configuration values)
# ---------------------------------------------------------------------------
FPS = 30
WINDOWWIDTH = 600
WINDOWHEIGHT = 600
BOARDWIDTH = 8
BOARDHEIGHT = 8
GEMIMAGESIZE = 64
NUMGEMIMAGES = 7
NUMMATCHSOUNDS = 6
MOVERATE = 25
DEDUCTSPEED = 0.8

PURPLE    = (255,   0, 255)
LIGHTBLUE = (170, 190, 255)
BLUE      = (  0,   0, 255)
RED       = (255, 100, 100)
BLACK     = (  0,   0,   0)
BROWN     = ( 85,  65,   0)

HIGHLIGHTCOLOR = PURPLE
BGCOLOR = LIGHTBLUE
GRIDCOLOR = BLUE
GAMEOVERCOLOR = RED
GAMEOVERBGCOLOR = BLACK
SCORECOLOR = BROWN

XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * BOARDHEIGHT) / 2)

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

EMPTY_SPACE = -1
ROWABOVEBOARD = 'row above board'


def resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    
    This function is used to find files like images, even when the game is packaged into an executable.
    When running as a script, it uses the current directory.
    When packaged with PyInstaller, it uses the temporary directory where files are extracted.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GemGame:
    def __init__(self):
        pygame.init()
        self.fps_clock = pygame.time.Clock()
        self.display_surf = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        pygame.display.set_caption('Gem-Gem')
        self.basic_font = pygame.font.Font('freesansbold.ttf', 36)

        # Load gem images
        self.gem_images = []
        for i in range(1, NUMGEMIMAGES + 1):
            gem_image = pygame.image.load(resource_path(os.path.join('assets', 'images', 'gem%s.png' % i)))
            if gem_image.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
                gem_image = pygame.transform.smoothscale(gem_image, (GEMIMAGESIZE, GEMIMAGESIZE))
            self.gem_images.append(gem_image)

        # Load sounds
        self.game_sounds = {}
        self.game_sounds['bad swap'] = pygame.mixer.Sound(resource_path(os.path.join('assets', 'audio', 'badswap.wav')))
        self.game_sounds['match'] = []
        for i in range(NUMMATCHSOUNDS):
            self.game_sounds['match'].append(pygame.mixer.Sound(resource_path(os.path.join('assets', 'audio', 'match%s.wav' % i))))

        # Create a list of pygame.Rect objects for each board cell
        self.board_rects = []
        for x in range(BOARDWIDTH):
            self.board_rects.append([])
            for y in range(BOARDHEIGHT):
                r = pygame.Rect(
                    (XMARGIN + (x * GEMIMAGESIZE),
                     YMARGIN + (y * GEMIMAGESIZE),
                     GEMIMAGESIZE,
                     GEMIMAGESIZE)
                )
                self.board_rects[x].append(r)

    def get_blank_board(self):
        board = []
        for x in range(BOARDWIDTH):
            board.append([EMPTY_SPACE] * BOARDHEIGHT)
        return board

    def get_swapping_gems(self, board, first_xy, second_xy):
        first_gem = {
            'imageNum': board[first_xy['x']][first_xy['y']],
            'x': first_xy['x'],
            'y': first_xy['y'],
        }

        second_gem = {
            'imageNum': board[second_xy['x']][second_xy['y']],
            'x': second_xy['x'],
            'y': second_xy['y'],
        }

        if first_gem['x'] == second_gem['x'] + 1 and first_gem['y'] == second_gem['y']:
            first_gem['direction'] = LEFT
            second_gem['direction'] = RIGHT
        elif first_gem['x'] == second_gem['x'] - 1 and first_gem['y'] == second_gem['y']:
            first_gem['direction'] = RIGHT
            second_gem['direction'] = LEFT
        elif first_gem['y'] == second_gem['y'] + 1 and first_gem['x'] == second_gem['x']:
            first_gem['direction'] = UP
            second_gem['direction'] = DOWN
        elif first_gem['y'] == second_gem['y'] - 1 and first_gem['x'] == second_gem['x']:
            first_gem['direction'] = DOWN
            second_gem['direction'] = UP
        else:
            return None, None

        return first_gem, second_gem

    def can_make_move(self, board):
        one_off_patterns = (
            ((0, 1), (1, 0), (2, 0)),
            ((0, 1), (1, 1), (2, 0)),
            ((0, 0), (1, 1), (2, 0)),
            ((0, 1), (1, 0), (2, 1)),
            ((0, 0), (1, 0), (2, 1)),
            ((0, 0), (1, 1), (2, 1)),
            ((0, 0), (0, 2), (0, 3)),
            ((0, 0), (0, 1), (0, 3)),
        )

        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                for pat in one_off_patterns:
                    if (
                        self.get_gem_at(board, x + pat[0][0], y + pat[0][1])
                        == self.get_gem_at(board, x + pat[1][0], y + pat[1][1])
                        == self.get_gem_at(board, x + pat[2][0], y + pat[2][1])
                        != None
                    ) or (
                        self.get_gem_at(board, x + pat[0][1], y + pat[0][0])
                        == self.get_gem_at(board, x + pat[1][1], y + pat[1][0])
                        == self.get_gem_at(board, x + pat[2][1], y + pat[2][0])
                        != None
                    ):
                        return True
        return False

    def draw_moving_gem(self, gem, progress):
        movex = 0
        movey = 0
        progress *= 0.01

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

        if basey == ROWABOVEBOARD:
            basey = -1

        pixelx = XMARGIN + (basex * GEMIMAGESIZE)
        pixely = YMARGIN + (basey * GEMIMAGESIZE)

        r = pygame.Rect((pixelx + movex, pixely + movey, GEMIMAGESIZE, GEMIMAGESIZE))
        self.display_surf.blit(self.gem_images[gem['imageNum']], r)

    def pull_down_all_gems(self, board):
        for x in range(BOARDWIDTH):
            gems_in_column = []
            for y in range(BOARDHEIGHT):
                if board[x][y] != EMPTY_SPACE:
                    gems_in_column.append(board[x][y])
            board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gems_in_column))) + gems_in_column

    def get_gem_at(self, board, x, y):
        if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
            return None
        else:
            return board[x][y]

    def get_drop_slots(self, board):
        board_copy = copy.deepcopy(board)
        self.pull_down_all_gems(board_copy)

        drop_slots = []
        for i in range(BOARDWIDTH):
            drop_slots.append([])

        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT - 1, -1, -1):
                if board_copy[x][y] == EMPTY_SPACE:
                    possible_gems = list(range(len(self.gem_images)))

                    for offset_x, offset_y in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                        neighbor_gem = self.get_gem_at(board_copy, x + offset_x, y + offset_y)
                        if neighbor_gem is not None and neighbor_gem in possible_gems:
                            possible_gems.remove(neighbor_gem)

                    new_gem = random.choice(possible_gems)
                    board_copy[x][y] = new_gem
                    drop_slots[x].append(new_gem)
        return drop_slots

    def find_matching_gems(self, board):
        gems_to_remove = []
        board_copy = copy.deepcopy(board)

        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                if (
                    self.get_gem_at(board_copy, x, y)
                    == self.get_gem_at(board_copy, x + 1, y)
                    == self.get_gem_at(board_copy, x + 2, y)
                    and self.get_gem_at(board_copy, x, y) != EMPTY_SPACE
                ):
                    target_gem = board_copy[x][y]
                    offset = 0
                    remove_set = []

                    while self.get_gem_at(board_copy, x + offset, y) == target_gem:
                        remove_set.append((x + offset, y))
                        board_copy[x + offset][y] = EMPTY_SPACE
                        offset += 1

                    gems_to_remove.append(remove_set)

                if (
                    self.get_gem_at(board_copy, x, y)
                    == self.get_gem_at(board_copy, x, y + 1)
                    == self.get_gem_at(board_copy, x, y + 2)
                    and self.get_gem_at(board_copy, x, y) != EMPTY_SPACE
                ):
                    target_gem = board_copy[x][y]
                    offset = 0
                    remove_set = []

                    while self.get_gem_at(board_copy, x, y + offset) == target_gem:
                        remove_set.append((x, y + offset))
                        board_copy[x][y + offset] = EMPTY_SPACE
                        offset += 1

                    gems_to_remove.append(remove_set)
        return gems_to_remove

    def highlight_space(self, x, y):
        pygame.draw.rect(self.display_surf, HIGHLIGHTCOLOR, self.board_rects[x][y], 4)

    def get_dropping_gems(self, board):
        board_copy = copy.deepcopy(board)
        dropping_gems = []

        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT - 2, -1, -1):
                if board_copy[x][y + 1] == EMPTY_SPACE and board_copy[x][y] != EMPTY_SPACE:
                    dropping_gems.append({
                        'imageNum': board_copy[x][y],
                        'x': x,
                        'y': y,
                        'direction': DOWN,
                    })
                    board_copy[x][y] = EMPTY_SPACE
        return dropping_gems

    def animate_moving_gems(self, board, gems, points_text, score):
        progress = 0

        while progress < 100:
            self.display_surf.fill(BGCOLOR)
            self.draw_board(board)

            for gem in gems:
                self.draw_moving_gem(gem, progress)

            self.draw_score(score)

            for point_text in points_text:
                points_surf = self.basic_font.render(str(point_text['points']), 1, SCORECOLOR)
                points_rect = points_surf.get_rect()
                points_rect.center = (point_text['x'], point_text['y'])
                self.display_surf.blit(points_surf, points_rect)

            pygame.display.update()
            self.fps_clock.tick(FPS)
            progress += MOVERATE

    def move_gems(self, board, moving_gems):
        for gem in moving_gems:
            if gem['y'] != ROWABOVEBOARD:
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

                board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
            else:
                board[gem['x']][0] = gem['imageNum']

    def fill_board_and_animate(self, board, points, score):
        drop_slots = self.get_drop_slots(board)

        while drop_slots != [[]] * BOARDWIDTH:
            moving_gems = self.get_dropping_gems(board)

            for x in range(len(drop_slots)):
                if len(drop_slots[x]) != 0:
                    moving_gems.append({
                        'imageNum': drop_slots[x][0],
                        'x': x,
                        'y': ROWABOVEBOARD,
                        'direction': DOWN,
                    })

            board_copy = self.get_board_copy_minus_gems(board, moving_gems)
            self.animate_moving_gems(board_copy, moving_gems, points, score)
            self.move_gems(board, moving_gems)

            for x in range(len(drop_slots)):
                if len(drop_slots[x]) == 0:
                    continue
                board[x][0] = drop_slots[x][0]
                del drop_slots[x][0]

    def check_for_gem_click(self, pos):
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                if self.board_rects[x][y].collidepoint(pos[0], pos[1]):
                    return {'x': x, 'y': y}
        return None

    def draw_board(self, board):
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                pygame.draw.rect(self.display_surf, GRIDCOLOR, self.board_rects[x][y], 1)

                gem_to_draw = board[x][y]
                if gem_to_draw != EMPTY_SPACE:
                    self.display_surf.blit(self.gem_images[gem_to_draw], self.board_rects[x][y])

    def get_board_copy_minus_gems(self, board, gems):
        board_copy = copy.deepcopy(board)

        for gem in gems:
            if gem['y'] != ROWABOVEBOARD:
                board_copy[gem['x']][gem['y']] = EMPTY_SPACE

        return board_copy

    def draw_score(self, score):
        score_img = self.basic_font.render(str(score), 1, SCORECOLOR)
        score_rect = score_img.get_rect()
        score_rect.bottomleft = (10, WINDOWHEIGHT - 6)
        self.display_surf.blit(score_img, score_rect)

    def run_game(self):
        game_board = self.get_blank_board()
        score = 0
        self.fill_board_and_animate(game_board, [], score)

        first_selected_gem = None
        last_mouse_down_x = None
        last_mouse_down_y = None
        game_is_over = False
        last_score_deduction = time.time()
        click_continue_text_surf = None

        while True:
            clicked_space = None

            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYUP and event.key == K_BACKSPACE:
                    return  # start a new game
                elif event.type == MOUSEBUTTONUP:
                    if game_is_over:
                        return  # start a new game

                    if event.pos == (last_mouse_down_x, last_mouse_down_y):
                        clicked_space = self.check_for_gem_click(event.pos)
                    else:
                        first_selected_gem = self.check_for_gem_click((last_mouse_down_x, last_mouse_down_y))
                        clicked_space = self.check_for_gem_click(event.pos)

                        if not first_selected_gem or not clicked_space:
                            first_selected_gem = None
                            clicked_space = None

                elif event.type == MOUSEBUTTONDOWN:
                    last_mouse_down_x, last_mouse_down_y = event.pos

            if clicked_space and not first_selected_gem:
                first_selected_gem = clicked_space
            elif clicked_space and first_selected_gem:
                first_swapping_gem, second_swapping_gem = self.get_swapping_gems(game_board, first_selected_gem, clicked_space)

                if first_swapping_gem is None and second_swapping_gem is None:
                    first_selected_gem = None
                    continue

                board_copy = self.get_board_copy_minus_gems(game_board, (first_swapping_gem, second_swapping_gem))
                self.animate_moving_gems(board_copy, [first_swapping_gem, second_swapping_gem], [], score)

                game_board[first_swapping_gem['x']][first_swapping_gem['y']] = second_swapping_gem['imageNum']
                game_board[second_swapping_gem['x']][second_swapping_gem['y']] = first_swapping_gem['imageNum']

                matched_gems = self.find_matching_gems(game_board)

                if matched_gems == []:
                    self.game_sounds['bad swap'].play()
                    self.animate_moving_gems(board_copy, [first_swapping_gem, second_swapping_gem], [], score)

                    game_board[first_swapping_gem['x']][first_swapping_gem['y']] = first_swapping_gem['imageNum']
                    game_board[second_swapping_gem['x']][second_swapping_gem['y']] = second_swapping_gem['imageNum']
                else:
                    score_add = 0
                    while matched_gems != []:
                        points = []
                        for gem_set in matched_gems:
                            score_add += (10 + (len(gem_set) - 3) * 10)
                            for gem in gem_set:
                                game_board[gem[0]][gem[1]] = EMPTY_SPACE

                            points.append({
                                'points': score_add,
                                'x': gem[0] * GEMIMAGESIZE + XMARGIN,
                                'y': gem[1] * GEMIMAGESIZE + YMARGIN,
                            })

                        random.choice(self.game_sounds['match']).play()
                        score += score_add
                        self.fill_board_and_animate(game_board, points, score)
                        matched_gems = self.find_matching_gems(game_board)

                first_selected_gem = None

                if not self.can_make_move(game_board):
                    game_is_over = True

            self.display_surf.fill(BGCOLOR)
            self.draw_board(game_board)

            if first_selected_gem is not None:
                self.highlight_space(first_selected_gem['x'], first_selected_gem['y'])

            if game_is_over:
                if click_continue_text_surf is None:
                    click_continue_text_surf = self.basic_font.render(
                        'Final Score: %s (Click to continue)' % (score),
                        1,
                        GAMEOVERCOLOR,
                        GAMEOVERBGCOLOR,
                    )
                    click_continue_text_rect = click_continue_text_surf.get_rect()
                    click_continue_text_rect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
                self.display_surf.blit(click_continue_text_surf, click_continue_text_rect)
            elif score > 0 and time.time() - last_score_deduction > DEDUCTSPEED:
                score -= 1
                last_score_deduction = time.time()

            self.draw_score(score)
            pygame.display.update()
            self.fps_clock.tick(FPS)

    def run(self):
        while True:
            self.run_game()


def main():
    game = GemGame()
    game.run()


if __name__ == '__main__':
    main()
