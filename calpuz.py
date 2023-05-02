#!/usr/bin/python3

import sys
import os
from datetime import datetime
import time
from copy import deepcopy

quiet = False
gonogo = False

##
 # Define a "board" object, which represents places to put all the pieces.
 # Any spots on the board that are not placeable are set to 1.
 # The spots on the board for the month and day are set to 1.
 # All other spots are left at zero.
 # Placing a piece on the board adds it's pattern for each spot it covers,
 # and any spot > 1 represents an overlap, either with unplaceable spots,
 # OR with already placed pieces.
 ##
class Board:
    def __init__(self, date):
        self.width = 7
        self.height = 7
        self.date = date
        self.month = self.date.month
        self.day = self.date.day
        self.locations = self.width * self.height
        self.hid = 0

        self.reset()

    def reset(self):
        # Represent board as 2D array.
        self.rows = [[0]*self.height for i in range(self.width)]

        # Establish unusable spots on the board.
        self.rows[0][6] = 9
        self.rows[1][6] = 9
        self.rows[6][3] = 9
        self.rows[6][4] = 9
        self.rows[6][5] = 9
        self.rows[6][6] = 9

        # Mark spots on board for date given, as these should not be covered.
        self.setDate()

    ##
     # Locate and group contiguous voids on the board, and report the smallest group.
     # Used to determine if a void has been created that no part could possibly
     # fit into, for the purpose of pruning fit() recursive branches.
     ##
    def smallestVoid(self):
        groupId = 0    # 0-based current group ID, incremented for each unique found
        spotGroups = [-1] * self.width*self.height      # 0-based group ID assignments for each spot on the board
        groupCounts = [0] * self.width*self.height      # count of spots for each group

        # Walk down each column to look for adjacent void spots, and start counts for each group found.
        for cidx in range (len(self.rows[0])):
            for ridx in range (len(self.rows)):
                pos = self.linearFromCoord(cidx, ridx)      # linear position for current spot
                if ridx == 0:
                    # First row: if zero, start a new group.
                    if self.rows[ridx][cidx] == 0:
                        spotGroups[pos] = groupId
                        groupCounts[spotGroups[pos]] = 1
                        groupId += 1
                else:
                    # Succeeding rows.
                    if self.rows[ridx][cidx] == 0:
                        ppos = self.linearFromCoord(cidx, ridx-1)   # linear position for spot above
                        if self.rows[ridx-1][cidx] == 0:
                            # If spot above is void, add to its group.
                            spotGroups[pos] = spotGroups[ppos]              # assign existing group to this position
                            groupCounts[spotGroups[ppos]] += 1              # add 1 spot to existing group
                        else:
                            # New void: start new group
                            spotGroups[pos] = groupId   # start new group
                            groupCounts[spotGroups[pos]] = 1   # start 1 spot for new group
                            groupId += 1                # increment group ID

        # Walk across each row, combining adjacent voids groups.
        # Note all voids have been assigned groups, above - now we're looking for adjacent horizontally.
        for ridx in range (len(self.rows)):
            for cidx in range (1, len(self.rows[0])):
                pos = self.linearFromCoord(cidx, ridx)      # linear position for current spot
                if self.rows[ridx][cidx] == 0:
                    ppos = self.linearFromCoord(cidx-1, ridx)   # linear position for spot to left
                    if self.rows[ridx][cidx-1] == 0:
                        toGroup = spotGroups[ppos]
                        fromGroup = spotGroups[pos]
                        # If void, and if not already in same group, combine with void group to the left.
                        if fromGroup != toGroup:
                            for i in range(self.locations):
                                if spotGroups[i] == fromGroup:
                                    groupCounts[toGroup] += 1  # add to existing group
                                    spotGroups[i] = spotGroups[ppos]
                            groupCounts[fromGroup] = 0    # zero-out group combined

        # # Debug: dump group mapping
        # print('\nMNMNMNMNMN')
        # for i in range(self.locations):
        #     if i and i % self.width == 0:
        #         sys.stdout.write('\n')
        #     if spotGroups[i] == -1:
        #         sys.stdout.write('X')
        #     else:
        #         sys.stdout.write(chr(spotGroups[i] + ord('a')))

        # Find and return the smallest group of voids
        smallest = sys.maxsize
        for i in range(groupId):
            if groupCounts[i] and (groupCounts[i] < smallest):
                smallest = groupCounts[i]
        return smallest

    # Mark spots on board for month and day that can't be covered.
    def setDate(self):
        m = self.date.month - 1  # get 0-based month {0..11}
        d = self.day - 1    # get 0-based day of month {0..20}
        self.rows[int(m / 6)][int(m % 6)] = 9
        self.rows[int(2 + d/7)][int(d % 7)] = 9

    ##
     # Place a piece on the board.
     # The piece rotation is already established before passing it to this method, so we don't worry about that here.
     # \param piece piece object to be placed
     # \param pos linear location - this is 0 at (0,0), incrementing across each column, then down each row
     # \returns True if valid - fits in board and does not overlap any invalid spot or other piece already placed
     ##
    def place(self, piece, pos):
        # Copy board, in case we fail to place the part.
        brdCopy = deepcopy(self.rows)

        # Derive coord of piece upper-left corner from linear location
        x0, y0 = self.coordFromLinear(pos)

        # Invalid if piece rectangle goes outside of board rectangle. This should be true regardless
        # of the actual shape of the piece.
        if (x0 + piece.width) > self.width or (y0 + piece.height) > self.height:
            return False

        # Superimpose piece onto board, by simpy adding it's ID to overlapping spots.
        for y in range(len(piece.rows)):
            for x in range(len(piece.rows[0])):
                # If piece would overlap an invalid spot, or another piece, restore board and return failure.
                if piece.rows[y][x] and self.rows[y0+y][x0+x]:
                    self.rows = deepcopy(brdCopy)
                    return False
                # Continue to fill piece into board.
                self.rows[y0+y][x0+x] += piece.rows[y][x] * piece.id

        # Check for too-small voids left by part, and disqualify if any found for the part.
        MIN_VOID_COUNT = 5          # minimum contiguous voids, since the smallest part overlaps 5 spots
        minVoid = self.smallestVoid()
        if minVoid < MIN_VOID_COUNT:
            self.remove(piece, pos)
            return False

        # Return successful placement.
        return True

    ##
     # Place a an 'X' mark on the given location on the board. Used to count voids and debugging.
     ##
    def mark(self, col, row):
        if self.rows[row][col] == 0:
            self.rows[row][col] = 'X'

    ##
     # Remove any alpha "marks" from the board, used for counting voids and debugging.
     ##
    def removeMarks(self):
        for y in range(len(self.rows)):
            for x in range(len(self.rows[0])):
                if self.rows[y][x] == 'X':
                    self.rows[y][x] = 0

    ##
     # Assuming the given piece has already been placed at the given location, remove the piece.
     # Caution: only call to remove a piece that is known to be at a given location - this is not checked.
     # \param piece piece object to be placed
     # \param x linear location - this is 0 at (0,0), incrementing across each column, then down each row
     ##
    def remove(self, piece, x):

        # Derive coord of piece upper-left corner from linear location
        x0, y0 = self.coordFromLinear(x)

        # Remove piece by subtracting out its pattern.
        for y in range(len(piece.rows)):
            for x in range(len(piece.rows[0])):
                self.rows[y0+y][x0+x] -= piece.rows[y][x] * piece.id

    ##
     # Scans all board spots, and return True only if no overlaps are detected.
     ##
    def isBoardValid(self):
        for r in self.rows:
            for c in r:
                if c > 1:
                    return False
        return True

    ##
     # Determine if a given coordinate on the board is "placeable", by the following criteria:
     #      o Must be within the boundaries of the board rectangle (not out of bounds of self.rows[][])
     #      o Must not be on an excluded/reserved spot, or selected for month or date (contains '9'), or overlapped by a placed piece
     ##
    def isPlaceable(self, row, col):
        return (row >= 0) and (col >= 0) and (row < self.width) and (col < self.height) and (self.rows[row][col] == 0)

    def dump(self):
        for r in self.rows:
            for c in r:
                if c <= 9:
                    sys.stdout.write(str(c))
                else:
                    sys.stdout.write(chr(c))    # for displaying marks, not number, for debugging
            sys.stdout.write('\n')

    ##
     # Get (col,row) of 2D board array from linear increment.
     ##
    def coordFromLinear(self, x):
        return int(x % self.width), int(x / self.width)

    ##
     # Get linear board position (spot) from (col,row) position.
     ##
    def linearFromCoord(self, col, row):
        return row * self.width + col

