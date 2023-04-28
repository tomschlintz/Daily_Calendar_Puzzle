#!/usr/bin/python3

import sys
from datetime import datetime
from copy import deepcopy

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

    # Mark spots on board for month and day that can't be covered.
    def setDate(self):
        m = self.date.month - 1  # get 0-based month {0..11}
        d = self.day - 1    # get 0-based day of month {0..20}
        self.rows[int(m / 12)][int(m % 12)] = 1
        self.rows[int(2 + d/7)][int(d % 7)] = 1

    ##
     # Place a piece on the board.
     # The piece rotation is already established before passing it to this method, so we don't worry about that here.
     # \param piece piece object to be placed
     # \param x linear location - this is 0 at (0,0), incrementing across each column, then down each row
     # \returns True if valid - fits in board and does not overlap any invalid spot or other piece already placed
     ##
    def place(self, piece, x):
        # Copy board, in case we fail to place the part.
        brdCopy = deepcopy(self.rows)

        # Derive coord of piece upper-left corner from linear location
        x0, y0 = self.coordFromLinear(x)

        # Invalid if piece rectangle goes outside of board rectangle. This should be true regardless
        # of the actual shape of the piece.
        if (x0 + piece.width) >= self.width or (y0 + piece.height) >= self.height:
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
    
        # # Invalid if any part of the piece overlaps either board spots that cannot be covered, or any other piece.
        # # Restore original board, and return failure to place.
        # if not self.isBoardValid():
        #     self.rows = deepcopy(brdCopy)
        #     return False
        
        # Return successful placement.
        return True
    
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

    def dump(self):
        for r in self.rows:
            for c in r:
                sys.stdout.write(str(c))
            sys.stdout.write('\n')

    ##
     # Get (col,row) of 2D board array from linear increment.
     ##
    def coordFromLinear(self, x):
        return int(x % self.width), int(x / self.width)

class Piece:
    pieces = []
    idx = 0         # use this to itterate through pieces, by 0-based index

    def __init__(self, rows):
        # Save parameters passed in object
        self.width = len(rows[0])
        self.height = len(rows)
        self.rows = rows
        self.rotation = 0   # Track current rotation for the piece
        self.id = len(Piece.pieces) + 1    # 1-based ID value for piece
        Piece.pieces.append(self)

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

    def dump(self):
        for r in self.rows:
            for c in r:
                sys.stdout.write(str(c))
            sys.stdout.write('\n')

    @classmethod
    def dumpAll(cls):
        for p in Piece.pieces:
            p.dump()
            print('='*10)

    @classmethod
    def nextPiece(cls):
        Piece.idx = (Piece.idx + 1) % len(Piece.pieces)
        if Piece.idx > 0:
            return Piece.pieces[Piece.idx]
        else:
            return None

    @classmethod
    def firstPiece(cls):
        Piece.idx = 0
        return Piece.pieces[Piece.idx]
    
    @classmethod
    def numPieces(cls):
        return len(Piece.pieces)

recurse = 0
def fit(board, piece):
    global recurse
    recurse += 1
    print(recurse)
    for pos in range(board.locations):
        for rotation in range(4):
            if board.place(piece, pos):
                nextPiece = Piece.nextPiece()
                if nextPiece:
                    if fit(board, nextPiece):
                        return True
                    else:
                        # Remove from board before trying more places and rotations.
                        board.remove(piece, pos)
                else:
                    return True    # No more pieces to place
    # All positions and rotations tried: got up a level and try again.
    return False

def main():

    # Establish the board on which to place the pieces.
    board = Board(datetime.now())

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
        print('Solution found!')
        board.dump()
    else:
        print('No solution found')

    # pos = 21

    # board.dump()
    # print('\n' + 'WM' * 10 + '\n')

    # print('\n' + 'WM' * 10 + '\n')
    # if not board.place(piece[0], pos):
    #     print('Will not fit')
    # board.dump()

    # print('\n' + 'WM' * 10 + '\n')
    # board.reset()
    # piece[0].rotate()
    # if not board.place(piece[0], pos):
    #     print('Will not fit')
    # board.dump()

    # # Piece.dumpAll()
    # return

    # # a = [[0,1,2],[10,11,12]]
    # # a[1][1] = 5
    # # print(a)
    # # return

    # print('Working..')
    # p = Piece([[1, 0, 1], [1, 1, 1]])
    # p.dump()
    # p.rotate()
    # p.dump()
    # p.rotate()
    # p.dump()
    # p.rotate()
    # p.dump()
    # p.rotate()
    # p.dump()
    # print('Done!')

if __name__ == "__main__":
    main()