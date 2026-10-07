# React (CRA) frontend. Build context must be the Frontend/Swiggy_Clone/
# directory. Produces a static build served by nginx.
#
# CRA bakes REACT_APP_* values into the JS bundle at BUILD time, not at
# container start — so the public backend/auth URLs must be passed as
# --build-arg when building this image, not as `docker run -e ...`:
#   docker build --build-arg REACT_APP_API_URL=https://api.example.com \
#                --build-arg REACT_APP_AUTH_URL=https://auth.example.com .

FROM node:20-slim AS build
WORKDIR /app

COPY package*.json ./
# --legacy-peer-deps: react-scroll-to-top@1.0.8 declares a peer dependency
# on React 16/17 (its package.json was never updated for React 18), which
# this project's actual React version (18.1.0) conflicts with under npm's
# strict peer-dependency resolution (what `npm ci` enforces by default).
# It works fine with React 18 in practice — the peerDependencies field is
# just stale. Verified this resolves cleanly in isolation before applying.
RUN npm ci --legacy-peer-deps

COPY . .

ARG REACT_APP_API_URL
ARG REACT_APP_AUTH_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_AUTH_URL=$REACT_APP_AUTH_URL
# CRA treats every ESLint warning as a fatal build error whenever CI is
# truthy (this codebase has a long-standing pile of pre-existing ones --
# == vs ===, missing alt text, unused vars -- harmless in dev, but fatal
# here). Many CI/build environments (including, apparently, this image's
# own build step under GitHub Actions) set CI=true ambiently -- pin it to
# false so this build's success never depends on where it's run.
ENV CI=false
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
