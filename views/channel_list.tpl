<ul>
  <li class="">
    <a href="/">Console</a>
  </li>
  % for chan in channels:
    % include('channel.tpl', channel=chan, date=date)
  % end
</ul>
