FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY app/ /usr/share/nginx/html/
COPY config/ /config/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
