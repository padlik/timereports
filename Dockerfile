FROM  python:3.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --update bash python3-dev postgresql-client postgresql-dev build-base mariadb-connector-c-dev libxml2 libxml2-dev libxslt libxslt-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./runthread.py" ]

