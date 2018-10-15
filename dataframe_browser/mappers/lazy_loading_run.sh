gunicorn --workers=4 -k gevent --log-level debug --bind 0.0.0.0:5050 lazy_loading_server:app
