FROM  python:3.7

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN  apt-get update && apt-get install -y postgresql-client \
     && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false -o APT::AutoRemove::SuggestsImportant=false

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./runthread.py" ]

