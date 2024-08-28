import os
import json
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
MSG_QUERY_SUBJECT = os.getenv('MSG_QUERY_SUBJECT', '104應徵履歷 OR 透過104轉寄履歷')
MSG_QUERY_DAYS = os.getenv('MSG_QUERY_DAYS', 1)
MSG_QUERY_LABELS = os.getenv('MSG_QUERY_LABELS', 'INBOX')
MSG_QUERY_CACHE_FILE = '.q'
CANDIDATES_CACHED_FILE = '.candidates'


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
    with open(MSG_QUERY_CACHE_FILE, 'w') as fh:
        fh.write(json.dumps(msgs, indent=2, ensure_ascii=False))
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
    # _file = os.path.join('./', DIGEST2_MSG_FOLDER, f'{msg_id}-{candidate.msg_receive_date}-{candidate.name}.md')
    # with open(_file, 'w', encoding='utf-8') as file:
    #     file.write(candidate_md)

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


def _print_candidate_digest(msg_id: str):
    msg_html = gmail.read_msg_from_cache(msg_id)
    candidate = orm.candidate_mapper(msg_id, msg_html)
    click.clear()
    click.echo(json.dumps(candidate.digest(), indent=2, ensure_ascii=False))


@click.command(name='nav-q')
def nav_q_msgs():
    """
    Navigate last gmail query results
    """
    if not os.path.exists(MSG_QUERY_CACHE_FILE):
        click.echo(f'No last query result exists')
        return

    with open(MSG_QUERY_CACHE_FILE, 'r') as fh:
        _q = json.loads(fh.read())

    if not len(_q):
        click.echo(f'Last query result empty')
        return

    assert isinstance(_q, list)
    _n = 0
    msg_id, _, _, _ = _q[_n]
    _print_candidate_digest(msg_id)
    while True:
        click.echo(f'===== {_n + 1}/{len(_q)} ====')
        click.echo(f'<n>: next msg')
        click.echo(f'<p>: prev msg')
        click.echo(f'<1>-<{len(_q)}>: jump msg')
        click.echo(f'<d>: detail msg')
        click.echo(f'<s>: save msg info')
        click.echo(f'<q> to exit')
        choice = click.prompt('cmd ?', type=str)

        if choice == 'n':
            _n = 0 if _n+1 >= len(_q) else _n+1
            msg_id, _, _, _ = _q[_n]
            _print_candidate_digest(msg_id)
        elif choice == 'p':
            _n = len(_q)-1 if _n-1 < 0 else _n-1
            msg_id, _, _, _ = _q[_n]
            _print_candidate_digest(msg_id)
        elif choice == 'd':
            click.clear()
            check_gmail_msg.callback(msg_id)
        elif f'{choice}'.isdigit():
            if 1 <= int(choice) <= len(_q):
                _n = int(choice) - 1
                msg_id, _, _, _ = _q[_n]
                _print_candidate_digest(msg_id)
            else:
                click.echo(f'Digit number invalid')
        elif choice == 's':
            with open(CANDIDATES_CACHED_FILE, 'a', encoding='utf-8') as fh:
                fh.write(f'{_q[_n]}\n')
            click.echo(f'saved {_q[_n]} into {CANDIDATES_CACHED_FILE}')
        elif choice == 'q':
            break
        else:
            pass


# Adding commands to the group
chatgmailcli.add_command(list_gmail_labels)
chatgmailcli.add_command(list_gmail_subject_msgs)
chatgmailcli.add_command(nav_q_msgs)
chatgmailcli.add_command(check_gmail_msg)
chatgmailcli.add_command(check_gmail_msg_all)

if __name__ == '__main__':
    chatgmailcli()
