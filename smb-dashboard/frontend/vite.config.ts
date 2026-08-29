import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 개발 서버(`npm run dev`)에서 프론트만 따로 띄울 때, /api 요청을 백엔드(8652)로 넘긴다.
// 프로덕션 빌드(`npm run build`)는 FastAPI가 정적 파일로 직접 서빙하므로 프록시가 필요 없다.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8652",
    },
  },
});
