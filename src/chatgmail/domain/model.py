import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    msg_id: str  # gmail message ID
    applied_position: str  # 應徵職務
    preferred_position: str  # 希望職稱
    # highest_education_level: str  # 最高學歷
    self_introduction: str  # 個人簡介
    self_recommendation: str  # 自我推薦
    msg_receive_date: str  # 應徵快照：2023/03/09 09:34
    job_104_code: str  # 代碼：1689936700883
    name: str  # 應徵者名字
    age: str  # 年齡
    gender: str  # 性別
    desired_job_title: str  # 希望職稱
    employment_status: str  # 就業狀態
    work_experiences: object  # 工作經驗
    education: str  # 教育背景
    lang_proficiency: str  # 語文能力
    specialized_skills: str  # 專長技能
    autobiography: str  # 自傳
    comment: str = ''  # 評論結果
    inspection: str = None

    def __repr__(self):
        _work = f'{self.work_experiences[0]}' if (isinstance(self.work_experiences, list)
                                                  and len(self.work_experiences)) else f'{self.work_experiences}'
        return (f'{self.name} for {self.applied_position} with {self.age}, {self.gender}, '
                f'{_work[:45]}...')

    def to_markdown(self) -> str:
        """convert to md format"""
        if isinstance(self.work_experiences, list):
            _work_experiences = '\n'.join([f'- {ex}' for ex in self.work_experiences])
        else:
            _work_experiences = self.work_experiences
        _md = f"""
# {self.name} ({self.job_104_code}) 

# 應徵職務：{self.applied_position}

# 基本資料
- 年齡：{self.age}
- 性別：{self.gender}
- 應徵快照：{self.msg_receive_date}
- 希望職稱：{self.desired_job_title}
- 就業狀態：{self.employment_status}

# 自我推薦
{self.self_recommendation}

# 希望職稱
{self.preferred_position}

# 自我簡介
{self.self_introduction}

# 工作經驗
{_work_experiences}

# 教育背景
{self.education}

# 語文能力
{self.lang_proficiency}

# 專長技能
{self.specialized_skills}

# 自傳
{self.autobiography}
        """
        return _md

    def digest(self) -> dict:
        assert isinstance(self.work_experiences, list), f'work_experiences is not a list: {self.work_experiences}'
        _max = 3
        _total = len(self.work_experiences)
        _n = _total if _total < _max else _max
        _exs = [f'{ex[:350]}...' for ex in self.work_experiences[:_n]]
        _digest = {
            'msg_id': self.msg_id,
            'name': self.name,
            'age': self.age,
            'applied_position': self.applied_position,
            'preferred_position': self.preferred_position,
            'receive_date': self.msg_receive_date,
            'job_104_code': self.job_104_code,
            'edu': f'{self.education[:80]}...',
            f'work ({_n}/{_total})': _exs,
            'skills': f'{self.specialized_skills[:350]} ...',
            'bio': f'{self.autobiography[:350]} ...'
        }
        return _digest

    def validate(self) -> bool:
        """
        Validate the candidate data.
        """
        _detail = {
            'msg_id': all([self.msg_id]),
            'applied_position': all([self.applied_position]),
            'preferred_position': all([self.preferred_position]),
            'self_recommendation': all([self.self_recommendation]),
            'msg_receive_date': all([self.msg_receive_date]),
            'job_104_code': all([self.job_104_code]),
            'desired_job_title': all([self.desired_job_title]),
            'employment_status': all([self.employment_status]),
            'name': all([self.name]),
            'age': all([self.age]),
            'gender': all([self.gender]),
            'work_experiences': all([self.work_experiences]),
            'education': all([self.education]),
        }
        logger.debug(f'validate detail: {_detail}')
        return all(
            [
                self.msg_id,
                # self.applied_position,
                # self.self_recommendation,
                self.preferred_position,
                self.msg_receive_date,
                self.job_104_code,
                self.desired_job_title,
                self.employment_status,
                self.name,
                self.age,
                self.gender,
                # self.work_experiences,
                self.education,
            ]
        )
