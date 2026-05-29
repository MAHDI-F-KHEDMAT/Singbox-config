name: Find Live Configs with Xray

on:
  schedule:
    - cron: '0 */6 * * *' # اجرای خودکار هر ۶ ساعت یک‌بار
  workflow_dispatch: # دکمه اجرای دستی

jobs:
  run-tester:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install Dependencies
      run: |
        pip install aiohttp aiohttp_socks

    - name: Download and Setup Xray Core
      run: |
        # دانلود آخرین نسخه پایدار هسته رسمی Xray
        wget "https://github.com/XTLS/Xray-core/releases/download/v1.8.24/Xray-linux-64.zip"
        
        # استخراج فایل باینری از حالت فشرده زیپ
        unzip Xray-linux-64.zip -d xray_extracted
        
        # انتقال فایل اجرایی اصلی به پوشه اصلی پروژه
        mv xray_extracted/xray .
        
        # دادن دسترسی اجرایی به فایل در سرور لینوکس گیت‌هاب
        chmod +x xray
        
        # پاکسازی فایل‌های زیپ اضافه
        rm -rf Xray-linux-64.zip xray_extracted

    - name: Run Config Tester Script
      run: |
        python main.py

    - name: Commit and Push Files
      run: |
        git config --global user.name "github-actions[bot]"
        git config --global user.email "github-actions[bot]@users.noreply.github.com"
        git add valid_configs.json sub.txt
        git diff --quiet && git diff --staged --quiet || git commit -m "Update configs using Xray: $(date)"
        git push
