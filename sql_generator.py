from llm_client import LLMClient, LLMProvider
from schema_knowledge import STOCK_BUSINESS_SCHEMA
import re
try:
    from qa_knowledge import QA_DATA, get_example_queries, get_example_sql, get_indicator_explanation
    use_qa_knowledge = True
except ImportError:
    use_qa_knowledge = False
    print("QA知识库未找到，将使用纯LLM生成SQL")

class SQLGenerator:
    def __init__(self, llm_client=None):
        """
        初始化SQL生成器
        
        Args:
            llm_client (LLMClient, optional): LLM客户端实例
        """
        # 直接使用Ollama而非OpenRouter，避免编码问题
        self.llm_client = llm_client or LLMClient(provider=LLMProvider.OLLAMA, 
                                                 base_url="http://localhost:11434",
                                                 model="qwen2.5-coder:latest")
        self.schema = STOCK_BUSINESS_SCHEMA
        # 初始化字段映射表
        self._init_field_mapping()
        # QA知识库匹配阈值
        self.qa_match_threshold = 0.7
    
    def _init_field_mapping(self):
        """初始化字段名映射表"""
        # 字段名映射：用户可能使用的字段名 -> 实际数据库字段名
        self.field_mapping = {
            # 基本字段
            'ts_code': 'ts_code',
            'stock_name': 'stock_name',
            '股票代码': 'ts_code',
            '股票名称': 'stock_name',
            'trade_date': 'trade_date',
            '交易日期': 'trade_date',
            'daily_close': 'daily_close',
            '收盘价': 'daily_close',
            
            # 换手率相关
            'turnover_rate': 'turnover_rate',
            'turnover_rate_f': 'turnover_rate_f',
            '换手率': 'turnover_rate',
            '自由流通股换手率': 'turnover_rate_f',
            
            # 量比
            'volume_ratio': 'volume_ratio',
            '量比': 'volume_ratio',
            
            # 市盈率相关
            'pe': 'pe',
            'pe_ttm': 'pe_ttm',
            '市盈率': 'pe',
            '市盈率ttm': 'pe_ttm',
            
            # 市净率
            'pb': 'pb',
            '市净率': 'pb',
            
            # 市销率
            'ps': 'ps',
            'ps_ttm': 'ps_ttm',
            '市销率': 'ps',
            '市销率ttm': 'ps_ttm',
            
            # 股息率
            'dv_ratio': 'dv_ratio',
            'dv_ttm': 'dv_ttm',
            '股息率': 'dv_ratio',
            '股息率ttm': 'dv_ttm',
            
            # 股本相关
            'total_share': 'total_share',
            'float_share': 'float_share',
            'free_share': 'free_share',
            '总股本': 'total_share',
            '流通股本': 'float_share',
            '自由流通股本': 'free_share',
            
            # 市值相关
            'total_mv': 'total_mv',
            'circ_mv': 'circ_mv',
            '总市值': 'total_mv',
            '流通市值': 'circ_mv',
            
            # 价格相关字段
            'factor_open': 'factor_open',
            'factor_high': 'factor_high',
            'factor_low': 'factor_low',
            'factor_pre_close': 'factor_pre_close',
            'factor_change': 'factor_change',
            'factor_pct_change': 'factor_pct_change',
            '开盘价': 'factor_open',
            '最高价': 'factor_high',
            '最低价': 'factor_low',
            '昨收价': 'factor_pre_close',
            '涨跌额': 'factor_change',
            '涨跌幅': 'factor_pct_change',
            'open': 'factor_open',
            'high': 'factor_high',
            'low': 'factor_low',
            'pre_close': 'factor_pre_close',
            'change': 'factor_change',
            'pct_change': 'factor_pct_change',
            
            # 成交量相关
            'factor_vol': 'factor_vol',
            'factor_amount': 'factor_amount',
            '成交量': 'factor_vol',
            '成交额': 'factor_amount',
            'vol': 'factor_vol',
            'amount': 'factor_amount',
            
            # 复权因子
            'factor_adj_factor': 'factor_adj_factor',
            '复权因子': 'factor_adj_factor',
            'adj_factor': 'factor_adj_factor',
            
            # 后复权价格
            'factor_open_hfq': 'factor_open_hfq',
            'factor_close_hfq': 'factor_close_hfq',
            'factor_high_hfq': 'factor_high_hfq',
            'factor_low_hfq': 'factor_low_hfq',
            'factor_pre_close_hfq': 'factor_pre_close_hfq',
            '后复权开盘价': 'factor_open_hfq',
            '后复权收盘价': 'factor_close_hfq',
            '后复权最高价': 'factor_high_hfq',
            '后复权最低价': 'factor_low_hfq',
            '后复权昨收价': 'factor_pre_close_hfq',
            
            # 前复权价格
            'factor_open_qfq': 'factor_open_qfq',
            'factor_close_qfq': 'factor_close_qfq',
            'factor_high_qfq': 'factor_high_qfq',
            'factor_low_qfq': 'factor_low_qfq',
            'factor_pre_close_qfq': 'factor_pre_close_qfq',
            '前复权开盘价': 'factor_open_qfq',
            '前复权收盘价': 'factor_close_qfq',
            '前复权最高价': 'factor_high_qfq',
            '前复权最低价': 'factor_low_qfq',
            '前复权昨收价': 'factor_pre_close_qfq',
            
            # MACD相关
            'macd_dif': 'factor_macd_dif',
            'macd_dea': 'factor_macd_dea',
            'macd': 'factor_macd',
            'factor_macd_dif': 'factor_macd_dif',
            'factor_macd_dea': 'factor_macd_dea',
            'factor_macd': 'factor_macd',
            'dif': 'factor_macd_dif',
            'dea': 'factor_macd_dea',
            
            # KDJ相关
            'kdj_k': 'factor_kdj_k',
            'kdj_d': 'factor_kdj_d',
            'kdj_j': 'factor_kdj_j',
            'factor_kdj_k': 'factor_kdj_k',
            'factor_kdj_d': 'factor_kdj_d',
            'factor_kdj_j': 'factor_kdj_j',
            'k值': 'factor_kdj_k',
            'd值': 'factor_kdj_d',
            'j值': 'factor_kdj_j',
            
            # RSI相关
            'rsi_6': 'factor_rsi_6',
            'rsi_12': 'factor_rsi_12',
            'rsi_24': 'factor_rsi_24',
            'factor_rsi_6': 'factor_rsi_6',
            'factor_rsi_12': 'factor_rsi_12',
            'factor_rsi_24': 'factor_rsi_24',
            
            # 布林带相关
            'boll_upper': 'factor_boll_upper',
            'boll_mid': 'factor_boll_mid',
            'boll_lower': 'factor_boll_lower',
            'factor_boll_upper': 'factor_boll_upper',
            'factor_boll_mid': 'factor_boll_mid',
            'factor_boll_lower': 'factor_boll_lower',
            '布林上轨': 'factor_boll_upper',
            '布林中轨': 'factor_boll_mid',
            '布林下轨': 'factor_boll_lower',
            
            # CCI指标
            'cci': 'factor_cci',
            'factor_cci': 'factor_cci',
            
            # 资金流相关
            'moneyflow_pct_change': 'moneyflow_pct_change',
            'moneyflow_latest': 'moneyflow_latest',
            'moneyflow_net_amount': 'moneyflow_net_amount',
            'moneyflow_net_d5_amount': 'moneyflow_net_d5_amount',
            '资金流涨跌幅': 'moneyflow_pct_change',
            '最新价': 'moneyflow_latest',
            '净流入额': 'moneyflow_net_amount',
            '5日净流入额': 'moneyflow_net_d5_amount',
            
            # 大单买入相关
            'moneyflow_buy_lg_amount': 'moneyflow_buy_lg_amount',
            'moneyflow_buy_lg_amount_rate': 'moneyflow_buy_lg_amount_rate',
            '大单买入额': 'moneyflow_buy_lg_amount',
            '大单买入额占比': 'moneyflow_buy_lg_amount_rate',
            
            # 中单买入相关
            'moneyflow_buy_md_amount': 'moneyflow_buy_md_amount',
            'moneyflow_buy_md_amount_rate': 'moneyflow_buy_md_amount_rate',
            '中单买入额': 'moneyflow_buy_md_amount',
            '中单买入额占比': 'moneyflow_buy_md_amount_rate',
            
            # 小单买入相关
            'moneyflow_buy_sm_amount': 'moneyflow_buy_sm_amount',
            'moneyflow_buy_sm_amount_rate': 'moneyflow_buy_sm_amount_rate',
            '小单买入额': 'moneyflow_buy_sm_amount',
            '小单买入额占比': 'moneyflow_buy_sm_amount_rate',
            
            # 均线相关
            'ma5': 'ma5',
            'ma10': 'ma10',
            'ma20': 'ma20',
            'ma30': 'ma30',
            'ma60': 'ma60',
            'ma120': 'ma120',
            '5日均线': 'ma5',
            '10日均线': 'ma10',
            '20日均线': 'ma20',
            '30日均线': 'ma30',
            '60日均线': 'ma60',
            '120日均线': 'ma120'
        }
    
    def generate_sql(self, user_query):
        """
        根据用户查询生成SQL
        
        Args:
            user_query (str): 用户的自然语言查询
            
        Returns:
            str: 生成的SQL语句
        """
        # 确保用户查询正确编码
        try:
            user_query = user_query.strip()
            # 尝试从QA知识库匹配
            if use_qa_knowledge:
                qa_sql = self._match_from_qa_knowledge(user_query)
                if qa_sql:
                    print(f"从QA知识库匹配到SQL: {qa_sql}")
                    return qa_sql
            
            # 如果知识库没有匹配，使用LLM生成
            sql = self.llm_client.generate_sql(user_query, self.schema)
            
            # 简单检查确保返回的是SQL语句
            if sql and ("select" in sql.lower() or "SELECT" in sql):
                # 转换字段名
                sql = self._convert_field_names(sql)
                # 增强SQL查询，确保包含查询条件中涉及的字段
                sql = self._enhance_sql(sql)
                return sql
            else:
                # 如果不是有效的SQL，返回一个默认查询
                print("生成的SQL无效，返回默认查询")
                return "SELECT ts_code, stock_name, pe, ma5 FROM stock_business LIMIT 5"
        except Exception as e:
            print(f"SQL生成过程中出错: {e}")
            return "SELECT ts_code, stock_name, pe, ma5 FROM stock_business LIMIT 5"
    
    def _match_from_qa_knowledge(self, user_query):
        """
        从QA知识库中匹配最相似的查询
        
        Args:
            user_query (str): 用户的自然语言查询
            
        Returns:
            str: 匹配到的SQL语句，如果没有匹配则返回None
        """
        if not use_qa_knowledge:
            return None
            
        # 获取所有示例查询
        example_queries = get_example_queries()
        
        # 简单的相似度匹配（可以替换为更复杂的算法）
        best_match_idx = -1
        best_match_score = 0
        
        # 标准化用户查询
        user_query = user_query.lower().strip()
        
        # 针对特殊标识进行匹配
        for idx, query in enumerate(example_queries):
            # 标准化示例查询
            example = query.lower().strip()
            
            # 计算简单相似度（包含关系）
            if example in user_query or user_query in example:
                score = len(example) / max(len(user_query), len(example))
                if score > best_match_score and score > self.qa_match_threshold:
                    best_match_score = score
                    best_match_idx = idx
        
        # 如果找到匹配，返回对应的SQL
        if best_match_idx >= 0:
            return get_example_sql(best_match_idx)
        
        return None
    
    def _convert_field_names(self, sql):
        """
        转换SQL中的字段名为实际数据库字段名
        
        Args:
            sql (str): 原始SQL语句
            
        Returns:
            str: 转换后的SQL语句
        """
        # 保存SQL的小写版本，用于不区分大小写的搜索
        sql_lower = sql.lower()
        
        # 需要替换的字段和对应位置
        replacements = []
        
        # 查找需要替换的字段
        for user_field, db_field in self.field_mapping.items():
            # 跳过已经是数据库字段名的情况
            if user_field == db_field:
                continue
                
            # 尝试查找字段名
            pos = 0
            while True:
                pos = sql_lower.find(user_field.lower(), pos)
                if pos == -1:
                    break
                
                # 确保找到的是独立的字段名，而不是更长字段名的一部分
                is_valid_field = False
                before = pos - 1
                after = pos + len(user_field)
                
                # 检查前一个字符
                if before < 0 or sql_lower[before] in " ,()=<>!*/+-\n\t":
                    # 检查后一个字符
                    if after >= len(sql_lower) or sql_lower[after] in " ,()=<>!*/+-\n\t;":
                        is_valid_field = True
                
                if is_valid_field:
                    replacements.append((pos, pos + len(user_field), user_field, db_field))
                
                pos += len(user_field)
        
        # 从后向前替换，避免位置偏移
        replacements.sort(reverse=True)
        sql_list = list(sql)
        for start, end, user_field, db_field in replacements:
            # 保持原始大小写
            if sql[start:end].isupper():
                replacement = db_field.upper()
            elif sql[start:end].islower():
                replacement = db_field.lower()
            else:
                replacement = db_field
            
            sql_list[start:end] = replacement
        
        return ''.join(sql_list)
    
    def _enhance_sql(self, sql):
        """
        增强SQL查询，确保包含WHERE条件中涉及的字段
        
        Args:
            sql (str): 原始SQL语句
            
        Returns:
            str: 增强后的SQL语句
        """
        # 如果SQL已经很复杂（包含JOIN、GROUP BY等），不做修改
        if any(keyword in sql.lower() for keyword in ['join', 'group by', 'having', 'union']):
            return sql
            
        # 提取SELECT和FROM之间的字段列表
        select_pattern = re.compile(r'SELECT\s+(.*?)\s+FROM', re.IGNORECASE | re.DOTALL)
        select_match = select_pattern.search(sql)
        
        if not select_match:
            return sql
            
        select_fields = select_match.group(1).split(',')
        select_fields = [field.strip() for field in select_fields]
        
        # 提取WHERE条件中的字段
        where_pattern = re.compile(r'WHERE\s+(.*?)($|;|\s+ORDER BY|\s+GROUP BY|\s+HAVING|\s+LIMIT)', re.IGNORECASE | re.DOTALL)
        where_match = where_pattern.search(sql)
        
        if not where_match:
            return sql
            
        where_clause = where_match.group(1)
        
        # 识别WHERE条件中涉及的字段
        condition_fields = set()
        for field_name in self.field_mapping.values():  # 使用实际的数据库字段名
            # 需要检查字段名是否出现在WHERE条件中
            pattern = r'\b' + field_name + r'\b'
            if re.search(pattern, where_clause, re.IGNORECASE):
                condition_fields.add(field_name)
        
        # 检查是否已经包含了所有条件字段
        fields_to_add = []
        for field in condition_fields:
            if not any(field == f.lower() or field == f or f.endswith('.' + field) or f.lower().endswith(' as ' + field) for f in select_fields):
                fields_to_add.append(field)
        
        # 如果有需要添加的字段，修改SQL
        if fields_to_add:
            new_select = 'SELECT ' + select_match.group(1) + ', ' + ', '.join(fields_to_add)
            sql = select_pattern.sub(new_select, sql)
        
        return sql 