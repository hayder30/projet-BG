FROM nginx:1.27-alpine

# static site
COPY index.html styles.css app.js config.js /usr/share/nginx/html/

# nginx runs every *.sh in this folder before starting
COPY docker-entrypoint.sh /docker-entrypoint.d/40-config.sh
RUN chmod +x /docker-entrypoint.d/40-config.sh

EXPOSE 80
