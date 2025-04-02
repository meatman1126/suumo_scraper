import argparse
import time
from typing import Dict, List, Any
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from src.utils.driver_manager import DriverManager
from src.utils.config_loader import ConfigLoader
from src.sheets.sheets_manager import SheetsManager
from src.scraper.property_parser import PropertyParser
from notification_service import NotificationService

class SuumoScraper:
    """SUUMO物件情報スクレイパー"""
    
    def __init__(self):
        """スクレイパーの初期化"""
        self.base_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/"
        self.driver_manager = DriverManager()
        self.config_loader = ConfigLoader()
        self.sheets_manager = SheetsManager()
        self.property_parser = PropertyParser()
        self.notification_service = NotificationService()
    
    def load_search_params(self, json_file: str = 'params.json') -> Dict[str, str]:
        """
        検索パラメータをJSONファイルから読み込む
        
        Args:
            json_file (str): JSONファイルのパス
            
        Returns:
            Dict[str, str]: 検索パラメータ
        """
        return self.config_loader.load_json(json_file)
    
    def build_search_url(self, params: Dict[str, str]) -> str:
        """
        検索パラメータからURLを構築する
        
        Args:
            params (Dict[str, str]): 検索パラメータ
            
        Returns:
            str: 構築したURL
        """
        url = self.base_url
        query_params = []
        
        for key, value in params.items():
            if value:
                query_params.append(f"{key}={value}")
        
        if query_params:
            url += "?" + "&".join(query_params)
        
        return url
    
    def scrape_properties(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        物件情報をスクレイピングする
        
        Args:
            params (Dict[str, str]): 検索パラメータ
            
        Returns:
            List[Dict[str, Any]]: 取得した物件情報のリスト
        """
        all_properties = []
        page = 1
        
        while True:
            current_params = params.copy()
            current_params['page'] = str(page)
            
            url = self.build_search_url(current_params)
            print(f"アクセスURL: {url}")
            
            try:
                self.driver_manager.driver.get(url)
                self.driver_manager.wait_for_page_load()
                time.sleep(5)
                
                self.driver_manager.wait_for_element(By.CSS_SELECTOR, "div.cassetteitem")
                
                html_content = self.driver_manager.driver.page_source
                properties = self.property_parser.parse_properties(html_content, self.base_url, current_params)
                
                if not properties:
                    print("物件情報が見つかりませんでした。全ページの取得を終了します。")
                    break
                
                all_properties.extend(properties)
                print(f"ページ {page} の物件数: {len(properties)}")
                print(f"累計物件数: {len(all_properties)}")
                
                # 次のページの確認
                soup = BeautifulSoup(html_content, 'html.parser')
                next_page = soup.select_one('.pagination-parts a:contains("次へ")')
                next_page_number = soup.select_one(f'.pagination-parts li a[href*="page={page+1}"]')
                
                if not next_page and not next_page_number:
                    print("次のページが存在しません。全ページの取得を終了します。")
                    break
                
                print(f"次のページが存在します。ページ {page+1} に移動します。")
                page += 1
                
            except Exception as e:
                print(f"スクレイピング中にエラーが発生: {e}")
                print(f"現在のURL: {self.driver_manager.driver.current_url}")
                print(f"ページのタイトル: {self.driver_manager.driver.title}")
                break
        
        print(f"全ページの取得が完了しました。総物件数: {len(all_properties)}")
        return all_properties
    
    def export_to_sheets(self, properties: List[Dict[str, Any]], spreadsheet_id: str, search_url: str) -> None:
        """
        物件情報をスプレッドシートに出力する
        
        Args:
            properties (List[Dict[str, Any]]): 物件情報のリスト
            spreadsheet_id (str): スプレッドシートID
            search_url (str): 検索URL
        """
        try:
            # 物件情報をスプレッドシートに出力
            new_properties_count = self.sheets_manager.export_properties(properties, spreadsheet_id, search_url)
            
            # 新着物件がある場合、メール通知を送信
            if new_properties_count > 0:
                # スプレッドシートのURLを構築
                sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                
                # 新着物件の情報を抽出
                new_properties = []
                for prop in properties:
                    if prop.get('is_new', False):  # 新着物件の場合
                        new_properties.append(prop)
                
                # メール通知を送信
                self.notification_service.send_notification(new_properties, sheet_url)
                print(f"新着物件{new_properties_count}件の通知メールを送信しました")
            
        except Exception as e:
            print(f"スプレッドシートへの出力中にエラーが発生: {e}")
            print(f"エラーの詳細: {str(e)}")
    
    def close(self) -> None:
        """スクレイパーのリソースを解放する"""
        self.driver_manager.close()

def main():
    """メイン処理"""
    scraper = SuumoScraper()
    
    try:
        params = scraper.load_search_params()
        if not params:
            print("検索パラメータの読み込みに失敗しました")
            return
        
        properties = scraper.scrape_properties(params)
        
        spreadsheet_id = scraper.config_loader.get_env_var('SPREADSHEET_ID')
        if spreadsheet_id:
            search_url = scraper.build_search_url(params)
            scraper.export_to_sheets(properties, spreadsheet_id, search_url)
            print(f"Successfully exported {len(properties)} properties to Google Sheets")
        else:
            print("SPREADSHEET_ID not found in environment variables")
    
    finally:
        scraper.close()

def schedule_scraping():
    """定期的なスクレイピングを実行（1日2回：午前6時と午後6時）"""
    run_times = ["06:00", "18:00"]
    print(f"実行時間: {', '.join(run_times)}")
    
    while True:
        try:
            current_time = time.strftime("%H:%M")
            
            if current_time in run_times:
                print(f"スクレイピングを開始します: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                main()
                print(f"スクレイピングが完了しました: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(60)
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SUUMO物件情報スクレイパー')
    parser.add_argument('--schedule', action='store_true', help='定期実行モードを有効化（1日2回：午前6時と午後6時）')
    args = parser.parse_args()
    
    if args.schedule:
        schedule_scraping()
    else:
        main() 