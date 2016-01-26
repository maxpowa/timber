import os
import sqlite3
from timber.utils import Channel


def get_db_cursor(filename):
    fd = os.open(filename, os.O_RDONLY)
    c = sqlite3.connect('/dev/fd/%d' % fd)
    os.close(fd)
    return c.cursor()


def get_channels(file, current):
    c = get_db_cursor(file)
    c.execute('SELECT channel FROM logquery GROUP BY channel ORDER BY channel ASC')
    res = c.fetchall()
    channels = []
    for chan in res:
        name = chan[0]
        channels = channels + [Channel(name, name==current),]
    return channels


def get_messages(file, channel, date):
    c = get_db_cursor(file)
    c.execute('SELECT * FROM logquery WHERE channel = ?, sent_at > ?, sent_at < ?')
    res = c.fetchall()

    return
