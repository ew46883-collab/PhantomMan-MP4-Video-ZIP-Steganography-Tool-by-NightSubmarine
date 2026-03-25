# 幽灵侠MP4视频ZIP隐写术工具 by NightSubmarine
一款支持视频隐写术的工具，通过将文件打包为ZIP压缩包，并将其嵌入MP4外壳文件中的隐藏框内。兼容Bandizip和WinRAR。采用Python及HTML/JavaScript编写，使用了html/js前端加pywebview。发行版使用nuitka编译。  
前端gui由Gemini生成，python后端逻辑由我编写，并由Gemini整理。  
**受到cenglin123的SteganographierGUI软件启发开发 https://github.com/cenglin123/SteganographierGUI**  

杀毒扫描 https://www.virustotal.com/gui/file/a48ef8dec8c594fb4b87bf7aeec37cd1c13b356d24d26432e158996912869ead?nocache=1

<h2>How to Use</h2>

![屏幕截图 2026-03-25 133602](https://github.com/user-attachments/assets/0c4c604e-1d44-40b3-9e3d-945c139ab847)

**小技巧：**  
1.最好预先把加密压缩包用无密码的zip压缩包嵌套打包，就是无密码的zip压缩包里面嵌套一个加密的压缩包，加密压缩包里面再放资源，在机械硬盘上使用时这种做法可以更快。因为对于无密码的.zip压缩文件和后缀名为.bin的文件，本软件会直接把它塞进mp4外壳视频里形成伪装文件。加密的zip压缩包，其他文件和文件夹，PhantomMan软件会先把它们打包成zip压缩文件，生成临时文件，再添加进视频的伪装mp4 hide box里。把文件和文件夹打包成zip临时文件可能会非常耗时，在机械硬盘上的时候。
2.你可以通过把文件后缀名改成.bin来把任何类型的文件以数据流的形式添加进mp4的hide box里，压缩软件能否识别它们另当别论。亲测7z和rar无法被主流压缩软件识别。
