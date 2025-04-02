import json
from typing import Dict, Any
import os
from dotenv import load_dotenv

class ConfigLoader:
    """設定ファイルの読み込みを管理するクラス"""
    
    def __init__(self):
        """環境変数の読み込み"""
        load_dotenv()
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """
        JSONファイルから設定を読み込む
        
        Args:
            file_path (str): JSONファイルのパス
            
        Returns:
            Dict[str, Any]: 読み込んだ設定値
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            json.JSONDecodeError: JSONの形式が不正な場合
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"設定ファイルを読み込みました: {file_path}")
            return config
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSONファイルの形式が不正です: {e}")
            raise
    
    def get_env_var(self, key: str) -> str:
        """
        環境変数の値を取得する
        
        Args:
            key (str): 環境変数のキー
            
        Returns:
            str: 環境変数の値
            
        Raises:
            KeyError: 環境変数が設定されていない場合
        """
        value = os.getenv(key)
        if value is None:
            raise KeyError(f"環境変数 {key} が設定されていません")
        return value 