#!/bin/sh

/notify.sh &
nginx -g "daemon off;"
