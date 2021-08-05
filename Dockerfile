FROM python:3.6.8

RUN apt update && apt install -y libgeos-dev

COPY rdx-0.0.8-py3-none-any.whl .

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install rdx-0.0.8-py3-none-any.whl && \
    pip install -r requirements.txt

RUN adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    "diycam"

USER diycam

WORKDIR /home/diycam

COPY --chown=diycam:diycam usecase.py usecase.py

COPY --chown=diycam:diycam database database

CMD [ "python3", "usecase.py" ]

