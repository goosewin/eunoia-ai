import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://localhost:5328/api/:path*' 
          : 'http://api:5328/api/:path*',
      },
      {
        source: '/socket.io/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://localhost:5328/socket.io/:path*' 
          : 'http://api:5328/socket.io/:path*',
      }
    ]
  },
};

export default nextConfig;
