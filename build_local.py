#!/usr/bin/env python3
"""
本地构建脚本 - 用于渲染 Scriban 模板
这个脚本会读取 source.json 并渲染 Website 目录中的模板文件
"""

import json
import re
import os
import shutil
from pathlib import Path

def load_source_json(lang='zh'):
    """加载配置文件"""
    if lang == 'en':
        source_file = 'source.en.json'
    elif lang == 'zh':
        source_file = 'source.zh.json'
    else:
        source_file = 'source.json'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def simple_template_render(template, data):
    """
    简单的模板渲染器（支持基本的 Scriban 语法）
    注意：这是一个简化版本，可能不支持所有 Scriban 功能
    """
    result = template
    
    # 处理简单的变量替换 {{ variable }}
    def replace_var(match):
        var_path = match.group(1).strip()
        try:
            value = data
            for key in var_path.split('.'):
                value = value[key]
            return str(value) if value is not None else ''
        except (KeyError, TypeError):
            return ''
    
    # 移除 Scriban 的空白控制符 ~
    result = re.sub(r'\{\{~\s*', '{{', result)
    result = re.sub(r'\s*~\}\}', '}}', result)
    
    # 处理条件语句 {{if condition; }}...{{end;}}
    def process_conditionals(text):
        # 简化处理：只处理存在性检查
        pattern = r'\{\{if\s+([^;]+);\s*\}\}(.*?)\{\{end;\s*\}\}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            content = match.group(2)
            
            # 检查条件是否为真
            try:
                value = data
                for key in condition.split('.'):
                    value = value.get(key) if isinstance(value, dict) else None
                    if value is None:
                        return ''
                return content if value else ''
            except:
                return ''
        
        return re.sub(pattern, replace_if, text, flags=re.DOTALL)
    
    # 处理循环 {{for item in items}}...{{end}}
    def process_loops(text):
        pattern = r'\{\{for\s+(\w+)\s+in\s+(\w+)\s*\}\}(.*?)\{\{end\s*\}\}'
        
        def replace_loop(match):
            item_name = match.group(1)
            array_name = match.group(2)
            loop_content = match.group(3)
            
            try:
                items = data.get(array_name, [])
                result_parts = []
                for item in items:
                    item_content = loop_content
                    # 替换循环项中的变量
                    for key, value in item.items():
                        item_content = item_content.replace(f'{{{{ {item_name}.{key} }}}}', str(value))
                    result_parts.append(item_content)
                return ''.join(result_parts)
            except:
                return ''
        
        return re.sub(pattern, replace_loop, text, flags=re.DOTALL)
    
    # 应用处理
    result = process_conditionals(result)
    result = process_loops(result)
    result = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, result)
    
    return result

