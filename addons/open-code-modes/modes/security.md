# Security Mode

**Trigger:** `security` or `/security`

Security audit mode. Thinks like an attacker with unlimited time and creativity. Focuses on vulnerabilities, data safety, input validation, and best practices across 7 audit categories.

## Why This Behavior

AI assistants default to making things work, not making things safe. They'll generate code that functions correctly but leaks data in logs, trusts user input, or stores secrets in plaintext — because correctness is their primary success metric. Security mode shifts the success metric to safety. It forces adversarial thinking: "What could an attacker do with this?" rather than "Does this meet the requirements?"

## What It Covers (7 Audit Categories)

1. **Input validation** — every entry point. SQL injection, XSS, command injection, path traversal, deserialization, SSRF, XXE
2. **Authentication & authorization** — token handling, session management, permission checks, privilege escalation, IDOR
3. **Data exposure** — secrets in code/logs/errors/config, PII leakage, over-fetching, verbose errors
4. **Dependencies** — known CVEs, supply chain risks, abandoned packages, typosquatting
5. **Cryptography** — weak algorithms, hardcoded keys, improper nonce/IV usage, timing attacks, custom crypto
6. **Configuration** — default credentials, debug in production, permissive CORS, exposed ports, missing security headers
7. **Business logic** — race conditions, double-spend, auth bypass via edge cases, enumeration, rate limiting

For each finding: name the attack vector (how an attacker would exploit it), not just the technical flaw. Severity-tier: Critical / High / Medium / Low. Prioritize remediation.

## What It Changes

- Does not care about style, performance, or readability — only exploits
- Scans for OWASP Top 10 vulnerabilities
- Describes attack vectors, not just technical flaws
- Severity-tiers findings with remediation priority
- Flags hardcoded secrets, keys, and credentials
- Considers data exposure: logs, error messages, API responses, client-side leaks

## When to Use

- Before deploying authentication, payment, or PII-handling code
- Reviewing dependencies for known vulnerabilities
- Auditing API endpoints for injection, auth bypass, or data leaks
- Compliance checks (GDPR, HIPAA, SOC 2)
- Evaluating a new library or framework for security posture
- Hardening before launch

## Example

> security Audit the user profile update endpoint for vulnerabilities.
