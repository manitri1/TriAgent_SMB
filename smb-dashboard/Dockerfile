# docs/13-mvp-dashboard-design.md §2: 프론트엔드는 빌드타임에 정적 파일로 번들되어
# FastAPI가 StaticFiles로 서빙한다 — 별도 nginx 컨테이너 없이 컨테이너 1개로 끝낸다.
# 빌드 컨텍스트는 이 파일이 있는 smb-dashboard/ (docker-compose.yml의 `build: ./smb-dashboard`).

FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8652

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8652"]
