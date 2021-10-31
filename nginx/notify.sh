#!/bin/sh

INOTIFY_FOLDER='/etc/nginx'
INOTIFY_COMMAND='nginx -t && nginx -s reload'

watchman -U /tmp/nginx --logfile /dev/stdout -- trigger ${INOTIFY_FOLDER} watch -- /bin/sh -c "echo $@ && sleep 2 && ${INOTIFY_COMMAND}";

