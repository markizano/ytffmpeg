#!/usr/bin/env python3

import os, sys

global UNIT_TESTING
UNIT_TESTING = 1

# Add the lib directory to the path.
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'lib')))

# Importing into the namespace is sufficient as pytest will find the test cases.
from mkzforgeunit.build import *
from mkzforgeunit.config import *
from mkzforgeunit.gpu_lock import *
from mkzforgeunit.webserv import *
from mkzforgefunc.vertical import *