class Piece:
    pieces = []
    idx = 0         # use this to itterate through pieces, by 0-based index

    def __init__(self, rows):
        # Save parameters passed in object
        self.startRows = deepcopy(rows)
        self.id = len(Piece.pieces) + 1    # 1-based ID value for piece
        self.reset()
        Piece.pieces.append(self)

    ##
     # Reset piece to initial state.
     ##
    def reset(self):
        self.rows = deepcopy(self.startRows)
        self.width = len(self.rows[0])
        self.height = len(self.rows)
        self.rotation = 0   # Track current rotation for the piece

    def rotate(self):
        # Create new rows, where width is height, heith is width.
        newRows = [[0]*self.height for i in range(self.width)]
        # newRows = [[None,None],[None,None],[None,None]]

        # No transpose, rotating CCW.
        spot = 0
        for nrnum in range(self.width):
            for ncnum in range(self.height):
                c = self.width - nrnum - 1
                r = ncnum
                spot = self.rows[r][c]
                newRows[nrnum][ncnum] = spot
        self.rows = newRows
        newWidth = self.height
        self.height = self.width
        self.width = newWidth
        self.rotation = (self.rotation + 1) % 4     # 0=none, 1=CCW once, 2=CCW twice, 3=CCW thrice
        return self.rotation    # return final rotation - rotates to zero if all rotations exhausted

    def dump(self):
        for r in self.rows:
            for c in r:
                sys.stdout.write(str(c))
            sys.stdout.write('\n')

    ##
     # Get next piece, given piece objects were instantiated in order.
     # \returns next piece object, or None if no more
     ##
    def nextPiece(self):
        idx = (self.id) % len(Piece.pieces)
        if idx > 0:
            return Piece.pieces[idx]
        else:
            return None

    @classmethod
    def dumpAll(cls):
        for p in Piece.pieces:
            p.dump()
            print('='*10)

    @classmethod
    def firstPiece(cls):
        Piece.idx = 0
        return Piece.pieces[Piece.idx]

    @classmethod
    def numPieces(cls):
        return len(Piece.pieces)

