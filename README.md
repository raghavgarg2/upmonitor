# Uptime Monitor

## Email alerts

The app uses Django's console email backend by default, so alerts appear in the
Celery worker terminal during local development. To send real emails, copy
`.env.example` to `.env` and set the SMTP values supplied by your email provider.

For production, use:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-provider-smtp-host
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=alerts@yourdomain.com
```

Do not commit `.env`; it contains credentials.
