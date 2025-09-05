import jieba
import jieba.analyse

async def gen_keyword(sentence: str, top_k: int) -> list:
    """
    关键词抽取，适用于中长文本，通用领域
    """
    keyword_list = jieba.analyse.textrank(sentence, topK=top_k, withWeight=False, allowPOS=('ns', 'nr', 'n', 'vn', 'v'))
    """
    参数说明：
    sentence: 待提取的文本, 
    topK: 返回几个关键词, 
    withWeight: 是否附带权重值, 
    allowPOS: 允许作为关键词的词性(ns: 地名, nr: 人名, n: 名词, vn: 动名词, v: 动词)
    """
    return keyword_list