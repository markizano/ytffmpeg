#!/usr/bin/env python3
'''
A instant cherrypy server that will scan a directory and find all `ytffmpeg.yml` files and
return the data structures in a JSON response.
'''

import io, os, sys
import cherrypy
import kizano
log = kizano.getLogger(__name__)

INDEX_HTML = '''
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Directory Server</title>
    <style type="text/css">
body { font-size: 16px; font-family: sans-serif, sans, Calibri;  }
ul li { margin: 2px; }
    </style>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script type="text/javascript">//<![CDATA[
/**
 * Render the few data points from the yaml that mean the most for us.
 * This includes: .videos[].output, .videos[].input, .videos[].attributes, and .videos[].metadata.
 * Make the .output as the title for the file, list the inputs under that,
 * attributes if present after inputs and metadata last.
 * @param yml 
 */
function showYML(yml) {
    $.getJSON(`yml?path=${yml}`, function(response) {
        $('#videos').empty();
        if (!response.videos.length) {
            $('#videos').append(`<div id="${yml}">No videos found in ${yml}.</div>`);
            return;
        }
        response.videos.forEach(function(video) {
            let videoDiv = `<div class="video">
                <h3 id=${yml}>${video.output}</h3>
                <ul>`;
            video.input.forEach(function(input) {
                videoDiv += `<li>${input.i}</li>`;
            });
            videoDiv += `</ul>`;
            if (video.attributes) {
                videoDiv += `<p>Attributes: ${video.attributes.join(', ')}</p>`;
            }
            if (video.filter_complex) {
                let filter_complex_str = video.filter_complex.map((x) => x.toString()).join(":\\n");
                videoDiv += `<p>Filter Complex: ${filter_complex_str}</p>`;
            }
            if (video.metadata) { // metadata is an object we can render in a key-pair like fashion.
                videoDiv += `<p>Metadata: <ul>`;
                for (let key in video.metadata) {
                    videoDiv += `<li>${key}: ${video.metadata[key]}</li>`;
                }
                videoDiv += `</ul></p>`;
            }
            videoDiv += `</div>`;
            $('#videos').append(videoDiv);
        });

    });
}

$(document).ready(function() {
    $.getJSON('ls', function(data) {
        $.each(data, function(i, yml) {
            $('#ymls').append(`<li><a href="#${yml}" onclick="showYML('${yml}')">${yml}</a></li>`);
        });
    });
});
    //]]></script>
  </head>
  <body>
    <div id="content">
        <h1>Directory Server</h1>
        <ul id="ymls"></ul>
        <br />
        <h2 id="ymlTitle"></h2>
        <div id="videos">
            <ul id="videoList">
                <li>Click a ytffmpeg.yml file to see its contents.</li>
            </ul>
        </div>
    </div>
  </body>
</html>
'''

class DirServ:
    '''
    Directory server class.
    '''
    def __init__(self, root: str):
        '''
        Initialize the directory server.
        '''
        self.root = root

    @cherrypy.expose
    def index(self):
        '''
        Return the index.html page.
        '''
        return INDEX_HTML

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def ls(self):
        '''
        Return a list of all ytffmpeg.yml files in the directory.
        '''
        ymls = []
        for root, dirs, files in os.walk(self.root):
            for file in files:
                if file == 'ytffmpeg.yml':
                    ymls.append(os.path.join(root, file).replace(self.root + os.path.sep, ''))
        return ymls

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def yml(self, path: str) -> dict:
        '''
        Return the contents of a ytffmpeg.yml file.
        '''
        # log.debug({'args': args, 'kwargs': kwargs})
        path = os.path.join(self.root, path)
        if not os.path.exists(path):
            return {
                'statusCode': 404,
                'message': f'{path} does not exist!'
            }
        return kizano.utils.read_yaml(path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: dirserv.py <directory>')
        sys.exit(1)
    root = os.path.realpath(sys.argv[1])
    cherrypy.quickstart(DirServ(root), '/', {
        'global': {
            'server.socket_host': os.environ.get('SERVER_HOST', '127.0.0.1'),
            'server.socket_port': int( os.environ.get('SERVER_PORT', '16555') )
        }
    })
