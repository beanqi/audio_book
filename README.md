## 拆分Epub文件，按照章节拆分

### 安装依赖
```
pip install -r requirements.txt
```


### 本地运行
```
python .\epub_parser.py wuchang.epub zhangwuchang --level 2
```
参数说明：
- wuchang.epub：epub文件
- zhangwuchang：拆分后的文件夹
- --level 2：拆分的层级，2表示按照二级章节拆分，建议先按照一级章节拆分，再按照二级章节拆分，依次类推，因为有些epub文件只有一级目录

### 以接口形式运行
```
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

接口说明：
```
 curl -X POST \                                                                
  -F "file=@./通胀，还是通缩：全球经济迷思 ([日]渡边努) (Z-Library).epub" \
  -F "level=1" \
  http://localhost:5000/parse_epub --output 1.zip
```

参数说明：
- file：epub文件
- level：拆分的层级，1表示按照一级章节拆分，2表示按照二级章节拆分，建议先按照一级章节拆分，再按照二级章节拆分，依次类推，因为有些epub文件只有一级目录



## 按照章节总结内容
