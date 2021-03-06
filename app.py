#!/usr/bin/env python
'''
Timber - An IRC log viewer, inspired by irclogger.com
'''
import os
import bottle
from timber import db
from datetime import date, datetime

# PostgreSQL connection statement
if not os.getenv('PG_CONNECT', False):
    raise ValueError('No PG_CONNECT env var defined.')
PG_CONNECT = os.getenv('PG_CONNECT', False)

app = application = bottle.Bottle()

@app.route('/static/<filename:path>')
def static(filename):
    return bottle.static_file(filename, root='./static')

@app.route('/')
def show_index():
    channels = db.get_channels(PG_CONNECT, None, datetime.strptime(date.today().isoformat(), '%Y-%m-%d').date())
    return bottle.template('main', channels=channels)

@app.route('/<channel>')
@app.route('/<channel>/<date>')
def show_channel(channel, date=date.today().isoformat()):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    channel = channel.replace(',', '#')
    channels = db.get_channels(PG_CONNECT, channel, date)
    messages = db.get_messages(PG_CONNECT, channel, date)
    return bottle.template('main', channels=channels, channel=channel, messages=messages, date=date)

@app.route('/logs/channel/<channel>')
def redirect_old_channel(channel):
    return bottle.redirect('/,'+channel)

@app.hook('before_request')
def strip_path():
    bottle.request.environ['PATH_INFO'] = bottle.request.environ['PATH_INFO'].rstrip('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, server='paste')
