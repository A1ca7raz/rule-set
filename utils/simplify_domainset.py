#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import os

def compare_domain(x):
    ret = x.count('.') * 10
    match x[0]:
        case '*':
            ret += 2
        case '-':
            ret += 5
        case _:
            ret += 9
    return ret

def traverse_domains(trie, path=[]):
    """
    递归遍历 Trie 树并根据规则输出域名
    :param trie: 当前层级的字典
    :param path: 当前路径的域名分段（逆序存储，如 ['com', 'baidu']）
    """
    results = []

    # 获取当前节点的标记状态
    is_end = trie.get('_end_', False)
    is_wildcard_all = trie.get('*', False)
    is_wildcard_self = trie.get('-', False)

    # 构造当前完整的域名字符串 (例如: baidu.com)
    current_domain = ".".join(reversed(path))

    # --- 规则处理逻辑 ---

    # 规则 1 & 2: 出现 _end_ 或 * 时，输出并停止向下遍历（忽略子域名）
    # 同时出现 * 和 - 等同于无通配符，即 _end_
    if is_end or (is_wildcard_all and is_wildcard_self) or is_wildcard_all:
        if current_domain:
            # 如果是 * 规则且没有 _end_，按要求输出原域名（对应 *.a.b 逻辑）
            # 这里统一输出 current_domain，因为逻辑上它们都代表覆盖该级及其子域
            results.append(current_domain)
        return results  # 停止遍历子树

    # 规则 3: 仅出现 - 时，输出当前域名，但“继续”遍历子域名
    if is_wildcard_self:
        if current_domain:
            results.append(f"-.{current_domain}")
        # 不 return，继续执行下面的子节点遍历

    # 遍历子节点（排除标记位键）
    for key, value in trie.items():
        if key not in ['_end_', '*', '-']:
            results.extend(traverse_domains(value, path + [key]))

    return results

def simplify_domains_large_scale(input_file, output_file):
    # Trie 树根节点
    root = {}

    # 1. 读取并预处理
    if not os.path.exists(input_file):
        print(f"Error: 输入文件 '{input_file}' 不存在。")
        return

    print(f"[*] 正在读取 {input_file} ...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # 使用 set 去重并过滤掉空行和空白字符
            domains = list(set(line.strip() for line in f if line.strip()))
    except Exception as e:
        print(f"Error: 读取文件时发生错误: {e}")
        return

    # 2. 排序：按域名级数（点号数量）从小到大排序
    print(f"[*] 正在对 {len(domains)} 个域名进行层级排序...")
    domains.sort(key=compare_domain)

    # 3. 构建 Trie 树并流式写入
    print(f"[*] 开始简化并写入 {output_file} ...")
    count = 0
    for domain in domains:
        # 倒序处理域名段：a.b.com -> ['com', 'b', 'a']
        parts = domain.lower().split('.')[::-1]
        current = root
        is_subdomain = False
        end_flag = '_end_'

        for part in parts:
            if part in ['', '*', '-']:
                if part != '':
                    end_flag = part
                break
            # 如果路径上已经有结束标记，说明当前域名是某个已存在短域名的子域
            if '_end_' in current or '*' in current:
                is_subdomain = True
                break
            if part not in current:
                current[part] = {}
            current = current[part]

        # 如果不是子域名，标记结尾
        if not is_subdomain:
            current[end_flag] = True

    # 4. 提取域名集
    print(f"[*] 正在提取域名集...")
    final_domainset = traverse_domains(root)
    final_domainset.sort()

    try:
        with open(output_file, 'w', encoding='utf-8') as out:
            for domain in final_domainset:
                out.write(domain + '\n')
        print(f"[!] 处理成功！原始去重后: {len(domains)} -> 简化后: {len(final_domainset)}")
    except Exception as e:
        print(f"Error: 写入失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="域名集简化工具：自动合并子域名",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # 添加命令行参数
    parser.add_argument("-i", "--input", required=True, help="输入的原始域名文件路径 (txt)")
    parser.add_argument("-o", "--output", required=False, default="test.txt", help="简化的域名输出路径 (txt)")

    args = parser.parse_args()

    simplify_domains_large_scale(args.input, args.output)
