FROM nginx:alpine

RUN apk add watchman --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/

CMD /run.sh

COPY ./notify.sh /notify.sh
COPY ./run.sh /run.sh

RUN chmod +x /run.sh && chmod +x /notify.sh


