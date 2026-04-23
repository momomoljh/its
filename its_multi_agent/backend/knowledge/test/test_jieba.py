import jieba

result = jieba.lcut("我来到北京清华大学",cut_all=True)
print(result)

print(set("我来到北京清华大学"))