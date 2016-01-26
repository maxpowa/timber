#!/usr/bin/python
'''
Timber - An IRC log viewer, inspired by irclogger.com
'''

import bottle

app = application = bottle.Bottle()

@app.route('/static/<filename:path>')
def static(filename):
    '''
    Serve static files
    '''
    return bottle.static_file(filename, root='./static')

@app.route('/')
def show_index():
    '''
    The front "index" page
    '''
    return bottle.template('main', channels=[])

@app.route('/page/<page_name>')
def show_page(page_name):
    '''
    Return a page that has been rendered using a template
    '''
    return bottle.template('page', page_name=page_name)

class StripPathMiddleware(object):
    '''
    Get that slash out of the request
    '''
    def __init__(self, a):
        self.a = a
    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)

if __name__ == '__main__':
    bottle.run(app=StripPathMiddleware(app),
        host='127.0.0.1',
        port=8080)
