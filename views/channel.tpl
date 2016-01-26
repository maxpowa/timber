<li class="{{channel.cssClasses()}}">
  <a href="/{{channel.safe_name()}}{{ '/' + date if defined('date') else '' }}">{{channel.name}}</a>
</li>
