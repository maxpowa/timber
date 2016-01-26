<div class="{{message.cssClass}}">
  <a href="#{{message.timestamp}}" name="{{message.timestamp}}">{{message.pretty_time()}}</a>
    % if message.intent == 'PRIVMSG':
      <span class="nickname">&lt;{{message.nick}}&gt;</span>
    % end
    {{message.text()}}
  <br>
</div>
