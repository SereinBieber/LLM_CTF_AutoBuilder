"""
模板匹配器 - 根据需求找到对应的instances模板
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from difflib import SequenceMatcher


class TemplateMatcher:
    """模板匹配器：根据任务配置找到合适的模板"""

    def __init__(self):
        """初始化模板匹配器"""
        self.project_root = Path(__file__).parent.parent
        self.instances_path = self.project_root / "templates" / "instances"

        # 加载所有可用模板
        self.available_templates = self._scan_templates()
        self.template_features = self._analyze_template_features()
        self.template_keywords = self._extract_template_keywords()

        print(f"📁 找到 {len(self.available_templates)} 个可用模板")
        print(f"📊 模板类型分布: {self._get_category_distribution()}")

        # ========== 根据实际模板列表更新漏洞映射 ==========
        self.vulnerability_mapping = {
            # Web漏洞
            'sqli': ['sqli', 'sql', '注入', 'mysql', 'database', '联合查询', 'union', '盲注'],
            'xss': ['xss', '跨站', 'script', 'javascript', '存储型', '反射型'],
            'rce': ['rce', '代码执行', '命令执行', 'exec', 'system', '远程执行'],
            'lfi': ['lfi', '文件包含', 'include', 'path traversal', '本地文件'],
            'upload': ['upload', '上传', 'file upload', '文件上传', 'webshell'],
            'ssrf': ['ssrf', '服务端请求', 'server request', '请求伪造'],
            'xxe': ['xxe', 'xml', 'external entity', '外部实体'],
            'unserialize': ['unserialize', '反序列化', 'php反序列化', '对象注入'],
            'ssti': ['ssti', '模板注入', 'template', 'jinja2'],
            'jwt': ['jwt', 'json web token', 'token', 'jwt伪造'],
            'login_bypass': ['login', '绕过', 'bypass', '认证绕过', '登录绕过'],

            # PWN漏洞
            'stack': ['stack', '栈溢出', 'buffer overflow', '栈', '返回地址'],
            'heap': ['heap', '堆溢出', 'uaf', 'use after free', '堆', '释放后使用'],
            'format': ['format', '格式化字符串', 'string', '格式化漏洞'],
            'rop': ['rop', 'return oriented', '面向返回', 'rop链'],
            'int_overflow': ['int', '整数溢出', 'integer overflow', '整数'],
            'shellcode': ['shellcode', 'shell代码', 'shell', '代码执行'],

            # 密码学
            'aes': ['aes', '对称加密', 'ecb', 'cbc', '高级加密标准'],
            'rsa': ['rsa', '非对称', 'lsb', 'oracle', 'rsa漏洞'],
            'xor': ['xor', '异或', 'cipher', '异或加密'],
            'hash': ['hash', '哈希', 'md5', 'sha', '哈希长度扩展', 'hash_ext'],

            # Reverse
            'reverse': ['reverse', '逆向', '逆向工程', 'crack', '破解', '反编译'],
            'anti_debug': ['反调试', 'anti-debug', 'ptrace', '反调试技术', '反跟踪', '调试检测'],
            'check_str': ['字符串检查', '字符串验证', 'check', '验证'],
            'vm': ['虚拟机', 'vm', '虚拟保护', '虚拟机保护'],
            'xor_enc': ['xor加密', '异或加密', '加密算法', '解密'],

            # Misc
            'jail': ['jail', '沙盒', 'sandbox', 'restricted', 'pyjail', 'python沙盒'],
            'bash_jail': ['bash', 'shell', 'bash沙盒', 'shell限制'],
            'stego': ['stego', '隐写', 'lsb', 'picture', '图片隐写', '隐写术'],
            'ppc': ['ppc', '编程', 'math', '数学', '算法', 'professional programming'],

            # Database
            'mongodb': ['mongo', 'mongodb', 'nosql', '未授权'],
            'mysql': ['mysql', 'mariadb', '弱密码', 'weakpass', '数据库'],
            'postgres': ['postgres', 'postgresql', '弱密码', 'pgsql'],
            'redis': ['redis', '未授权', 'unauth', '缓存'],
        }

        # ========== 精确匹配规则（根据模板名优化）==========
        self.exact_match_rules = [
            # Web精确匹配
            ('sqli', 'sqli', 200),
            ('xss', 'xss', 200),
            ('rce', 'rce', 200),
            ('lfi', 'lfi', 200),
            ('upload', 'upload', 200),
            ('ssrf', 'ssrf', 200),
            ('xxe', 'xxe', 200),
            ('ssti', 'ssti', 200),
            ('jwt', 'jwt', 200),
            ('login', 'login-bypass', 150),

            # PWN精确匹配
            ('stack', 'stack', 200),
            ('heap', 'heap', 200),
            ('uaf', 'uaf', 200),
            ('format', 'format', 200),
            ('rop', 'rop', 200),
            ('shellcode', 'shellcode', 200),

            # Reverse精确匹配
            ('反调试', 'anti-debug', 200),
            ('reverse', 'reverse', 200),
            ('字符串检查', 'check-str', 150),
            ('虚拟机', 'vm', 150),
            ('xor加密', 'xor-enc', 150),

            # Crypto精确匹配
            ('aes', 'aes', 200),
            ('rsa', 'rsa', 200),
            ('xor', 'xor', 200),
            ('hash', 'hash', 200),

            # Misc精确匹配
            ('pyjail', 'pyjail', 200),
            ('bash jail', 'bash-jail', 200),
            ('stego', 'stego', 200),
            ('隐写', 'stego', 200),
            ('ppc', 'ppc', 150),

            # Database精确匹配
            ('mongodb', 'mongo', 200),
            ('mysql', 'mysql', 200),
            ('postgres', 'postgres', 200),
            ('redis', 'redis', 200),
        ]

        # ========== 反向匹配规则（避免错误匹配）==========
        self.reverse_match_rules = [
            # Web vs 其他
            ('web', 'pwn', 50),
            ('web', 'crypto', 50),
            ('web', 'reverse', 50),

            # PWN vs 其他
            ('pwn', 'web', 50),
            ('pwn', 'crypto', 50),

            # Reverse vs 其他
            ('reverse', 'web', 50),
            ('reverse', 'pwn', 50),
            ('reverse', 'crypto', 50),

            # 具体漏洞类型的互斥
            ('sqli', 'xss', 100),
            ('sqli', 'rce', 100),
            ('stack', 'heap', 100),
            ('aes', 'rsa', 100),
        ]

    def _scan_templates(self) -> Dict[str, Path]:
        """扫描instances文件夹中的所有模板"""
        templates = {}
        if not self.instances_path.exists():
            print(f"⚠️ 警告: instances文件夹不存在: {self.instances_path}")
            return templates

        for template_dir in self.instances_path.iterdir():
            if template_dir.is_dir():
                template_name = template_dir.name
                templates[template_name] = template_dir
        return templates

    def _extract_template_keywords(self) -> Dict[str, List[str]]:
        """从模板名称中提取关键词"""
        keywords = {}
        for name in self.available_templates.keys():
            # 按 '-' 分割，过滤掉数字和版本号
            parts = re.split(r'[-_]', name)
            keywords[name] = [p for p in parts if not p.isdigit() and len(p) > 2]
        return keywords

    def _analyze_template_features(self) -> Dict[str, Dict]:
        """分析每个模板的特征"""
        features = {}

        for name, path in self.available_templates.items():
            # 统计各类文件
            php_files = list(path.rglob("*.php"))
            py_files = list(path.rglob("*.py"))
            js_files = list(path.rglob("*.js"))
            c_files = list(path.rglob("*.c"))
            cpp_files = list(path.rglob("*.cpp"))
            h_files = list(path.rglob("*.h"))
            sql_files = list(path.rglob("*.sql"))
            conf_files = list(path.rglob("*.conf"))
            docker_files = list(path.rglob("Dockerfile"))

            # 读取manifest获取更多信息
            manifest = self._read_template_metadata(path)

            feat = {
                'has_dockerfile': len(docker_files) > 0,
                'has_src_dir': (path / "src").exists(),
                'has_db_dir': (path / "db").exists(),
                'has_manifest': (path / "manifest.json").exists(),
                'php_files': len(php_files),
                'py_files': len(py_files),
                'js_files': len(js_files),
                'c_files': len(c_files) + len(cpp_files) + len(h_files),
                'sql_files': len(sql_files),
                'conf_files': len(conf_files),
                'file_count': sum(1 for _ in path.rglob("*") if _.is_file()),
                'type': self._detect_template_type(name),
                'language': self._detect_language(php_files, py_files, js_files, c_files, cpp_files),
                'has_db': len(sql_files) > 0 or (path / "db").exists(),
                'description': manifest.get('description', ''),
                'category': name.split('-')[0] if '-' in name else 'other',
            }
            features[name] = feat

        return features

    def _detect_language(self, php_files, py_files, js_files, c_files, cpp_files) -> str:
        """检测模板主要编程语言"""
        if len(php_files) > 0:
            return 'php'
        elif len(py_files) > 0:
            return 'python'
        elif len(js_files) > 0:
            return 'javascript'
        elif len(c_files) > 0 or len(cpp_files) > 0:
            return 'c'
        return 'unknown'

    def _detect_template_type(self, template_name: str) -> str:
        """检测模板类型"""
        if 'sqli' in template_name:
            return 'web_sql_injection'
        elif 'xss' in template_name:
            return 'web_xss'
        elif 'rce' in template_name:
            return 'web_rce'
        elif 'lfi' in template_name:
            return 'web_lfi'
        elif 'upload' in template_name:
            return 'web_upload'
        elif 'ssrf' in template_name:
            return 'web_ssrf'
        elif 'xxe' in template_name:
            return 'web_xxe'
        elif 'ssti' in template_name:
            return 'web_ssti'
        elif 'jwt' in template_name:
            return 'web_jwt'
        elif 'login-bypass' in template_name:
            return 'web_login_bypass'
        elif 'stack' in template_name:
            return 'pwn_stack'
        elif 'heap' in template_name:
            return 'pwn_heap'
        elif 'uaf' in template_name:
            return 'pwn_uaf'
        elif 'format' in template_name:
            return 'pwn_format'
        elif 'rop' in template_name:
            return 'pwn_rop'
        elif 'shellcode' in template_name:
            return 'pwn_shellcode'
        elif 'reverse' in template_name:
            return 'reverse'
        elif 'anti-debug' in template_name:
            return 'reverse_anti_debug'
        elif 'check-str' in template_name:
            return 'reverse_check_str'
        elif 'vm' in template_name:
            return 'reverse_vm'
        elif 'xor-enc' in template_name:
            return 'reverse_xor'
        elif 'crypto' in template_name:
            return 'crypto'
        elif 'aes' in template_name:
            return 'crypto_aes'
        elif 'rsa' in template_name:
            return 'crypto_rsa'
        elif 'xor' in template_name:
            return 'crypto_xor'
        elif 'hash' in template_name:
            return 'crypto_hash'
        elif 'misc' in template_name:
            return 'misc'
        elif 'pyjail' in template_name:
            return 'misc_pyjail'
        elif 'bash-jail' in template_name:
            return 'misc_bash_jail'
        elif 'stego' in template_name:
            return 'misc_stego'
        elif 'ppc' in template_name:
            return 'misc_ppc'
        elif 'db' in template_name:
            return 'database'
        elif 'mongo' in template_name:
            return 'db_mongo'
        elif 'mysql' in template_name:
            return 'db_mysql'
        elif 'postgres' in template_name:
            return 'db_postgres'
        elif 'redis' in template_name:
            return 'db_redis'
        elif template_name.startswith('web-'):
            return 'web_general'
        elif template_name.startswith('pwn-'):
            return 'pwn'
        else:
            return 'other'

    def _get_category_distribution(self) -> Dict[str, int]:
        """获取模板类别分布"""
        dist = {}
        for name in self.available_templates.keys():
            cat = name.split('-')[0] if '-' in name else 'other'
            dist[cat] = dist.get(cat, 0) + 1
        return dist

    def match_template(self, task_config: Dict) -> Optional[Dict]:
        """
        根据任务配置匹配模板
        """
        if not self.available_templates:
            print("❌ 没有可用模板")
            return None

        # 1. 深度分析需求
        requirements = self._deep_analyze_requirements(task_config)
        print(f"\n🔍 深度需求分析:")
        print(f"  漏洞类型: {requirements['vuln_types']}")
        print(f"  技术栈: {requirements['tech']}")
        print(f"  数据库: {requirements['db_type']}")
        print(f"  关键词: {requirements['keywords'][:10]}")

        # 2. 对每个模板进行多维评分
        scored_templates = []

        for template_name in self.available_templates.keys():
            score = self._calculate_template_score(template_name, requirements)
            if score > 0:
                scored_templates.append((template_name, score))

        # 3. 按分数排序
        scored_templates.sort(key=lambda x: x[1], reverse=True)

        if not scored_templates:
            print("❌ 未找到匹配的模板")
            return None

        # 4. 显示排名
        print("\n📊 模板匹配排名:")
        for name, score in scored_templates[:10]:
            confidence = self._score_to_confidence(score)
            print(f"  {confidence:3d}% - {name} ({score}分)")

        # 5. 选择最佳匹配
        best_match = scored_templates[0][0]
        best_score = scored_templates[0][1]
        template_path = self.available_templates[best_match]

        # 6. 获取详细信息
        metadata = self._read_template_metadata(template_path)
        features = self.template_features.get(best_match, {})
        confidence = self._score_to_confidence(best_score)

        result = {
            'template_name': best_match,
            'template_path': str(template_path),
            'metadata': metadata,
            'features': features,
            'confidence': confidence,
            'score': best_score,
            'all_candidates': [{'name': n, 'score': s} for n, s in scored_templates[:5]]
        }

        print(f"\n✅ 最佳匹配: {best_match} (置信度: {confidence}%)")
        print(f"   📊 模板特征: {features}")
        return result

    def _deep_analyze_requirements(self, task_config: Dict) -> Dict:
        """深度分析需求"""
        meta = task_config.get('meta', {})

        name = meta.get('name', '').lower()
        description = meta.get('description', '').lower()
        category = meta.get('category', '').lower()

        full_text = f"{name} {description} {category}"

        # 检测漏洞类型
        vuln_types = []
        for vuln, keywords in self.vulnerability_mapping.items():
            if any(k in full_text for k in keywords):
                vuln_types.append(vuln)

        # 如果没有检测到，尝试从名称推断
        if not vuln_types:
            for vuln in self.vulnerability_mapping.keys():
                if vuln in full_text:
                    vuln_types.append(vuln)

        # 检测技术栈
        tech = None
        if 'php' in full_text or 'index.php' in full_text:
            tech = 'php'
        elif 'python' in full_text or 'flask' in full_text or 'django' in full_text:
            tech = 'python'
        elif 'node' in full_text or 'express' in full_text or 'javascript' in full_text:
            tech = 'javascript'
        elif 'java' in full_text or 'spring' in full_text:
            tech = 'java'
        elif 'c' in full_text or 'cpp' in full_text or 'c++' in full_text or 'c语言' in full_text:
            tech = 'c'
        elif 'go' in full_text or 'golang' in full_text:
            tech = 'go'

        # 检测数据库
        db_type = None
        if 'mysql' in full_text or 'mariadb' in full_text:
            db_type = 'mysql'
        elif 'postgres' in full_text:
            db_type = 'postgres'
        elif 'mongo' in full_text:
            db_type = 'mongo'
        elif 'redis' in full_text:
            db_type = 'redis'

        # 提取关键词
        keywords = self._extract_smart_keywords(full_text)

        return {
            'vuln_types': vuln_types,
            'tech': tech,
            'db_type': db_type,
            'has_db': 'db' in full_text or 'database' in full_text or 'sql' in full_text,
            'category': category,
            'keywords': keywords,
            'full_text': full_text,
            'name': name,
            'description': description
        }

    def _extract_smart_keywords(self, text: str) -> List[str]:
        """智能提取关键词"""
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for', 'with',
                     'this', 'that', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'of'}

        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b', text.lower())
        keywords = list(set([w for w in words if w not in stopwords and len(w) > 2]))
        keywords.sort(key=len, reverse=True)

        return keywords

    def _calculate_template_score(self, template_name: str, requirements: Dict) -> int:
        """计算模板匹配分数"""
        score = 0
        features = self.template_features.get(template_name, {})
        template_lower = template_name.lower()
        req_text = requirements['full_text'].lower()

        # 1. 漏洞类型匹配（最高权重）
        vuln_types = requirements['vuln_types']
        if vuln_types:
            for vuln in vuln_types:
                if vuln in template_lower:
                    score += 150
                elif any(v in template_lower for v in self.vulnerability_mapping.get(vuln, [])):
                    score += 100

        # 2. 技术栈匹配
        if requirements['tech']:
            if requirements['tech'] == 'php' and features['php_files'] > 0:
                score += 50
            elif requirements['tech'] == 'python' and features['py_files'] > 0:
                score += 50
            elif requirements['tech'] == 'javascript' and features['js_files'] > 0:
                score += 50
            elif requirements['tech'] == 'c' and features['c_files'] > 0:
                score += 50

        # 3. 数据库匹配
        if requirements['db_type']:
            if requirements['db_type'] in template_lower:
                score += 40
            if features['sql_files'] > 0:
                score += 20
        elif requirements['has_db'] and features['sql_files'] > 0:
            score += 30

        # 4. 关键词匹配
        for keyword in requirements['keywords'][:10]:
            if keyword in template_lower:
                score += 10
            elif any(self._fuzzy_match(keyword, part) for part in template_lower.split('-')):
                score += 5

        # 5. 模板完整性加分
        if features['has_dockerfile']:
            score += 15
        if features['has_manifest']:
            score += 10
        if features['file_count'] > 3:
            score += min(features['file_count'], 20)

        # 6. 类别匹配
        if requirements['category'] and requirements['category'] in template_lower:
            score += 25

        # 7. 名称相似度
        if requirements['name']:
            for part in requirements['name'].split():
                if len(part) > 3:
                    similarity = self._string_similarity(part, template_name)
                    if similarity > 0.6:
                        score += int(similarity * 30)

        # 8. 精确匹配加分
        for req_keyword, template_keyword, points in self.exact_match_rules:
            if req_keyword in req_text and template_keyword in template_lower:
                score += points

        # 9. 反向匹配减分
        for req_keyword, bad_keyword, penalty in self.reverse_match_rules:
            if req_keyword in req_text and bad_keyword in template_lower:
                score -= penalty

        return score

    def _fuzzy_match(self, keyword: str, text: str) -> bool:
        """模糊匹配关键词"""
        if len(keyword) < 4:
            return keyword in text
        return keyword in text or text in keyword

    def _string_similarity(self, a: str, b: str) -> float:
        """计算字符串相似度"""
        return SequenceMatcher(None, a, b).ratio()

    def _score_to_confidence(self, score: int) -> int:
        """将分数转换为置信度百分比"""
        if score >= 300:
            return 98
        elif score >= 250:
            return 95
        elif score >= 200:
            return 90
        elif score >= 150:
            return 80
        elif score >= 100:
            return 70
        elif score >= 70:
            return 60
        elif score >= 50:
            return 50
        elif score >= 30:
            return 40
        else:
            return 30

    def _read_template_metadata(self, template_path: Path) -> Dict:
        """读取模板元数据"""
        metadata = {}
        metadata_file = template_path / "manifest.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                pass
        return metadata

    def list_templates(self) -> Dict[str, List[str]]:
        """按类别列出所有模板"""
        result = {}
        for template_name in self.available_templates.keys():
            category = template_name.split('-')[0] if '-' in template_name else 'other'
            if category not in result:
                result[category] = []
            result[category].append(template_name)
        return result

    def get_template_details(self, template_name: str) -> Optional[Dict]:
        """获取模板详细信息"""
        if template_name not in self.available_templates:
            return None

        return {
            'name': template_name,
            'path': str(self.available_templates[template_name]),
            'features': self.template_features.get(template_name, {}),
            'keywords': self.template_keywords.get(template_name, [])
        }