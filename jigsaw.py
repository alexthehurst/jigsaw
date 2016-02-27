#!/usr/bin/python


import argparse
import copy
import random
import itertools

import sys


class Puzzle(list):
    def __init__(self, dimensions=(5, 5)):
        """

        :param dimensions:
        """
        if sys.version_info < (3, 0, 0):
            super(list, self).__init__()
        else:
            super().__init__(self)

        self.lx, self.ly = dimensions
        self.max_x = self.lx - 1
        self.max_y = self.ly - 1

        # Construct a 2D array of Coord objects
        for x_pos in range(self.lx):
            col = []
            for y_pos in range(self.ly):
                col.append(Coord(x_pos, y_pos, self))
            self.append(col)

        self.all_items = [coord for coord in itertools.chain(*self)]
        self.empty_coords = self.all_items
        self.exposed_coords = []
        self.tries = 0
        self.reporter = Reporter(self)

    def gridlabel(self, number):
        """
        Sane numbers for labeling the bottom row of the grid. 0, 5, 10, 5, 20...
        :param number:
        :return:
        """
        if (number % 10 == 1) and (number > 1):  # Part of a tens label
            return '0'
        elif number % 5:  # odd
            return ' '
        elif number % 10 == 0:
            return str(number / 10)
        else:
            return str(number % 10)

    def __repr__(self):

        """
        An ASCII representation of the puzzle's state
        :return: str
        """

        full_repr = ''

        for i, row in enumerate(range(self.ly), start=1):
            row_repr = ' '
            if self.reporter.labels:
                row_repr += str(self.ly - i)
            for col in range(self.lx):
                row_repr += self[col][self.max_y - row].glyph()
            full_repr += row_repr + '\n'
        if self.reporter.labels:
            full_repr += (' ' +
                          ''.join([self.gridlabel(a) for a in range(self.lx)]))
            full_repr += '\n'

        return full_repr

    def update_empty_coords(self):
        """
        Refresh the list of coords which are not filled
        :return:
        """
        self.empty_coords = [coord for coord in self.empty_coords
                             if not coord.is_filled]

    def update_exposed_coords(self):
        """
        Refresh the list of coords which are testable spots for fitting a piece
        :return: None
        """
        self.exposed_coords = [coord for coord in self.empty_coords if
                               coord.is_exposed]

    def add(self, piece):
        """
        Place a puzzle piece on the grid
        :param piece:
        """
        x = piece.x
        y = piece.y
        self[x][y].fill(piece)
        self.update_empty_coords()
        self.update_exposed_coords()
        self.reporter.placed(piece)

    def is_solved(self):
        return len(self.empty_coords) == 0


class Coord(object):
    def __init__(self, x, y, puzzle):
        self.coordinates = (x, y)
        self.x, self.y = x, y
        self.puzzle = puzzle  # The owner of this coord
        self.is_filled = False
        self.piece = None

        # Cache this instead of recalculating all the time
        self._position_type = None

        # Cache this instead of recalculating all the time
        self._neighbors = None

        # Empty coords adjacent to filled coords are considered exposed.
        # You could put a puzzle piece there to see if it fits.
        self.is_exposed = False

        # When running in coord mode, a one-off puzzle will be created for
        # display only after failed tries. This glyph is the failed try.
        self.failed = False

    def position_type(self):
        """
        Middle, edge, or corner. Read from cache, populate if necessary.
        :return: str
        """
        if self._position_type is not None:
            return self._position_type
        else:
            num_neighbors = len(self.neighbors())
            if num_neighbors == 4:
                self._position_type = "middle"
            elif num_neighbors == 3:
                self._position_type = "edge"
            elif num_neighbors == 2:
                self._position_type = "corner"
            else:
                raise Exception("Error calculating the number of neighbors: "
                                "%s neighbors" % num_neighbors)
            return self._position_type

    def neighbors(self):
        """
        List of adjacent neighbors. Will have 2, 3, or 4 depending on position.
        Read from cache, populate if necessary.
        :return: list
        """
        if self._neighbors is not None:
            return self._neighbors
        else:
            neighbors = []
            if self.y < self.puzzle.max_y:
                neighbors.append(self.puzzle[self.x][self.y + 1])  # up
            if self.y > 0:
                neighbors.append(self.puzzle[self.x][self.y - 1])  # down
            if self.x < self.puzzle.max_x:
                neighbors.append(self.puzzle[self.x + 1][self.y])  # right
            if self.x > 0:
                neighbors.append(self.puzzle[self.x - 1][self.y])  # left
            self._neighbors = neighbors
            return self._neighbors

    def has_new_neighbor(self):
        """
        A piece has been placed in a neighbor coord. This coord should now be
        considered exposed, if it's not filled already.
        :return:
        """
        if not self.is_filled:
            self.is_exposed = True

    def fill(self, piece):
        """
        The given piece has been found to fit in this coord.
        :param piece:
        :return:
        """
        self.piece = piece
        self.is_filled = True
        self.is_exposed = False
        for neighbor in self.neighbors():
            neighbor.has_new_neighbor()

    def is_empty(self):
        """
        Very simply the opposite of is_filled.
        :return:
        """
        return not self.is_filled

    def glyph(self):
        """
        The ASCII representation of this piece depends on its state and
        location.
        :return:
        """

        if self.failed:
            return "x"
        elif self.is_empty():
            return "."
        elif self.position_type() == "middle":
            return "#"
        elif self.position_type() == "corner":
            return "+"
        else:
            assert self.position_type() == "edge"
            if self.x in [0, self.puzzle.max_x]:
                return "|"
            else:
                return "-"

    def set_failed(self):
        self.failed = True

    def __repr__(self):
        """
        Coordinates and state
        :return:
        """
        return "(%s, %s) - %s" % (self.x,
                                  self.y,
                                  'Filled' if self.is_filled else 'Empty')


