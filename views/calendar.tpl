% from calendar import TextCalendar
% import datetime
% import re
% setdefault('date', datetime.date.today())
% setdefault('links', False)
<section id="calendar">
  <pre>
    <%
      date = get('date')
      links = get('links')
      calendar = TextCalendar(firstweekday=6).formatmonth(date.year, date.month)

      if links:
          def gen_day_link(match):
              d = date.strftime('%Y-%m-{0:02d}'.format(int(match.group(0))))
              cls = 'current' if date.isoformat() == d else ''
              return '<a class="{0}" href="/{1}/{2}">{3}</a>'.format(cls, channel, 

          re.sub('\b(\d{1,2})\b', gen_day_link, calendar)

      next_month = 
    %>
    {{calendar}}
  </pre>
</section>
