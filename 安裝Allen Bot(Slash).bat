@echo off
echo 安裝Allen Bot(Slash)中...
echo 從GitHub下載檔案中...
git clone https://github.com/Alllen95Wei/My-Discord-Bot-Slash.git
cd My-Discord-Bot-Slash
echo 安裝套件中...
pip install -r requirements.txt
echo 創建"user_data"資料夾...
mkdir user_data
echo 安裝完成！
echo 在啟動前，請先按照下列步驟執行：
echo 1. 在 https://discord.com/developers/applications 創建一個應用程式，並複製Token。
echo 2. 使用記事本開啟"TOKEN-example.env"，並在"TOKEN="後面輸入你的機器人的Token。
echo 3. 將檔案重新命名為"TOKEN.env"。
echo 4. 在 https://discord.com/developers/applications 創建一個邀請連結，並將機器人加入伺服器。
echo 5. 完成之後，請在此視窗按下任意鍵，執行Allen Bot(Slash)。
pause
echo 啟動Allen Bot(Slash)中...
python main.py