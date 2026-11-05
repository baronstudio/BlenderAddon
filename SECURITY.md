# Security Policy

## Supported versions

Only the latest version on the `master` branch receives fixes.

## Reporting a vulnerability

**Please don't open a public issue for security problems**, for example a leaked API key, unsafe file handling, or code execution from a crafted `.blend` or preset file.

Instead, report it privately:

- Use GitHub's **[private vulnerability reporting](https://github.com/baronstudio/BlenderAddon/security/advisories/new)**, or
- Email **tech4artconseil@gmail.com** with the subject `[SECURITY] BlenderAddon`.

You should get a reply within 7 days. Once the issue is fixed, you'll be credited in the release notes unless you'd rather stay anonymous.

## Note on AI features

T4A 3D Files QC Check can call the Google Gemini API. Your API key is stored in your local Blender preferences. Never paste it into an issue, a screenshot or a shared `.blend` file.
