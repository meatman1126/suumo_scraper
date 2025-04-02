from typing import Dict, List, Any
import time
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os

class SheetsManager:
    """Google Sheetsの操作を管理するクラス"""
    
    def __init__(self):
        """Google Sheets APIの初期化"""
        self.service = self._setup_sheets_service()
    
    def _setup_sheets_service(self) -> Any:
        """
        Google Sheets APIのサービスを設定する
        
        Returns:
            Any: Google Sheets APIのサービスオブジェクト
        """
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('sheets', 'v4', credentials=creds)
    
    def export_properties(self, properties: List[Dict[str, Any]], spreadsheet_id: str, search_url: str) -> int:
        """
        物件情報をスプレッドシートに出力する
        
        Args:
            properties (List[Dict[str, Any]]): 物件情報のリスト
            spreadsheet_id (str): スプレッドシートID
            search_url (str): 検索URL
            
        Returns:
            int: 新着物件の数
        """
        if not properties:
            print("出力するデータがありません")
            return 0
        
        try:
            # シート名の設定
            sheet_name = self._get_sheet_name()
            
            # 新規シートの作成
            sheet_id = self._create_new_sheet(spreadsheet_id, sheet_name)
            
            # データの準備と出力
            self._write_data(spreadsheet_id, sheet_name, sheet_id, properties, search_url)
            
            # 新着物件の処理
            new_properties_count = self._handle_new_properties(spreadsheet_id, sheet_name, sheet_id, properties)
            
            print("Google Sheetsへの書き込みが完了しました")
            return new_properties_count
            
        except Exception as e:
            print(f"Google Sheetsへの書き込み中にエラーが発生: {e}")
            print(f"エラーの詳細: {str(e)}")
            return 0
    
    def _get_sheet_name(self) -> str:
        """
        シート名を生成する
        
        Returns:
            str: シート名
        """
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        sheet_suffix = "AM" if current_hour < 12 else "PM"
        current_date = time.strftime("%Y/%m/%d")
        return f"{current_date}/{sheet_suffix}"
    
    def _create_new_sheet(self, spreadsheet_id: str, sheet_name: str) -> int:
        """
        新規シートを作成する
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            
        Returns:
            int: 作成したシートのID
        """
        request = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
        ).execute()
        return request['replies'][0]['addSheet']['properties']['sheetId']
    
    def _write_data(self, spreadsheet_id: str, sheet_name: str, sheet_id: int,
                   properties: List[Dict[str, Any]], search_url: str) -> None:
        """
        データをスプレッドシートに書き込む
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            sheet_id (int): シートID
            properties (List[Dict[str, Any]]): 物件情報のリスト
            search_url (str): 検索URL
        """
        df = pd.DataFrame(properties)
        output_columns = [col for col in df.columns if col not in ['search_params']]
        df = df[output_columns]
        
        headers = [list(df.columns)]
        values = [list(row) for row in df.values]
        
        body = {
            'values': [
                [f"スクレイピングURL: {search_url}"],
                [""],
                headers[0],
            ] + values
        }
        
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def _handle_new_properties(self, spreadsheet_id: str, sheet_name: str, sheet_id: int,
                             properties: List[Dict[str, Any]]) -> int:
        """
        新着物件の処理を行う
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            sheet_id (int): シートID
            properties (List[Dict[str, Any]]): 物件情報のリスト
            
        Returns:
            int: 新着物件の数
        """
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        
        # 実行時間に応じて前回の実行結果を特定
        if current_hour < 12:  # 午前中（0時から11時59分まで）の実行
            # 前日のPMの実行結果を参照
            yesterday = time.time() - 24*60*60
            target_sheet = time.strftime("%Y/%m/%d/PM", time.localtime(yesterday))
        else:  # 午後（12時から23時59分まで）の実行
            # 同日のAMの実行結果を参照
            target_sheet = f"{time.strftime('%Y/%m/%d')}/AM"
        
        print(f"前回の実行結果を参照: {target_sheet}")
        
        # 前回のデータを取得
        previous_data = self._get_previous_data(spreadsheet_id, target_sheet)
        
        # 新着物件を特定してマーク
        if previous_data is not None and not previous_data.empty:
            return self._mark_new_properties(spreadsheet_id, sheet_name, sheet_id, properties, previous_data)
        else:
            return self._mark_all_as_new(spreadsheet_id, sheet_name, sheet_id, properties)
    
    def _get_previous_data(self, spreadsheet_id: str, target_sheet: str) -> pd.DataFrame:
        """
        前回のデータを取得する
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            target_sheet (str): 対象シート名
            
        Returns:
            pd.DataFrame: 前回のデータ
        """
        try:
            previous_data = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{target_sheet}!A:Z"
            ).execute()
            
            if 'values' in previous_data:
                return pd.DataFrame(previous_data['values'][2:], columns=previous_data['values'][2])
            return None
        except Exception:
            return None
    
    def _mark_new_properties(self, spreadsheet_id: str, sheet_name: str, sheet_id: int,
                           properties: List[Dict[str, Any]], previous_data: pd.DataFrame) -> int:
        """
        新着物件をマークする
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            sheet_id (int): シートID
            properties (List[Dict[str, Any]]): 物件情報のリスト
            previous_data (pd.DataFrame): 前回のデータ
            
        Returns:
            int: 新着物件の数
        """
        if '物件URL' in previous_data.columns:
            previous_urls = set(previous_data['物件URL'].tolist())
            new_properties_rows = []
            
            for i, property_info in enumerate(properties, start=4):
                if property_info['物件URL'] not in previous_urls:
                    new_properties_rows.append(i)
                    property_info['is_new'] = True  # 新着物件フラグを設定
            
            if new_properties_rows:
                self._highlight_rows(spreadsheet_id, sheet_name, sheet_id, new_properties_rows)
                print(f"{len(new_properties_rows)}件の新着物件を黄色でマークしました")
                return len(new_properties_rows)
        return 0
    
    def _mark_all_as_new(self, spreadsheet_id: str, sheet_name: str, sheet_id: int,
                        properties: List[Dict[str, Any]]) -> int:
        """
        すべての物件を新着としてマークする
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            sheet_id (int): シートID
            properties (List[Dict[str, Any]]): 物件情報のリスト
            
        Returns:
            int: 新着物件の数
        """
        new_rows = list(range(4, len(properties) + 4))
        if new_rows:
            self._highlight_rows(spreadsheet_id, sheet_name, sheet_id, new_rows)
            # すべての物件を新着としてマーク
            for prop in properties:
                prop['is_new'] = True
            print(f"{len(new_rows)}件の物件を黄色でマークしました")
            return len(new_rows)
        return 0
    
    def _highlight_rows(self, spreadsheet_id: str, sheet_name: str, sheet_id: int,
                       rows: List[int]) -> None:
        """
        指定された行を黄色でハイライトする
        
        Args:
            spreadsheet_id (str): スプレッドシートID
            sheet_name (str): シート名
            sheet_id (int): シートID
            rows (List[int]): ハイライトする行番号のリスト
        """
        requests = []
        for row in rows:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': row - 1,
                        'endRowIndex': row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 100  # 十分大きな数
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 0.0,
                                'alpha': 0.5
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
        
        if requests:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute() 