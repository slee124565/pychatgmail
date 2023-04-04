from __future__ import print_function
import dotenv
import base64
import os.path
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

dotenv.load_dotenv()
GMAIL_QUERY_SUBJECT_TXT = os.getenv('GMAIL_QUERY_SUBJECT_TXT')
GMAIL_QUERY_LABELS = os.getenv('GMAIL_QUERY_LABELS', 'token.json')
GMAIL_QUERY_DAYS = os.getenv('GMAIL_QUERY_DAYS', -7)
GMAIL_MSG_MAX = os.getenv('GMAIL_MSG_MAX', 100)
GMAIL_SET_MSG_READ = os.getenv('GMAIL_SET_MSG_READ', False)
OAUTH_CLIENT_SECRET_FILE = os.getenv('OAUTH_CLIENT_SECRET_FILE', 'credentials.json')
USER_TOKEN_FILE = os.getenv('USER_TOKEN_FILE', 'token.json')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def set_gmail_msg_read(
        msg_id,
        oauth_client_secret_file=OAUTH_CLIENT_SECRET_FILE,
        user_token_file=USER_TOKEN_FILE):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(user_token_file):
        creds = Credentials.from_authorized_user_file(user_token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                oauth_client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(user_token_file, 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        labels = message['labelIds']
        if 'UNREAD' in labels:
            labels.remove('UNREAD')
            body = {'removeLabelIds': ['UNREAD']}
            service.users().messages().modify(userId='me', id=msg_id, body=body).execute()
            print(f'Message with ID: {msg_id} marked as read.')
        else:
            print(f'Skip, message with ID: {msg_id} already marked as read.')

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
    pass


def read_gmail_for_subject(
        query_subject,
        query_labels=GMAIL_QUERY_LABELS,
        query_days=GMAIL_QUERY_DAYS,
        gmail_msg_max=GMAIL_MSG_MAX,
        oauth_client_secret_file=OAUTH_CLIENT_SECRET_FILE,
        user_token_file=USER_TOKEN_FILE,
        output_dir=OUTPUT_DIR):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(user_token_file):
        creds = Credentials.from_authorized_user_file(user_token_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                oauth_client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(user_token_file, 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        query = f'after:{(date.today() + timedelta(days=int(query_days))).strftime("%Y/%m/%d")}'
        if query_subject.strip():
            query = f'subject:({query_subject}) {query}'
        print(f'gmail query {query_subject} with {query}')

        results = service.users().messages().list(
            userId='me',
            maxResults=gmail_msg_max,
            labelIds=query_labels.split(','),
            q=query
        ).execute()
        messages = results.get('messages')
        print(f'there are {len(messages)} matched messages')
        if not messages:
            print(f'no gmail message query result')
            return

        match_msgs = []
        for msg in results.get('messages'):
            msg_id = msg.get('id')
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            if not message:
                print(f'no message for id {msg_id}')
                continue

            msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                header['name'] == 'Subject'), None)
            if not str(msg_subject).startswith(query_subject):
                print(f'message subject not started with "{query_subject}", {msg_id}, {msg_subject}')
                continue

            data = message.get('payload').get('body').get('data')
            if not data:
                data = message.get('payload').get('parts')[0].get('parts')[0].get('body').get('data')
            if not data:
                continue
            msg_body = base64.urlsafe_b64decode(data).decode("utf-8")
            output_file = os.path.join(output_dir, f'{msg_id}.html'.replace('/', '_'))
            with open(output_file, 'w') as fh:
                fh.write(msg_body)
            print([msg_id, msg_subject, output_file])
            match_msgs.append([msg_id, msg_subject, output_file])
        return match_msgs

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query_subject',
                        help='gmail query subject match string',
                        default=os.getenv('GMAIL_QUERY_SUBJECT_TXT', '104應徵履歷【IoT'))
    parser.add_argument('-d', '--query_days',
                        type=int,
                        help='gmail query the day before query_days',
                        default=os.getenv('GMAIL_QUERY_DAYS', -14))
    parser.add_argument('-l', '--query_labels',
                        help='gmail query labels',
                        default=os.getenv('GMAIL_QUERY_LABELS', 'INBOX'))
    parser.add_argument('-r', '--set_msg_read',
                        type=bool,
                        help='set gmail message as been read',
                        default=os.getenv('GMAIL_MSG_SET_READ', False))
    parser.add_argument('--max_result',
                        type=int,
                        help='gmail message max number list',
                        default=os.getenv('GMAIL_MSG_MAX', 100))
    parser.add_argument('--oauth_client_secret_file',
                        help='gcp project oauth client desktop app credentials file',
                        default=os.getenv('OAUTH_CLIENT_SECRET_FILE', 'credentials.json'))
    parser.add_argument('--user_token_file',
                        help='user access and refresh tokens file',
                        default=os.getenv('USER_TOKEN_FILE', 'token.json'))
    parser.add_argument('-o', '--output_dir',
                        help='output subdirectory name',
                        default=os.getenv('OUTPUT_DIR', 'output'))

    args = parser.parse_args()

    # set_gmail_msg_read(msg_id='1871863fee1b6c67')

    read_gmail_for_subject(
        query_subject=args.query_subject,
        query_labels=args.query_labels,
        query_days=args.query_days,
        gmail_msg_max=args.max_result,
        oauth_client_secret_file=args.oauth_client_secret_file,
        user_token_file=args.user_token_file,
        output_dir=args.output_dir)
