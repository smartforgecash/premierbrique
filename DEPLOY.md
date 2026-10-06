# Legacy deployment notes (Google Cloud Run + Firebase Hosting)

For the current Railway launch with a new PostgreSQL database and Mollie card + bank transfer payments, use [RAILWAY.md](RAILWAY.md). The instructions below are historical and may no longer apply.

Free at your traffic level, allows commercial use, and supports your Namecheap domain.
Budget ~45 minutes of work plus DNS propagation.

Why this stack:
- **Cloud Run** always-free tier: 2M requests, 400,000 vCPU-seconds, 1 GB egress per month.
- **Firebase Hosting** provides the custom domain + free TLS + a CDN. Cloud Run's own
  domain mapping is still preview and Google states it is "not production-ready".
- The CDN matters: `staticfiles/` is 4.8 MB, and Cloud Run's free egress is only 1 GB/month.
  Firebase caches the hashed static assets so they mostly stop costing egress.

Your app is a clean fit: no media uploads, WhiteNoise serves static, and state lives
entirely in the external Postgres you already have.

---

## 0. First, two minutes on Render (optional but worth it)

Log into Render and read the suspension notice. If it says *billing* or *free-tier limits*,
that may be fixable in minutes. If it mentions **terms of service or abuse review**, read
the "Read this before you rely on a free tier" section at the bottom of this file — it
changes what you should do.

## 1. Install the CLIs

Google Cloud CLI (Windows installer):
https://cloud.google.com/sdk/docs/install

Then, in a fresh PowerShell window:

```bash
gcloud version
```

Firebase CLI (needs Node.js):

```bash
npm install -g firebase-tools
```

## 2. Create the project and attach billing

```bash
gcloud auth login
```

```bash
gcloud projects create premierbrique-prod --name="Premier Brique"
```

```bash
gcloud config set project premierbrique-prod
```

Now link a billing account in the console (card required for verification; the free tier
still applies): https://console.cloud.google.com/billing/linkedaccount

**Set a budget alert immediately** so "free" stays free —
https://console.cloud.google.com/billing/budgets → Create budget → amount **$1** →
alert at 50%/90%/100%. This emails you long before any real charge.

## 3. Enable the APIs

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## 4. Fill in your secrets

Copy the template and edit it with real values:

```bash
cp env.yaml.example env.yaml
```

Generate a fresh `DJANGO_SECRET_KEY` (don't reuse the Render one — treat it as exposed):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste that plus your real `DATABASE_URL`, Stripe keys, Google OAuth keys, and SMTP
settings into `env.yaml`. It is gitignored and excluded from the Docker image.

## 5. Run migrations once, from your machine

The container deliberately does **not** run `migrate` on start — every scaled instance
would race the others. Run it yourself against the same database:

```bash
$env:DATABASE_URL = "postgres://USER:PASSWORD@HOST:PORT/DBNAME"; python manage.py migrate
```

## 6. Deploy to Cloud Run

```bash
gcloud run deploy premierbrique --source . --region europe-west1 --allow-unauthenticated --env-vars-file env.yaml --memory 512Mi --max-instances 3 --min-instances 0 --timeout 60
```

Notes on those flags:
- `europe-west1` (Belgium) — low latency for France and supported by Firebase rewrites.
- `--max-instances 3` caps any runaway scaling, so a traffic spike can't produce a bill.
- `--min-instances 0` keeps it free; the tradeoff is a ~2–5 second cold start after idle.
- `--allow-unauthenticated` is required — Firebase Hosting must be able to invoke it.

The first build takes 5–8 minutes. When it finishes you get a `https://…run.app` URL.
Open it and confirm the site loads (`.run.app` is already in `ALLOWED_HOSTS`).

Check `https://YOUR-URL.run.app/health/` too.

## 7. Put Firebase Hosting in front

```bash
firebase login
```

```bash
firebase use --add
```

Pick `premierbrique-prod` and give it the alias `prod`. `firebase.json` is already
configured to rewrite every request to the `premierbrique` service in `europe-west1`.

```bash
firebase deploy --only hosting
```

You now have a working `https://premierbrique-prod.web.app`. Test login on it before
touching DNS.

## 8. Connect the Namecheap domain

In the Firebase console → Hosting → **Add custom domain** → enter `premierbrique.com`,
then repeat for `www.premierbrique.com`. Firebase gives you a TXT record for verification
and two A records.

In Namecheap → Domain List → Manage → **Advanced DNS**:
- Add the TXT record Firebase asks for.
- Set `@` to the two **A records** Firebase provides (delete the old Render records).
- Set `www` to an **A record** pair as well, or CNAME per Firebase's instructions.
- Do **not** use Namecheap's "URL Redirect Record" — it breaks TLS provisioning.

DNS propagates in ~30 minutes; Firebase then issues the certificate (usually under an
hour, occasionally up to 24). Verify with:

```bash
nslookup premierbrique.com
```

## 9. Update the two external integrations

Both point at your old Render URL and will silently break:

1. **Google OAuth** — https://console.cloud.google.com/apis/credentials → your OAuth
   client → Authorized redirect URIs → add
   `https://premierbrique.com/auth/complete/google-oauth2/`
   (and the `.web.app` equivalent while testing).
2. **Stripe webhook** — https://dashboard.stripe.com/webhooks → point the endpoint at
   `https://premierbrique.com/wallet/deposit/webhook/`. The signing secret changes if you
   create a new endpoint, so update `STRIPE_WEBHOOK_SECRET` in `env.yaml` and redeploy.

## Redeploying later

```bash
gcloud run deploy premierbrique --source . --region europe-west1 --env-vars-file env.yaml
```

Firebase Hosting only needs redeploying if `firebase.json` changes.

Logs:

```bash
gcloud run services logs read premierbrique --region europe-west1 --limit 50
```

---

## Read this before you rely on a free tier

You don't know why Render suspended you, and that matters more than the migration itself.
This site takes investment money from the public and displays an IBAN. Automated
trust-and-safety systems at free hosts frequently flag finance and investment sites as
possible fraud, and a free tier gets suspended first and reviewed later — that is the most
likely explanation for a suspension arriving with no clear warning.

If that is what happened, Cloud Run is a genuine improvement (Google reviews a billed
account far less trigger-happily than a free Render service), but the durable fix for a
site that handles money is a paid host where you are a customer: a €4–5/month Hetzner or
similar VPS, or Cloud Run with `--min-instances 1`. On a paid plan a dispute becomes a
support ticket instead of a dead site.

Two related notes:
- **Vercel is not an option here** despite `.vercel.app` sitting in `ALLOWED_HOSTS`. Its
  Hobby tier prohibits commercial use, so you would be trading one suspension for another.
- **Get your data out on a schedule.** Your Postgres is external, which already saved you
  this time. Keep it that way and take periodic `pg_dump` backups.
