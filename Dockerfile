FROM nginx:alpine
RUN apk add --no-cache python3
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY app/ /usr/share/nginx/html/
COPY config/ /config/
COPY proxy.py /proxy.py
EXPOSE 80
CMD ["sh", "-c", "python3 /proxy.py & nginx -g 'daemon off;'"]
