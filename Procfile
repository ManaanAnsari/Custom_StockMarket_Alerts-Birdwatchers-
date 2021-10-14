web: gunicorn telelogin.wsgi --timeout 480 --keep-alive 5 --log-level debug
worker:  cd alerts/ && python alerts_main.py 