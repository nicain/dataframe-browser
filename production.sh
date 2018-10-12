gunicorn --workers=4 -k gevent --log-level debug --bind 0.0.0.0:5001 autoapp:app
