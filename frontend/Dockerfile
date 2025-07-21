# frontend/Dockerfile
# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
#CMD cp -r build result_build
CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]