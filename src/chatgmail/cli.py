import os
import shutil
import click
import dotenv
import logging.config as logging_config
from chatgmail import config
from chatgmail.adapters import gmail, orm

dotenv.load_dotenv()
logging_config.dictConfig(config.logging_config)
GMAIL_MSG_FOLDER = os.getenv('GMAIL_MSG_FOLDER', '.gmail')
PROCESSED_MSG_FOLDER = os.getenv('GMAIL_MSG_FOLDER', '.processed')
DIGEST_MSG_FOLDER = os.getenv('GMAIL_MSG_FOLDER', '.mdigest')
DIGEST2_MSG_FOLDER = os.getenv('GMAIL_MSG_FOLDER', '.m2digest')
MSG_QUERY_SUBJECT = os.getenv('MSG_QUERY_SUBJECT', '104應徵履歷 OR 透過104轉寄履歷 OR 104自訂配對人選')
MSG_QUERY_DAYS = os.getenv('MSG_QUERY_DAYS', 1)
MSG_QUERY_LABELS = os.getenv('MSG_QUERY_LABELS', 'INBOX')


@click.group()
def chatgmailcli():
    """
    ChatGmail CLI Group Command.
    """
    pass


# @click.command(name='get-mail-by-id')
# @click.argument('msg_id')
# def get_mail_by_id(msg_id):
#     """
#     Get Gmail message by msg_id
#     """
#     click.echo(f'Get Gmail messages by ID: {msg_id}')
#     gmail_inbox = gmail.GmailInbox()
#     msg = gmail_inbox.get_msg_by_id(msg_id=msg_id)

@click.command(name='list-labels')
def list_gmail_labels():
    """
    List Gmail Labels based on User account.
    """
    click.echo(f'Listing user Gmail Labels')
    gmail_inbox = gmail.GmailInbox()
    labels = gmail_inbox.list_labels()
    for label in labels:
        assert isinstance(label, dict)
        click.echo(f'ID: {label.get("id")}, NAME: {label.get("name")}, TYPE: {label.get("type")}')


@click.command(name='list-mail')
@click.option('-s', '--query_subject', default=MSG_QUERY_SUBJECT, help='Gmail query subject match string.')
@click.option('-d', '--query_offset_days', default=MSG_QUERY_DAYS, type=int,
              help='Gmail query after timedelta days.')
@click.option('-l', '--gmail_label_ids', default=MSG_QUERY_LABELS, help='Gmail label IDs.')
def list_gmail_subject_msgs(query_subject, query_offset_days, gmail_label_ids):
    """
    List Gmail messages based on subject and offset-days.
    """
    click.echo(
        f'Listing Gmail messages with sub: {query_subject} and days: {query_offset_days}, labels: {gmail_label_ids}...')
    gmail_inbox = gmail.GmailInbox()
    msgs = gmail_inbox.list_msg(subject=query_subject, offset_days=query_offset_days, label_ids=gmail_label_ids)
    if msgs:
        for msg in msgs:
            click.echo(msg)
    else:
        click.echo('No matched messages found.')


@click.command(name='check-mail')
@click.argument('msg_id')
def check_gmail_msg(msg_id):
    """
    Check the content of specified email message html format.
    """
    msg_html = gmail.read_msg_from_cache(msg_id)
    candidate = orm.candidate_mapper(msg_id, msg_html)
    click.echo(f'{msg_id}|{candidate.validate()}|{candidate}')
    # click.echo(f'{json.dumps(candidate.digest(), indent=2, ensure_ascii=False, default=str)}')
    candidate_md = candidate.to_markdown()
    click.echo(candidate_md)
    if not os.path.exists(PROCESSED_MSG_FOLDER):
        os.makedirs(PROCESSED_MSG_FOLDER)

    if not os.path.exists(DIGEST_MSG_FOLDER):
        os.makedirs(DIGEST_MSG_FOLDER)
    _file = f'./{DIGEST_MSG_FOLDER}/{msg_id}.md'
    with open(_file, 'w', encoding='utf-8') as file:
        file.write(candidate_md)

    if not os.path.exists(DIGEST2_MSG_FOLDER):
        os.makedirs(DIGEST2_MSG_FOLDER)
    _file = f'./{DIGEST2_MSG_FOLDER}/{msg_id}-{candidate.msg_receive_date}-{candidate.name}.md'
    _file = os.path.join('./', DIGEST2_MSG_FOLDER, f'{msg_id}-{candidate.msg_receive_date}-{candidate.name}.md')
    with open(_file, 'w', encoding='utf-8') as file:
        file.write(candidate_md)

    # source_file = f'./{GMAIL_MSG_FOLDER}/{msg_id}.html'
    # destination_folder = f'./{PROCESSED_MSG_FOLDER}'
    # shutil.move(source_file, destination_folder)


@click.command(name='check-all-mail', help='Check all the email messages in the cache folder.')
@click.option('-q', '--query_applied_job', default=None, help='query job title text match string.')
def check_gmail_msg_all(query_applied_job):
    """
    Check all the email (filename end with .html) messages in the cache folder.
    """
    for msg_file in os.listdir(GMAIL_MSG_FOLDER):
        # 使用 os.path.splitext() 分割文件名和扩展名
        file_name, file_extension = os.path.splitext(msg_file)

        # 检查文件扩展名是否为 .html
        if file_extension.lower() == '.html':
            msg_id = file_name
            msg_html = gmail.read_msg_from_cache(msg_id)
            candidate = orm.candidate_mapper(msg_id, msg_html)
            if query_applied_job:
                if candidate.applied_position.find(query_applied_job) == -1:
                    continue
                _work = f'{candidate.work_experiences[0]}' if (isinstance(candidate.work_experiences, list)
                                                               and len(
                            candidate.work_experiences)) else f'{candidate.work_experiences}'
                click.echo(f'{candidate.name}, {candidate.age}, {candidate.gender}, {_work[:45]}...')
            else:
                click.echo(f'{msg_id}|{candidate.validate()}|{candidate}')
        # else:
        #     click.echo(f'\n** skipping file: {msg_file} **\n')


@click.command(name='analyze-mail')
@click.argument('msg_id')
@click.argument('prompt')
def analyze_mail(msg_id, prompt):
    """
    Analyze the content of specified email messages.
    """
    msg_html = gmail.read_msg_from_cache(msg_id)
    candidate = orm.candidate_mapper(msg_id, msg_html)
    if not candidate.validate():
        click.echo(f'Invalid candidate: {candidate}')
        return
    candidate_md = candidate.to_markdown()


# Adding commands to the group
chatgmailcli.add_command(list_gmail_labels)
chatgmailcli.add_command(list_gmail_subject_msgs)
chatgmailcli.add_command(analyze_mail)
chatgmailcli.add_command(check_gmail_msg)
chatgmailcli.add_command(check_gmail_msg_all)

if __name__ == '__main__':
    chatgmailcli()
