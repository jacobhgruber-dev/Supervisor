# Security Mode

**Trigger:** `security` or `/security`

Security audit mode. Focuses on vulnerabilities, data safety, input validation, and best practices.

## Why This Behavior

AI assistants default to making things work, not making things safe. They'll generate code that functions correctly but leaks data in logs, trusts user input, or stores secrets in plaintext — because correctness is their primary success metric. Security mode shifts the success metric to safety. It forces the AI to think adversarially: "What could an attacker do with this?" rather than "Does this meet the requirements?" This matters most for auth, payment, PII, and any public-facing endpoint where a security bug isn't a bug — it's an incident.

## When to Use

- Before deploying authentication, payment, or PII-handling code
- Reviewing dependencies for known vulnerabilities
- Auditing API endpoints for injection, auth bypass, or data leaks
- Compliance checks (GDPR, HIPAA, SOC 2)
- Evaluating a new library or framework for security posture

## What It Changes

- Scans for OWASP Top 10 vulnerabilities (injection, XSS, auth failures, etc.)
- Checks input validation, output encoding, and sanitization
- Flags hardcoded secrets, keys, and credentials
- Reviews authentication and authorization logic
- Evaluates dependency risks and supply chain security
- Considers data exposure: logs, error messages, API responses

## Example

> security Audit the user profile update endpoint for vulnerabilities.