class Piece(object):
    """
    You can do a few things with pieces:

    - Pass them around as objects, to move from one bag to another
    - Test them for fit against given coords in the puzzle
    - Place them into particular coords
    """

    def __init__(self, puzzle, coordinates):

        # A piece knows its proper coordinates, but it'll never tell the user.
        self.coordinates = coordinates

        # Unpack this tuple into separate variables for maximum speed
        # while referencing
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.is_placed = False
        self.puzzle = puzzle
        self.current_tries = 0

        # Numbered as if you were counting left to right from the bottom left
        # corner
        self.id = (self.y * self.puzzle.lx) + (self.x + 1)

    def __repr__(self):
        """
        Coordinates and status
        :return:
        """
        return "(%s, %s) - %s" % (self.x,
                                  self.y,
                                  "Placed" if self.is_placed else "Unplaced")

    def place(self, seed=False):
        """
        Only to be used when the piece has been tested against the correct coord
        :param mode:
        :return:
        """
        self.is_placed = True
        self.is_seed = seed
        self.puzzle.add(self)

    def test_or_discard(self, scratchpile):
        """
        Attempt to place the piece in one of the exposed coords.
        If it's not possible, move it to the scratchpile.
        :param scratchpile:
        :param verbose:
        :return: tuple
        """

        exposed_coords = self.puzzle.exposed_coords
        for i, coord in enumerate(exposed_coords, start=1):

            self.current_tries = i

            if self.coordinates == coord.coordinates:
                # Instead of adding to the try count every single time, just use
                # the loop counter and add it after we're done trying.
                self.puzzle.tries += self.current_tries

                self.place()

                return

            # This coord wasn't right
            self.puzzle.reporter.failed_coord(coord, self)

        # The piece wasn't successfully placed
        scratchpile.append(self)
        self.puzzle.tries += self.current_tries
        self.puzzle.reporter.failed_piece(self)


class Pool(list):
    """
    Just a list of pieces, with an associated puzzle and constructor to
    create all the pieces.
    """

    def __init__(self, puzzle=None):
        if sys.version_info < (3, 0, 0):
            super(list, self).__init__()
        else:
            super().__init__(self)
        if puzzle:
            self += [Piece(puzzle, (x, y))
                     for x, y in itertools.product(range(puzzle.lx),
                                                   range(puzzle.ly))]
        random.shuffle(self)

    def draw_piece(self):
        return self.pop()


def solve(puzzle, labels=False, seed_piece_count=1, mode='pile'):
    """
    Lay down one or more pieces to start the puzzle, then iteratively try to
    attach each piece to the finished section until they have all been placed.

    :param puzzle:
    :param seed_piece_count:
    :param verbose:
    :return:
    """

    puzzle.reporter.mode = mode
    puzzle.reporter.labels = labels
    draw_pile = Pool(puzzle)
    discard_pile = Pool()  # Empty

    # These are gimmie pieces. You have to start somewhere with any jigsaw
    # puzzle. By default, just place one piece on the table, but 2-5 might
    # also make sense.

    for i in range(seed_piece_count):
        draw_pile.draw_piece().place(seed=True)

    while not puzzle.is_solved():

        puzzle.reporter.start_pile(draw_pile)
        random.shuffle(draw_pile)  # In-place
        discard_pile = Pool()

        # Attempt to fit each piece in turn
        for x in range(len(draw_pile)):
            draw_pile.draw_piece().test_or_discard(scratchpile=discard_pile)

        # Move the remaining pieces to the drawpile and try them again
        draw_pile = discard_pile

    puzzle.reporter.solved()


