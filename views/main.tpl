% import datetime
% setdefault('date', datetime.date.today())
% setdefault('links', True if defined('channel') else False)
<section id="channels">
  % include('calendar.tpl', links=get('links', True))
  % include('channel_list.tpl', channels=channels, date=get('date').isoformat())
</section>
% include('message_list.tpl' if defined('messages') else 'console_msg.tpl', messages=get('messages', None))

% rebase layout
