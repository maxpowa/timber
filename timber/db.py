import os
import psycopg2
from psycopg2.extras import DictCursor
import datetime
from timber.utils import Channel, Message


def get_db_cursor(connect_stmt):
    c = psycopg2.connect(connect_stmt)
    return c.cursor(cursor_factory=DictCursor)


def get_channels(connect_stmt, current):
    c = get_db_cursor(connect_stmt)
    c.execute('SELECT lower(channel) FROM chanlogs GROUP BY lower(channel) ORDER BY lower(channel) ASC;')
    res = c.fetchall()
    c.close()
    channels = []
    for chan in res:
        name = chan[0]
        channels = channels + [Channel(name, name==current),]
    return channels


def get_messages(connect_stmt, channel, date):
    c = get_db_cursor(connect_stmt)
    start_of_day = datetime.datetime(date.year, date.month, date.day, 0, 0, 0).isoformat()
    end_of_day = datetime.datetime(date.year, date.month, date.day, 23, 59, 59).isoformat()
    c.execute('SELECT * FROM chanlogs WHERE lower(channel)=lower(%s) AND timestamp>%s::timestamp AND timestamp<%s::timestamp;', (channel, start_of_day, end_of_day))
    res = c.fetchall()
    c.close()
    print(repr(c.query))
    messages = []
    for msg in res:
        messages = messages + [Message(msg),]
    return messages
