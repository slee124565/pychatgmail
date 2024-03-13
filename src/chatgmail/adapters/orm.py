import bs4
from lxml import etree
import os
import json
import re
import logging
from chatgmail.domain import model

logger = logging.getLogger(__name__)


def _xpath_string_mapping(dom: etree.HTML, xpath: str) -> str:
    elements = dom.xpath(xpath)
    logger.debug(f'xpath: {xpath}')
    logger.debug(f'elements: {elements}')
    if elements:
        if hasattr(elements[0], 'text'):
            inner_text = elements[0].text
        else:
            inner_text = f'{elements[0]}'.strip()
        value = inner_text
    else:
        value = ''
    return value.replace('\n', '').strip()


def candidate_mapper(msg_id: str, resume_104_html: str) -> model.Candidate:
    """
    Map the 104 job application resume HTML to Candidate object.
    """
    soup = bs4.BeautifulSoup(resume_104_html, 'html.parser')
    dom = etree.HTML(str(soup))

    field_xpath_mapping = {
        'applied_position': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a',
        'self_recommendation': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[2]/td/div[2]',
        'job_104_code': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[2]/text()[2]',
        'name': "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span",
        'age': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/text()[1]',
        'gender': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/text()[2]',
    }

    return model.Candidate(
        msg_id=msg_id,
        applied_position=_xpath_string_mapping(dom, field_xpath_mapping['applied_position']),
        self_recommendation=_xpath_string_mapping(dom, field_xpath_mapping['self_recommendation']),
        job_104_code=_xpath_string_mapping(dom, field_xpath_mapping['job_104_code']),
        name=_xpath_string_mapping(dom, field_xpath_mapping['name']),
        age=_xpath_string_mapping(dom, field_xpath_mapping['age']),
        gender=_xpath_string_mapping(dom, field_xpath_mapping['gender']),
    )


