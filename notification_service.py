import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

class NotificationService:
    def __init__(self):
        """メール通知サービスの初期化"""
        load_dotenv()
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        self.max_properties = 5  # メールに含める最大物件数

    def send_notification(self, new_properties: List[Dict], sheet_url: str):
        """新着物件の通知メールを送信"""
        if not new_properties:
            return

        try:
            # メール本文の作成
            current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
            total_count = len(new_properties)
            subject = f"SUUMO新着物件通知 ({current_time})"
            
            # 表示する物件数を制限
            display_properties = new_properties[:self.max_properties]
            
            # HTMLメール本文の作成
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .property {{ 
                        border: 1px solid #ddd; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px;
                    }}
                    .property img {{ max-width: 300px; }}
                    .highlight {{ background-color: #fff3cd; }}
                    .summary {{ 
                        background-color: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="summary">
                    <h2>新着物件が{total_count}件見つかりました</h2>
                    <p>スプレッドシート: <a href="{sheet_url}">{sheet_url}</a></p>
                    {f'<p>※ 上位{self.max_properties}件の物件情報を表示しています。全{total_count}件の情報はスプレッドシートでご確認ください。</p>' if total_count > self.max_properties else ''}
                </div>
                <hr>
            """
            
            for prop in display_properties:
                html_content += f"""
                <div class="property">
                    <h3>{prop['物件名']}</h3>
                    <p><strong>所在地:</strong> {prop['所在地']}</p>
                    <p><strong>賃料:</strong> {prop['賃料']}</p>
                    <p><strong>間取り:</strong> {prop['間取り']}</p>
                    <p><strong>専有面積:</strong> {prop['専有面積']}</p>
                    <p><strong>アクセス:</strong> {prop['アクセス']}</p>
                    <p><strong>築年数:</strong> {prop['築年数']}</p>
                    <p><strong>管理費:</strong> {prop['管理費']}</p>
                    <p><strong>敷金:</strong> {prop['敷金']}</p>
                    <p><strong>礼金:</strong> {prop['礼金']}</p>
                    <p><strong>詳細URL:</strong> <a href="{prop['物件URL']}">{prop['物件URL']}</a></p>
                    <img src="{prop['メイン画像']}" alt="物件画像">
                </div>
                <hr>
                """
            
            html_content += """
            </body>
            </html>
            """

            # メールの作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = self.notification_email
            
            # HTMLコンテンツの追加
            msg.attach(MIMEText(html_content, 'html'))

            # メールの送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"新着物件の通知メールを送信しました: {total_count}件")
            
        except Exception as e:
            print(f"メール送信中にエラーが発生: {e}") 