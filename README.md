# PhantomMan-Steganography-Tool-Hide-ZIP-Files-in-MP4-Videos-by-NightSubmarine
A tool that enables video steganography by packaging files into ZIP archives and embedding them within a hide box in MP4 shell files.Compatible with Bandizip and WinRAR. Written in Python and HTML/JavaScript.  
**Inspired by cenglin123's SteganographierGUI https://github.com/cenglin123/SteganographierGUI**  
Developed with the assistance of Gemini. The front-end GUI was written by Gemini.  

https://www.virustotal.com/gui/file/a48ef8dec8c594fb4b87bf7aeec37cd1c13b356d24d26432e158996912869ead?nocache=1  

<h2>How to Use</h2>

![屏幕截图 2026-03-25 135950](https://github.com/user-attachments/assets/76a1eedc-5035-462c-a9de-e5b1bf4e4d3a)

![屏幕截图 2026-03-25 133602](https://github.com/user-attachments/assets/0c4c604e-1d44-40b3-9e3d-945c139ab847)

**Tips**  
1. It is best to first nest the encrypted archive inside a password-free ZIP archive. That is, place the resources inside the encrypted archive, and then place that encrypted archive containing the resources inside a password-free ZIP file. This method is faster when used on a mechanical hard drive. This is because, for password-free .zip files and files with the .bin extension, the software will directly embed them into the MP4 shell video to create a disguised file. For encrypted ZIP archives, other files, and folders, PhantomMan will first pack them into a ZIP archive to create a temporary file, then add them to the video’s disguised MP4 hide box. Packing files and folders into a temporary ZIP file can be very time-consuming when using a mechanical hard drive.  

2. You can add any type of file to the MP4 hide box as a data stream by changing the file extension to .bin, though whether compression software can recognize them is another matter. Based on personal testing, 7z and RAR files cannot be recognized by mainstream compression software.  
