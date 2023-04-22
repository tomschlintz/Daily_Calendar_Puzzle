#!/usr/bin/python3

import sys

class Piece:
    def __init__(self, rows):
        # Save parameters passed in object
        self.width = len(rows[0])
        self.height = len(rows)
        self.rows = rows

    def rotate(self):
        # Create new rows, where width is height, heith is width.
        newRows = [[None]*self.height for i in range(self.width)]
        # newRows = [[None,None],[None,None],[None,None]]

        # No transpose, rotating CCW.
        spot = False
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

    def dump(self):
        print('{} wide'.format(self.width))
        print('{} high'.format(self.height))
        print('Pattern:')
        for r in self.rows:
            for c in r:
                if c:
                    sys.stdout.write('X')
                else:
                    sys.stdout.write(' ')
            sys.stdout.write('\n')

def main():

    # a = [[0,1,2],[10,11,12]]
    # a[1][1] = 5
    # print(a)
    # return

    print('Working..')
    p = Piece([[True, False, True], [True, True, True]])
    p.dump()
    p.rotate()
    p.dump()
    print('Done!')

if __name__ == "__main__":
    main()