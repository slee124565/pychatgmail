import os
import json
import click
import dotenv
import subprocess
import platform
import logging.config as logging_config
from chatgmail import config
from chatgmail.adapters import gmail, orm

dotenv.load_dotenv()
logging_config.dictConfig(config.logging_config)
GMAIL_MSG_FOLDER = config.get_gmail_msg_saved_folder()
GMAIL_MSG_TRANSFER_FOLDER = config.get_gmail_msg_transfer_folder()
MSG_QUERY_SUBJECT = os.getenv('MSG_QUERY_SUBJECT', '')
MSG_QUERY_SUB_OPTIONS = os.getenv('MSG_QUERY_SUB_OPTIONS', '104應徵履歷,透過104轉寄履歷')
MSG_QUERY_DAYS = os.getenv('MSG_QUERY_DAYS', 1)
MSG_QUERY_LABELS = os.getenv('MSG_QUERY_LABELS', 'INBOX')
MSG_QUERY_CACHE_FILE = '.q'
CANDIDATES_CACHED_FILE = '.candidates'


def read_msg_from_cache(msg_id: str) -> str:
    """
    Read the email message from cache file.
    """
    cache_file = get_msg_cache_html_file_by_id(msg_id=msg_id)
    with open(cache_file, 'r', encoding='utf-8') as file:
        return file.read()


def get_msg_cache_html_file_by_id(msg_id: str) -> str:
    return os.path.join(GMAIL_MSG_FOLDER, f'{msg_id}.html')


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


@click.command(name='group-sub')
@click.option('-d', '--query_offset_days', default=MSG_QUERY_DAYS, type=int,
              help='Gmail query after timedelta days.')
@click.option('-l', '--gmail_label_ids', default=MSG_QUERY_LABELS, help='Gmail label IDs.')
def group_gmail_subject_digest(query_offset_days, gmail_label_ids):
    """Group Gmail messages subject digest( `】`) as data list"""
    click.echo(f'Gmail subject set in `{gmail_label_ids}` digest by  `】`')
    msgs = list_gmail_subject_msgs.callback('*', query_offset_days, gmail_label_ids)
    # click.echo(f'{msgs}')
    _subjects = set()
    for _, _subject, _, _ in msgs:
        n = str(_subject).find('】')
        if n > 0:
            _subjects.add(str(_subject)[:n + 1])
        else:
            pass
    for _s in sorted(_subjects):
        click.echo(f'{_s}')


@click.command(name='list-mail-menu')
@click.option('-s', '--query_menu', default=MSG_QUERY_SUB_OPTIONS, help='Gmail query subject match string.')
@click.option('-d', '--query_offset_days', default=MSG_QUERY_DAYS, type=int,
              help='Gmail query after timedelta days.')
@click.option('-l', '--gmail_label_ids', default=MSG_QUERY_LABELS, help='Gmail label IDs.')
def list_gmail_sub_menu_msgs(query_menu: str, query_offset_days: int, gmail_label_ids: str):
    """
    List Gmail messages based on subject menu and offset-days.
    """
    _options = query_menu.split(',')
    if not len(_options):
        click.echo(f'No query options exist in env var MSG_QUERY_SUB_OPTIONS `{MSG_QUERY_SUB_OPTIONS}`')
        return
    while True:
        for i, o in enumerate(_options):
            click.echo(f'{i + 1}: query subject {o}')
        click.echo(f'press <enter> to exit')
        choice = click.prompt(f'choice? 1-{len(_options)}', default='')
        if f'{choice}'.isdigit() and 0 < int(choice) <= len(_options):
            _subject = _options[int(choice) - 1]
            list_gmail_subject_msgs.callback(_subject, query_offset_days, gmail_label_ids)
        elif choice == '':
            break
        else:
            click.echo(f'Invalid option number enter')


@click.command(name='list-mail')
@click.option('-s', '--query_subject', default=MSG_QUERY_SUBJECT, help='Gmail query subject match string.')
@click.option('-d', '--query_offset_days', default=MSG_QUERY_DAYS, type=int,
              help='Gmail query after timedelta days.')
