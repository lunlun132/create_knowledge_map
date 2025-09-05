""""这个文件是对文件进行预处理"""

import os
from app.service.file_parser import extract_file_content
from app.service.keyword_extract import gen_keyword
from cnocr import CnOcr  # 导入CnOcr库用于OCR识别
from time import time
from typing import Union
from fastapi import APIRouter, UploadFile

doc_process = APIRouter(prefix="/document", tags=["文档"])  # 创建一个APIRouter实例用来处理文档相关的路由，其中prefix表示路由的前缀，tags用于给路由打标签，方便文档分类
ocr = CnOcr()  # 创建一个CnOcr实例用于OCR识别

@doc_process.post(
    path="/pre_process", 
    summary="文件预处理",
    description="文件预处理，包括读取文件内容、关键字抽取、文本向量化、关键字向量化"
)
async def gen_doc_content(
    file: Union[UploadFile, None] = None,
    sentence_size: int = 2000
):
    """文件预处理，包括读取文件内容、关键字抽取、文本向量化、关键字向量化

    Args:
        file (Union[UploadFile, None], optional): 上传的文件. Defaults to None.
        sentence_size (int, optional): 每个句子的最大长度. Defaults to 2000.

    Returns:
        dict: 返回处理后的文件内容（含原始文件名、唯一文件名、提取内容、处理耗时等）
    """
    # 1. 获取文件名
    file_name = os.path.splitext(file.filename)[0]  # 获取文件名（不包含扩展名）
    # 2. 读取文件内容
    content = await extract_file_content(file)
    # 3. 关键词抽取
    keyword = await gen_keyword(content, top_k=10)
    # 4. 文本向量化
    