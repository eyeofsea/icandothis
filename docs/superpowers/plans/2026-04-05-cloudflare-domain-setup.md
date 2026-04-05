# Cloudflare Domain Setup for GCP Cloud Run

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect `vints.ai` (frontend) and `api.vints.ai` (backend) via Cloudflare DNS to GCP Cloud Run services.

**Architecture:** Cloudflare DNS proxied CNAME records pointing to Cloud Run custom domain mappings. Cloud Run handles SSL termination for the custom domains. Cloudflare provides CDN caching, DDoS protection, and edge security with SSL mode set to "Full (Strict)" since Cloud Run provides valid certificates via Google-managed SSL.

**Tech Stack:** Cloudflare DNS, GCP Cloud Run custom domain mapping, Google-managed SSL certificates

---

## Prerequisites

- Cloudflare account with `vints.ai` zone configured
- Cloudflare MCP server connected (already done)
- GCP project `scm-risk-platform` with Cloud Run services deployed (already done)
- `gcloud` CLI authenticated (already done)

---

### Task 1: Verify Cloudflare Zone for vints.ai

**Files:** None (DNS configuration only)

- [ ] **Step 1: List Cloudflare zones to confirm vints.ai exists**

Use Cloudflare MCP to list zones and find the zone ID for `vints.ai`.

```bash
# Or via CLI if MCP unavailable:
curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=vints.ai" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json"
```

Expected: Zone found with `name: vints.ai` and a zone ID.

- [ ] **Step 2: List existing DNS records for vints.ai**

Check what DNS records already exist to avoid conflicts.

Expected: Note any existing A/AAAA/CNAME records for `vints.ai` and `api.vints.ai`.

---

### Task 2: Map Custom Domain to Cloud Run Frontend (vints.ai)

**Files:** None (GCP configuration only)

- [ ] **Step 1: Verify domain ownership in GCP**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' domains verify vints.ai --project=scm-risk-platform"
```

This may open a browser for domain verification via Google Search Console. Follow the prompts to verify ownership.

- [ ] **Step 2: Map vints.ai to Cloud Run frontend service**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' beta run domain-mappings create --service=scm-risk-web --domain=vints.ai --region=asia-northeast3 --project=scm-risk-platform"
```

Expected: Domain mapping created. Note the CNAME target (e.g., `ghs.googlehosted.com.`).

- [ ] **Step 3: Verify the mapping was created**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' beta run domain-mappings describe --domain=vints.ai --region=asia-northeast3 --project=scm-risk-platform"
```

Expected: Shows `resourceRecords` with the CNAME target to use in Cloudflare.

---

### Task 3: Map Custom Domain to Cloud Run Backend (api.vints.ai)

**Files:** None (GCP configuration only)

- [ ] **Step 1: Map api.vints.ai to Cloud Run backend service**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' beta run domain-mappings create --service=scm-risk-api --domain=api.vints.ai --region=asia-northeast3 --project=scm-risk-platform"
```

Expected: Domain mapping created with CNAME target.

