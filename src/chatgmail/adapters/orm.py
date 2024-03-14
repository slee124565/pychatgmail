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

    # 關鍵字列表
    keywords = [
        '應徵職務：',
        '個人資料',
        '求職者希望條件',
        '工作經歷',
        '教育背景',
        '語文能力',
        '技能專長',
        '自傳',
    ]

    # 使用 XPath 找到所有 class 屬性包含 mail__container 的 <table> 標籤
    xpath_string = "//table[contains(@class, 'mail__container')]"
    tables = dom.xpath(xpath_string)
    logger.debug(f"tables: {len(tables)}")

    # 存儲匹配到的信息
    matches = []

    if tables:
        # 在第一個 mail__container <table> 元素中，找到所有子 <table> 標籤
        parent_table = tables[0]
        child_tables = parent_table.xpath(".//table")

        # 遍歷所有找到的子 <table> 標籤
        for index, child_table in enumerate(child_tables):
            table_text = etree.tostring(child_table, method="text", encoding="unicode")

            # 對每個關鍵詞進行檢查
            for keyword in keywords:
                if keyword in table_text:
                    # 紀錄匹配到的關鍵詞及其所在的子表格索引和在文本中的位置
                    keyword_position = table_text.find(keyword)
                    matches.append({
                        "child_table_index": index,
                        "keyword": keyword,
                        "position": keyword_position
                    })

    # 輸出匹配到的信息
    for match in matches:
        logger.debug(
            f"Child Table Index: {match['child_table_index']}, Keyword: '{match['keyword']}', Position: {match['position']}")

    return model.Candidate(
        msg_id=msg_id,
        applied_position=_xpath_string_mapping(dom, field_xpath_mapping['applied_position']),
        self_recommendation=_xpath_string_mapping(dom, field_xpath_mapping['self_recommendation']),
        job_104_code=_xpath_string_mapping(dom, field_xpath_mapping['job_104_code']),
        name=_xpath_string_mapping(dom, field_xpath_mapping['name']),
        age=_xpath_string_mapping(dom, field_xpath_mapping['age']),
        gender=_xpath_string_mapping(dom, field_xpath_mapping['gender']),
    )
