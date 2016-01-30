# coding=utf-8
from calendar import TextCalendar
import datetime
import re
import cgi


class Channel(object):
    def __init__(self, name, selected=False):
        self.name = name
        self.selected = selected

    def cssClasses(self):
        return '' if not self.selected else 'current'

    def safe_name(self):
        return self.name.replace('#', ',')


class Message(object):
    def __init__(self, row):
        self.row = row
        self.intent = row['type']
        self.message = row['message']
        self.ts = row['timestamp']
        self.timestamp = int((self.ts - datetime.datetime(1970,1,1)).total_seconds())
        self.nick = row['nick']
        self.row['args'] = row['args'] if row['args'] else [row['channel'], '?']
        self.cssClass = 'msg' if self.intent == 'PRIVMSG' or self.intent == 'ACTION' else 'info'


    def pretty_time(self):
        return self.ts.strftime('%H:%M')


    def replace_groups(self, match):
        bg = ''
        if (match.group(2)):
            bg = match.group(2)
        return u'<span class="fg{0} bg{1}">{2}</span>'.format(match.group(1), bg, match.group(3))


    def html(self):
        MESSAGE_TPL = u"{message}"
        ACTION_TPL = u"* {nick} {message}"
        NICK_TPL = u"{nick} is now known as {message}"
        JOIN_TPL = u"{nick} joined"
        PART_TPL = u"{nick} left ({message})"
        QUIT_TPL = u"{nick} quit ({message})"
        KICK_TPL = u"{nick} kicked {args[1]} ({message})"
        MODE_TPL = u"{nick} set {message}"

        response = ''
        intent = self.intent
        msg = self.row
        if (intent == 'PRIVMSG' or intent == 'NOTICE'):
            response = MESSAGE_TPL.format(**msg)
        elif (intent == 'ACTION'):
            response =  ACTION_TPL.format(**msg)
        elif (intent == 'NICK'):
            response =  NICK_TPL.format(**msg)
        elif (intent == 'JOIN'):
            response =  JOIN_TPL.format(**msg)
        elif (intent == 'PART'):
            response =  PART_TPL.format(**msg)
        elif (intent == 'QUIT'):
            response =  QUIT_TPL.format(**msg)
        elif (intent == 'KICK'):
            response =  KICK_TPL.format(**msg)
        elif (intent == 'MODE'):
            response =  MODE_TPL.format(**msg)

        response = cgi.escape(response)

        fmt = [
            (r'\003([0-9]{1,2})[,]?([0-9]{1,2})?([^\003\017]+)', self.replace_groups),
            (r'\002([^\002\017<]+)(\002)?', lambda m: u'<b>{}</b>'.format(m.group(1))),
            (r'\037([^\037\017<]+)(\037)?', lambda m: u'<u>{}</u>'.format(m.group(1))),
            (r'\035([^\035\017<]+)(\035)?', lambda m: u'<i>{}</i>'.format(m.group(1)))
        ]
        for regex, rep_func in fmt:
            response = re.sub(regex, rep_func, response)

        if (intent == 'PRIVMSG'):
            response = u'<span class="nickname">&lt;{}&gt;</span> {}'.format(msg['nick'], response)
        elif (intent == 'NOTICE'):
            response = u'<span class="nickname">-{}-</span> {}'.format(msg['nick'], response)

        return response


def day_link(channel, date, match):
    d = date.strftime('%Y-%m-{0:02d}'.format(int(match.group(0))))
    cssCls = 'today' if datetime.date.today().isoformat() == d else ''
    cssCls = cssCls + ' current' if date.isoformat() == d else cssCls
    channel = channel + '/' + d if len(channel) > 0 else ''
    return '<a class="{0}" href="/{1}">{2}</a>'.format(cssCls, channel, match.group(0))


def get_calendar(channel, date, links=True):
    calendar = TextCalendar(firstweekday=6).formatmonth(date.year, date.month)

    if not links:
        return calendar

    calendar = re.sub(r'\b(\d{1,2})\b', lambda m: day_link(channel, date, m), calendar)

    next_month = add_one_month(date)
    prev_month = subtract_one_month(date)

    parts = [
        '<a href="/{0}/{1}">&lt;</a>'.format(channel, prev_month.isoformat()),
        '{}'.format(date.strftime("%B %Y").center(18)),
        '<a href="/{0}/{1}">&gt;</a>'.format(channel, next_month.isoformat()),
        '\n{}'.format('\n'.join(calendar.split('\n')[1:-1]))
    ]

    return ''.join(parts)


def add_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month earlier.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> add_one_month(datetime.date(2010, 1, 31))
        datetime.date(2010, 2, 28)
    """
    import datetime
    one_day = datetime.timedelta(days=1)
    one_month_later = t + one_day
    while one_month_later.month == t.month:  # advance to start of next month
        one_month_later += one_day
    target_month = one_month_later.month
    while one_month_later.day < t.day:  # advance to appropriate day
        one_month_later += one_day
        if one_month_later.month != target_month:  # gone too far
            one_month_later -= one_day
            break
    return one_month_later


def subtract_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month later.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> subtract_one_month(datetime.date(2010, 3, 31))
        datetime.date(2010, 2, 28)
    """
    import datetime
    one_day = datetime.timedelta(days=1)
    one_month_earlier = t - one_day
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier
