gunicorn --workers=1 -k gevent --log-level debug --bind 0.0.0.0:5000 autoapp:app
