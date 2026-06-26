import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow cross-origin requests to the FastAPI backend in dev
  async rewrites() {
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
