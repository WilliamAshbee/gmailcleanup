import argparse
from collections import Counter

from gmail_auth import get_service


def get_top_senders(k=10, limit=500):
    service = get_service()

    print(f"Fetching the last {limit} messages...")
    results = service.users().messages().list(userId='me', maxResults=500).execute()
    messages = results.get('messages', [])

    while 'nextPageToken' in results and len(messages) < limit:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', pageToken=page_token, maxResults=500).execute()
        messages.extend(results.get('messages', []))

    messages = messages[:limit]
    sender_counter = Counter()

    print(f"Analyzing {len(messages)} message headers. This may take a moment...")

    for msg in messages:
        # Requesting format='metadata' drastically reduces the payload size
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From']
        ).execute()

        headers = msg_data.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'] == 'From':
                sender = header['value']
                sender_counter[sender] += 1
                break

    print(f"\n--- Top {k} Senders ---")
    for sender, count in sender_counter.most_common(k):
        print(f"{count} emails - {sender}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Show the most frequent senders among recent messages.")
    parser.add_argument('-k', type=int, default=10, help="Number of senders to show")
    parser.add_argument('--limit', type=int, default=500, help="How many recent messages to scan")
    args = parser.parse_args()
    get_top_senders(k=args.k, limit=args.limit)