class Reporter:

    @staticmethod
    def wait(prompt='Continue? '):
        """
        Used when pausing for the user. Wrapper for version inconsistencies.
        :param prompt:
        :return:
        """

        if sys.version_info < (3, 0, 0):
            response = raw_input(prompt)
        else:
            response = input(prompt)
        if (response is not '') and (response[0] in ['q', 'n']):
            exit()
        return response

    def __init__(self, puzzle, mode='pile', labels=False):
        self.puzzle = puzzle
        self.puzzle.reporter = self
        self.mode = mode
        self.labels = labels

    def failed_coord(self, coord, piece):
        """
        The piece didn't match in the given coordinate.
        :param coord:
        :param piece:
        :return:
        """
        if self.mode == 'coord':
            display_puzzle = copy.deepcopy(self.puzzle)
            display_puzzle[coord.x][coord.y].set_failed()
            print(display_puzzle)
            print("Tried to place Piece %s at (%s, %s) but it didn't fit." %
                  (piece.id, coord.x, coord.y))
            self.wait()

    def failed_piece(self, piece):
        """
        Tried the piece in all exposed coordinates and didn't find a match.
        :param piece:
        :return:
        """
        if self.mode in ['coord', 'piece']:
            display_puzzle = copy.deepcopy(self.puzzle)
            display_puzzle[piece.x][piece.y].set_failed()
            print(display_puzzle)
            print("Couldn't place Piece %s  - actual location was (%s, %s))" %
                  (piece.id, piece.x, piece.y))
            self.wait()

    def placed(self, piece):
        """
        A piece was placed on the grid, either by a successful match or as a
        seed piece.
        :param piece:
        :return:
        """
        if self.mode in ['coord', 'piece']:
            print(self.puzzle)
            if piece.is_seed:
                print("Placed Piece %s at (%s, %s) [seed piece]" %
                      (piece.id, piece.x, piece.y))
            else:
                print("Placed Piece %s at (%s, %s) after trying %s coords" %
                      (piece.id, piece.x, piece.y, piece.current_tries))
            self.wait()

    def start_pile(self, pile):
        """
        The bag is being shuffled and we're about to iterate through the
        whole thing.
        :param pile:
        :return:
        """
        if self.mode in ['coord', 'piece', 'pile']:
            print(self.puzzle)
            print("*** SHAKE SHAKE SHAKE ***\n"
                  "Shaking the bag and doing another pass. %s pieces are "
                  "placed, %s pieces remaining.\n"
                  "*** SHAKE SHAKE SHAKE ***"
                  % (len(self.puzzle.all_items) - len(self.puzzle.empty_coords),
                     len(pile)))
            self.wait()

    def solved(self):
        """
        All pieces have been placed on the puzzle grid.
        :return:
        """
        if self.mode != 'stats':
            print(self.puzzle)
        print("Solved after %s comparisons" % self.puzzle.tries)
        print("at 1 sec per comparison, it would have taken %s hours" % (
            self.puzzle.tries / 3600.0))


def main(dimensions=(5, 5), initial_pieces=1, verbose=True):
    import argparse

    parser = argparse.ArgumentParser(description='All the tedium of a jigsaw '
                                                 'puzzle, from the command '
                                                 'line! Optionally specify '
                                                 'a feedback mode or number '
                                                 'of pieces to seed the board '
                                                 'with.')

    parser.add_argument('--dim', action='store', nargs=2, type=int,
                        metavar=('H', 'W'), dest='dimensions',
                        default=[5, 5],
                        help='width and height (default 5x5)')

    parser.add_argument('-i', dest='seed_piece_count', default=1, type=int,
                        metavar='pieces',
                        help='The number of pieces to seed the board with ('
                             'default 1)')

    parser.add_argument('--labels',
                        action='store_true', default=False,
                        help='Show numeric labels along the puzzle axes')

    parser.add_argument('--coord',
                        action='store_const', const='coord',
                        dest='mode', default='pile',
                        help='Display the grid after trying a piece in any '
                             'spot')

    parser.add_argument('--piece',
                        action='store_const', const='piece',
                        dest='mode', default='pile',
                        help='Display the grid after placing any piece')

    parser.add_argument('--pile',
                        action='store_const', const='pile',
                        dest='mode', default='pile',
                        help='(Default) Display the grid after trying all '
                             'letters in the pile')

    parser.add_argument('--stats',
                        action='store_const', const='stats',
                        dest='mode', default='pile',
                        help='Solve the puzzle silently, showing only final '
                             'stats')

    prefs = parser.parse_args()

    dimensions = tuple(prefs.dimensions)
    seed_piece_count = prefs.seed_piece_count
    mode = prefs.mode
    labels = prefs.labels

    puzzle = Puzzle(dimensions)

    solve(puzzle, mode=mode, labels=labels, seed_piece_count=seed_piece_count)


if __name__ == '__main__':
    main()
