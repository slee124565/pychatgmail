from __future__ import print_function

import base64
import os.path
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def main(args):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                args.client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        query = f'after:{(date.today() + timedelta(days=args.query_after)).strftime("%Y/%m/%d")}'
        if args.query_subject.strip():
            query = f'subject:({args.query_subject}) {query}'
        print(f'gmail query {args.query_labels} with {query}')

        results = service.users().messages().list(
            userId='me',
            labelIds=args.query_labels.split(','),
            q=query
        ).execute()
        messages = results.get('messages')
        print(f'there are {len(messages)} matched messages')
        if not messages:
            print(f'no gmail message query result')
            return

        for msg in results.get('messages'):
            msg_id = msg.get('id')
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            if not message:
                print(f'no message for id {msg_id}')
                continue

            msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                header['name'] == 'Subject'), None)
            if not str(msg_subject).startswith(args.query_subject):
                print(f'message subject not started with "{args.query_subject}", {msg_id}, {msg_subject}')
                continue

            data = message.get('payload').get('body').get('data')
            if not data:
                data = message.get('payload').get('parts')[0].get('parts')[0].get('body').get('data')
            if not data:
                continue
            msg_body = base64.urlsafe_b64decode(data).decode("utf-8")
            output_file = os.path.join(args.out_dir, f'{args.query_subject}_{msg_id}.html'.replace('/', '_'))
            with open(output_file, 'w') as fh:
                fh.write(msg_body)
            print([msg_id, msg_subject, output_file])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--client_secret_file',
                        help='gcp project oauth client desktop app credentials file',
                        default='credentials.json')
    parser.add_argument('--user_token_file',
                        help='user access and refresh tokens file',
                        default='token.json')
    parser.add_argument('--max_result',
                        type=int,
                        help='gmail message max number list',
                        default=100)
    parser.add_argument('-l', '--query_labels',
                        help='gmail query labels',
                        default='INBOX')
    parser.add_argument('-s', '--query_subject',
                        help='gmail query subject match string',
                        default='104應徵履歷【UI/UX')
    parser.add_argument('-d', '--query_after',
                        type=int,
                        help='gmail query after timedelta days',
                        default=-7)
    parser.add_argument('-o', '--out_dir',
                        help='output subdirectory name',
                        default='output')

    args = parser.parse_args()

    main(args)
