from python:3.7

COPY . /app/
WORKDIR /app/
RUN pip install -r /app/retranslator/requirements.txt
# logs redirected to stdout. it's for demo.sh
RUN sed -e '/retranslator\.log/d' /app/retranslator/config.cfg
