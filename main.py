import os
import re
import sys
import shutil
import markdown
from pathlib import Path
from pypinyin import lazy_pinyin
from types import SimpleNamespace

root_folder = '' # 当前目录
css_path = ''
# 标题列表
tilte_list = [
    ['一、','二、','三、','四、','五、','六、','七、','八、','九、','十、','十一、','十二、','十三、','十四、','十五、','十六、','十七、','十八、','十九、','二十、'],
    ['（一）','（二）','（三）','（四）','（五）','（六）','（七）','（八）','（九）','（十）','（十一）','（十二）','（十三）','（十四）','（十五）','（十六）','（十七）','（十八）','（十九）','（二十）']
]
# 对应目录字典
menu_dict = {}
# 转换类型
inline_folder = False
# 单独文件夹，只执行部分操作
is_single = False
# 监控传入的根目录
monitoring_path = ''
# 分隔
divide = '\\'

# 递归遍历目录树
def deep_directory(path, _type='md'):
    global css_path
    if _type == 'md':
        # 为直接目录
        if inline_folder and not is_single:
            # 拷贝css样式
            shutil.copy(css_path, str(path))
            css_path = str(path) + f"{divide}styles.css"
        if is_single:
            _path, _ext = os.path.splitext(str(path))
            print(f"转换文件：{_path}")
            css_path = str(monitoring_path) + f"{divide}styles.css"
            markdown_text = read_file(str(path))
            content_convert(markdown_text, _path)
        else:
            for item in path.rglob('*.md'):
                # 分离文件名和后缀
                path, _ext = os.path.splitext(str(item))
                print(f"转换文件：{path}")
                markdown_text = read_file(str(item))
                content_convert(markdown_text, path)
    elif _type == 'html':
        if is_single:
            print(f"校验文件：{path.name}")
            HTML_PATH(path)
            print(f"校验完成：{path.name}")
        else:
            # 地址转换, 因为需要查找文件是否存在，所以地址转换分离
            for item in path.rglob('*.html'):
                print(f"校验文件：{item}")
                HTML_PATH(item)
    # 生成目录
    else:
        dir_list = []
        entries = sorted(
            [entry for entry in os.scandir(path) if entry.is_dir() and entry.name not in [".git", ".github",".obsidian",".trash", "Markdown2HTML"]],  # 过滤条件
            key=lambda e: e.name  # 按名称排序
        )
        for entry in entries:
            if not inline_folder:
                # 拷贝css样式
                shutil.copy(css_path, entry)
                css_path = entry.path + f"{divide}styles.css"
            # 是否是全是文件夹的结构
            is_all_dir = True
            if not inline_folder:
                dir_list = []
            inline_html_list = []
            for folder in os.scandir(entry.path):
                if not inline_folder:
                    html_list = []
                    # 最外层目录
                    if folder.is_dir():
                        # 次级目录
                        for item in os.scandir(folder.path):
                            if item.name.endswith('html'):
                                print(f"找到目录项：{entry.name}{divide}{folder.name}")
                                html_list.append(item)
                        # 按拼音排序
                        html_list = sorted(html_list, key=lambda x: lazy_pinyin(x.name))
                        if html_list:
                            dir_list.append({
                                'father': folder,
                                'childrens': html_list
                            })
                    elif folder.name not in ['styles.css', 'index.html', '.gitignore']:
                        is_all_dir = False
                else:
                    if folder.name.endswith('html'):
                        print(f"找到目录项：{entry.name}{divide}{folder.name}")
                        add_html = SimpleNamespace(**{
                            'name': folder.name,
                            'path': f"." + folder.path.replace(str(root_folder), '')
                        })
                        inline_html_list.append(add_html)
                        inline_html_list = sorted(inline_html_list, key=lambda x: lazy_pinyin(x.name))

            if inline_folder:
                dir_list.append({
                            'father': entry,
                            'childrens': inline_html_list
                        })

            if not inline_folder:
                # 全是文件夹，生成目录页
                dir_list = sorted(dir_list, key=lambda x: lazy_pinyin(x['father'].name))
                if is_all_dir and not inline_folder:
                    index_page(dir_list, entry)
        # 直接目录
        if inline_folder:
            # 将字典转换为 SimpleNamespace 对象
            index_page(dir_list, SimpleNamespace(**{
                'name': path.name,
                'path': str(path)
            }))
