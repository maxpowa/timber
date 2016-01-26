# coding=utf-8
from calendar import TextCalendar
import datetime
import re
from collections import namedtuple
from functools import update_wrapper
from threading import RLock

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


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
        self.intent = row['intent']
        self.message = row['message']
        self.ts = datetime.datetime.strptime(row['sent_at'], "%Y-%m-%d %H:%M:%S.%f")
        self.timestamp = int((self.ts- datetime.datetime(1970,1,1)).total_seconds())
        self.nick = row['nick']
        self.cssClass = 'msg' if self.intent == 'PRIVMSG' or self.intent == 'ACTION' else 'info'


    def pretty_time(self):
        return self.ts.strftime('%H:%M')


    def text(self):
        MESSAGE_TPL = u"{message}"
        ACTION_TPL = u"* {nick} {message}"
        NICK_TPL = u"{nick} is now {message}"
        JOIN_TPL = u"{nick} joined"
        PART_TPL = u"{nick} left ({message})"
        QUIT_TPL = u"{nick} quit ({message})"
        KICK_TPL = u"{nick} kicked {message}"
        MODE_TPL = u"{nick} set {message}"

        intent = self.intent
        msg = self.row
        if (intent == 'PRIVMSG'):
            return MESSAGE_TPL.format(**msg)
        elif (intent == 'ACTION'):
            return ACTION_TPL.format(**msg)
        elif (intent == 'NICK'):
            return NICK_TPL.format(**msg)
        elif (intent == 'JOIN'):
            return JOIN_TPL.format(**msg)
        elif (intent == 'PART'):
            return PART_TPL.format(**msg)
        elif (intent == 'QUIT'):
            return QUIT_TPL.format(**msg)
        elif (intent == 'KICK'):
            return KICK_TPL.format(**msg)
        elif (intent == 'MODE'):
            return MODE_TPL.format(**msg)


class _HashedSeq(list):
    __slots__ = 'hashvalue'

    def __init__(self, tup, hash=hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue


def day_link(channel, date, match):
    d = date.strftime('%Y-%m-{0:02d}'.format(int(match.group(0))))
    cssCls = 'today' if datetime.date.today().isoformat() == d else ''
    cssCls = cssCls + ' current' if date.isoformat() == d else cssCls
    channel = channel + '/' + d if len(channel) > 0 else ''
    return '<a class="{0}" href="/{1}">{2}</a>'.format(cssCls, channel, match.group(0))


def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str, frozenset, type(None)},
             sorted=sorted, tuple=tuple, type=type, len=len):
    'Make a cache key from optionally typed positional and keyword arguments'
    key = args
    if kwds:
        sorted_items = sorted(kwds.items())
        key += kwd_mark
        for item in sorted_items:
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for k, v in sorted_items)
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)


def lru_cache(maxsize=16, typed=False):
    """Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.

    Arguments to the cached function must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize) with
    f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """

    # Users should only access the lru_cache through its public API:
    #       cache_info, cache_clear, and f.__wrapped__
    # The internals of the lru_cache are encapsulated for thread safety and
    # to allow the implementation to change (including a possible C version).

    def decorating_function(user_function):

        cache = dict()
        stats = [0, 0]                  # make statistics updateable non-locally
        HITS, MISSES = 0, 1             # names for the stats fields
        make_key = _make_key
        cache_get = cache.get           # bound method to lookup key or return None
        _len = len                      # localize the global len() function
        lock = RLock()                  # because linkedlist updates aren't threadsafe
        root = []                       # root of the circular doubly linked list
        root[:] = [root, root, None, None]      # initialize by pointing to self
        nonlocal_root = [root]                  # make updateable non-locally
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3    # names for the link fields

        if maxsize == 0:

            def wrapper(*args, **kwds):
                # no caching, just do a statistics update after a successful call
                result = user_function(*args, **kwds)
                stats[MISSES] += 1
                return result

        elif maxsize is None:

            def wrapper(*args, **kwds):
                # simple caching without ordering or size limit
                key = make_key(args, kwds, typed)
                result = cache_get(key, root)   # root used here as a unique not-found sentinel
                if result is not root:
                    stats[HITS] += 1
                    return result
                result = user_function(*args, **kwds)
                cache[key] = result
                stats[MISSES] += 1
                return result

        else:

            def wrapper(*args, **kwds):
                # size limited caching that tracks accesses by recency
                key = make_key(args, kwds, typed) if kwds or typed else args
                with lock:
                    link = cache_get(key)
                    if link is not None:
                        # record recent use of the key by moving it to the front of the list
                        root, = nonlocal_root
                        link_prev, link_next, key, result = link
                        link_prev[NEXT] = link_next
                        link_next[PREV] = link_prev
                        last = root[PREV]
                        last[NEXT] = root[PREV] = link
                        link[PREV] = last
                        link[NEXT] = root
                        stats[HITS] += 1
                        return result
                result = user_function(*args, **kwds)
                with lock:
                    root, = nonlocal_root
                    if key in cache:
                        # getting here means that this same key was added to the
                        # cache while the lock was released.  since the link
                        # update is already done, we need only return the
                        # computed result and update the count of misses.
                        pass
                    elif _len(cache) >= maxsize:
                        # use the old root to store the new key and result
                        oldroot = root
                        oldroot[KEY] = key
                        oldroot[RESULT] = result
                        # empty the oldest link and make it the new root
                        root = nonlocal_root[0] = oldroot[NEXT]
                        oldkey = root[KEY]
                        oldvalue = root[RESULT]
                        root[KEY] = root[RESULT] = None
                        # now update the cache dictionary for the new links
                        del cache[oldkey]
                        cache[key] = oldroot
                    else:
                        # put result in a new link at the front of the list
                        last = root[PREV]
                        link = [last, root, key, result]
                        last[NEXT] = root[PREV] = cache[key] = link
                    stats[MISSES] += 1
                return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stats[HITS], stats[MISSES], maxsize, len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = nonlocal_root[0]
                root[:] = [root, root, None, None]
                stats[:] = [0, 0]

        wrapper.__wrapped__ = user_function
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return update_wrapper(wrapper, user_function)

    return decorating_function


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
