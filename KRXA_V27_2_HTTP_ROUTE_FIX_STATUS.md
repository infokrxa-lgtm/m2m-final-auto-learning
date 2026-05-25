# KRXA V27.2 HTTP ROUTE FIX

Fixes Render crash from Flask-style @app.route in a http.server based app.

Changes:
- Removed Flask decorators.
- /api/krxai/thinking/status handled inside KRXAHandler.do_GET.
- /api/krxai/thinking handled inside KRXAHandler.do_POST.
- Thinking response uses ROOT→MEMORY→JUDGEMENT→LOOP structured engine.
