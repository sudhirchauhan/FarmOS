const config = {
  // DRF uses trailing-slash routes; avoid redirect loops at the proxy boundary.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.DJANGO_API_ORIGIN || 'http://127.0.0.1:8000'}/api/:path*/` }];
  },
};
export default config;