@click.option('-l', '--gmail_label_ids', default=MSG_QUERY_LABELS, help='Gmail label IDs.')
@click.option('--msg-id-only', is_flag=True, help='Output Gmail MSG ID List Only')
def list_gmail_subject_msgs(query_subject, query_offset_days, gmail_label_ids, msg_id_only=False):
    """
    List Gmail messages based on subject and offset-days.
    """
    if not msg_id_only:
        click.echo(
            f'Listing Gmail messages with sub: {query_subject} and days: {query_offset_days}, labels: {gmail_label_ids}...')
    gmail_inbox = gmail.GmailInbox()
    labels = gmail_inbox.list_labels()
    _ids = set()
    for _id in f'{gmail_label_ids}'.split(','):
        _ids.add(next((label.get('id') for label in labels if label.get('id') == _id), None))
    for _id in f'{gmail_label_ids}'.split(','):
        _ids.add(next((label.get('id') for label in labels if label.get('name') == _id), None))

    # 移除 None 元素
    _elements = {_e for _e in _ids if _e is not None}
    _ids = ','.join(map(str, _elements))

    # click.echo(f'{_ids}')
    msgs = gmail_inbox.list_msg(subject=query_subject, offset_days=query_offset_days, label_ids=_ids)
    with open(MSG_QUERY_CACHE_FILE, 'w') as fh:
        fh.write(json.dumps(msgs, indent=2, ensure_ascii=False))
    if msgs:
        if msg_id_only:
            for msg in msgs:
                click.echo(msg[0])
            return [msg[0] for msg in msgs]
        else:
            click.clear()
            for msg in msgs:
                click.echo(msg)
            click.echo('=====')
            click.echo(f'total: {len(msgs)}')
            return msgs
    else:
        if not msg_id_only:
            click.echo('No matched messages found.')
        return []


@click.command(name='check-mail')
@click.argument('msg_id')
def check_gmail_msg(msg_id):
    """
    Check the content of specified email message html format.
    """
    msg_html = read_msg_from_cache(msg_id)
    candidate = orm.candidate_mapper(msg_id, msg_html)
    click.echo(f'{msg_id}|{candidate.validate()}|{candidate}')
    # click.echo(f'{json.dumps(candidate.digest(), indent=2, ensure_ascii=False, default=str)}')
    candidate_md = candidate.to_markdown()
    click.echo(candidate_md)

    if not os.path.exists(GMAIL_MSG_TRANSFER_FOLDER):
        os.makedirs(GMAIL_MSG_TRANSFER_FOLDER)

    _file = f'./{GMAIL_MSG_TRANSFER_FOLDER}/{msg_id}.md'
    with open(_file, 'w', encoding='utf-8') as file:
        file.write(candidate_md)
    return candidate


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
            msg_html = read_msg_from_cache(msg_id)
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
    msg_html = read_msg_from_cache(msg_id)
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
        click.echo(f'<o>: open msg 104 html')
        click.echo(f'<s>: save msg info')
        click.echo(f'<enter> to exit')
        choice = click.prompt('cmd ?', type=str, default='')

        if choice == 'n':
            _n = 0 if _n + 1 >= len(_q) else _n + 1
            msg_id, _, _, _ = _q[_n]
            _print_candidate_digest(msg_id)
        elif choice == 'p':
            _n = len(_q) - 1 if _n - 1 < 0 else _n - 1
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
        elif choice == 'o':
            _html_file = get_msg_cache_html_file_by_id(msg_id)
            if platform.system() == 'Windows':
                subprocess.run(['start', _html_file], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', _html_file])
            else:  # Linux
                subprocess.run(['xdg-open', _html_file])
        elif choice == 's':
            with open(CANDIDATES_CACHED_FILE, 'a', encoding='utf-8') as fh:
                fh.write(f'{_q[_n]}\n')
            click.echo(f'saved {_q[_n]} into {CANDIDATES_CACHED_FILE}')
        elif choice == '':
            break
        else:
            click.echo('Invalid cmd')
            pass


@click.command('fwd')
@click.argument('msg_id')
@click.argument('addresses')
def fwd_gmail_msg(msg_id, addresses):
    """Forward a Gmail message to specified email addresses."""
    gmail_inbox = gmail.GmailInbox()
    fwd_msg_id = gmail_inbox.fwd_msg(msg_id, f'{addresses}'.split(','))
    click.echo(f'msg_id {msg_id} forward to {addresses}, {fwd_msg_id}')


# Adding commands to the group
chatgmailcli.add_command(list_gmail_labels)
chatgmailcli.add_command(list_gmail_subject_msgs)
chatgmailcli.add_command(list_gmail_sub_menu_msgs)
chatgmailcli.add_command(group_gmail_subject_digest)
chatgmailcli.add_command(nav_q_msgs)
chatgmailcli.add_command(fwd_gmail_msg)
chatgmailcli.add_command(check_gmail_msg)
# chatgmailcli.add_command(check_gmail_msg_all)

if __name__ == '__main__':
    chatgmailcli()
