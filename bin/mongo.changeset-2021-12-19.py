#!/usr/bin/env python3

import io, os, sys
import json

from kizano import getLogger
log = getLogger(__name__)

import changeset

class Changeset20211219(changeset.MakefileConfigChangeset):
    '''
    Class implementation of the changeset operator.
    '''

    def mutateMakefile(self, mkfile):
        '''
        Context: Let's just change the data structure here.
        Mutate the data structure to our liking and return the result.
        '''
        for video in mkfile['videos']:
            if 'input' not in video: continue
            if isinstance(video['input'], str):
                video['input'] = [ { 'i': video['input'] } ]
            elif isinstance(video['input'], list):
                for i, putin in enumerate(video['input']):
                    if isinstance(putin, str):
                        video['input'][i] = {
                          'i': putin
                        }
        return mkfile


def main():
    '''
    Main entry point.
    '''
    chset = Changeset20211219()
    chset.updateFiles()

sys.exit(main())

