# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by emailing the maintainer directly rather than opening a public issue.

**Email**: Create a private security advisory at https://github.com/gsaugg/compare/security/advisories/new

## Scope

**In scope:**

- The web scraper (`scripts/`)
- The static frontend (`src/`)
- GitHub Actions workflows (`.github/`)
- Dependencies (npm, pip)

**Out of scope:**

- The external stores being scraped (report issues to those vendors directly)
- Third-party services (GitHub Pages, Tailscale)

## Supported Versions

Only the latest version on the `main` branch is supported with security updates.

## Security Measures

This project uses:

- Dependabot for automated dependency updates
- GitHub secret scanning
- CodeQL static analysis
