FROM python:3
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN mkdir /src
WORKDIR /src
RUN pip install --upgrade pip
COPY requirements/* /src/requirements/
RUN ls -la
RUN pip install -r ./requirements/development.txt
COPY . /src/