# 打开Markdown文件并读取内容
def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as md_file:
            return md_file.read()
    except Exception as e:
        print(f"▻ 读取{path}发生异常:", e)

# 查找文件绝对地址
def find_absolute_path(path):
    # 将输入路径转换为Path对象
    target = Path(path)
    if target.is_absolute():
        return str(target.resolve())  # 直接返回规范化的绝对路径

    # 递归搜索相对路径
    _list = list(root_folder.glob(f"**/{path}"))
    return str(_list[0].resolve()) if _list else path

# 替换图片路径
def replace_with_img(match, path):
    img_path = match.group(1)  # 图片路径
    abs_img_path = find_absolute_path(img_path)
    rel_path = relative_address(path, abs_img_path)
    if rel_path:
        img_path = rel_path
    try:
        align = match.group(2)  # L 或 R
        width = match.group(3)  # 宽度
    except IndexError:
        align = ''
        width = ''
    img_tag = f'<img src="{img_path}" alt="Image"'
    if align:
        # 如果有 |L 或 |R，可以添加对应的 CSS 类
        if align == 'L':
            img_tag += ' class="align-left"'
        elif align == 'R':
            img_tag += ' class="align-right"'
    if width:
        img_tag += f' width="{width}"'
    else:
        img_tag += f'  style="max-width: 80%;"'
    img_tag += '>'
    return img_tag

# Mermaid图表样式
def mermaid_style(index, uuid):
    match index % 5:
        case 0:
            fill = "e1f5fe"
            stroke = "2196f3"
        case 1:
            fill = "e8f5e9"
            stroke = "4caf50"
        case 2:
            fill = "f3e5f6"
            stroke = "9c27b0"
        case 3:
            fill = "fff8e1"
            stroke = "ffc107"
        case 4:
            fill = "ffebee"
            stroke = "f44336"
    return f"style {uuid} fill:#{fill},stroke:#{stroke}"

# 数字转化
def num_to_seq(level, num):
    if not isinstance(num, int) or num < 0:
        return num
    # 小于20直接从参数中读取数据
    if num <= 20:
        return tilte_list[level-1][num-1]
    match level:
        case 3:
            return f"{num}."
        case 4:
            return f"({num})"

    units = ['', '十', '百', '千', '万', '十', '百', '千', '亿']
    chinese_num = {
        0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
        5: '五', 6: '六', 7: '七', 8: '八', 9: '九'
    }
    result = ''
    str_num = str(num)
    length = len(str_num)
    for i in range(length):
        n = int(str_num[i])
        if n != 0:
            result += chinese_num[n] + units[length - i - 1]
        else:
            if not result.endswith('零'):
                result += '零'
    # 处理连续的零
    result = result.replace('零零', '零')
    # 处理零万、零亿
    result = result.replace('零万', '万')
    result = result.replace('零亿', '亿')
    # 处理最后的零
    result = result.rstrip('零')
    match level:
        case 1:
            return f"{result}、"
        case 2:
            return f"（{result}）"
    return result

# 目录页
def index_page(data, info):
    """
    生成目录页
    :param data: 首页网页数据
    :param info: 目录信息
        - name: 目录名字
        - path: 目录地址
    """
    global menu_list
    head = head_chunk(info.name, "") + "</head>"
    body_text = ''
    for folder in enumerate(data):
        # 最近序号，去除【数字】
        if folder[1]['childrens']:
            body_text += f"<h3><a href=\"{folder[1]['childrens'][0].path}\">{num_to_seq(1, folder[0]+1)}{re.sub(r'【\d+】', '', folder[1]['father'].name)}</a></h3></h3>\n"
        for child in enumerate(folder[1]['childrens']):
            body_text += f"<p><a href=\"{child[1].path}\">{num_to_seq(2, child[0]+1)}{child[1].name.replace(".html", "")}</a></p>\n"
            menu_dict[child[1].path.replace(".html", "")] = f"{info.path}{divide}index.html"
    body = "<body>\r\n<hr style='border-top-style: dotted !important;'>" + body_text + "</body>\r\n</html>"
    write_file(head + body, f"{info.path}{divide}index.html")

