import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["motive-radiated-cloak.ngrok-free.dev"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
      {
        source: "/auth/:path*",
        destination: "http://localhost:8000/auth/:path*",
      },
    ];
  },
};

export default nextConfig;
