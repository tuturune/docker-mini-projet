FROM ubuntu:latest
LABEL authors="tonyp"

ENTRYPOINT ["top", "-b"]