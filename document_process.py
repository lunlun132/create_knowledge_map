""""这个文件是对文件进行预处理"""

import os
import docx  # 导入docx库用于处理Word文档
import uuid  # 导入uuid库用于生成唯一标识符
import random
import string  # 导入string库用于生成随机字符串
import subprocess  # 导入subprocess库用于调用外部命令

from cnocr import CnOcr  # 导入CnOcr库用于OCR识别
from PIL import Image  # 导入PIL库用于处理图像
from time import time
from typing import Union
from fastapi import APIRouter, UploadFile
from PyPDF2 import PdfReader  # 导入PyPDF2库用于处理PDF文件
from io import BytesIO  # 导入BytesIO用于处理二进制数据流
from tempfile import NamedTemporaryFile  # 导入NamedTemporaryFile用于创建临时文件

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
    st_time = time()  # 记录开始时间
    content = ""  # 初始化内容变量
    unique_filename = None  # 初始化唯一文件名（docx专用）

    # 1. 校验文件是否上传（修复：避免file为None时访问filename报错）
    if not file:
        return {
            "code": 400,
            "message": "请上传PDF或docx格式的文件",
            "data": None
        }
    
    # 2. 获取文件名和后缀
    file_name = os.path.splitext(file.filename)[0]
    ext = os.path.splitext(file.filename)[1].lower()  # 转小写，兼容".PDF"".DocX"等后缀
    
    try:
        # 3. 读取文件内容（按格式分支处理）
        if ext == ".pdf":
            pdf_reader = PdfReader(BytesIO(await file.read())) 
            for page in pdf_reader.pages:
                text = page.extract_text() or ""  # 修复：避免None值拼接
                content += text + "\n"  # 加换行区分页面，提升可读性
        
        elif ext == ".docx":
            doc = docx.Document(BytesIO(await file.read()))
            # 3.1 生成docx专属的唯一文件名（保持原有生成逻辑）
            name_prefix = str(uuid.uuid1()).replace("-", "")
            name_mid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            unique_filename = f"{name_prefix}_{name_mid}{ext}"
            
            content_list = []  # 用列表暂存内容，最后拼接（保持原有逻辑）
            for nd in doc.element.xpath('//w:body/*'):
                text = ""
                if not isinstance(nd, docx.oxml.xmlchemy.BaseOxmlElement):
                    # 3.2 处理altChunk节点（修复：补充r:id提取和校验，避免id未定义）
                    if nd.tag == f'{{{nd.nsmap[nd.prefix]}}}altChunk':
                        # 提取altChunk关联的r:id（关键修复：原代码直接用id，未定义）
                        r_id = nd.attrib.get(f'{{{nd.nsmap["r"]}}}id')
                        if r_id and r_id in doc.part.rels:
                            # 解码外部内容，添加错误处理避免特殊字符崩溃
                            text = doc.part.rels[r_id].target_part.blob.decode('utf-8', errors='ignore')
                        else:
                            text = ""
                    else:
                        text = ""
                elif nd.tag == f'{{{nd.nsmap[nd.prefix]}}}tbl':
                    # 3.3 处理表格（保持原有xpath逻辑，仅优化空值处理）
                    text = '\n'.join([
                        '|'.join([
                            ''.join(tc.xpath('.//w:t/text()')) or "" for tc in tr.xpath('.//w:tc')
                        ]) for tr in nd.xpath('.//w:tr')
                    ])
                    # 给表格内容加标识，方便后续区分
                    text = f"[表格开始]\n{text}\n[表格结束]"
                # （可选）若需恢复图片处理，取消注释下方代码（保持原有注释风格）
                # elif x := nd.xpath('.//@r:embed'):
                #     # 处理图片（需补充图片存储逻辑，此处暂留原有注释）
                #     img = doc.part.rels[x[0]].target_part
                #     img_path = "待补充图片存储路径（如MinIO）"
                #     text = f'![]({img_path})'
                else:
                    # 3.4 处理普通文本（保持原有xpath逻辑）
                    text = ''.join(nd.xpath('.//w:t/text()')) or ""
                
                # 3.5 过滤空内容（保持原有逻辑）
                text = text.strip()
                if text:
                    content_list.append(text)
            
            # 3.6 列表转字符串（保持原有逻辑）
            content = "\n".join(content_list)
        
        elif ext == ".doc":
            with NamedTemporaryFile(delete=True) as tmp:
                """
                创建一个临时文件对象
                delete=True表示文件在关闭后会自动删除
                使用with确保文件在使用后会被正确关闭
                """
                tmp.write(await file.read())  # 异步读取上传的文件内容，并写入临时文件
                tmp.flush()  # 确保所有写入的数据被保存到磁盘，清空缓冲区
                # TODO: 此处依赖antiword工具，需确保服务器已安装（如未安装需补充安装逻辑或替换为其他库）
                result = subprocess.run(f"antiword -mUTF-8 {tmp.name}", shell=True, capture_output=True, text=True)  # 将word文档转换为文本，指定输出编码为utf-8，tmp.name是临时文件的路径，允许通过shell执行命令
                if result.returncode == 0:
                    content = result.stdout  # 成功后，将转换后的文本内容赋值给 content 变量
                else:
                    # TODO: 补充处理转换失败的逻辑（如返回具体错误信息）
                    content = ""
        
        elif ext in [".jpg", ".png"]:
            # TODO: 可根据需要调整OCR模型参数（如识别语言、精度等）
            result = ocr.ocr(Image.open(BytesIO(await file.read())))
            content = ''.join([item['text'] for item in result])
        
        # 语音文件处理（待补充）
        # elif ext in [".mp3", ".mp4", ".wav"]:
        #     # TODO: 补充语音转文字逻辑（如使用 SpeechRecognition 库或API）
        #     pass
            
        elif ext in ['.txt', '.md', '.html']:
            # TODO: 对于html文件，可能需要补充标签清理逻辑（如使用BeautifulSoup）
            content = (await file.read()).decode('utf-8')  # 直接读取文本文件内容
        
        else:
            # 4. 处理不支持的文件格式
            return {
                "code": 400,
                "message": f"不支持{ext}格式，仅支持PDF、docx、doc、jpg、png、txt、md、html",  # 修复原提示信息不全的问题
                "data": None
            }
        
        # 5. 计算处理耗时
        cost_time = round(time() - st_time, 2)
        
        # 6. 返回结果（符合函数Returns定义的dict类型，补充关键信息）
        return {
            "code": 200,
            "message": "文件预处理成功",
            "data": {
                "original_file_name": f"{file_name}{ext}",  # 原始完整文件名
                "unique_file_name": unique_filename,  # docx专属唯一文件名（其他格式为None）
                "content": content.strip(),  # 去除首尾空字符，优化结果
                "content_length": len(content.strip()),  # 内容长度，方便校验
                "sentence_size": sentence_size,  # 返回入参，保持接口一致性
                "cost_time": f"{cost_time}s"  # 处理耗时
            }
        }
    
    except Exception as e:
        # 7. 捕获异常，返回错误信息
        # TODO: 生产环境中可补充日志记录逻辑，便于排查问题
        return {
            "code": 500,
            "message": f"文件预处理失败：{str(e)}",
            "data": None
        }