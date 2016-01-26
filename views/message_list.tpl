<section id="log">
  % for message in messages:
    % include('message.tpl', message=message)
  % end
  {{ 'It sure is quiet here...' if len(messages) < 1 else '' }}
</section>
