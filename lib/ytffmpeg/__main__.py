import sys
import ytffmpeg

if __name__ == '__main__':
    scriptName = sys.argv[0]
    if scriptName not in ('ytffmpeg', 'ytffmpeg-serv'):
        raise ValueError('Invalid script name')
    script = {
        'ytffmpeg': ytffmpeg.main,
        'ytffmpeg-serv': ytffmpeg.directoryserver.main,
    }
    sys.exit(script())
