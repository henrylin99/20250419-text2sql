# 存储常见查询模式与对应SQL的知识库
# 可以随时修改和扩展这个知识库

QA_DATA = {
    "提示词": [
        "KDJ金叉",
        "MACD金叉",
        "量比大于2",
        "换手率大于 5%",
        "市盈率低于40%"
    ],
    "SQL": [
        "SELECT ts_code, stock_name, factor_kdj_k, factor_kdj_d FROM stock_business WHERE factor_kdj_k > factor_kdj_d AND factor_kdj_k<20 AND factor_kdj_d<20",
        "SELECT ts_code, stock_name, factor_macd_dif, factor_macd_dea FROM stock_business WHERE factor_macd_dif > factor_macd_dea",
        "SELECT ts_code, stock_name, volume_ratio FROM stock_business WHERE volume_ratio > 2",
        "SELECT ts_code, stock_name, turnover_rate FROM stock_business WHERE turnover_rate > 5",
        "SELECT ts_code, stock_name, pe FROM stock_business WHERE pe < 40"
    ]
}

# 技术指标解释，可以用于增强模型的理解
TECH_INDICATORS = {
    "KDJ金叉": "KDJ指标中，K线从下向上穿越D线，是一种买入信号。通常在K和D都低于20时更有效。",
    "MACD金叉": "MACD指标中，DIF线从下向上穿越DEA线，是一种买入信号。",
    "量比": "量比是指当日成交量与过去一段时间平均成交量之比。量比大于1表示放量，小于1表示缩量。",
    "换手率": "换手率是指一定时间内的成交量与流通股本之比，反映市场活跃度。",
    "市盈率": "市盈率是指股票价格与每股收益之比，反映股票的估值水平。"
}

def get_example_queries():
    """获取示例查询列表"""
    return QA_DATA["提示词"]

def get_example_sql(index):
    """获取指定索引的示例SQL"""
    if 0 <= index < len(QA_DATA["SQL"]):
        return QA_DATA["SQL"][index]
    return None

def get_indicator_explanation(indicator):
    """获取技术指标的解释"""
    return TECH_INDICATORS.get(indicator, "没有找到该指标的解释") 