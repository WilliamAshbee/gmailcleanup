import argparse

from gmail_auth import get_service


def batch_trash_sender(sender_email, dry_run=False):
    service = get_service()
    query = f"from:{sender_email}"

    print(f"Fetching messages for query: {query}")
    results = service.users().messages().list(userId='me', q=query, maxResults=500).execute()
    messages = results.get('messages', [])

    # Handle pagination if there are more than 500 messages
    while 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', q=query, pageToken=page_token, maxResults=500).execute()
        messages.extend(results.get('messages', []))

    if not messages:
        print("No messages found.")
        return

    message_ids = [msg['id'] for msg in messages]
    if dry_run:
        print(f"Found {len(message_ids)} messages. Dry run, nothing trashed.")
        return
    print(f"Found {len(message_ids)} messages. Trashing...")

    # The batchModify endpoint accepts a maximum of 1000 IDs per request
    chunk_size = 1000
    for i in range(0, len(message_ids), chunk_size):
        chunk = message_ids[i:i + chunk_size]
        body = {
            'ids': chunk,
            'addLabelIds': ['TRASH']
        }
        service.users().messages().batchModify(userId='me', body=body).execute()
        print(f"Trashed {len(chunk)} messages.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Move all mail from a sender to the Gmail trash.")
    parser.add_argument('sender', help="Sender address, e.g. newsletter@example.com")
    parser.add_argument('--dry-run', action='store_true', help="Count matches without trashing them")
    args = parser.parse_args()
    batch_trash_sender(args.sender, dry_run=args.dry_run)
