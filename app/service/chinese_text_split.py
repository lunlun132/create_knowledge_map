from typing import List
import re


class ChineseTextSplitter():
    def __init__(self, sentence_size: int = 512):
        self.sentence_size = sentence_size  # 类初始化时的默认长度（可备用）
    
    def split_text_by_sentence(self, text: str | List[str], max_len: int) -> List[str] | List[List[str]]:
        """
        先按中文标点断句，再按 max_len 合并句子，避免文本块过长/过短
        
        参数：
            text: 待分割文本（支持单字符串/多段落列表）
            max_len: 每个文本块的最大字符长度（核心控制参数）
        返回：
            分割后的文本块列表（与输入类型匹配：str→List[str]；List[str]→List[List[str]]）
        """
        # -------------------------- 2. 处理输入类型，调用内部逻辑 --------------------------
        if isinstance(text, str):
            return self._process_single_para(text, max_len)
        elif isinstance(text, list):
            # 新增：校验列表中每个元素是否为str
            for idx, para in enumerate(text):
                if not isinstance(para, str):
                    raise TypeError(f"列表第{idx+1}个元素类型为「{type(para)}」，需为str")
            return [self._process_single_para(para, max_len) for para in text]
        else:
            raise TypeError(f"不支持的输入类型「{type(text)}」，仅接受 str 或 List[str]")
    def _process_single_para(self, para: str, max_len: int = None) -> List[str]:
        if max_len is None:
            max_len = self.sentence_size
        
        # 步骤1：按中文标点断句（原逻辑不变）
        para_cut = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)
        para_cut = re.sub('(\.{6})([^”’])', r"\1\n\2", para)
        para_cut = re.sub('(\…{2})([^”’])', r"\1\n\2", para)
        para_cut = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
        single_sents = para_cut.rstrip().split("\n")
        
        # 新增：过滤空字符串（避免合并后出现空白）
        single_sents = [sent.strip() for sent in single_sents if sent.strip()]
        
        # 新增：处理「单个句子超过max_len」的情况
        processed_sents = []
        for sent in single_sents:
            if len(sent) <= max_len:
                processed_sents.append(sent)
            else:
                # 超长句按max_len分割（优先按逗号/分号分割，无则硬切）
                sub_sents = re.split(r'(?<=[，；])\s*', sent)  # 正向断言：按逗号/分号后分割
                # 若分割后仍有超长句（如无逗号），则硬切
                for sub_sent in sub_sents:
                    if len(sub_sent) <= max_len:
                        processed_sents.append(sub_sent)
                    else:
                        # 硬切：按max_len分段，避免单个块过长
                        for i in range(0, len(sub_sent), max_len):
                            processed_sents.append(sub_sent[i:i+max_len])
        
        # 步骤2：按max_len合并句子（原逻辑不变，将single_sents改为processed_sents）
        stack = []
        curr_len = 0
        merged_chunks = []
        for sent in processed_sents:
            sent_total_len = len(sent) + 1  # +1：句子间用换行符连接的长度
            if curr_len + sent_total_len > max_len and curr_len > 0:
                merged_chunks.append('\n'.join(stack))
                stack = []
                curr_len = 0
            stack.append(sent)
            curr_len += sent_total_len
        if stack:
            merged_chunks.append('\n'.join(stack))
        
        return merged_chunks