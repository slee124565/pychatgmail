import abc
import base64
import os.path
import logging
from datetime import date, timedelta, datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from chatgmail.config import get_gcp_credentials_file

logger = logging.getLogger(__name__)
# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]


class MailInbox(abc.ABC):

    @abc.abstractmethod
    def list_msg(self, subject, offset_days=7):
        """Lists the user's Gmail labels."""


def get_credentials():
    """從客戶端密鑰檔案中取得新的憑證並啟動本地伺服器進行授權。"""
    _client_secret_file = get_gcp_credentials_file()
    flow = InstalledAppFlow.from_client_secrets_file(_client_secret_file, SCOPES)
    return flow.run_local_server(port=0)


def save_credentials(creds):
    """將憑證儲存到本地檔案中。"""
    with open('token.json', 'w') as token:
        token.write(creds.to_json())


def refresh_or_get_credentials(creds):
    """檢查並更新或重新取得憑證。"""
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as err:
            logger.debug(f'RefreshError: {err}')
            creds = get_credentials()
    else:
        creds = get_credentials()
    save_credentials(creds)
    return creds


class GmailInbox(MailInbox):
    @staticmethod
    def _build_gmail_service():

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            creds = refresh_or_get_credentials(creds)

        # if not creds or not creds.valid:
        #     if creds and creds.expired and creds.refresh_token:
        #         try:
        #             creds.refresh(Request())
        #         except RefreshError as err:
        #             logger.debug(f'RefreshError: {err}')
        #             flow = InstalledAppFlow.from_client_secrets_file(
        #                 _client_secret_file, SCOPES)
        #             creds = flow.run_local_server(port=0)
        #
        #     else:
        #         flow = InstalledAppFlow.from_client_secrets_file(
        #             _client_secret_file, SCOPES)
        #         creds = flow.run_local_server(port=0)
        #     # Save the credentials for the next run
        #     with open('token.json', 'w') as token:
        #         token.write(creds.to_json())

        try:
            # Call the Gmail API
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            logger.debug(f'An error occurred: {error}')

    def get_msg_by_id(self, msg_id: str):
        service = self._build_gmail_service()
        try:
            message = service.users().messages().get(
                userId='me',
                id=msg_id
            ).execute()
            return message
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            logger.debug(f'An error occurred: {error}')

    def list_labels(self):
        """List user's Gmail labels"""
        service = self._build_gmail_service()
        # 呼叫 users.labels.list 方法
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        logger.debug(f'Gmail label IDs: {labels}')
        return labels

    def fwd_msg(self, msg_id: str, addresses: list):
        service = self._build_gmail_service()

        # 取得指定郵件內容
        message = service.users().messages().get(userId="me", id=msg_id, format='full').execute()
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        subject = headers.get('Subject', 'No Subject')

        # 取得郵件主體
        body_html = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        # 建立新的郵件
        new_subject = f"Fwd: {subject}"
        new_body_html = f"---------- Forwarded message ---------<br>{body_html}"
        email_message = MIMEMultipart('alternative')
        email_message['Subject'] = new_subject
        email_message['From'] = "me"
        email_message['To'] = ', '.join(addresses)

        # 增加 HTML 內容
        email_message.attach(MIMEText(new_body_html, 'html'))

        # 編碼郵件
        encoded_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        # 發送郵件
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f'Message Id: {send_message["id"]}')

        logger.debug(f'Message({msg_id}) has been forwarded FWD Message ({send_message["id"]})')
        return send_message["id"]

    @staticmethod
    def _convert_to_pst_seconds(year, month, day):
        """依據台灣時區時間來轉換成timestamp"""
        # 台灣時間是 UTC+8
        taiwan_time = datetime(year, month, day, tzinfo=timezone(timedelta(hours=8)))
        # pst_time = taiwan_time.astimezone(timezone(timedelta(hours=-8)))

        # 取得該日期的開始時間（午夜）
        start_time = int(taiwan_time.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        # 取得該日期的結束時間（午夜下一天）
        end_time = int((taiwan_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        return start_time, end_time

    def list_msg(self, subject, offset_days=7, label_ids='INBOX'):
        """List the user's Gmail Inbox messages with the specified subject and offset days."""
        _gmail_query_labels = label_ids
        service = self._build_gmail_service()
        _date = date.today() - timedelta(days=offset_days)
        # query = f'after:{(date.today() - timedelta(days=offset_days)).strftime("%Y/%m/%d")}'
        _start_time, _ = self._convert_to_pst_seconds(_date.year, _date.month, _date.day)
        query = f'after:{_start_time}'
        if subject.strip():
            query = f'subject:("{subject}") AND {query}'
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
            thread_id = msg.get('threadId')
            if thread_id != msg_id:
                thread = service.users().threads().get(userId='me', id=thread_id).execute()
                msgs_in_thread = thread.get('messages', [])
                logger.debug(f'skip thread msg {thread_id} with msgs_in_thread {len(msgs_in_thread)}')
                continue
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            if not message:
                logger.debug(f'no message for id {msg_id}')
                continue

            msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                header['name'] == 'Subject'), None)
            # if str(msg_subject).find(subject) != 0:
            #     logger.debug(f'message subject not started with "{subject}", {msg_id}, {msg_subject}')
            #     continue

            internal_date_timestamp = int(int(message['internalDate']) / 1000)  # 轉換為秒
            # received_datetime = parsedate_to_datetime(str(internal_date_timestamp))
            # receive_date = received_datetime.strftime('%Y-%m-%d')
            dt_object = datetime.fromtimestamp(internal_date_timestamp)
            receive_date = dt_object.strftime('%Y-%m-%d')

            try:
                msg_body = base64.urlsafe_b64decode(message.get('payload').get('body').get('data')).decode("utf-8")

                # create a hidden folder (.gmail) if not exist to store the html files
                if not os.path.exists('.gmail'):
                    os.makedirs('.gmail')

                # save the html file
                html_file = os.path.join('.gmail', f'{msg_id}.html')
                # html_file = f'{msg_id}-{msg_subject}.html'
                with open(html_file, 'w') as fh:
                    fh.write(msg_body)
                logger.debug([msg_id, msg_subject, receive_date, html_file])
                msgs.append([msg_id, msg_subject, receive_date, html_file])
            except Exception as e:
                logger.error(f'error: {e}, {msg_id}, {msg_subject}')
                continue

        return msgs


if __name__ == '__main__':
    gmail = GmailInbox()
    gmail.get_msg_by_id(msg_id='18fb8942e2590167')
