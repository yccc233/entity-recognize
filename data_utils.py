import re


def split_text_to_sentences(text):
    # 文本数据清洗，文本转句子
    text.replace('\t', '')
    text.replace('\n', '')
    return text.split('。')


def split_text_to_paragraph(text):
    text.replace('\t', '')
    return text.split('\n')


def split_paragraph_to_sentences(paragraph):
    if paragraph.find('。') < 0:
        return []
    sentences = [p.strip() + '。' for p in paragraph.split('。') if p]
    return sentences


def classify_kind_to_list(predict):
    # 分类json格式的返回值，按照covid，gene，phen，protein顺序返回列表
    covid = gene = phen = protein = []
    if 'COVID' in predict:
        covid = predict['COVID']
    if 'GENE' in predict:
        gene = predict['GENE']
    if 'PHEN' in predict:
        phen = predict['PHEN']
    if 'DISEASE' in predict:
        phen = phen + predict['DISEASE']  # 目前将疾病和表型合并
    if 'PROTEIN' in predict:
        protein = predict['PROTEIN']
    return covid, gene, phen, protein


def handle_list_to_highlight(covid, gene, phen, protein):
    hl = []
    for c in covid:
        hl.append(['COVID', c])
    for g in gene:
        hl.append(['GENE', g])
    for p in phen:
        hl.append(['PHEN', p])
    for p in protein:
        hl.append(['PROTEIN', p])
    return hl


def getDouble_by_sentence(predict):
    # 通过一句话的分析获取两元组的关系，返回一个二维列表，具体index包括种类1，name1，种类2，name2
    # 第一层是covid，第二层是gene，第三层是phen
    # protein也属于第二层，disease属于第三层
    dou = []
    GENE = []
    PHEN = []
    # 获取基因型，gene和protein重复的即忽略
    if 'GENE' in predict:
        GENE += predict['GENE']
    elif 'PROTEIN' in predict:
        GENE += predict['PROTEIN']

    if 'PHEN' in predict:
        PHEN += predict['PHEN']
    if 'DISEASE' in predict:
        PHEN += predict['DISEASE']

    if 'COVID' in predict:  # 有新冠关键字
        if GENE:
            for gene in GENE:
                dou.append(['covid', 'COVID-19', 'gene', gene])
        if PHEN:
            for phen in PHEN:
                dou.append(['covid', 'COVID-19', 'phen', phen])
    if GENE and PHEN:
        for gene in GENE:
            for phen in PHEN:
                dou.append(['gene', gene, 'phen', phen])
    return dou


def getDouble_by_sentence_and_isCovid(predict, isCovid):
    # 通过一句话的分析获取两元组的关系，返回一个二维列表，具体index包括种类1，name1，种类2，name2
    # 第一层是covid，第二层是gene，第三层是phen
    # protein也属于第二层，disease属于第三层
    # 与上一个方法不同的是这个是根据段落来判断与新冠的关系
    dou = []
    GENE = []
    PHEN = []
    # 获取基因型，gene和protein重复的即忽略
    if 'GENE' in predict:
        GENE += predict['GENE']
    if 'PROTEIN' in predict:
        GENE += predict['PROTEIN']

    if 'PHEN' in predict:
        PHEN += predict['PHEN']
    if 'DISEASE' in predict:
        PHEN += predict['DISEASE']

    if isCovid:  # 有新冠有关（段落内）
        if GENE:
            for gene in GENE:
                dou.append(['covid', 'COVID-19', 'gene', gene])
        if PHEN:
            for phen in PHEN:
                dou.append(['covid', 'COVID-19', 'phen', phen])
    if GENE and PHEN:
        for gene in GENE:
            for phen in PHEN:
                dou.append(['gene', gene, 'phen', phen])
    return dou


# 清洗text数据，符号乱入
def clean_text_character(text):
    li = list(text)

    for i in range(len(li)):
        if li[i] == '.':
            if 0 < i < len(li) and li[i - 1].isdigit() and li[i + 1].isdigit():  # 小数形式
                pass
            else:
                li[i] = '。'
            if li[0] == '.':
                li = li[1:]
            if li[-1] == '.':
                li = li[:-1]
        if li[i] == ';' or li[i] == '；':
            li[i] = '。'
        if li[i] == ' ':
            if (li[i - 1].islower() or li[i - 1].isupper() or li[i - 1].isdigit()) and (li[i + 1].islower() or li[i + 1].isupper() or li[i + 1].isdigit()):
                pass
            else:
                li[i] = ''
        if li[i] == '/' and li[i - 1] == '和':
            li[i] = ''
        if li[i] == '-' and li[i-1].islower() and (li[i+1].islower() or li[i+1].isupper()):
            li[i] = ' '
        if li[i] == ',':
            li[i] = '，'
        if li[i] == '|':
            li[i] = ''
        if li[i] in ['\'', '\"', '“', '”']:
            li[i] = ''
        if li[i] in ['!', '！', '？', '?']:
            li[i] = '。'

    return ''.join(li)


# 清洗文本数据
def clean_sentences(sentences):
    for sen in sentences:  # 删除空元素
        if not sen:
            sentences.remove(sen)
    for i in range(len(sentences)):
        sentences[i] = sentences[i].strip()
    return sentences


# 清洗实体识别数据，这是个二维数组
def clean_entities_from_predict(entitis):
    tar_entitis = []
    for entity in entitis:
        if entity not in tar_entitis and not re.search(r"[()（）%@&*$¥#!]", entity[1]):
            entity[1] = entity[1].replace('_', '-')
            tar_entitis.append(entity)
    return tar_entitis


if __name__ == '__main__':
    str = '新型冠状病毒感染的肺炎潜伏期一般为3~7d,多数不超过14d,但目前发现最长可达24天或许更长。以发热、乏力、干咳为主要表现，少数患者伴有鼻塞、流涕、腹泻等症状。重型病例多在一周后出现呼吸困难，严重者快速进展为急性呼吸窘迫综合征、脓毒症休克、难以纠正的代谢性酸中毒和出凝血功能障碍。'

    print(split_paragraph_to_sentences(str))
