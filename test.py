import logging.config as logging_config
from chatgmail import config
from chatgmail.adapters import orm

logging_config.dictConfig(config.logging_config)

msg_id = '18e35dada52335b2'
with open(f'.gmail/{msg_id}.html', 'r', encoding='utf-8') as file:
    resume_104_html = file.read()
candidate = orm.candidate_mapper(msg_id, resume_104_html)
print(f'{candidate}')
