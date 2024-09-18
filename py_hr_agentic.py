import json
import os

import llm
import dotenv
import logging
import logging.config as logging_config
from chatgmail import cli, config
from chatgmail.adapters import slack

logging_config.dictConfig(config.logging_config)
dotenv.load_dotenv()
logger = logging.getLogger(__name__)
LLM_ANALYZED_FOLDER = os.getenv('LLM_ANALYZED_FOLDER', '.analyzed')


def main(subject: str, days: int = 1, labels: str = 'Resume'):
    ch_webhook = os.getenv('MSG_NOTIFY_SLACK_WEBHOOK', '')
    fwd_addresses = os.getenv('MSG_FWD_ADDRESSES', '')
    msg_ids = cli.list_gmail_subject_msgs.callback(subject, days, labels, True)
    llm_model = config.get_llm_model()
    assert isinstance(llm_model, llm.models.Model)
    with open('py_hr_prompt.txt', 'r') as fh:
        llm_system = fh.read()

    for msg_id in msg_ids[:]:
        candidate = cli.check_gmail_msg.callback(msg_id)

        _file = f'./{LLM_ANALYZED_FOLDER}/{msg_id}.txt'
        if os.path.exists(_file):
            logger.info(f'candidate {candidate.job_104_code} {candidate.name} already analyzed, skip')
            continue

        response = llm_model.prompt(
            prompt=candidate.to_markdown(),
            system=llm_system,
            stream=False
        ).text()

        if not os.path.exists(LLM_ANALYZED_FOLDER):
            os.makedirs(LLM_ANALYZED_FOLDER)
            logger.info(f'create folder: {LLM_ANALYZED_FOLDER}')

        with open(_file, 'w', encoding='utf-8') as file:
            file.write(response)
            logger.info(f'candidate {candidate.job_104_code} {candidate.name} analyzed and saved {_file}')

        _digest = json.dumps(candidate.digest(), indent=2, ensure_ascii=False)
        if f'{response}'.find('True') >= 0:
            notify = (f'HR-AI Notify: {candidate.name}, {candidate.job_104_code}, '
                      f'\napply:[{candidate.applied_position}], \nprefer:[{candidate.preferred_position}]'
                      f'\n<<< LLM Analysis\n{response}\n>>>\n')
            if ch_webhook:
                slack.send_slack_message(ch_webhook=ch_webhook, msg=notify)
            if fwd_addresses:
                cli.fwd_gmail_msg.callback(msg_id, fwd_addresses)
            break
        else:
            logger.debug(f'HR-AI skip candidate: {candidate.digest()}')


if __name__ == '__main__':
    # main(subject='104應徵履歷【軟體工程師】')
    main(subject='104自訂配對人選【軟體工程師】')
    # main(subject='104應徵履歷【雲端軟體工程師】')
    # main(subject='104自訂配對人選【雲端軟體工程師】')
