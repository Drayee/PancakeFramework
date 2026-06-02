"""
SQL 解析器
- #{param} 参数绑定 -> :param
- <if test="expr"> 条件 SQL
- <where> 自动处理 AND/OR
- <set> 自动处理逗号
- <foreach> 迭代集合
"""

import re


def _eval_test(test_expr: str, params: dict) -> bool:
    """评估 test 表达式，支持简单条件"""
    test_expr = test_expr.strip()

    # 处理 "and"/"or" 逻辑
    if " and " in test_expr:
        parts = test_expr.split(" and ", 1)
        return _eval_test(parts[0], params) and _eval_test(parts[1], params)
    if " or " in test_expr:
        parts = test_expr.split(" or ", 1)
        return _eval_test(parts[0], params) or _eval_test(parts[1], params)

    # 处理 "!= null" / "== null"
    if "!= null" in test_expr:
        key = test_expr.replace("!= null", "").strip()
        return params.get(key) is not None
    if "== null" in test_expr:
        key = test_expr.replace("== null", "").strip()
        return params.get(key) is None

    # 处理 "!= ''" / "== ''"
    if "!= ''" in test_expr:
        key = test_expr.replace("!= ''", "").strip()
        val = params.get(key)
        return val is not None and val != ""
    if "== ''" in test_expr:
        key = test_expr.replace("== ''", "").strip()
        val = params.get(key)
        return val is None or val == ""

    # 处理比较运算符
    for op in ["!=", ">=", "<=", "==", ">", "<", "="]:
        if op in test_expr:
            parts = test_expr.split(op, 1)
            key = parts[0].strip()
            val_str = parts[1].strip().strip("'\"")
            param_val = params.get(key)
            if param_val is None:
                return False
            try:
                val_str = type(param_val)(val_str)
            except (ValueError, TypeError):
                pass
            if op in ("==", "="):
                return param_val == val_str
            elif op == "!=":
                return param_val != val_str
            elif op == ">":
                return param_val > val_str
            elif op == "<":
                return param_val < val_str
            elif op == ">=":
                return param_val >= val_str
            elif op == "<=":
                return param_val <= val_str

    # 简单变量名 -> 检查是否为 truthy
    return bool(params.get(test_expr))


def _process_foreach(foreach_sql: str, params: dict) -> str:
    """处理 <foreach> 标签"""
    m = re.search(
        r'<foreach\s+collection="(\w+)"\s+item="(\w+)"(?:\s+open="([^"]*)")?'
        r'(?:\s+close="([^"]*)")?(?:\s+separator="([^"]*)")?\s*>(.*?)</foreach>',
        foreach_sql,
        re.DOTALL,
    )
    if not m:
        return foreach_sql

    collection_key, item_name = m.group(1), m.group(2)
    open_char = m.group(3) or ""
    close_char = m.group(4) or ""
    separator = m.group(5) or ","
    body = m.group(6).strip()

    items = params.get(collection_key, [])
    if not items:
        return ""

    parts = []
    for i, item_val in enumerate(items):
        part = body.replace(f"#{{{item_name}}}", f":__foreach_{collection_key}_{i}")
        params[f"__foreach_{collection_key}_{i}"] = item_val
        parts.append(part)

    return open_char + separator.join(parts) + close_char


def parse_sql(sql: str, params: dict) -> tuple[str, dict]:
    """
    解析 MyBatis 风格的 SQL，返回 (parsed_sql, bound_params)

    Args:
        sql: 带 MyBatis 标签的 SQL
        params: 参数字典

    Returns:
        (解析后的SQL, 绑定后的参数)
    """
    # 处理 <foreach> (先处理，因为它可能在 <if> 内)
    sql = re.sub(
        r'<foreach[^>]*>.*?</foreach>',
        lambda m: _process_foreach(m.group(0), params),
        sql,
        flags=re.DOTALL,
    )

    # 处理 <if test="...">
    def replace_if(match):
        test_expr = match.group(1)
        body = match.group(2)
        if _eval_test(test_expr, params):
            return " " + body + " "
        return " "

    sql = re.sub(
        r'\s*<if\s+test="([^"]*)">(.*?)</if>\s*',
        replace_if,
        sql,
        flags=re.DOTALL,
    )

    # 处理 <choose>/<when>/<otherwise>
    def replace_choose(match):
        choose_body = match.group(0)
        when_matches = re.findall(
            r'<when\s+test="([^"]*)">\s*(.*?)\s*</when>',
            choose_body,
            re.DOTALL,
        )
        for test_expr, body in when_matches:
            if _eval_test(test_expr, params):
                return body
        otherwise_match = re.search(
            r'<otherwise>\s*(.*?)\s*</otherwise>',
            choose_body,
            re.DOTALL,
        )
        if otherwise_match:
            return otherwise_match.group(1)
        return ""

    sql = re.sub(
        r'<choose>\s*(.*?)\s*</choose>',
        replace_choose,
        sql,
        flags=re.DOTALL,
    )

    # 处理 <where> - 去掉开头多余的 AND/OR
    def replace_where(match):
        body = match.group(1).strip()
        body = re.sub(r'^\s*(AND|OR)\s+', '', body, flags=re.IGNORECASE)
        if body:
            return "WHERE " + body
        return ""

    sql = re.sub(r'<where>\s*(.*?)\s*</where>', replace_where, sql, flags=re.DOTALL)

    # 处理 <set> - 去掉末尾多余的逗号
    def replace_set(match):
        body = match.group(1).strip()
        body = re.sub(r',\s*$', '', body)
        if body:
            return "SET " + body
        return ""

    sql = re.sub(r'<set>\s*(.*?)\s*</set>', replace_set, sql, flags=re.DOTALL)

    # #{param} -> :param
    sql = re.sub(r'#\{(\w+)\}', r':\1', sql)

    # 清理多余空白
    sql = re.sub(r'\s+', ' ', sql).strip()

    # 过滤掉 SQL 中未使用的参数
    used_params = set(re.findall(r':(\w+)', sql))
    # 保留 foreach 生成的参数
    foreach_params = {k for k in params if k.startswith("__foreach_")}
    filtered = {k: v for k, v in params.items() if k in used_params or k in foreach_params}

    return sql, filtered