# head片段
def head_chunk(title, root_path=''):
    global css_path
    if root_path:
        css_path = root_path + "styles.css"
    else:
        css_path = "styles.css"
    return f"<!DOCTYPE html>\r\n<html lang=\"zh-CN\">\r\n<head>\r\n<meta charset=\"UTF-8\">\r\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\r\n<title>{title}</title>\r\n<link rel=\"stylesheet\" href=\"{css_path}\">\r\n"

# 地址转换相对地址
def relative_address(father, child):
    if not isinstance(father, Path):
        father = Path(father)
    if not isinstance(child, Path):
        child = Path(child)
    # print(f"父目录：{father}")
    # print(f"子文件：{child}")
    result = ''
    if child.suffix == '.png':
        result = str(child).replace(str(father), '')
        if result[0] == divide:
            result = result.replace(divide, "", 1)
    while (child.parent!= father):
        result += f'..{divide}'
        child = child.parent
    return result

# markdown内容转换
def content_convert(text, path):
    global css_path, root_folder
    is_root = False
    child_path = Path(path)
    ground_father_path = child_path.parent.parent
    menu_path = ''
    # 直接目录当上上级为根目录时
    if inline_folder and str(ground_father_path) == str(root_folder) or (is_single and (str(monitoring_path) == str(ground_father_path) or str(monitoring_path.parent) == str(ground_father_path))):
        is_root = True
        if is_single:
            if str(monitoring_path) == str(ground_father_path):
                menu_path = str(monitoring_path)
            else:
                menu_path = str(ground_father_path)
        else:
            menu_path = str(root_folder)
        menu_path = relative_address(menu_path, child_path)
        menu_start = f"<blockquote>\n<p><a href=\"{menu_path}index.html\">首页</a></p></blockquote>\n"
        menu_end = f"<hr style='border-top-style: dotted !important;'>\n<blockquote>\n<p><a href=\"{menu_path}index.html\">END</a></p></blockquote>\n"
    # 多一级目录
    if not inline_folder and str(ground_father_path.parent) == str(root_folder):
        is_root = True
        menu_start = f"<blockquote>\n<p><a href=\"{str(ground_father_path)}{divide}index.html\">首页</a></p></blockquote>\n"
        menu_end = f"<hr style='border-top-style: dotted !important;'>\n<blockquote>\n<p><a href=\"{str(ground_father_path)}{divide}index.html\">END</a></p></blockquote>\n"
        # 拷贝css样式
        shutil.copy(css_path, str(ground_father_path))
        css_path = str(ground_father_path) + f"{divide}styles.css"
    # 替换md为html
    text = re.sub(f".md", ".html", text)
    # 转换Markdown到HTML
    body = markdown.markdown(text)
    pattern = r'!\[\[(assets/[^|]+)\|?([A-Z])?\|?(\d+)?\]\]'
    if not menu_path:
        menu_path = relative_address(root_folder, path)
    head = head_chunk(Path(path).name, menu_path)
    # 有数学公式
    if re.search(r'(.*\$.*\^.*)|(frac)', text):
        head += "<script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\r\n<script>MathJax={ tex: { inlineMath: [['$', '$'], ['" + "f{divide}(', '{divide}$']] } };</script>"
    # 有Mermaid图表
    if re.search(r'(mermaid)', text):
        head += "<script src=\"https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js\"></script>\r\n<script>mermaid.initialize({startOnLoad: true,theme: 'neutral',securityLevel: 'loose',flowchart: { useMaxWidth: false,htmlLabels: true } });</script>"

    head += "</head>"

    # 替换所有匹配的内容
    if is_root:
        body = "<body>\r\n" + menu_start + re.sub(pattern, lambda m: replace_with_img(m, Path(path).parent), body).replace('target="_blank"', '') + menu_end + "</body>\r\n"
    body = "<body>\r\n" + re.sub(pattern, lambda m: replace_with_img(m, Path(path).parent), body).replace('target="_blank"', '') + "</body>\r\n"

    if re.search(r'(mermaid)', body):
        # 找到第一个匹配的```mermaid,并循环替换对应的```mermaid... ```
        _pattern = r"```mermaid"
        match = re.search(_pattern, body)
        while match:
            # 找到开始位置
            start_index = match.end()
            # 替换 ```mermaid 为 <div class="mermaid"> 只替换第一个
            start = re.sub(r'```mermaid', r'<div class="mermaid">', body[:start_index], count=1)
            # 找到结束位置
            match_2 = re.search(r"```", body[start_index:])
            end_index = start_index + match_2.end()
            # 替换第一个 ``` 为 </div>
            end = re.sub(r'```', r'</div>', body[start_index:end_index], count=1)
            cleaned_text = re.sub(r'<p>|</p>|</div>', '', end)
            # 颜色处理
            color_pattern = r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b'
            uuids_list = re.findall(color_pattern, cleaned_text)
            if uuids_list:
                line_style = "style emperor fill:#ffd700,stroke:#ffa500,stroke-width:2px"
                for _item in enumerate(uuids_list):
                    line_style += "\n" +mermaid_style(_item[0], _item[1])
            # 确保 Mermaid 代码格式正确
            end = re.sub(r'--&gt;', '-->', cleaned_text) + f"{line_style}</div>"
            body = start + end + body[end_index:]
            match = re.search(_pattern, body)

    end = "</html>"

    write_file(head + body + end, f"{path}.html")

