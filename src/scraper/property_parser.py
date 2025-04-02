from bs4 import BeautifulSoup
from typing import Dict, List, Any
from selenium.webdriver.common.by import By

class PropertyParser:
    """物件情報のパースを管理するクラス"""
    
    def parse_properties(self, html_content: str, base_url: str, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        HTMLから物件情報を抽出する
        
        Args:
            html_content (str): パース対象のHTML
            base_url (str): ベースURL
            search_params (Dict[str, Any]): 検索パラメータ
            
        Returns:
            List[Dict[str, Any]]: 抽出した物件情報のリスト
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        properties = []
        
        items = soup.select('div.cassetteitem')
        if not items:
            print("物件情報が見つかりませんでした")
            return properties
        
        for item in items:
            try:
                property_info = self._extract_property_info(item, base_url, search_params)
                properties.append(property_info)
                print(f"物件情報を取得: {property_info['物件名']}")
            except Exception as e:
                print(f"物件情報の取得中にエラーが発生: {e}")
                continue
        
        return properties
    
    def _extract_property_info(self, item: BeautifulSoup, base_url: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        個々の物件情報を抽出する
        
        Args:
            item (BeautifulSoup): 物件情報のHTML要素
            base_url (str): ベースURL
            search_params (Dict[str, Any]): 検索パラメータ
            
        Returns:
            Dict[str, Any]: 抽出した物件情報
        """
        # メイン画像のURLを取得
        main_image = item.select_one('.cassetteitem_object-item img')
        main_image_url = main_image['src'] if main_image else 'N/A'
        
        # サムネイル画像のURLリストを取得
        thumbnail_div = item.select_one('.casssetteitem_other-thumbnail')
        thumbnail_urls = thumbnail_div['data-imgs'].split(',') if thumbnail_div and 'data-imgs' in thumbnail_div.attrs else []
        
        return {
            '物件名': self._get_text(item, '.cassetteitem_content-title'),
            '所在地': self._get_text(item, '.cassetteitem_detail-col1'),
            'アクセス': self._get_text(item, '.cassetteitem_detail-col2'),
            '築年数': self._get_text(item, '.cassetteitem_detail-col3'),
            '賃料': self._get_text(item, '.cassetteitem_price--rent'),
            '管理費': self._get_text(item, '.cassetteitem_price--administration'),
            '敷金': self._get_text(item, '.cassetteitem_price--deposit'),
            '礼金': self._get_text(item, '.cassetteitem_price--gratuity'),
            '間取り': self._get_text(item, '.cassetteitem_madori'),
            '専有面積': self._get_text(item, '.cassetteitem_menseki'),
            '物件URL': self._get_property_url(item, base_url),
            'メイン画像': main_image_url,
            '画像一覧': ','.join(thumbnail_urls) if thumbnail_urls else 'N/A',
            'search_params': search_params
        }
    
    def _get_text(self, item: BeautifulSoup, selector: str) -> str:
        """
        指定されたセレクタのテキストを取得する
        
        Args:
            item (BeautifulSoup): 親要素
            selector (str): CSSセレクタ
            
        Returns:
            str: 抽出したテキスト
        """
        element = item.select_one(selector)
        return element.text.strip() if element else 'N/A'
    
    def _get_property_url(self, item: BeautifulSoup, base_url: str) -> str:
        """
        物件のURLを取得する
        
        Args:
            item (BeautifulSoup): 物件情報の要素
            base_url (str): ベースURL
            
        Returns:
            str: 物件のURL
        """
        link = item.select_one('.js-cassette_link_href')
        if link and 'href' in link.attrs:
            href = link['href']
            # クエリパラメータを除去
            href = href.split('?')[0]
            # 相対パスの場合はドメインを付与
            if href.startswith('/'):
                return f"https://suumo.jp{href}"
            return href
        return 'N/A' 
