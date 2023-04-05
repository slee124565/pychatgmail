from __future__ import print_function

import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import date, timedelta
import os.path
import dotenv
import base64
import logging

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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


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
            logger.info(f'msg {msg_id} marked as read.')
        else:
            logger.debug(f'msg {msg_id} already marked as read.')

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
    pass


def read_gmail_for_subject(query_subject, query_days=GMAIL_QUERY_DAYS):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(USER_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(USER_TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(USER_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        query = f'after:{(date.today() + timedelta(days=int(query_days))).strftime("%Y/%m/%d")}'
        if query_subject.strip():
            query = f'subject:({query_subject}) {query}'
        logger.info(f'query gmail w/ {query}')

        results = service.users().messages().list(
            userId='me',
            maxResults=GMAIL_MSG_MAX,
            labelIds=GMAIL_QUERY_LABELS.split(','),
            q=query
        ).execute()
        messages = results.get('messages')
        if not len(messages):
            logger.warning(f'no matched msg exist!')
            return

        logger.info(f'matched msg count {len(messages)}')

        match_msgs = []
        for msg in results.get('messages'):
            msg_id = msg.get('id')
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                header['name'] == 'Subject'), None)
            received_date = int(message['internalDate']) / 1000  # Convert to seconds
            received_datetime = datetime.datetime.fromtimestamp(received_date)
            if not str(msg_subject).startswith(query_subject):
                logger.debug(f'msg {msg_id} subject [ {msg_subject}] not started w/ "{query_subject}".')
                continue

            data = message.get('payload').get('body').get('data')
            if not data:
                data = message.get('payload').get('parts')[0].get('parts')[0].get('body').get('data')
            if not data:
                continue
            msg_body = base64.urlsafe_b64decode(data).decode("utf-8")
            output_file = os.path.join(OUTPUT_DIR, f'{msg_id}.html'.replace('/', '_'))
            with open(output_file, 'w') as fh:
                fh.write(msg_body)
            logger.info(f'msg saved: {[msg_id, received_datetime.strftime("%Y-%m-%d"), msg_subject, output_file]}')
            match_msgs.append([msg_id, msg_subject, output_file])

        return match_msgs
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        logger.error(f'An error occurred: {error}')


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
    # parser.add_argument('-l', '--query_labels',
    #                     help='gmail query labels',
    #                     default=os.getenv('GMAIL_QUERY_LABELS', 'INBOX'))
    # parser.add_argument('-r', '--set_msg_read',
    #                     type=bool,
    #                     help='set gmail message as been read',
    #                     default=os.getenv('GMAIL_MSG_SET_READ', False))
    # parser.add_argument('--max_result',
    #                     type=int,
    #                     help='gmail message max number list',
    #                     default=os.getenv('GMAIL_MSG_MAX', 100))
    # parser.add_argument('--oauth_client_secret_file',
    #                     help='gcp project oauth client desktop app credentials file',
    #                     default=os.getenv('OAUTH_CLIENT_SECRET_FILE', 'credentials.json'))
    # parser.add_argument('--user_token_file',
    #                     help='user access and refresh tokens file',
    #                     default=os.getenv('USER_TOKEN_FILE', 'token.json'))
    # parser.add_argument('-o', '--output_dir',
    #                     help='output subdirectory name',
    #                     default=os.getenv('OUTPUT_DIR', 'output'))
    parser.add_argument('--debug',
                        action='store_true',
                        help='logging level DEBUG',
                        default=True)
    parser.add_argument('--info',
                        action='store_true',
                        help='logging level INFO',
                        default=False)

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    if args.info:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # set_gmail_msg_read(msg_id='1871863fee1b6c67')

    read_gmail_for_subject(
        query_subject=args.query_subject,
        query_days=args.query_days)
