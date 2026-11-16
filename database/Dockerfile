FROM postgres:16-alpine

# scripts in this folder run once, the first time the database volume is created
COPY init/ /docker-entrypoint-initdb.d/

# defaults for local use - override them in .env
ENV POSTGRES_DB=brazilian_glow \
    POSTGRES_USER=glow \
    POSTGRES_PASSWORD=change-me

EXPOSE 5432
