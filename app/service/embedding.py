from typing import Union, List
from app.service.chinese_text_split import ChineseTextSplitter

async def gen_embedding(text: Union[list[str], str]) -> list:
    """
    文本向量化
    """
    