# 将HTML保存到文件
def write_file(text, path):
    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(text)
    except Exception as e:
        print(f"▻ 写入{path}发生异常:", e)

# 地址转换
def HTML_PATH(path):
    # 读取文件
    html = read_file(str(path))
    # 匹配所有的超链接
    pattern = r'<a[^>]*\s+href="([^"]+)"'
    matches = re.findall(pattern, html)
    if matches:
        for item in matches:
            if item == f"..{divide}":
                continue
            name = item.split('#')
            new_name = ''
            # 进入子页
            if 'assets' in name[0]:
                # 同子页
                if 'assets' in str(path):
                    new_path = Path(name[0]).name
                    html = html.replace(item, new_path)
            else:
                # 返回目录
                if len(name) > 1 and '^' in name[1]:
                    abs_path = Path(find_absolute_path(name[0]))
                    # 次级目录，子项
                    if 'assets' in str(abs_path):
                        new_path = abs_path.name + name[1]
                    else:
                        new_path = f'..{divide}..{divide}..{divide}' + name[0]
                # 返回首页
                else:
                    # 文件存在时替换为绝对地址
                    abs_path = Path(find_absolute_path(name[0]))
                    if abs_path.name == 'index.html':
                        new_path = f'..{divide}'
                    else:
                        if str(abs_path.parent) == '.':
                            new_path = ''
                        else:
                            new_path = relative_address(root_folder, abs_path.parent)

                    new_name = abs_path.name
                html = html.replace(item, new_path + new_name)
    # 锚点
    html = html.replace('#^', '#')
    # 替换UUID为id
    html_list = [s for s in html.split('\n') if s != ""]
    for i in range(len(html_list)):
        pattern = r"\^.{8}-.{4}-.{4}-.{4}-.{12}"
        match = re.search(pattern, html_list[i])
        if match:
            # 去除默认的锚点
            item = re.sub(pattern, "", html_list[i])
            # 去除前方的^
            _id = f" id=\"{match.group(0)[1:]}\""
            # 将锚点添加到a标签中作为id
            _pattern = r'<a href="([^"]+)"'
            _match = re.search(_pattern, item)
            # 超链接的情况
            if _match:
                _end = _match.end()
                html_list[i] = item[:_end] + _id + item[_end:]
            else:
                # 非超链接的情况
                _match = re.search(r'>', item)
                _start = _match.start()
                html_list[i] = item[:_start] + _id + item[_start:]
    html = '\n'.join(html_list)
    write_file(html, str(path))

