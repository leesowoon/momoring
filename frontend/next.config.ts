import type { NextConfig } from "next";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/v1/:path*", destination: `${backendUrl}/v1/:path*` },
      { source: "/audio/:path*", destination: `${backendUrl}/audio/:path*` },
    ];
  },
};

export default nextConfig;
