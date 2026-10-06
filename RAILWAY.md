# Railway launch checklist

This is a Django application, not a static site. Deploy the web service and a **new** PostgreSQL database in the same Railway project. The old Koyeb/Render database is not used, and its users, investments, and transactions will not appear in the new database.

## 1. Create the services

1. In Railway, create a project from the `smartforgecash/premierbrique` GitHub repository.
2. Add a PostgreSQL database in the same Railway project.
3. In the **web service** Variables tab, add `DATABASE_URL` as a reference to the PostgreSQL service's `DATABASE_URL` (typically `${{Postgres.DATABASE_URL}}`; select the service in Railway rather than typing its password).
4. Add `DEBUG=false` and a fresh, long random `DJANGO_SECRET_KEY`. Do not reuse an old key or commit it to GitHub.
5. The root `Dockerfile` builds the app. `railway.json` runs database migrations before each deploy and uses `/health/` for health checks. If the initial deployment failed before the database existed, redeploy the web service after adding the database reference.
6. In the web service's Settings > Networking, select **Generate Domain**. Check that `https://<generated-domain>/health/` returns `ok`, then load the homepage and registration page.

Railway provides `RAILWAY_PUBLIC_DOMAIN` automatically for its generated domain. Leave `SITE_URL` unset while using that domain. When you connect the purchased custom domain, set `SITE_URL=https://your-domain.example` (no trailing slash), add the domain in Railway Networking, and set its DNS records exactly as Railway instructs. Add `www` as a second Railway domain if you want it, and configure its redirect. If your domain is not covered automatically, use `DJANGO_ALLOWED_HOSTS` for extra hostnames and `DJANGO_CSRF_TRUSTED_ORIGINS` for their full `https://` origins (comma separated).

## 2. Google sign-in and admin

If you use Google sign-in, set `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` and `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET` in the web service. In the matching Google OAuth web client, add the exact authorized redirect URI `https://<generated-domain>/auth/complete/google-oauth2/`. Later also add `https://your-domain.example/auth/complete/google-oauth2/`. Add the corresponding origins without paths. Do not delete old entries until the new sign-in has been tested. Update any Google OAuth consent-screen authorized-domain settings required for the new domain.

Once the database is live, create a new administrator with `python manage.py createsuperuser` from the Railway service shell, then visit `/admin/`. No admin account is created from a default password. Configure an SMTP provider before relying on email delivery; the default email backend discards mail.

## 3. Mollie: card and SEPA bank transfer

The site offers both `creditcard` and `banktransfer` through Mollie Checkout. In the Mollie dashboard, make sure **Cards** and **SEPA Bank Transfer** are both activated for your website profile. For a real-money launch, the Mollie profile must be approved and have a working **live** API key. Never send the live key in chat or commit it to GitHub.

Set these variables on the Railway **web service**:

```text
MOLLIE_API_KEY=live_...           # paste privately in Railway
MOLLIE_PAYMENTS_ENABLED=true
```

The app creates a per-payment `redirectUrl` and `webhookUrl` automatically from `SITE_URL`, or from the incoming public Railway domain while `SITE_URL` is unset. After connecting the final domain, setting `SITE_URL` is normally enough; optional overrides are `MOLLIE_REDIRECT_BASE_URL` and `MOLLIE_WEBHOOK_URL`. The webhook endpoint is `/payments/mollie/webhook/`. It must be publicly reachable by Mollie. You do **not** need to configure a global Mollie webhook just for this Payments API flow: each payment supplies its own URL. You can change the webhook URL later for **new** payments. Keep the old service reachable for any still-pending bank transfers created with its old webhook URL, or reconcile those payments manually before shutting it down.

Do one small card payment and one SEPA bank transfer test end to end. Bank transfers may remain pending for days; the wallet is credited only after Mollie confirms `paid`, not when the customer merely starts the transfer. Check the Mollie dashboard, wallet transaction, and Railway logs. If a method is unavailable, verify that it is enabled in Mollie for the live profile and country/currency.

## 4. Before inviting real investors

- A fresh database means **no previous accounts or investments are recovered**. Reconcile any actual past payments before accepting new ones.
- Confirm the legal/regulated status of the investment offering, privacy notice, identity verification, and data retention for your target countries. The current application does not enforce email verification and stores identity documents in the database; review these flows before handling real customers.
- Set up PostgreSQL backups and test a restore. Do not rely on the web container's filesystem for persistent data.
- Test registration, Google sign-in, project browsing, both Mollie payment methods, webhook completion, and the Django admin on the final domain.

Official references: [Railway Django](https://docs.railway.com/guides/django), [Railway PostgreSQL](https://docs.railway.com/databases/postgresql), [Railway pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command), [Mollie payment methods](https://docs.mollie.com/docs/payment-methods).
