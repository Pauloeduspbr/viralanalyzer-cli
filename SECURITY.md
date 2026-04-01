# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

- **Email**: security@viralanalyzer.com.br
- **Do NOT** open a public issue for security vulnerabilities

We will respond within 48 hours and provide a fix timeline.

## Security Practices

- API keys are stored locally with restricted permissions (0600)
- All API communication is encrypted (HTTPS/TLS)
- No credentials are logged or transmitted to third parties
- Rate limiting protects against abuse (60 req/min per client)
- LGPD compliant: data export and account deletion available

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
