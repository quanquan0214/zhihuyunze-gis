import csv

with open('D:/Google/output/RSEI对比数据.csv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print("CSV文件列名:", reader.fieldnames)  # 打印所有列名