% import datetime
% setdefault('date', datetime.date.today())
<section id="channels">
  % include('calendar.tpl')
  % include('channel_list.tpl', channels=channels, date=get('date').isoformat())
</section>
% include('message_view.tpl' if defined('messages') else 'console_msg.tpl', messages=get('messages', None))

% rebase layout
