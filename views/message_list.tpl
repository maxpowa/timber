<section id="log">
  % for message in messages:
    % include('message.tpl', message=message)
  % end
  {{ 'It sure is quiet here...' if len(messages) < 1 else '' }}
</section>
<script>
  var chat = document.getElementById('log');
  var config = {
    stripPrefix: false,
    email: false,
    twitter: false,
    truncate: {
      length: 48,
      location: 'smart'
    },
    urls: {
      schemeMatches: true,
      wwwMatches: true,
      tldMatches: false
    }
  };
  chat.innerHTML = Autolinker.link( chat.innerHTML, config );
</script>
