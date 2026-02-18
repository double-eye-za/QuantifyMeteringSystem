# Client Check Items

Items that need clarification or confirmation from the client before proceeding.

---

## 1. Low Balance Threshold on Estate Form

**Location:** Add Estate modal in `app/templates/estates/estates.html`

**Issue:** The "Low Balance Threshold (ZAR)" field is present in the Add Estate form, but:
- The `Estate` model does not have a `low_balance_threshold` field
- The `create_estate` service does not save this value
- `low_balance_threshold` is actually a `Wallet` model field (per-unit setting)

**Question for Client:**
- Should estates have a default `low_balance_threshold` that gets applied to all wallets/units created under that estate?
- Or should this field be removed from the Estate form since it's a wallet-level setting?

**Current Behavior:** The field collects input but the value is never saved.

---
