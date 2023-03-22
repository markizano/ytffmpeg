#!/usr/bin/python3

import os, sys

fps = float( os.environ.get('FPS', '29.45') )

def t2s(h=0,m=0,s=0,f=0):
  return round( (h * 24) + (m * 60) + s + (f / fps), 3 )

print( t2s(*[ round(float(x), 3) for x in sys.argv[1:] ]) )
