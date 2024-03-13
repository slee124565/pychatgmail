import abc
import base64
import os.path
import logging
from datetime import date, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from chatgmail.config import get_gcp_credentials_file

logger = logging.getLogger(__name__)
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class MailInbox(abc.ABC):

    @abc.abstractmethod
    def list_msg(self, subject, offset_days=7):
        """Lists the user's Gmail labels."""


class GmailInbox(MailInbox):
    def list_msg(self, subject, offset_days=7):
        """List the user's Gmail Inbox messages with the specified subject and offset days."""
        _client_secret_file = get_gcp_credentials_file()
        _gmail_query_labels = 'INBOX'

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
                    _client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            # Call the Gmail API
            service = build('gmail', 'v1', credentials=creds)
            query = f'after:{(date.today() - timedelta(days=offset_days)).strftime("%Y/%m/%d")}'
            if subject.strip():
                query = f'subject:({subject}) {query}'
            logger.debug(f'Gmail Inbox query with {query}')

            results = service.users().messages().list(
                userId='me',
                labelIds=_gmail_query_labels.split(','),
                q=query
            ).execute()
            messages = results.get('messages')
            logger.debug(f'messages {messages}')
            if not messages:
                logger.debug(f'no gmail message query result')
                return
            logger.debug(f'there are {len(messages)} matched messages')

            msgs = []
            for msg in results.get('messages'):
                msg_id = msg.get('id')
                message = service.users().messages().get(userId='me', id=msg_id).execute()
                if not message:
                    logger.debug(f'no message for id {msg_id}')
                    continue

                msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                    header['name'] == 'Subject'), None)
                if str(msg_subject).find(subject) != 0:
                    logger.debug(f'message subject not started with "{subject}", {msg_id}, {msg_subject}')
                    continue

                msg_body = base64.urlsafe_b64decode(message.get('payload').get('body').get('data')).decode("utf-8")
                
                # create a hidden folder (.gmail) if not exist to store the html files
                if not os.path.exists('.gmail'):
                    os.makedirs('.gmail')
                
                # save the html file
                html_file = os.path.join('.gmail', f'{msg_id}.html')
                # html_file = f'{msg_id}-{msg_subject}.html'
                with open(html_file, 'w') as fh:
                    fh.write(msg_body)
                logger.debug([msg_id, msg_subject, html_file])
                msgs.append([msg_id, msg_subject, html_file])
            
            return msgs

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            logger.debug(f'An error occurred: {error}')
