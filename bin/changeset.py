#! /usr/bin/python3
# Broken shell on purpose as this is supposed to be imported

import io, os, sys
import json

from kizano import getLogger
log = getLogger(__name__)

class Makefile(dict):
    '''
    Makefile class file that let's you load a JSON as a Makefile config object.
    '''
    def __init__(self, filename, *args, **kwargs):
        super().__init__()
        self._filename = filename
        for k, v in json.load(io.open(filename)).items():
            self[k] = v
    def save(self):
        '''
        Function to explicitly flush the current data structure to disk.
        '''
        log.debug(json.dumps(self, indent=2))
        with io.open(self._filename, 'w') as fd:
            json.dump(self, fd, indent=2)
            fd.write('\n')
            fd.flush()

# /* abstract */
class MakefileConfigChangeset(object):
    '''
    Changeset base class that handles the rough edges of the console, configuration and creating the
    class instance.
    '''

    def __init__(self):
        '''
        Parse commandline arguments and initialize the configuration.
        '''
        self.parseArgs()
        self.makefiles = []

    def getMakefiles(self):
        '''
        Get the list of Makefiles to update.
        '''
        if len(self.makefiles):
            return self.makefiles

        result = []
        for root, dirs, files in os.walk( self.config.dir ):
            for f in files:
                if self.config.makefile != f: continue
                result.append( os.path.join(root, f) )
        self.makefiles = sorted(result)
        return self.makefiles

    def updateFiles(self):
        '''
        Execute on the actual updating of the files.
        This function opens file descriptors and writes to files.
        @return None
        '''
        self.getMakefiles()
        for makefileFilename in self.makefiles:
            log.debug('loading %s file' % makefileFilename)
            mkfile = Makefile(makefileFilename)
            newMakefile = self.mutateMakefile( mkfile )
            newMakefile.save()
            log.info('Updated %s.' % makefileFilename)
        else:
            log.info('No Makefiles to iterate.')

    def parseArgs(self):
        from argparse import ArgumentParser
        options = ArgumentParser(
          usage='Usage: %(prog)s [options]',
        )

        options.add_argument(
          '--dir', '-d',
          action='store',
          dest='dir',
          help='Specify the target directory to execute. Defaults to current working directory.',
          default=os.getcwd()
        )

        options.add_argument(
          '--makefile', '-m',
          action='store',
          dest='makefile',
          help='Specify the name of the Makefile.config.json filename to update. Default="Makefile.config.json"',
          default='Makefile.config.json'
        )
        self.config = options.parse_args()

    def mutateMakefile(self, Makefile):
        '''
        HOW TO IMPLEMENT:
        - Accept [Makefile] as an object.
        - Muate the target object's values as desired.
        - Return the resulting mutated input argument.
        '''
        raise RuntimeError('Not implemented')


