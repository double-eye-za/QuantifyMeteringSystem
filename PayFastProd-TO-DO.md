# PayFast Production To-Do

Everything needed to go from the current working sandbox integration to production-ready PayFast payments.

---

## 1. PayFast Account & Credentials

- [ ] **Create a live PayFast merchant account** at [payfast.co.za](https://www.payfast.co.za) (if not already done)
- [ ] **Complete merchant verification** — PayFast requires ID, proof of address, and bank confirmation before activating live payments
- [ ] **Get your live credentials** from the PayFast dashboard:
  - Merchant ID
  - Merchant Key
  - Set a passphrase under Settings → Security
- [ ] **Set the live notify_url** in PayFast dashboard settings (optional — we pass it per transaction, but having a default is a good fallback)

---

## 2. Environment Variables

Set these on your production server (DO NOT commit live credentials to git):

```env
PAYFAST_MERCHANT_ID=<your_live_merchant_id>
PAYFAST_MERCHANT_KEY=<your_live_merchant_key>
PAYFAST_PASSPHRASE=<your_live_passphrase>
PAYFAST_SANDBOX=false
PAYFAST_PROCESS_URL=https://www.payfast.co.za/eng/process
PAYFAST_VALIDATE_URL=https://www.payfast.co.za/eng/query/validate
```

> **Important:** When `PAYFAST_SANDBOX=false`, the ITN webhook will perform server-to-server verification with PayFast AND the sandbox-confirm endpoint will be disabled.

---

## 3. Server / Networking

- [ ] **Ensure `/api/payfast/notify` is publicly accessible** — PayFast's servers must be able to POST to this URL. No firewall/WAF rules blocking it.
- [ ] **Allow PayFast IP ranges** — If you use IP whitelisting, resolve these hostnames and allow them:
  - `www.payfast.co.za`
  - `w1w.payfast.co.za`
  - `w2w.payfast.co.za`
- [ ] **HTTPS required** — PayFast requires all URLs (notify, return, cancel) to be served over HTTPS
- [ ] **Verify `url_for(_external=True)` generates correct public URLs** — Flask needs to know its public hostname. Set `SERVER_NAME` or use a reverse proxy that sets `X-Forwarded-Host` / `X-Forwarded-Proto` headers, and configure Flask with `ProxyFix`:
  ```python
  from werkzeug.middleware.proxy_fix import ProxyFix
  app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
  ```

---

## 4. Security Hardening

- [ ] **Add PayFast source IP validation to the ITN webhook** — Currently we validate the signature and do server-to-server verification, but we don't check that the POST actually came from PayFast's IP ranges. This is PayFast's recommended 3rd check. Resolve the PayFast hostnames above via DNS and compare `request.remote_addr`.
- [ ] **Add amount verification to the ITN webhook** — Verify that `amount_gross` in the PayFast POST matches `txn.amount`. This prevents an attacker from paying a lower amount and triggering a full credit. (PayFast recommends this as their 4th check.)
- [ ] **Rate-limit the ITN endpoint** — Prevent abuse with a rate limiter (e.g. Flask-Limiter). Something like 30 requests/minute is reasonable.
- [ ] **CSRF exemption** — If you add CSRF protection globally (Flask-WTF), the `/api/payfast/notify` endpoint must be exempt since it receives external POSTs from PayFast servers.
- [ ] **Remove or disable the sandbox-confirm endpoint** — Currently it's gated behind `PAYFAST_SANDBOX=true`, so it's already disabled in production. But consider removing it entirely from the codebase before deploying to production for defence in depth.

---

## 5. Celery / Background Tasks

- [ ] **Ensure the `payments` queue is consumed** — The Celery worker must listen on the `payments` queue for the expiry task:
  ```bash
  celery -A celery_app.celery worker --queues=notifications,prepaid,payments --loglevel=info
  ```
- [ ] **Ensure Celery Beat is running** — The `expire_stale_payfast_transactions` task runs every 30 minutes via Beat:
  ```bash
  celery -A celery_app.celery beat --loglevel=info
  ```
- [ ] **Test the expiry task** — Verify that pending PayFast transactions older than 1 hour are correctly marked as `expired`

---

## 6. Database

- [ ] **Add index on `transactions.reference`** — The ITN webhook looks up transactions by `filter_by(reference=m_payment_id)`. This should be indexed for fast lookups at scale:
  ```sql
  CREATE INDEX ix_transactions_reference ON transactions (reference);
  ```
  Or via Alembic migration:
  ```python
  op.create_index('ix_transactions_reference', 'transactions', ['reference'])
  ```
- [ ] **Add index on `transactions.payment_gateway` + `status`** — The expiry task and cancel page query by these fields:
  ```sql
  CREATE INDEX ix_transactions_gateway_status ON transactions (payment_gateway, status);
  ```

---

## 7. Monitoring & Logging

- [ ] **Set up alerts for ITN failures** — Monitor logs for:
  - `PayFast ITN signature validation failed` — could indicate tampering
  - `PayFast server-to-server verification failed` — network or config issue
  - `TRANSACTION NOT FOUND` — mismatch between portal and PayFast
  - `WALLET NOT FOUND` — data integrity issue
- [ ] **Monitor pending transaction count** — Alert if pending PayFast transactions pile up (indicates ITN not reaching your server)
- [ ] **Log rotation** — Ensure PayFast-related logs don't grow unbounded (they log every ITN POST)

---

## 8. Testing Before Go-Live

- [ ] **Test with ngrok + sandbox** — Before switching to live, test the full ITN flow using ngrok so PayFast can actually reach your webhook:
  ```bash
  ngrok http 5000
  ```
  Then set the `notify_url` in your form to the ngrok URL. Verify the wallet gets credited automatically without needing the sandbox-confirm button.
- [ ] **Test edge cases:**
  - [ ] User closes browser during PayFast payment (no return, but ITN should still arrive)
  - [ ] User pays, then hits back button (idempotency check should prevent double-credit)
  - [ ] PayFast sends CANCELLED status
  - [ ] Pending transaction expires after 1 hour (Celery task)
  - [ ] Two concurrent payments for the same wallet
- [ ] **Do a live test with a small amount** (R10) once credentials are set, to confirm the full production flow end-to-end

---

## 9. Mobile App Integration

- [ ] **Update Flutter app's `notify_url`** to point to either:
  - The shared endpoint: `https://yourdomain.com/api/payfast/notify` (preferred), or
  - The mobile redirect: `https://yourdomain.com/api/mobile/payment/notify` (307 redirects to shared endpoint)
- [ ] **Update Flutter app's PayFast credentials** — Replace sandbox credentials with live ones in the mobile app config
- [ ] **Test mobile payment flow** end-to-end with live credentials

---

## 10. Optional Enhancements (Post-Launch)

- [ ] **Payment receipt email** — Send a confirmation email after successful top-up (in addition to the in-app notification)
- [ ] **Transaction history page** — Show PayFast reference numbers and payment gateway status on the portal transaction history
- [ ] **Retry failed ITNs** — PayFast retries automatically (immediately, then 10 min, then progressively longer), but consider a manual retry mechanism in the admin panel
- [ ] **Reconciliation report** — Periodic job to compare PayFast dashboard transactions vs local database transactions and flag mismatches
- [ ] **Multiple payment methods** — PayFast supports EFT, credit card, Instant EFT, and Masterpass. Currently we send users to the full PayFast page which offers all methods. Could pre-select a method via the `payment_method` form field.

---

## Quick Reference

| Item | Sandbox (current) | Production |
|------|-------------------|------------|
| Process URL | `sandbox.payfast.co.za/eng/process` | `www.payfast.co.za/eng/process` |
| Validate URL | `sandbox.payfast.co.za/eng/query/validate` | `www.payfast.co.za/eng/query/validate` |
| Merchant ID | `10000100` | Your live ID |
| Merchant Key | `46f0cd694581a` | Your live key |
| Passphrase | `jt7NOE43FZPn` | Your live passphrase |
| `PAYFAST_SANDBOX` | `true` | `false` |
| Sandbox confirm button | Enabled | Disabled (403) |
| Server-to-server verify | Skipped | Enforced |
| ITN endpoint | Not reachable from localhost | Must be publicly accessible |
