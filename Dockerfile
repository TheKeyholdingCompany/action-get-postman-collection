FROM python:alpine3.18
COPY fetch-postman-collection.py /fetch-postman-collection.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