def merge_css_advanced(file1, file2, output_file, add_comments=True, minify=False):
    """
    合并CSS文件（支持注释和压缩）
    :param file1: normal片段css文件路径
    :param file2: 自定义css文件路径
    :param output_file: 输出文件路径
    :param add_comments: 是否添加来源注释
    :param minify: 是否压缩CSS（需安装 csscompressor 库）
    """
    try:
        # 验证文件存在性
        for f in [file1, file2]:
            if not Path(f).exists():
                raise FileNotFoundError(f"文件不存在: {f}")

        # 读取文件内容
        css1 = Path(file1).read_text(encoding='utf-8')
        css2 = Path(file2).read_text(encoding='utf-8')

        # 压缩处理
        if minify:
            try:
                from csscompressor import compress
                css1 = compress(css1)
                css2 = compress(css2)
            except ImportError:
                print("未安装 csscompressor 库，跳过压缩步骤")
                minify = False

        # # 合并内容
        files = [(file1, css1), (file2, css2)]  # 扩展文件列表
        merged = []

        for idx, (file, css) in enumerate(files):
            # 添加分隔符（从第二个文件开始）
            if idx > 0:
                merged.append("\n" if not add_comments else f"\n/* === {os.path.basename(file)} === */")

            # 添加CSS内容
            merged.append(css)

        # 写入文件
        Path(output_file).write_text('\n'.join(merged), encoding='utf-8')

        print(f"css合并成功！文件大小: {os.path.getsize(output_file)} 字节")
        return True

    except Exception as e:
        print(f"错误: {str(e)}")
        return False

# 保存监控目录
def init_path(path):
    global monitoring_path
    if path.endswith(divide):
        path = path[:-1]
    monitoring_path = Path(path)

# 清除所有变量
def clear_all_cariable():
    global root_folder, css_path, menu_dict, inline_folder, is_single, monitoring_path
    root_folder = ''
    css_path = ''
    menu_dict = {}
    inline_folder = False
    is_single = False
    monitoring_path = ''

# 主函数
def run(path):
    global inline_folder, css_path, root_folder, is_single
    inline_folder = True
    css_path = os.getcwd() + f"{divide}module{divide}html{divide}tyles.css"
    if not os.path.exists(css_path):
        css_path = f"..{divide}module{divide}html{divide}styles.css"
    root_folder = Path(path)
    if root_folder.is_dir():
        print("Markdown转为HTML...")
        deep_directory(root_folder, 'md')
        print("HTML 链接校验...")
        deep_directory(root_folder, 'html')
        print("目录生成...")
        deep_directory(root_folder, 'menu')
    else:
        # xmind修改触发，传入xmind路径
        is_single = True
        print("Markdown转为HTML...")
        root_folder = Path(path.replace("xmind", "md"))
        deep_directory(root_folder, 'md')
        print("HTML 链接校验...")
        root_folder = Path(path.replace("xmind", "html"))
        deep_directory(root_folder, 'html')

if __name__ == "__main__":
    inline_folder = True
    if len(sys.argv) > 1:
        # 获取命令行参数，手动输入需要转换的目录
        # 参数1：外层地址，该地址下为多个需要转换的文件夹
        # 参数2：0: 外部有一层文件夹 1: 实际所在文件夹
        #       C:\Users\DearX\Documents\Github\Markdown2HTML\test 1 ---> 外层文件夹，在里面具体目录下生成目录
        #       C:\Users\DearX\Documents\Github\Markdown2HTML\test\GWY---> 实际文件夹，直接在该地址下生成目录
        path = sys.argv[1]
        if len(sys.argv) > 2 and int(sys.argv[2]):
            inline_folder = False
    else:
        # 指定目录路径,将需要转为html的目录放在该目录下
        # path = os.getcwd() + "\\test"
        path = os.getcwd()
    # css_path = os.getcwd() + "\\module\\html\\styles.css"

    if sys.platform.startswith('linux'):
        divide = '/'
    css_module_path = os.getcwd() + divide + "module.css"
    css_path = os.getcwd() + divide + "styles.css"
    # 是否是obsidian
    obsidian_css = f"{path}{divide}.obsidian{divide}snippets{divide}normal.css"
    if os.path.exists(obsidian_css):
        print("找到Obsidian的css样式")
        merge_css_advanced(
            obsidian_css,
            css_module_path,
            css_path,
            add_comments=True,
            minify=False
        )
    root_folder = Path(path)
    print("Markdown转为HTML...")
    deep_directory(root_folder, 'md')
    print("HTML 链接校验...")
    deep_directory(root_folder, 'html')
    print("目录生成...")
    deep_directory(root_folder, 'menu')
    print("Markdown转为HTML操作完成...")
