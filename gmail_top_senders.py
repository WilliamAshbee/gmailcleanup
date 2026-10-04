import argparse
import random
import time
from collections import Counter
from email.utils import parseaddr

from gmail_auth import get_service

# messages.get costs 5 quota units and the per-user limit is 250 units/sec.
# Larger batches (40) trigger 429 errors and sustained bursts trigger 403
# rate-limit errors, so keep batches small and paced; failures are retried.
BATCH_SIZE = 10
MIN_BATCH_SECONDS = 0.5
MAX_ROUNDS = 6


def list_all_ids(service, query=None):
    ids = []
    page_token = None
    while True:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=500, pageToken=page_token,
            fields='messages/id,nextPageToken',
        ).execute(num_retries=8)
        ids.extend(msg['id'] for msg in results.get('messages', []))
        print(f"  listed {len(ids)} message ids", end='\r')
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    print()
    return ids


def fetch_metadata(service, ids):
    """Fetch From header and size for each id using batched requests."""
    results = {}
    error_codes = Counter()
    pending = list(ids)
    for attempt in range(MAX_ROUNDS):
        failed = []

        def callback(request_id, response, exception):
            if exception is not None:
                failed.append(request_id)
                error_codes[getattr(getattr(exception, 'resp', None), 'status', 'unknown')] += 1
            else:
                results[request_id] = response

        for i in range(0, len(pending), BATCH_SIZE):
            started = time.time()
            batch = service.new_batch_http_request(callback=callback)
            for message_id in pending[i:i + BATCH_SIZE]:
                batch.add(
                    service.users().messages().get(
                        userId='me', id=message_id, format='metadata',
                        metadataHeaders=['From'],
                        fields='id,sizeEstimate,payload/headers',
                    ),
                    request_id=message_id,
                )
            batch.execute()
            print(f"  fetched {len(results)}/{len(ids)}", end='\r')
            time.sleep(max(0, MIN_BATCH_SECONDS - (time.time() - started)))

        pending = failed
        if not pending:
            break
        time.sleep(min(2 ** attempt * 2, 30))  # back off before retrying rate-limited requests
    print()
    if pending:
        print(f"Skipped {len(pending)} messages that kept failing. HTTP errors seen: {dict(error_codes)}")
    return results


def sender_key(message, by):
    for header in message.get('payload', {}).get('headers', []):
        if header['name'].lower() == 'from':
            address = parseaddr(header['value'])[1].lower() or header['value']
            if by == 'domain' and '@' in address:
                return address.split('@', 1)[1]
            return address
    return '(unknown)'


def format_size(num_bytes):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num_bytes < 1024 or unit == 'GB':
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024


def get_top_senders(k=10, sample=5000, by='domain', sort='size', query=None):
    service = get_service()

    print("Listing message ids...")
    ids = list_all_ids(service, query)
    total = len(ids)
    if total == 0:
        print("No messages found.")
        return

    if sample and sample < total:
        ids = random.sample(ids, sample)
    print(f"Scanning {len(ids)} of {total} messages (random sample).")

    messages = fetch_metadata(service, ids)
    if not messages:
        print("No messages could be fetched.")
        return
    scale = total / len(messages)

    counts = Counter()
    sizes = Counter()
    for message in messages.values():
        key = sender_key(message, by)
        counts[key] += 1
        sizes[key] += int(message.get('sizeEstimate', 0))

    ranking = sizes if sort == 'size' else counts
    print(f"\n--- Top {k} senders by {sort} (estimated over {total} messages) ---")
    print(f"{'est. count':>11}  {'est. size':>10}  sender")
    for key, _ in ranking.most_common(k):
        print(f"{round(counts[key] * scale):>11}  {format_size(sizes[key] * scale):>10}  {key}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Estimate the biggest senders across the whole mailbox.")
    parser.add_argument('-k', type=int, default=10, help="Number of senders to show")
    parser.add_argument('--sample', type=int, default=5000,
                        help="Messages to sample (0 scans everything; slow on large mailboxes)")
    parser.add_argument('--by', choices=['domain', 'address'], default='domain', help="Group senders by domain or address")
    parser.add_argument('--sort', choices=['size', 'count'], default='size', help="Rank by total size or message count")
    parser.add_argument('--query', help="Only scan messages matching this Gmail search, e.g. 'older_than:1y'")
    args = parser.parse_args()
    get_top_senders(k=args.k, sample=args.sample, by=args.by, sort=args.sort, query=args.query)
