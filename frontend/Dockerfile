FROM node:18-alpine
WORKDIR /app

# zkopíruj package.json a package-lock.json (pokud existuje)
COPY package*.json ./

# použij npm ci pokud existuje lock, jinak npm install
RUN if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi

# zkopíruj zbytek aplikace
COPY . .

# expose a spusť dev server hostovaný na 0.0.0.0
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]
