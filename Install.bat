@echo off
git clone https://github.com/Alllen95Wei/My-Discord-Bot-Slash.git
if %errorlevel% neq 0 goto error
cd My-Discord-Bot-Slash
if %errorlevel% neq 0 goto error
pip install -r requirements.txt
if %errorlevel% neq 0 goto error
echo Finished! Before you run the bot, please edit the "TOKEN-example.env" file by adding your bot token.
echo After that, rename the file to "TOKEN.env".
pause

: error
echo An error has occurred. Please check the error message above.
pause
exit /b 1