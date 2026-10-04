# Inbox cleanup plan

Goal: get incoming email down to an amount worth committing to read, with digests for the rest. Then audit account security.

## Phases

### 1. Purge the backlog
- [x] Trash bulk senders by domain (`gmail_cleanup.py <domain>`)
- [x] Trash Promotions older than 1 year (`gmail_trash_promotions.py`)
- [ ] Run the account inventory scan **before** purging Updates (see phase 5)
- [ ] Purge Updates, Social and Forums older than a cutoff, keeping receipts and account notices. Dry run first.

Trashed mail stays in Gmail's Trash for about 30 days and can be restored. Emptying Trash is permanent, so keep Trash until the audit inventory is done.

### 2. Cut the inflow
- [ ] Ranked table of senders from the last 60-90 days: volume, how many were opened, unsubscribe link
- [ ] Unsubscribe from legitimate senders; mark sketchy ones as spam (do not click their unsubscribe links)

### 3. Route what's left
- [ ] Keep in inbox: real people plus a short allowlist (bank, school, landlord, work)
- [ ] Filter to skip the inbox and label `Digest`: newsletters, alerts, receipts
- [ ] Auto-trash worst senders that can't be unsubscribed from

### 4. Digest
- [ ] Weekly script that summarizes the `Digest` label (sender, subjects, links)

### 5. Security audit (separate project)
- [ ] Account inventory from signup, verify and password-reset emails (read-only scan, save to a file)
- [ ] Breach check for each email address; password manager breach report
- [ ] Unique passwords in a password manager; change reused or exposed ones, starting with email, banking and money
- [ ] Two-factor authentication on key accounts (authenticator app or passkey)
- [ ] Google Security Checkup; revoke third-party app access, including this project's OAuth app when finished
- [ ] Close accounts that are no longer used

## Scripts

| Script | What it does |
|---|---|
| `gmail_auth.py` | OAuth login; writes `token.json` |
| `gmail_top_senders.py` | Samples the mailbox and ranks senders by size or count |
| `gmail_cleanup.py` | Trashes all mail from a sender or domain (`--dry-run` to count first) |
| `gmail_trash_promotions.py` | Trashes Promotions-tab mail older than a cutoff (`--older-than`, `--dry-run`) |

## Notes
- Needs `credentials.json` (Desktop OAuth client from Google Cloud). It and `token.json` are git-ignored.
- While the OAuth app is in Testing mode, the token expires after 7 days and the browser login repeats.
- Gmail's API has a per-minute quota. Don't run two heavy scripts at once; the scripts retry, but contention slows them.
- Scope is full Gmail access (`https://mail.google.com/`). `gmail.modify` is enough for trashing and filtering, and is safer.