def build_website(lang='all', output_dir='dist'):
    """构建网站 - 现在构建包含所有语言的单个页面"""
    print(f"正在构建网站...")
    
    # 加载中英文配置
    config_zh = load_source_json('zh')
    config_en = load_source_json('en')
    
    # 语言文本
    lang_texts = {
        'zh': {
            'switch_lang': 'English',  # 中文页面显示 English
            'search_placeholder': '搜索...',
            'add_to_vcc': '添加到VCC',
            'copy': '复制',
            'published_by': '发布者',
            'name_header': '名称',
            'type_header': '类型',
            'add_to_vcc_btn': '添加至 VCC',
            'download_zip': '下载.ZIP'
        },
        'en': {
            'switch_lang': '中文',  # 英文页面显示 中文
            'search_placeholder': 'Search...',
            'add_to_vcc': 'Add to VCC',
            'copy': 'Copy',
            'published_by': 'Published by',
            'name_header': 'Name',
            'type_header': 'Type',
            'add_to_vcc_btn': 'Add to VCC',
            'download_zip': 'Download .ZIP'
        }
    }
    
    # 准备中文数据
    listing_info_zh = {
        'Name': config_zh.get('name', ''),
        'Description': config_zh.get('description', ''),
        'Url': config_zh.get('url', ''),
        'BannerImage': config_zh.get('bannerUrl', ''),
        'BannerImageUrl': config_zh.get('bannerUrl', ''),
        'Author': config_zh.get('author', {}),
        'InfoLink': config_zh.get('infoLink', {}),
        'LangTexts': lang_texts['zh']
    }
    
    # 准备英文数据
    listing_info_en = {
        'Name': config_en.get('name', ''),
        'Description': config_en.get('description', ''),
        'Url': config_en.get('url', ''),
        'BannerImage': config_en.get('bannerUrl', ''),
        'BannerImageUrl': config_en.get('bannerUrl', ''),
        'Author': config_en.get('author', {}),
        'InfoLink': config_en.get('infoLink', {}),
        'LangTexts': lang_texts['en']
    }
    
    # 处理中文包列表
    package_display_names_zh = {'com.rlvrc.cn': '中文活动日历'}
    package_descriptions_zh = {'com.rlvrc.cn': '在VRChat世界中显示中文节日和活动日历的组件'}
    
    packages_zh = []
    for pkg in config_zh.get('packages', []):
        pkg_name = pkg.get('name', '')
        packages_zh.append({
            'Name': pkg_name,
            'DisplayName': package_display_names_zh.get(pkg_name, pkg_name.split('.')[-1].title()),
            'Description': package_descriptions_zh.get(pkg_name, f"Package {pkg_name}"),
            'Version': '1.0.0',
            'Type': 'Package',
            'ZipUrl': pkg.get('releases', [None])[-1] if pkg.get('releases') else '',
            'Author': config_zh.get('author', {}),
            'Dependencies': {},
            'Keywords': [],
            'License': 'MIT',
            'LicensesUrl': ''
        })
    
    # 处理英文包列表
    package_display_names_en = {'com.rlvrc.cn': 'Chinese Events Calendar'}
    package_descriptions_en = {'com.rlvrc.cn': 'Component for displaying Chinese holidays and events calendar in VRChat worlds'}
    
    packages_en = []
    for pkg in config_en.get('packages', []):
        pkg_name = pkg.get('name', '')
        packages_en.append({
            'Name': pkg_name,
            'DisplayName': package_display_names_en.get(pkg_name, pkg_name.split('.')[-1].title()),
            'Description': package_descriptions_en.get(pkg_name, f"Package {pkg_name}"),
            'Version': '1.0.0',
            'Type': 'Package',
            'ZipUrl': pkg.get('releases', [None])[-1] if pkg.get('releases') else '',
            'Author': config_en.get('author', {}),
            'Dependencies': {},
            'Keywords': [],
            'License': 'MIT',
            'LicensesUrl': ''
        })
    
    # 默认使用中文
    template_data = {
        'listingInfo': listing_info_zh,
        'packages': packages_zh
    }
    
    # 创建输出目录
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)
    
    # 渲染 index.html（默认中文）
    print("渲染 index.html...")
    with open('Website/index.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    rendered_html = simple_template_render(template, template_data)
    with open(output_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    
    # 创建语言数据 JSON 文件供 JavaScript 使用
    print("创建语言数据...")
    lang_data = {
        'zh': {
            'listingInfo': listing_info_zh,
            'packages': packages_zh
        },
        'en': {
            'listingInfo': listing_info_en,
            'packages': packages_en
        }
    }
    
    with open(output_path / 'lang-data.json', 'w', encoding='utf-8') as f:
        json.dump(lang_data, f, ensure_ascii=False, indent=2)
    
    # 渲染 app.js
    print("渲染 app.js...")
    with open('Website/app.js', 'r', encoding='utf-8') as f:
        template = f.read()
    
    rendered_js = simple_template_render(template, template_data)
    
    with open(output_path / 'app.js', 'w', encoding='utf-8') as f:
        f.write(rendered_js)
    
    # 复制 styles.css
    print("复制 styles.css...")
    if os.path.exists('Website/styles.css'):
        shutil.copy('Website/styles.css', output_path / 'styles.css')
    
    # 复制 banner.png
    print("复制 banner.png...")
    if os.path.exists('Website/banner.png'):
        shutil.copy('Website/banner.png', output_path / 'banner.png')
    
    # 复制 favicon.ico（如果存在）
    if os.path.exists('Website/favicon.ico'):
        print("复制 favicon.ico...")
        shutil.copy('Website/favicon.ico', output_path / 'favicon.ico')
    
    print(f"✅ 构建完成！输出目录: {output_dir}")
    print(f"   中文版本: {output_dir}/index.html (默认)")
    print(f"   语言切换: 点击页面右上角按钮")
    print(f"   运行: cd {output_dir} && python -m http.server 8000")

if __name__ == '__main__':
    import sys
    
    output = sys.argv[1] if len(sys.argv) > 1 else 'dist'
    build_website('all', output)
