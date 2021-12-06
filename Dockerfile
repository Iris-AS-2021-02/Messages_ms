FROM python:3.8
COPY . /src
WORKDIR /src
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install flask-pymongo
RUN python -m pip install "pymongo[srv]"
RUN python -m pip install pika
EXPOSE 8085
ENTRYPOINT [ "python", "src/app.py"]
