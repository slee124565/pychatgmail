import json

import click
import logging.config as logging_config
from chatgmail import config
from chatgmail.adapters import gmail, orm

logging_config.dictConfig(config.logging_config)


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
    click.echo(f'check mgs: {msg_id} | {candidate.validate()}')
    click.echo(f'{json.dumps(candidate.digest(), indent=2, ensure_ascii=False, default=str)}')


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

if __name__ == '__main__':
    chatgmailcli()
