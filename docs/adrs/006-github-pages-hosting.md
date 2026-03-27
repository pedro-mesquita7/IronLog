# ADR 006: GitHub Pages Hosting

## Status
Accepted

## Context
The React PWA needs hosting. Options: S3 + CloudFront, Vercel/Netlify, GitHub Pages.

## Decision
Use GitHub Pages with the `gh-pages` branch. The PWA is built with Vite and deployed via `peaceiris/actions-gh-pages` in CI/CD. HashRouter is used instead of BrowserRouter to avoid SPA 404 issues (GitHub Pages doesn't support URL rewrites).

## Consequences
- **Positive**: Free hosting, zero configuration, automatic HTTPS
- **Positive**: Deployment is a simple branch push from CI/CD
- **Negative**: No server-side configuration (no redirects, no custom headers) — mitigated by HashRouter
- **Negative**: No CloudFront CDN (AWS account not verified) — acceptable for single-user, EU-based access
