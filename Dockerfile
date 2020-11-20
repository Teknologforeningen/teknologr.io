FROM python:3.7-alpine

# Install prereqs
#RUN apt-get update && apt-get install -y libsasl2-dev libldap2-dev libssl-dev libpq-dev
RUN apk update
RUN apk add openssl-dev libpq musl openldap-dev
# Create directories
RUN mkdir -p /var/log/teknologr
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /opt/app/teknologr

# Copy files
COPY requirements.txt start-teknologr.sh /opt/app/
COPY .pip_cache /opt/app/pip_cache/
COPY teknologr /opt/app/teknologr
COPY testenv/test.env /opt/app/teknologr/.env

# Set workdir
WORKDIR /opt/app

# Install pip requirements
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache

# Chown directories
RUN chown -R www-data:www-data /opt/app
RUN chown -R www-data:www-data /var/log/teknologr

# Create logfile
RUN touch /var/log/teknologr/info.log
RUN chmod -R 775 /var/log/teknologr/info.log

#start server
EXPOSE 8010
STOPSIGNAL SIGTERM
CMD ["/opt/app/start-teknologr.sh"]
