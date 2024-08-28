import bs4
from lxml import etree
import os
import json
import re
import logging
from chatgmail.domain import model

logger = logging.getLogger(__name__)


def _xpath_key_table_mapping(dom: etree.HTML) -> dict:
    # 关键词列表
    keywords = [
        '應徵職務：',
        '個人資料',
        '求職者希望條件',
        '工作經歷',
        '教育背景',
        '語文能力',
        '技能專長',
        '自傳',
        '附件',
        '專案成就',
        '其他作品'
    ]

    # 使用 XPath 找到所有 class 属性包含 mail__container 的 <table> 标签
    xpath_string = "//table[contains(@class, 'mail__container')]"
    tables = dom.xpath(xpath_string)

    # 在第一个 mail__container <table> 元素中，找到所有子 <table> 标签
    parent_table = tables[0]
    child_tables = parent_table.xpath(".//table")

    # 儲存簡歷 table 文字訊息
    _count = 0
    contents = []
    for _table in child_tables:
        table_text = etree.tostring(_table, method="text", encoding="unicode")
        table_text = ' '.join(table_text.split())  # 清理文本
        # 显示每个 child_table 的摘要信息
        logger.debug(f'{_count}: {table_text[:50]}...')
        _count += 1
        contents.append(table_text)

    # 存储匹配到的信息
    matches = []

    for keyword in keywords:
        match_found = False
        if tables:
            # 遍历所有找到的子 <table> 标签
            for index, child_table in enumerate(child_tables):
                # 使用 etree.tostring() 方法并设置 method="text" 来获取纯文本，然后清理空白符
                table_text = etree.tostring(child_table, method="text", encoding="unicode")
                table_text = ' '.join(table_text.split())  # 清理文本

                # 检查关键词是否在文本开头
                if table_text.startswith(keyword):
                    matches.append({
                        "keyword": keyword,
                        "child_table_index": index,
                        "position": 0
                    })
                    match_found = True
                    break  # 匹配到后即跳出循环

        # 如果没有找到匹配项，则添加没有匹配的记录
        if not match_found:
            matches.append({
                "keyword": keyword,
                "child_table_index": None,
                "position": None
            })

    # 输出匹配到的信息
    for match in matches:
        logger.debug(
            f"Keyword: '{match['keyword']}', Child Table Index: {match['child_table_index']}, Position: {match['position']}")

    # 蒐集 keyword '工作經歷' 到 keyword '教育背景' 之間 tables 的所有文字
    logger.debug(f'contents: {len(contents)}')
    work_ex_matched = next((match for match in matches if match['keyword'] == '工作經歷'), None)
    logger.debug(f'work_ex_matched: {work_ex_matched}')
    edu_matched = next((match for match in matches if match['keyword'] == '教育背景'), None)
    logger.debug(f'edu_matched: {edu_matched}')
    if not work_ex_matched or not edu_matched:
        raise ValueError('No matched keyword found for "工作經歷" or "教育背景"')
    logger.debug(f'contents sliced: {work_ex_matched["child_table_index"] + 2}: {edu_matched["child_table_index"]}')
    # work_experience = contents[work_ex_matched['child_table_index']+2:edu_matched['child_table_index']]

    experiences = contents[work_ex_matched['child_table_index'] + 2:edu_matched['child_table_index']]
    work_experiences = []

    # 使用 range 函数和 len(contents) 确定循环范围，步长为 2
    # 使用 min 函数确保在 contents 为奇数长度时不会出现索引越界
    for i in range(0, min(len(experiences), len(experiences) - len(experiences) % 2), 2):
        # 格式化字符串并添加到新的列表中

        # 檢查關鍵字是否存在
        skill_keyword = "工作技能"
        content_keyword = "工作內容"

        _experience = experiences[i + 1]
        skill_index = _experience.find(skill_keyword)
        content_index = _experience.find(content_keyword)

        # 如果兩個關鍵字都存在，擷取「工作技能」字串（包含）之後的內容
        if skill_index != -1 and content_index != -1:
            _experience = _experience[skill_index:]

        # 如果只有「工作內容」存在，擷取「工作內容」字串（包含）之後的內容
        elif skill_index == -1 and content_index != -1:
            _experience = _experience[content_index:]

        # 如果兩個關鍵字都不存在，直接回覆原始字串
        else:
            pass

        work_experience = f'曾經任職公司：{experiences[i]} ，當時的{_experience}'
        work_experiences.append(work_experience)

    # 如果 contents 的长度为奇数，处理最后一个元素
    if len(experiences) % 2 != 0:
        work_experience = f'曾經任職公司：{experiences[-1]} ，當時的工作內容：未提供'
        work_experiences.append(work_experience)

    # 打印结果
    for experience in work_experiences:
        logger.debug(experience)

    # 擷取 keyword '教育背景' 對應到的 position_index + 1 table 的文字
    education_matched = next((match for match in matches if match['keyword'] == '教育背景'), None)
    education = contents[education_matched['child_table_index'] + 1]
    logger.debug(f'education: {education}')

    # 擷取 keyword '語文能力' 對應到的 position_index + 1 table 的文字
    lang_proficiency = next((match for match in matches if match['keyword'] == '語文能力'), None)
    lang_proficiency = contents[lang_proficiency['child_table_index'] + 1] \
        if lang_proficiency['child_table_index'] else ''
    logger.debug(f'lang_proficiency: {lang_proficiency}')

    # 擷取 keyword '技能專長' 對應到的 position_index + 1 table 的文字
    specialized_skills = next((match for match in matches if match['keyword'] == '技能專長'), None)
    specialized_skills = contents[specialized_skills['child_table_index'] + 1] \
        if specialized_skills['child_table_index'] else ''
    logger.debug(f'specialized_skills: {specialized_skills}')

    # 擷取 keyword '自傳' 對應到的 position_index + 1 table 的文字
    autobiography_matched = next((match for match in matches if match['keyword'] == '自傳'), None)
    autobiography = contents[autobiography_matched['child_table_index'] + 1] \
        if autobiography_matched['child_table_index'] else ''
    logger.debug(f'autobiography: {autobiography}')

    return {
        '工作經歷': work_experiences,
        '教育背景': education,
        '語文能力': lang_proficiency,
        '技能專長': specialized_skills,
        '自傳': autobiography,
    }


