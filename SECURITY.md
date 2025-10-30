# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

We take the security of inv-vmware-opa seriously. If you discover a security vulnerability, please follow these steps:

### 🚨 DO NOT create a public GitHub issue

Public disclosure of a security vulnerability can put the entire community at risk. Instead:

1. **Email the maintainers** directly at: [security contact - update with actual email]
2. **Include detailed information:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)
   - Your contact information

### What to Expect

- **Acknowledgment:** We'll acknowledge receipt of your vulnerability report within 48 hours
- **Updates:** We'll keep you informed about the progress of addressing the vulnerability
- **Credit:** We'll credit you for the discovery (if you wish) when we publicly disclose the fix
- **Timeline:** We aim to patch critical vulnerabilities within 7 days, and moderate vulnerabilities within 30 days

## Security Best Practices

When using inv-vmware-opa, please follow these security best practices:

### Database Security

1. **Use Strong Connection Strings**
   - Never hardcode database credentials
   - Use environment variables for sensitive data
   - Restrict database user permissions to minimum required

```bash
# Good - using environment variable
export DB_URL="postgresql://user:password@localhost/vmware_inv"
vmware-inv stats --db-url $DB_URL

# Bad - hardcoding credentials in scripts
vmware-inv stats --db-url "postgresql://admin:admin123@prod-server/vmware"
```

2. **File Permissions**
   - Protect SQLite database files with appropriate permissions
   - Store databases in secure locations

```bash
chmod 600 data/vmware_inventory.db
```

### Input Validation

1. **Excel Files**
   - Only load Excel files from trusted sources
   - Validate file size before processing
   - Be cautious with files from external sources

2. **Database Queries**
   - The application uses SQLAlchemy ORM to prevent SQL injection
   - Never bypass ORM for raw SQL queries without parameterization

### Dashboard Security

1. **Access Control**
   - Run Streamlit dashboard on localhost only in production
   - Use reverse proxy with authentication for external access
   - Never expose dashboard directly to the internet without authentication

```bash
# Good - local only
streamlit run src/dashboard/app.py --server.address localhost

# Requires authentication layer (nginx, etc.)
streamlit run src/dashboard/app.py --server.address 0.0.0.0
```

2. **Data Protection**
   - Dashboard displays sensitive VM inventory data
   - Ensure only authorized users have access
   - Consider network segmentation

### Dependencies

1. **Keep Dependencies Updated**
   ```bash
   # Check for security vulnerabilities
   uv pip install safety
   safety check
   
   # Or use pip-audit
   pip install pip-audit
   pip-audit
   ```

2. **Review Dependency Changes**
   - Review CHANGELOG when updating dependencies
   - Test thoroughly after updates
   - Use version constraints in pyproject.toml

### API Keys and Credentials

1. **Never Commit Secrets**
   - Use environment variables
   - Add sensitive files to .gitignore
   - Use pre-commit hooks to detect secrets

2. **Environment Variables**
   ```bash
   # .env file (add to .gitignore!)
   DB_URL=postgresql://user:password@localhost/db
   VMWARE_API_KEY=your-api-key-here
   ```

## Known Security Considerations

### Data Sensitivity

This application handles VMware infrastructure data which may include:
- Server names and IP addresses
- Network topology information
- Resource allocation details
- Operating system versions

**Recommendations:**
- Treat all inventory data as confidential
- Implement appropriate access controls
- Follow your organization's data classification policies
- Be cautious when sharing reports or exports

### Local Storage

- SQLite databases are stored unencrypted
- Consider disk encryption for sensitive environments
- Implement database backups with encryption
- Secure backup storage locations

### PDF Reports

- PDF reports contain sensitive infrastructure information
- Protect generated reports with appropriate permissions
- Consider PDF password protection for distribution
- Delete temporary reports after use

## Security Features

### Current Protections

- ✅ **SQL Injection Prevention**: Uses SQLAlchemy ORM
- ✅ **Secret Detection**: Pre-commit hooks detect private keys
- ✅ **Input Validation**: Excel file validation
- ✅ **Dependency Scanning**: Optional security scanning with bandit
- ✅ **Version Constraints**: Dependency version upper bounds

### Planned Enhancements

- ⏳ **Rate Limiting**: For API endpoints
- ⏳ **Audit Logging**: Track data access
- ⏳ **Encryption**: Database encryption at rest
- ⏳ **Authentication**: Built-in dashboard authentication
- ⏳ **RBAC**: Role-based access control

## Vulnerability Disclosure Policy

### Responsible Disclosure

We follow coordinated vulnerability disclosure:

1. **Report received** → Acknowledged within 48 hours
2. **Vulnerability confirmed** → Investigation begins
3. **Fix developed** → Patch created and tested
4. **Release prepared** → Security advisory drafted
5. **Public disclosure** → Patch released, advisory published
6. **Credit given** → Reporter credited (if desired)

### Public Disclosure Timeline

- **Critical vulnerabilities**: 7-14 days after patch release
- **High vulnerabilities**: 30 days after patch release
- **Medium/Low vulnerabilities**: 60 days after patch release

We may request early disclosure if a vulnerability is being actively exploited.

## Security Updates

Security updates are released as:
- **Patch versions** for fixes (e.g., 0.5.1 → 0.5.2)
- **Security advisories** on GitHub
- **CHANGELOG.md** entries marked with `[SECURITY]`

Subscribe to repository releases to be notified of security updates.

## Scope

### In Scope

- Authentication and authorization bypasses
- SQL injection vulnerabilities
- Cross-site scripting (XSS) in dashboard
- Remote code execution
- Sensitive data exposure
- Dependency vulnerabilities with proof of exploitability

### Out of Scope

- Denial of service (DOS) attacks
- Social engineering attacks
- Physical security issues
- Issues in dependencies (report to the dependency maintainers)
- Issues requiring local system access or physical access

## Contact

For security concerns, please contact:
- **Email**: [Update with actual security contact]
- **PGP Key**: [Optional - provide PGP key for encrypted communication]

For general questions and non-security bugs, please use GitHub Issues.

## Acknowledgments

We would like to thank the following people for responsibly disclosing security vulnerabilities:

- [List will be updated as vulnerabilities are reported and fixed]

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated:** 2025-10-30
