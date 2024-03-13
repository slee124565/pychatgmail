"""
google api client doc: https://googleapis.github.io/google-api-python-client/docs/
"""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os.path
from typing import *
import json
import dateutil.parser
import pytz

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailApi:
    def __init__(self, client_secret_file: str):
        creds = self._get_user_credential(client_secret_file)
        self.service = build('gmail', 'v1', credentials=creds)
        self.user_id = 'me'

    @staticmethod
    def _get_user_credential(client_secret_file: str):
        token_file = 'gmail_api_token.json'

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_file,
                    SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        return creds

    def query_labels(self) -> List[str]:
        try:
            results = self.service.users().labels().list(userId=self.user_id).execute()
            labels = results.get('labels', [])
            return [label['name'] for label in labels]
        except HttpError as error:
            print(f'An error occurred: {error}')

    def query_emails(
            self, labels: List[str] = None, query: str = '', next_token: str = None
    ) -> Tuple[List[Dict], str | None]:
        """

        Args:
            - labels (List[str], optional): mail label
            - query (str, optional): same as in gmail query search. e.g. "from:(abc@mail.com) after:2023/3/14"
            - next_token (str):
        """
        labels = [] if labels is None else labels

        msgs = self.service.users().messages().list(
            userId=self.user_id,
            labelIds=labels,
            maxResults=100,
            q=query,
            pageToken=next_token
        ).execute()
        # print(json.dumps(msgs))

        final_list = []
        for msg in msgs.get('messages', []):
            m_id = msg['id']
            # https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message
            message = self.service.users().messages().get(userId=self.user_id, id=m_id).execute()
            payload = message.get('payload', {})
            headers = payload.get('headers', [])

            email_data = {}
            for header in headers:
                if header['name'] == 'Subject':
                    email_data['subject'] = header['value']
                elif header['name'] == 'Date':
                    date = dateutil.parser.parse(header['value'])
                    date = date.astimezone(tz=pytz.timezone('Asia/Taipei'))
                    email_data['date'] = date.isoformat(timespec='seconds')

            email_data['ori_message'] = json.dumps(message)
            print(f"get email: {email_data.get('date')} | {email_data.get('subject')}")
            final_list.append(email_data)
        return final_list, msgs.get('nextPageToken')

    # @staticmethod
    # def _parse_message_parts_body(msg_parts: List[Dict]):
    #     class MessagePartBody(pydantic.BaseModel):
    #         size: int
    #         data: str | None
    #
    #     class MessagePart(pydantic.BaseModel):
    #         partId: str
    #         mimeType: str
    #         filename: str
    #         headers: List[Dict]
    #         body: MessagePartBody
    #         parts: List[Dict] | None
