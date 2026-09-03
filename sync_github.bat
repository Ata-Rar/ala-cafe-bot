@echo off
title Ala Cafe GitHub Senkronizasyonu
echo ========================================================
echo   Ala Cafe Bot ve Web Paneli GitHub'a Yukleniyor...
echo ========================================================
cd /d "C:\Users\ataha\Documents\HayriOS\Projects\Ala-Cafe-Discord-Bot"
echo.
echo 1. GitHub Yetkilendirmesi Baslatiliyor...
gh auth login --web -h github.com -p https -w
echo.
echo 2. Kodlar gonderiliyor...
git push -u origin main
echo.
echo ========================================================
echo   ISLEM TAMAMLANDI!
echo ========================================================
pause
