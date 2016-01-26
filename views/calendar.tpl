% from timber.utils import get_calendar
<section id="calendar">
  <pre>{{ !get_calendar(get('channel', '').replace('#', ','), get('date', datetime.date.today()), get('links', False)) }}</pre>
</section>
