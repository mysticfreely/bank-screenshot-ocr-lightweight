#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级银行截图OCR处理器
使用第三方API调用，减少内存占用和部署复杂度
"""

import os
import re
import json
import base64
import hashlib
import sqlite3
import requests
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from PIL import Image
import io

class LightweightOCRProcessor:
    """轻量级OCR处理器 - 基于API调用"""
    
    def __init__(self, config_path: str = "config/api_config.json"):
        """
        初始化轻量级OCR处理器
        
        Args:
            config_path: API配置文件路径
        """
        self.config = self._load_config(config_path)
        self.results = []
        self.bank_database = self._load_bank_database()
        
        # 支持的OCR API提供商
        self.api_providers = {
            'baidu': self._call_baidu_ocr,
            'tencent': self._call_tencent_ocr,
            'aliyun': self._call_aliyun_ocr,
            'azure': self._call_azure_ocr,
            'google': self._call_google_ocr
        }
        
        print("轻量级OCR处理器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载API配置文件"""
        default_config = {
            "ocr_apis": {
                "baidu": {
                    "enabled": False,
                    "api_key": "",
                    "secret_key": "",
                    "url": "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
                    "confidence_threshold": 0.8
                },
                "tencent": {
                    "enabled": False,
                    "secret_id": "",
                    "secret_key": "",
                    "region": "ap-beijing",
                    "confidence_threshold": 0.8
                },
                "aliyun": {
                    "enabled": False,
                    "access_key_id": "",
                    "access_key_secret": "",
                    "endpoint": "ocr.cn-shanghai.aliyuncs.com",
                    "confidence_threshold": 0.8
                },
                "azure": {
                    "enabled": False,
                    "subscription_key": "",
                    "endpoint": "",
                    "confidence_threshold": 0.8
                },
                "google": {
                    "enabled": False,
                    "api_key": "",
                    "confidence_threshold": 0.8
                }
            },
            "image_preprocessing": {
                "max_size": 4096,
                "quality": 85,
                "format": "JPEG"
            },
            "extraction_rules": {
                "bank_name_patterns": [
                    r"(中国[农业工商建设银行]{2,3}|交通银行|招商银行|上海浦东发展银行|中信银行|兴业银行|广发银行|民生银行|光大银行|华夏银行|平安银行)",
                    r"(农[业行]|工[商行]|建[设行]|中[国行]|交[通行]|招[商行]|浦发|中信|兴业|广发|民生|光大|华夏|平安)"
                ],
                "account_patterns": [
                    r"\d{10,25}",
                    r"\d{4}[\s-]*\d{4}[\s-]*\d{4}[\s-]*\d{4,}",
                    r"账号[:：]?\s*(\d{10,25})",
                    r"卡号[:：]?\s*(\d{10,25})"
                ],
                "balance_patterns": [
                    r"可用余额[:：]?\s*[¥￥]?([\d,]+\.?\d*)",
                    r"账户余额[:：]?\s*[¥￥]?([\d,]+\.?\d*)",
                    r"余额[:：]?\s*[¥￥]?([\d,]+\.?\d*)",
                    r"当前余额[:：]?\s*[¥￥]?([\d,]+\.?\d*)"
                ],
                "company_patterns": [
                    r"([^，,。.]{2,30}(?:有限公司|股份有限公司|科技有限公司|贸易有限公司|新能源有限公司))",
                    r"户名[:：]?\s*([^，,。.]{2,30}(?:有限公司|股份有限公司))",
                    r"账户名称[:：]?\s*([^，,。.]{2,30}(?:有限公司|股份有限公司))"
                ]
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # 创建默认配置文件
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config
        except Exception as e:
            print(f"配置文件加载失败，使用默认配置: {e}")
            return default_config
    
    def _load_bank_database(self) -> pd.DataFrame:
        """加载银行数据库"""
        try:
            database_path = "公司在用银行库20250412.xlsx"
            if os.path.exists(database_path):
                excel_file = pd.ExcelFile(database_path)
                if 'bank' in excel_file.sheet_names:
                    df = pd.read_excel(database_path, sheet_name='bank')
                else:
                    df = pd.read_excel(database_path, sheet_name=0)
                print(f"银行数据库加载成功，共 {len(df)} 条记录")
                return df
            else:
                print("银行数据库文件不存在")
                return pd.DataFrame()
        except Exception as e:
            print(f"银行数据库加载失败: {e}")
            return pd.DataFrame()
    
    def _preprocess_image(self, image_path: str) -> str:
        """图像预处理并转换为base64"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                max_size = self.config["image_preprocessing"]["max_size"]
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, 
                        format=self.config["image_preprocessing"]["format"],
                        quality=self.config["image_preprocessing"]["quality"])
                
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return image_data
                
        except Exception as e:
            print(f"图像预处理失败: {e}")
            return ""
    
    def _call_baidu_ocr(self, image_data: str) -> List[Dict]:
        """调用百度OCR API"""
        try:
            config = self.config["ocr_apis"]["baidu"]
            if not config["enabled"] or not config["api_key"]:
                return []
            
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_params = {
                "grant_type": "client_credentials",
                "client_id": config["api_key"],
                "client_secret": config["secret_key"]
            }
            
            token_response = requests.post(token_url, params=token_params, timeout=10)
            if token_response.status_code != 200:
                print("百度OCR获取token失败")
                return []
            
            access_token = token_response.json().get("access_token")
            if not access_token:
                print("百度OCR token无效")
                return []
            
            ocr_url = f"{config['url']}?access_token={access_token}"
            ocr_data = {
                "image": image_data,
                "language_type": "CHN_ENG"
            }
            
            response = requests.post(ocr_url, data=ocr_data, timeout=30)
            if response.status_code != 200:
                print(f"百度OCR调用失败: {response.status_code}")
                return []
            
            result = response.json()
            if "words_result" not in result:
                print("百度OCR返回格式错误")
                return []
            
            text_data = []
            for item in result["words_result"]:
                confidence = item.get("probability", {}).get("average", 0.9)
                if confidence >= config["confidence_threshold"]:
                    text_data.append({
                        'text': item["words"],
                        'confidence': confidence,
                        'engine': 'baidu'
                    })
            
            return text_data
            
        except Exception as e:
            print(f"百度OCR调用失败: {e}")
            return []
    
    def _call_tencent_ocr(self, image_data: str) -> List[Dict]:
        """调用腾讯OCR API"""
        try:
            config = self.config["ocr_apis"]["tencent"]
            if not config["enabled"] or not config["secret_id"]:
                return []
            print("腾讯OCR API调用需要SDK支持")
            return []
        except Exception as e:
            print(f"腾讯OCR调用失败: {e}")
            return []
    
    def _call_aliyun_ocr(self, image_data: str) -> List[Dict]:
        """调用阿里云OCR API"""
        try:
            config = self.config["ocr_apis"]["aliyun"]
            if not config["enabled"] or not config["access_key_id"]:
                return []
            print("阿里云OCR API调用需要SDK支持")
            return []
        except Exception as e:
            print(f"阿里云OCR调用失败: {e}")
            return []
    
    def _call_azure_ocr(self, image_data: str) -> List[Dict]:
        """调用Azure OCR API"""
        try:
            config = self.config["ocr_apis"]["azure"]
            if not config["enabled"] or not config["subscription_key"]:
                return []
            
            endpoint = config["endpoint"]
            subscription_key = config["subscription_key"]
            
            url = f"{endpoint}/vision/v3.2/ocr"
            headers = {
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'language': 'zh-Hans',
                'detectOrientation': 'true'
            }
            
            image_bytes = base64.b64decode(image_data)
            response = requests.post(url, headers=headers, params=params, 
                                   data=image_bytes, timeout=30)
            
            if response.status_code != 200:
                print(f"Azure OCR调用失败: {response.status_code}")
                return []
            
            result = response.json()
            text_data = []
            
            for region in result.get("regions", []):
                for line in region.get("lines", []):
                    line_text = " ".join([word["text"] for word in line.get("words", [])])
                    if line_text.strip():
                        text_data.append({
                            'text': line_text.strip(),
                            'confidence': 0.9,
                            'engine': 'azure'
                        })
            
            return text_data
            
        except Exception as e:
            print(f"Azure OCR调用失败: {e}")
            return []
    
    def _call_google_ocr(self, image_data: str) -> List[Dict]:
        """调用Google OCR API"""
        try:
            config = self.config["ocr_apis"]["google"]
            if not config["enabled"] or not config["api_key"]:
                return []
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={config['api_key']}"
            
            payload = {
                "requests": [{
                    "image": {"content": image_data},
                    "features": [{"type": "TEXT_DETECTION", "maxResults": 50}]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"Google OCR调用失败: {response.status_code}")
                return []
            
            result = response.json()
            text_data = []
            
            if "responses" in result and result["responses"]:
                annotations = result["responses"][0].get("textAnnotations", [])
                for annotation in annotations[1:]:
                    confidence = annotation.get("confidence", 0.9)
                    if confidence >= config["confidence_threshold"]:
                        text_data.append({
                            'text': annotation["description"],
                            'confidence': confidence,
                            'engine': 'google'
                        })
            
            return text_data
            
        except Exception as e:
            print(f"Google OCR调用失败: {e}")
            return []