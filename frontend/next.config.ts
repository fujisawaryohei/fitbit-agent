import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
const fitbitRedirectUri =
  process.env.FITBIT_REDIRECT_URI ?? `${backendUrl}/auth/fitbit/callback`;
const corsOrigins = (process.env.CORS_ORIGINS ?? "")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);

// FITBIT_REDIRECT_URI がバックエンドを直接指していない場合（ngrok等）は
// /auth/:path* をバックエンドにプロキシする
const useAuthProxy = !fitbitRedirectUri.startsWith(backendUrl);

const nextConfig: NextConfig = {
  allowedDevOrigins: corsOrigins,
  async rewrites() {
    const rules = [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];

    // OAuth 開始エンドポイントは常にバックエンドにプロキシ
    rules.push({
      source: "/auth/fitbit",
      destination: `${backendUrl}/auth/fitbit`,
    });

    // コールバックは ngrok 使用時のみプロキシ
    // （localhost 時はバックエンドが直接受け取るため不要。
    //   Next.js 経由にするとリダイレクトを内部で追いかけて Set-Cookie が失われる）
    if (useAuthProxy) {
      rules.push({
        source: "/auth/fitbit/callback",
        destination: `${backendUrl}/auth/fitbit/callback`,
      });
    }

    return rules;
  },
};

export default nextConfig;
