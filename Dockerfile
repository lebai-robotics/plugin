FROM registry.cn-shanghai.aliyuncs.com/lebai/util:14.04

WORKDIR /app
COPY . .

ARG AWS_ENDPOINT
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

RUN bash ./ci.sh
