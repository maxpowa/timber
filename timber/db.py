import os
import sqlite3
import datetime
from timber.utils import Channel, Message, lru_cache


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db_cursor(filename):
    fd = os.open(filename, os.O_RDONLY)
    c = sqlite3.connect('/dev/fd/%d' % fd)
    os.close(fd)
    c.row_factory = dict_factory
    return c.cursor()


@lru_cache()
def get_channels(file, current):
    c = get_db_cursor(file)
    c.execute('SELECT channel FROM logquery GROUP BY channel ORDER BY channel ASC')
    res = c.fetchall()
    channels = []
    for chan in res:
        name = chan['channel']
        channels = channels + [Channel(name, name==current),]
    return channels


@lru_cache()
def get_messages(file, channel, date):
    c = get_db_cursor(file)
    start_of_day = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    end_of_day = datetime.datetime(date.year, date.month, date.day, 23, 59, 59)
    c.execute('SELECT * FROM logquery WHERE channel = ? AND sent_at > ? AND sent_at < ?', (channel, start_of_day, end_of_day))
    res = c.fetchall()
    messages = []
    for msg in res:
        messages = messages + [Message(msg),]
    return messages
