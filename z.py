#!/usr/bin/python3

import sys
import os
import calpuz
from datetime import datetime
import calendar

YEAR = 2024

def main():

    for m in range(7, 13):
        lastDayInMonth = calendar.monthrange(2024, m)[1]
        for d in range(1, lastDayInMonth+1):
            dstr = '{}/{}/{}'.format(m, d, YEAR)
            sys.argv = ['calpuz.py', dstr, 'gonogo']
            calpuz.main()

if __name__ == "__main__":
    main()