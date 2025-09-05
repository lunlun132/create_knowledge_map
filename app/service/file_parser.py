import os
import docx
import subprocess
from cnocr import CnOcr
from PIL import Image
from PyPDF2 import PdfReader
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import Union  # 仅保留必要的类型注解

# 初始化OCR实例（按需可改为函数内初始化，避免全局占用资源）
ocr = CnOcr()


async def extract_file_content(file: Union[object, None]) -> str:
    """
    提取上传文件的文字内容，仅返回纯文本内容
    
    Args:
        file: FastAPI UploadFile对象（或支持read()的文件对象）
    
    Returns:
        str: 提取到的纯文本内容（空字符串表示提取失败或无内容）
    
    Raises:
        ValueError: 不支持的文件格式
        Exception: 其他提取过程中的异常（如文件损坏、工具缺失等）
    """
    # 1. 校验文件是否为空
    if not file:
        return ""
    
    # 2. 一次性读取文件二进制内容（避免重复read导致后续读空）
    file_buffer = await file.read()
    # 获取文件后缀（转小写，兼容大小写后缀如.PDF/.DocX）
    file_ext = os.path.splitext(file.filename)[1].lower()
    content = ""

    try:
        # 3. 按文件格式分支提取内容
        if file_ext == ".pdf":
            # PDF内容提取
            pdf_reader = PdfReader(BytesIO(file_buffer))
            for page in pdf_reader.pages:
                # 避免None值拼接，空页面补空字符串
                page_text = page.extract_text() or ""
                content += page_text + "\n"  # 换行区分页面

        elif file_ext == ".docx":
            # Docx内容提取（删除无关的唯一文件名生成逻辑）
            doc = docx.Document(BytesIO(file_buffer))
            content_list = []
            
            for node in doc.element.xpath('//w:body/*'):
                node_text = ""
                # 处理altChunk节点（外部嵌入内容）
                if not isinstance(node, docx.oxml.xmlchemy.BaseOxmlElement):
                    if node.tag == f'{{{node.nsmap[node.prefix]}}}altChunk':
                        # 提取关联的r:id，校验是否存在
                        r_id = node.attrib.get(f'{{{node.nsmap["r"]}}}id')
                        if r_id and r_id in doc.part.rels:
                            # 解码内容，忽略特殊字符避免崩溃
                            node_text = doc.part.rels[r_id].target_part.blob.decode('utf-8', errors='ignore')
                # 处理表格节点
                elif node.tag == f'{{{node.nsmap[node.prefix]}}}tbl':
                    # 表格内容按行|列拼接，添加标识便于区分
                    table_rows = []
                    for row in node.xpath('.//w:tr'):
                        row_cells = [''.join(cell.xpath('.//w:t/text()')) or "" for cell in row.xpath('.//w:tc')]
                        table_rows.append('|'.join(row_cells))
                    node_text = f"[表格开始]\n{'\n'.join(table_rows)}\n[表格结束]"
                # 处理普通文本节点
                else:
                    node_text = ''.join(node.xpath('.//w:t/text()')) or ""
                
                # 过滤空内容，非空才添加
                if node_text.strip():
                    content_list.append(node_text.strip())
            
            # 列表转字符串，换行分隔
            content = "\n".join(content_list)

        elif file_ext == ".doc":
            # Doc内容提取（依赖antiword工具，需确保服务器已安装）
            with NamedTemporaryFile(delete=True) as tmp_file:
                # 写入二进制内容到临时文件
                tmp_file.write(file_buffer)
                tmp_file.flush()  # 确保内容写入磁盘
                
                # 调用antiword转换为UTF-8文本
                result = subprocess.run(
                    f"antiword -mUTF-8 {tmp_file.name}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                # 转换成功则取stdout，失败返回空
                content = result.stdout if result.returncode == 0 else ""

        elif file_ext in [".jpg", ".png"]:
            # 图片OCR提取文字
            img = Image.open(BytesIO(file_buffer))
            ocr_result = ocr.ocr(img)
            # 拼接所有OCR识别结果
            content = ''.join([item['text'] for item in ocr_result])

        elif file_ext in ['.txt', '.md', '.html']:
            # 纯文本/Markdown/HTML提取（HTML可后续补充标签清理）
            content = file_buffer.decode('utf-8', errors='ignore')

        else:
            # 不支持的格式，抛出异常（便于上层捕获处理）
            raise ValueError(f"不支持的文件格式：{file_ext}，仅支持PDF、docx、doc、jpg、png、txt、md、html")

        # 4. 返回提取到的纯文本（去除首尾空字符）
        return content.strip()

    except Exception as e:
        raise Exception(f"文件内容提取失败：{str(e)}") from e