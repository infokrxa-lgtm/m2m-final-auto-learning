# KRXA FULL WEB SERVER WRAP v13

Status: READY

Routes:
- `/` -> index.html
- `/user` -> samples/m2m/user/user_ui.html
- `/multi` -> samples/m2m/user/multi_user_ui.html
- `/control` -> admin/control_ui.html
- `/api/state` -> multi room state JSON
- `/api/send` -> message send API
- `/api/health` -> service health

Render start command:

```text
python app.py
```

The server binds to `0.0.0.0:$PORT`, which is required by Render.
