import argparse

from gmail_auth import get_service

DEFAULT_QUERY = "category:promotions older_than:{age}"


def list_ids(service, query):
    ids = []
    page_token = None
    while True:
        results = service.users().messages().list(
            userId='me', q=query, maxResults=500, pageToken=page_token,
            fields='messages/id,nextPageToken',
        ).execute(num_retries=8)
        ids.extend(msg['id'] for msg in results.get('messages', []))
        print(f"  found {len(ids)} messages", end='\r')
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    print()
    return ids


def trash_old_promotions(age='1y', dry_run=False, assume_yes=False):
    service = get_service()
    query = DEFAULT_QUERY.format(age=age)

    print(f"Searching: {query}")
    ids = list_ids(service, query)
    if not ids:
        print("No messages found.")
        return
    print(f"Found {len(ids)} promotional messages older than {age}.")
    if dry_run:
        print("Dry run, nothing trashed.")
        return
    if not assume_yes and input("Move them all to Trash? [y/N] ").strip().lower() != 'y':
        print("Cancelled.")
        return

    # The batchModify endpoint accepts a maximum of 1000 IDs per request
    chunk_size = 1000
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        service.users().messages().batchModify(
            userId='me', body={'ids': chunk, 'addLabelIds': ['TRASH']},
        ).execute(num_retries=8)
        print(f"Trashed {min(i + chunk_size, len(ids))}/{len(ids)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Move old Promotions-tab mail to the Gmail trash.")
    parser.add_argument('--older-than', default='1y',
                        help="Age cutoff in Gmail syntax, e.g. 1y, 6m, 30d (default: 1y)")
    parser.add_argument('--dry-run', action='store_true', help="Count matches without trashing them")
    parser.add_argument('--yes', action='store_true', help="Skip the confirmation prompt")
    args = parser.parse_args()
    trash_old_promotions(age=args.older_than, dry_run=args.dry_run, assume_yes=args.yes)
