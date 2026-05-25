# KRXA V27.1 ROUTE NAME FIX

Fixes Render crash:

NameError: name 'app' is not defined at aapp.route(...)

Cause: route decorator typo/corruption in app.py.

Fix: replace aapp.route(...) with @app.route(...).
