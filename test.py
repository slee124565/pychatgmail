import click
import logging.config as logging_config

import chatgmail.cli
from chatgmail import config
from chatgmail.adapters import gmail
from chatgmail.adapters import orm

logging_config.dictConfig(config.logging_config)


# msg_id = '18fb8942e2590167'
# with open(f'.gmail/{msg_id}.html', 'r', encoding='utf-8') as file:
#     resume_104_html = file.read()
# candidate = orm.candidate_mapper(msg_id, resume_104_html)
# print(f'{candidate}')

def check_msg(msg_id: str):
    msg_html = chatgmail.cli.read_msg_from_cache(msg_id)
    candidate = orm.candidate_mapper(msg_id, msg_html)
    click.echo(f'{msg_id}|{candidate.validate()}|{candidate}')
    # click.echo(f'{json.dumps(candidate.digest(), indent=2, ensure_ascii=False, default=str)}')
    candidate_md = candidate.to_markdown()
    click.echo(candidate_md)


def fwd_msg(msg_id: str, addresses: list):
    inbox = gmail.GmailInbox()
    inbox.fwd_msg(msg_id, addresses)


def list_msg():
    inbox = gmail.GmailInbox()
    inbox.list_msg(subject='104應徵履歷 OR 透過104轉寄履歷', offset_days=0, label_ids='Label_6866544674998790970')


if __name__ == '__main__':
    # msg_id = '18fb8942e2590167'
    # msg_id = '19154932940d00a3'  # 轉寄履歷(完整)
    msg_id = '1918fe8005e5cba1'  # 配對信(完整)
    # msg_id = '1916e5660c6c5be8'  # 主動應徵履歷
    # gml = gmail.GmailInbox()
    # msg = gml.get_msg_by_id(msg_id=msg_id)
    # gml.list_msg('104應徵履歷 OR 透過104轉寄履歷')

    # check_msg(msg_id)
    # fwd_msg(msg_id, ['lee.shiueh@gmail.com'])
    list_msg()
