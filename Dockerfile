FROM python:alpine3.18
COPY fetch-postman-collection.py /fetch-postman-collection.py
ENTRYPOINT ["/entrypoint.sh"]