def _xpath_string_mapping(dom: etree.HTML, xpath: str) -> str:
    elements = dom.xpath(xpath)
    logger.debug(f'xpath: {xpath}')
    logger.debug(f'elements: {elements}')
    if elements:
        if hasattr(elements[0], 'text'):
            inner_text = elements[0].text
        else:
            inner_text = f'{elements[0]}'.strip()
        value = inner_text if inner_text else ''
    else:
        value = ''
    return value.replace('\n', '').strip()


def _soup_find_th_field_value(soup: bs4.BeautifulSoup, th_name: str) -> str:
    desired_header_row = soup.find("th", string=th_name)
    if desired_header_row:
        return desired_header_row.find_next_sibling("td").get_text(strip=True)
    else:
        return ''


def candidate_mapper(msg_id: str, resume_104_html: str) -> model.Candidate:
    """
    Map the 104 job application resume HTML to Candidate object.
    """
    soup = bs4.BeautifulSoup(resume_104_html, 'html.parser')
    dom = etree.HTML(str(soup))

    field_xpath_mapping = {
        'applied_position': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a',
        'matched_position': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a',
        # 'self_recommendation': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[2]/td/div[2]',
        'self_recommendation': '/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td',
        'msg_received_date': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[2]/text()[1]',
        'job_104_code': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[2]/text()[2]',
        'job_104_code_matched': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[2]',
        'name': "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span",
        'name2': "/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/a/b",
        # /html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span
        # /html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/a/b
        'age': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/text()[1]',
        'gender': '/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/text()[2]',
        'desired_job_title': '/html/body/table[2]/tbody/tr/td/table[3]/tbody/tr[2]/td/div[2]/table/tbody/tr[2]/td',
        'employment_status': '/html/body/table[2]/tbody/tr/td/table[5]/tbody/tr[1]/td',
    }

    # 找到郵件 title 分類：配對信、轉寄履歷(完整)、主動應徵履歷
    _title = soup.title.string.strip()

    # 找到所有符合「自我推薦」「轉寄」的 <div> 標籤
    _self_recommendation = ''
    if _title == '主動應徵履歷':
        # 查找包含 "自我推薦" 的 <div> 标签
        self_intro_div = soup.find("div", string="自我推薦：")
        # 找到相邻的 <div> 标签并提取其文本内容
        if self_intro_div:
            adjacent_div = self_intro_div.find_next("div", class_="py-1 font-16 inline-block mb-width-492 vtop")
            if adjacent_div:
                _self_recommendation = adjacent_div.get_text(strip=True)
        _msg_receive_date = _xpath_string_mapping(dom, field_xpath_mapping['msg_received_date'])
        _job_104_code = _xpath_string_mapping(dom, field_xpath_mapping['job_104_code'])
    else:
        _search_class = 'px-5 pt-0 pb-0 text-left'  # py-1 font-16 inline-block mb-width-492 vtop
        td_elements = soup.find_all("td", class_=_search_class)
        _self_recommendation = td_elements[0].get_text().replace('\n', ' ') if len(td_elements) else ''
        _self_recommendation = f'{_title}:{_self_recommendation}'
        _msg_receive_date = ''
        _job_104_code = _xpath_string_mapping(dom, field_xpath_mapping['job_104_code_matched'])

    # 找到包含「希望職稱」的 th 元素，擷取所對應的實際字串
    _preferred_position = _soup_find_th_field_value(soup=soup, th_name='希望職稱')
    _highest_education_level = _soup_find_th_field_value(soup=soup, th_name='最高學歷')
    _self_introduction = _soup_find_th_field_value(soup=soup, th_name='個人簡介')

    key_contents = _xpath_key_table_mapping(dom)
    # '工作經歷': work_experiences,
    # '教育背景': education,
    # '自傳': autobiography,

    return model.Candidate(
        msg_id=msg_id,
        applied_position=_xpath_string_mapping(dom, field_xpath_mapping['applied_position']),
        preferred_position=_preferred_position,
        # self_recommendation=_xpath_string_mapping(dom, field_xpath_mapping['self_recommendation']),
        self_recommendation=_self_recommendation,
        self_introduction=_self_introduction,
        msg_receive_date=_msg_receive_date,
        job_104_code=_job_104_code,
        name=_xpath_string_mapping(dom, field_xpath_mapping['name']) if _xpath_string_mapping(dom, field_xpath_mapping[
            'name']) else _xpath_string_mapping(dom, field_xpath_mapping['name2']),
        age=_xpath_string_mapping(dom, field_xpath_mapping['age']),
        gender=_xpath_string_mapping(dom, field_xpath_mapping['gender']),
        desired_job_title=_xpath_string_mapping(dom, field_xpath_mapping['desired_job_title']),
        employment_status=_xpath_string_mapping(dom, field_xpath_mapping['employment_status']),
        work_experiences=key_contents.get('工作經歷', ''),
        education=key_contents.get('教育背景', ''),
        lang_proficiency=key_contents.get('語文能力', ''),
        specialized_skills=key_contents.get('技能專長', ''),
        autobiography=key_contents.get('自傳', ''),
    )
