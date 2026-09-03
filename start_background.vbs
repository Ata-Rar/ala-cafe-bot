Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\ataha\Documents\HayriOS\Projects\Ala-Cafe-Discord-Bot"
WshShell.Run "python bot.py", 0, False