##
 # Recursive function to try all placements and rotations for a given piece.
 # \param board board object to receive the pieces
 # \param piece next piece to place
 # \returns True when last piece has been placed
 ##
recurse = 0
def fit(board, piece):
    global recurse
    recurse += 1
    # print(recurse)
    for pos in range(board.locations):
        piece.reset()   # reset piece back to its initial rotation
        for rotation in range(4):
            if board.place(piece, pos):
                if not quiet:
                    if piece.id == 1:
                        # os.system('clear')
                        print('=======')
                        board.dump()
                nextPiece = piece.nextPiece()
                if nextPiece:
                    if fit(board, nextPiece):
                        recurse -= 1
                        return True
                    else:
                        # Remove from board before trying more places and rotations.
                        board.remove(piece, pos)
                        piece.rotate()
                else:
                    recurse -= 1
                    return True    # No more pieces to place
            else:
                # Piece could not be placed, due to fit on board, or overlap.
                # Go to next rotation.
                piece.rotate()
    # All positions and rotations tried: got up a level and try again.
    recurse -= 1
    return False

def main():
    global quiet
    global gonogo

    if len(sys.argv) > 1:
        dt = datetime.strptime(sys.argv[1], '%m/%d/%Y')
    else:
        dt = datetime.now()
    # dt = datetime.strptime('4/1/2023', '%m/%d/%Y')  # DEBUG

    if 'quiet' in sys.argv:
        quiet = True

    if 'gonogo' in sys.argv:
        gonogo = True
        quiet = True

    if not gonogo:
        print('Solving for {}'.format(dt.strftime('%m/%d/%Y')))

    startTime = time.time()

    board = Board(dt)

    # Establish all pieces used. Initial orientation for each is arbitrary.
    piece = \
        [ \
            Piece([[1,0,1],[1,1,1]]), \
            Piece([[0,0,1],[1,1,1],[1,0,0]]), \
            Piece([[1,1,1],[1,0,0],[1,0,0]]), \
            Piece([[0,0,1,1],[1,1,1,0]]), \
            Piece([[1,1,1,1],[1,0,0,0]]), \
            Piece([[1,1,1,1],[0,0,1,0]]), \
            Piece([[1,1,1],[0,1,1]]), \
            Piece([[1,1,1],[1,1,1]]), \
        ]

    if fit(board, piece[0]):
        if not gonogo:
            print('\nSolution found in {:.01f}s:'.format(time.time() - startTime))
            board.dump()
        else:
            print('{}: solved in {:.01f}s'.format(dt.strftime('%m/%d/%Y'), time.time() - startTime))
    else:
        print('{}: No solution found ({:.01f}s)'.format(dt.strftime('%m/%d/%Y'), time.time() - startTime))

if __name__ == "__main__":
    main()