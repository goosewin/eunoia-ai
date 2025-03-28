import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://localhost:5328/api/:path*'  // For local development without Docker
          : 'http://api:5328/api/:path*',       // For Docker environment
      },
      {
        source: '/socket.io/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://localhost:5328/socket.io/:path*'  // For local development
          : 'http://api:5328/socket.io/:path*',       // For Docker environment
      }
    ]
  },
};

export default nextConfig;
