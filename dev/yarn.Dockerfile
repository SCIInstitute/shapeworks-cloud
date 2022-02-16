FROM node:latest

WORKDIR /app/server
RUN yarn install
CMD yarn serve
