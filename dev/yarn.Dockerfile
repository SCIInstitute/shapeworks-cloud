FROM node:latest

WORKDIR /app/server
RUN echo here!
RUN yarn install
CMD yarn serve
