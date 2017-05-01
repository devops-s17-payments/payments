# Start with a Linux micro-container to keep the image tiny
FROM alpine:3.3

# Install just the Python runtime (no dev)
RUN apk add --update \
    python \
    py-pip \
    py-gdbm \
    postgresql-dev \ 
    python-dev \
    gcc \ 
    musl-dev \
 && rm -rf /var/cache/apk/*
 #RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/main py-psycopg2

# Expose any ports the app is expecting in the environment
ENV PORT 5000
EXPOSE $PORT

# Set up a working folder and install the pre-reqs
WORKDIR /payments
ADD requirements.txt /payments
RUN pip install -r requirements.txt

# Add the code as the last Docker layer because it changes the most
ADD app /payments/app
ADD run.py /payments
ADD config.py /payments

# Run the service
CMD [ "python", "run.py" ]