#! /bin/sh
cd /var/wsgi
tar -zcvf $1 xml --exclude=imdb\* --exclude=session-\*