- [ ] **Step 2: Verify the mapping**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' beta run domain-mappings describe --domain=api.vints.ai --region=asia-northeast3 --project=scm-risk-platform"
```

Expected: `resourceRecords` showing type CNAME with target `ghs.googlehosted.com.`

---

### Task 4: Configure Cloudflare DNS Records

**Files:** None (Cloudflare DNS configuration)

- [ ] **Step 1: Add CNAME record for vints.ai (frontend)**

Using Cloudflare MCP or dashboard, create DNS record:
- Type: `CNAME`
- Name: `@` (root domain)
- Target: `ghs.googlehosted.com`
- Proxy: **ON** (orange cloud) — enables Cloudflare CDN/security
- TTL: Auto

Note: Cloudflare supports CNAME flattening at the root, so a CNAME for `@` works.

- [ ] **Step 2: Add CNAME record for api.vints.ai (backend)**

Create DNS record:
- Type: `CNAME`
- Name: `api`
- Target: `ghs.googlehosted.com`
- Proxy: **ON** (orange cloud)
- TTL: Auto

- [ ] **Step 3: Verify DNS records were created**

```bash
dig vints.ai CNAME +short
dig api.vints.ai CNAME +short
```

Expected: Both resolve (may show Cloudflare IPs if proxied).

---

### Task 5: Configure Cloudflare SSL Settings

**Files:** None (Cloudflare configuration)

- [ ] **Step 1: Set SSL mode to Full (Strict)**

In Cloudflare dashboard or via MCP:
- Navigate to SSL/TLS settings for `vints.ai`
- Set encryption mode to **Full (Strict)**

This ensures end-to-end encryption: Browser → Cloudflare (Cloudflare cert) → Cloud Run (Google-managed cert).

- [ ] **Step 2: Enable "Always Use HTTPS"**

- Navigate to SSL/TLS > Edge Certificates
- Enable "Always Use HTTPS"

- [ ] **Step 3: Enable "Automatic HTTPS Rewrites"**

- Navigate to SSL/TLS > Edge Certificates
- Enable "Automatic HTTPS Rewrites"

---

### Task 6: Update Application Configuration

**Files:**
- Modify: `backend/app/config.py`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add vints.ai to backend CORS origins**

In `backend/app/config.py`, add the custom domain to CORS:

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "https://scm-risk-web-1057913091051.asia-northeast3.run.app",
    "https://vints.ai",
    "https://www.vints.ai",
]
```

- [ ] **Step 2: Update frontend API base URL**

In `frontend/src/lib/api.ts`, update the API URL to use the custom domain in production:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.vints.ai';
```

- [ ] **Step 3: Rebuild and deploy backend with CORS update**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' builds submit --tag=asia-northeast3-docker.pkg.dev/scm-risk-platform/scm-risk/backend:latest ./backend --project=scm-risk-platform"

powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' run services update scm-risk-api --image=asia-northeast3-docker.pkg.dev/scm-risk-platform/scm-risk/backend:latest --region=asia-northeast3 --project=scm-risk-platform"
```

- [ ] **Step 4: Rebuild and deploy frontend with API URL update**

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' builds submit --tag=asia-northeast3-docker.pkg.dev/scm-risk-platform/scm-risk/frontend:latest ./frontend --project=scm-risk-platform"

powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' run services update scm-risk-web --image=asia-northeast3-docker.pkg.dev/scm-risk-platform/scm-risk/frontend:latest --region=asia-northeast3 --project=scm-risk-platform --update-env-vars='NEXT_PUBLIC_API_URL=https://api.vints.ai'"
```

- [ ] **Step 5: Commit changes**

```bash
git add backend/app/config.py frontend/src/lib/api.ts
git commit -m "feat: add vints.ai custom domain CORS and API URL"
```

---

### Task 7: Verify End-to-End

- [ ] **Step 1: Wait for Google-managed SSL certificates**

SSL certificates may take 15-30 minutes to provision. Check status:

```bash
powershell.exe -Command "& 'C:\Users\Joseph\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd' beta run domain-mappings describe --domain=vints.ai --region=asia-northeast3 --project=scm-risk-platform"
```

Look for `certificateStatus: ACTIVE`.

- [ ] **Step 2: Test frontend**

```bash
curl -s -o /dev/null -w "%{http_code}" https://vints.ai
```

Expected: `200`

- [ ] **Step 3: Test backend API**

```bash
curl -s https://api.vints.ai/health
```

Expected: `{"status":"healthy","services":{"neo4j":"connected","redis":"connected"}}`

- [ ] **Step 4: Test CORS from frontend domain**

```bash
curl -s -H "Origin: https://vints.ai" -H "Access-Control-Request-Method: GET" -X OPTIONS https://api.vints.ai/api/projects -I | head -10
```

Expected: `Access-Control-Allow-Origin: https://vints.ai`

---

## Optional: Cloudflare Performance Tuning

After verification passes, consider enabling:
- **Caching Rules:** Cache static assets from frontend (CSS, JS, images)
- **Page Rules:** Set `api.vints.ai/*` to bypass cache (API responses should not be cached)
- **Rate Limiting:** Protect API endpoints from abuse
- **WAF:** Enable Cloudflare Web Application Firewall rules
