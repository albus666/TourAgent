#!/usr/bin/env python3
"""
整合脚本：自动使用pip freeze获取包列表，然后通过pip show获取确切版本号
生成干净的requirements.txt文件
"""
import os
import subprocess
import re
import sys

def get_installed_packages():
    """使用pip freeze获取已安装的包列表"""
    try:
        print("正在获取已安装的包列表...")
        result = subprocess.run(
            ['pip', 'freeze'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        packages = []
        for line in result.stdout.strip().split('\n'):
            # 处理pip freeze输出中的每一行
            if line:
                # 提取包名（去除版本号）
                match = re.match(r'^([a-zA-Z0-9_\-]+)', line)
                if match:
                    package_name = match.group(1)
                    packages.append(package_name)
        
        print(f"找到{len(packages)}个已安装的包")
        return packages
    except Exception as e:
        print(f"错误: 执行pip freeze命令时出错: {str(e)}")
        return []

def get_package_info(package_name):
    """使用pip show获取包的详细信息"""
    try:
        result = subprocess.run(
            ['pip', 'show', package_name], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            print(f"警告: 无法获取包 {package_name} 的信息")
            return None
        
        # 解析输出
        info = {}
        for line in result.stdout.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    except Exception as e:
        print(f"错误: 执行pip show {package_name}时出错: {str(e)}")
        return None

def generate_requirements():
    """生成requirements.txt文件"""
    packages = get_installed_packages()
    if not packages:
        print("未找到已安装的包，无法生成requirements.txt文件")
        return False
    
    requirements = []
    total = len(packages)
    
    print(f"正在获取{total}个包的详细信息...")
    for i, package_name in enumerate(packages, 1):
        print(f"[{i}/{total}] 处理包: {package_name}")
        
        info = get_package_info(package_name)
        if info and 'Name' in info and 'Version' in info:
            # 使用包的确切名称和版本
            name = info['Name']
            version = info['Version']
            requirements.append(f"{name}=={version}")
        else:
            # 如果无法获取详细信息，则只使用包名
            requirements.append(package_name)
    
    # 排序和写入文件
    requirements.sort()
    output_file = "requirements.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for req in requirements:
            f.write(f"{req}\n")
    
    print(f"\n成功创建requirements.txt文件，包含{len(requirements)}个包")
    print(f"文件位置: {os.path.abspath(output_file)}")
    
    # 显示文件内容预览
    print("\n文件内容预览:")
    for i, req in enumerate(requirements[:10], 1):
        print(f"  {i}. {req}")
    
    if len(requirements) > 10:
        print(f"  ... 以及{len(requirements)-10}个其他包")
    
    return True

if __name__ == "__main__":
    print("=== 自动生成requirements.txt ===")
    print("该脚本将使用pip freeze获取包列表，然后通过pip show获取确切版本号")
    generate_requirements() 