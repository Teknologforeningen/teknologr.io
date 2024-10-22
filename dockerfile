# FROM python:3.10.12-ubuntu22.04.3
FROM ubuntu:22.04
USER root

# Required for older version of docker to solve problem with `RUN apt update`.
# Try removing first and if it works don't worry.
RUN sed -i -e 's/^APT/# APT/' -e 's/^DPkg/# DPkg/' \
    /etc/apt/apt.conf.d/docker-clean

RUN apt update && \
    apt install -y python3.10 && \
    apt install -y python3-pip --upgrade pip && \
    apt install -y git && \ 
    apt install -y locales locales-all

RUN apt install -y  \
    libsasl2-dev  \
    python3-dev \
    libldap2-dev \
    libssl-dev \
    libpq-dev

COPY requirements.txt .

RUN pip install --progress-bar off -r requirements.txt

COPY . .

EXPOSE 8080

ENTRYPOINT [ "python3" ]

RUN ["python3", "teknologr/manage.py", "migrate"]

RUN ["python3", "teknologr/manage.py", "makemigrations", "--check", "--dry-run"]

CMD ["teknologr/manage.py", "runserver", "8888" ]