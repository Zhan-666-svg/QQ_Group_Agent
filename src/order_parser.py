# -*- coding: utf-8 -*-
import re

def parse_ecommerce_order(text: str) -> dict:
    """
    电商订单与地址解析提取器：
    专门针对订单号、收件人、手机号/隐私分机号、省市区详细地址、商品规格、物流备注等复合格式
    样例支持：
      - 5127480146240009319，张荣，17898745795-9219，云南省 昆明市 官渡区 关上街道 菜鸟驿站(青棚新村39号店)
      - 小鸭KA WBH30339LXY星河灰   刘先生，17809844054-5969， 青海省 西宁市 城北区 马坊街道柴达木路172号和泰居小区
      - 小鸭4.0高温白KA WBH40JU528T，发顺丰   张松柏，18472166356-5415， 湖北省 荆州市 松滋市 新江口街道 划子嘴小区15栋2501
      - 5.6高端热烘干白色
    """
    raw = (text or "").strip()
    if not raw:
        return {}

    order_id = ""
    recipient = ""
    phone = ""
    province = ""
    city = ""
    district = ""
    address = ""
    product_spec = ""
    remark = ""

    # 1. 提取订单号（>=15 位连续数字，且前后不能是更多数字）
    m_order = re.search(r"(?<!\d)(\d{15,25})(?!\d)", raw)
    clean_line = raw
    if m_order:
        order_id = m_order.group(1)
        # 将订单号从待分析文本中去除，避免后续手机号或规格误判
        clean_line = clean_line.replace(order_id, " ")

    # 2. 提取手机号/虚拟分机号：11位开头1[3-9]，可选带 -xxxx 或 _xxxx
    m_phone = re.search(r"(?<!\d)(1[3-9]\d{9}(?:[-_#转]\d{3,6})?)(?!\d)", clean_line)
    if m_phone:
        phone = m_phone.group(1)

    # 3. 提取特殊备注（如发顺丰、加急等）
    for r_kw in ["发顺丰", "顺丰包邮", "顺丰特快", "顺丰速运", "发京东", "送货上门", "加急发货", "加急"]:
        if r_kw in raw:
            remark = r_kw
            break

    # 4. 提取收件地址（从中国省/直辖市/自治区，或市/区特征一直到末尾）
    addr_match = re.search(
        r"((?:(?:北京|天津|上海|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆)(?:省|自治区|直辖市|市)?\s*)?"
        r"[^\s，,、]{2,10}(?:市|地区|自治州|盟)?\s*"
        r"[^\s，,、]{2,10}(?:区|县|市|旗|海域|岛)\s*"
        r"[\s\S]+)$", clean_line
    )
    extra_spec = ""
    if addr_match:
        full_addr = addr_match.group(1).strip()
        if remark and remark in full_addr:
            full_addr = full_addr.replace(remark, "").strip(" ，,、")
        
        # 检查地址后是否有换行附带的下半部分规格（例如样例3末尾的 5.6高端热烘干白色）
        addr_lines = [l.strip() for l in full_addr.split("\n") if l.strip()]
        if len(addr_lines) > 1:
            address = addr_lines[0]
            extra_spec = " ".join(addr_lines[1:])
        else:
            address = full_addr

        # 提取省市区
        p_match = re.search(r"^([^\s，,、]{2,6}?(?:省|自治区|直辖市|市))\s*([^\s，,、]{2,6}?市)?\s*([^\s，,、]{2,6}?(?:区|县|市|旗))?", address)
        if p_match:
            province = p_match.group(1) or ""
            city = p_match.group(2) or ""
            district = p_match.group(3) or ""

    # 5. 提取收件人姓名与商品型号
    if phone:
        # 以手机号为锚点，人名一般在手机号紧靠的左侧
        parts = clean_line.split(phone)
        prefix = parts[0].strip(" ，,、\t")
        
        # 按照逗号或多个连续空格切分候选块
        sub_tokens = [t.strip() for t in re.split(r"[，,;\t\n]+|\s{2,}", prefix) if t.strip()]
        
        if sub_tokens:
            cand = sub_tokens[-1]
            # 人名一般小于等于8个字
            if len(cand) <= 8 and not re.search(r"(?:KA|WBH|型号|白色|灰色|黑色|烘干|公斤|kg)", cand, re.I):
                recipient = cand
                if len(sub_tokens) > 1:
                    product_spec = " ".join(sub_tokens[:-1])
            else:
                product_spec = " ".join(sub_tokens)
    else:
        # 没有手机号的短句或规格消息（如 "5.6高端热烘干白色"）
        product_spec = clean_line

    if extra_spec:
        if product_spec:
            product_spec = f"{product_spec} / {extra_spec}"
        else:
            product_spec = extra_spec

    # 清理商品规格中夹带的备注
    if remark and remark in product_spec:
        product_spec = product_spec.replace(remark, "").strip(" ，,、")

    return {
        "order_id": order_id,
        "recipient": recipient,
        "phone": phone,
        "province": province,
        "city": city,
        "district": district,
        "address": address,
        "product_spec": product_spec,
        "remark": remark
    }
