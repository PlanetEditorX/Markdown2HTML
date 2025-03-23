import os
import re
import markdown
from pathlib import Path

root_folder = '' # 当前目录

# 递归遍历目录树
def deep_directory(path):
    for item in path.rglob('*.md'):
        # 分离文件名和后缀
        path, _ext = os.path.splitext(item._raw_path)
        markdown_text = read_file(path)
        HTML2File(markdown_text, path)

# 打开Markdown文件并读取内容
def read_file(path, ext='.md'):
    try:
        with open(path + ext, 'r', encoding='utf-8') as md_file:
            return md_file.read()
    except Exception as e:
        print(f"▻ 读取{path}发生异常:", e)

# markdown内容转换
def content_convert(text, path):
    # 替换#和UUID
    pattern = r"(?:#)?\^.{8}-.{4}-.{4}-.{4}-.{12}"
    text = re.sub(pattern, "", text)

    # 替换md为html
    text = re.sub(f".md", ".html", text)

    # 替换路径
    # 使用 splitlines() 方法拆分换行符并去除空项
    text_list = [item for item in text.splitlines() if item]
    pattern = r"(assets/.*\.html)"
    result_list = []
    parent = Path(path).parent._raw_path
    for item in text_list:
        site = re.search(pattern, item)
        if site:
            result = re.sub(pattern, lambda match: parent + '\\' + match.group(1), item)
            result_list.append(result.replace("/", "\\"))
        else:
            result_list.append(item)
    result ="\n\n".join(result_list)
    return result

# 将HTML保存到文件
def HTML2File(text, path):
    # 转换Markdown到HTML
    html_output = markdown.markdown(content_convert(text, path))
    with open(path+'.html', 'w', encoding='utf-8') as file:
        file.write(html_output)

# 地址转换
def HTML_PATH(path):
    # 逐行读取文件
    html = read_file(path, '.html')
    print(html)
    # 替换路径
    # 使用 splitlines() 方法拆分换行符并去除空项
    text_list = [item for item in text.splitlines() if item]
    pattern = r"(assets/.*\.html)"
    result_list = []
    for item in text_list:
        site = re.search(pattern, item)
        if site:
            result = re.sub(pattern, lambda match: path + '\\' + match.group(1), item)
            result_list.append(result.replace("/", "\\"))
        else:
            result_list.append(item)
    result ="\n\n".join(result_list)
    # # 转换Markdown到HTML
    # html_output = markdown.markdown(content_convert(text))
    # with open(path+'.html', 'w', encoding='utf-8') as file:
    #     file.write(html_output)


if __name__ == "__main__":
    # 指定目录路径
    path = os.getcwd() + "\\test"
    directory = Path(path)
    deep_directory(directory)
