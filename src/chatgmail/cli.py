import json
import os

import click
import dotenv
import logging.config as logging_config
from chatgmail import config
from chatgmail.adapters import gmail, orm

dotenv.load_dotenv()
logging_config.dictConfig(config.logging_config)
GMAIL_MSG_FOLDER = os.getenv('GMAIL_MSG_FOLDER', '.gmail')


@click.group()
def chatgmailcli():
    """
    ChatGmail CLI Group Command.
    """
    pass


@click.command(name='list-mail')
@click.option('-s', '--query_subject', default='104應徵履歷', help='Gmail query subject match string.')
@click.option('-d', '--query_offset_days', default=7, type=int, help='Gmail query after timedelta days.')
def list_gmail_subject_msgs(query_subject, query_offset_days):
    """
    List Gmail messages based on subject and offset-days.
    """
    gmail_inbox = gmail.GmailInbox()
    msgs = gmail_inbox.list_msg(query_subject, query_offset_days)
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
    _file = f'./{GMAIL_MSG_FOLDER}/{msg_id}.md'
    with open(_file, 'w', encoding='utf-8') as file:
        file.write(candidate_md)


@click.command(name='check-all-mail')
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
@click.option('--input_file', help='Input file containing email messages for analysis.', required=True)
@click.option('--output_file', default='analysis_result.txt', help='Output file to save the analysis results.')
def analyze_mail(input_file, output_file):
    """
    Analyze the content of specified email messages.
    """
    click.echo(f'Analyzing emails from {input_file} and saving results to {output_file}')
    # Placeholder for actual implementation


# Adding commands to the group
chatgmailcli.add_command(list_gmail_subject_msgs)
chatgmailcli.add_command(analyze_mail)
chatgmailcli.add_command(check_gmail_msg)
chatgmailcli.add_command(check_gmail_msg_all)

if __name__ == '__main__':
    chatgmailcli()
