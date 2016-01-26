#!/usr/bin/env python
'''
Timber - An IRC log viewer, inspired by irclogger.com
'''
import bottle
from timber import db
from datetime import date, datetime

SQLITE_DATABASE = 'logquery.db'

app = application = bottle.Bottle()

@app.route('/static/<filename:path>')
def static(filename):
    return bottle.static_file(filename, root='./static')

@app.route('/')
def show_index():
    channels = db.get_channels(SQLITE_DATABASE, None)
    return bottle.template('main', channels=channels)

@app.route('/<channel>')
@app.route('/<channel>/<date>')
def show_channel(channel, date=date.today().isoformat()):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    channel = channel.replace(',', '#')
    channels = db.get_channels(SQLITE_DATABASE, channel)
    messages = db.get_messages(SQLITE_DATABASE, channel, date)
    return bottle.template('main', channels=channels, channel=channel, date=date)

@app.hook('before_request')
def strip_path():
    bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
