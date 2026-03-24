import webview
import os
import struct
import zipfile
import shutil
import sys
import threading

# 常量定义
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB，适合处理 1-2GB 大文件
HIDE_BOX_TYPE = b'hide'

class StegoApi:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    # --- 1. 前端 UI 交互辅助方法 ---
    def log(self, msg):
        """推送日志到前端"""
        # 替换单引号，防止 JS 语法错误
        safe_msg = str(msg).replace("'", "\\'")
        self._window.evaluate_js(f"addLog('{safe_msg}')")

    def progress(self, percent):
        """推送进度条到前端"""
        self._window.evaluate_js(f"updateProgress({percent})")

    def remove_double_quotes(self, text):
        if text[0] and text[-1] == r'"':
            text=text[1:-1]
        return text

    def select_file(self):
        result = self._window.create_file_dialog(webview.OPEN_DIALOG)
        #print(result,type(result),type(result[0]))
        result=list(result)
        #print(result, type(result), type(result[0]))
        result[0]=self.remove_double_quotes(result[0])
        return result[0] if result else None

    def select_folder(self):
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        #print(result,type(result),type(result[0]))
        result=list(result)
        result[0] = self.remove_double_quotes(result[0])
        #print(result, type(result), type(result[0]))
        return result[0] if result else None

    # --- 2. 核心文件处理工具 ---
    def get_unique_path(self, target_path):
        """处理文件/目录名冲突，生成类似 xxx(1).mp4 的名字"""
        if not os.path.exists(target_path):
            return target_path
        base, ext = os.path.splitext(target_path)
        counter = 1
        while True:
            new_path = f"{base}({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def is_zip_encrypted(self, filepath):
        """检测 ZIP 文件是否包含加密内容"""
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for info in zf.infolist():
                    if info.flag_bits & 0x1:
                        return True
            return False
        except Exception:
            return False

    def get_archive_type(self, filepath):
        """根据文件头（Magic Number）判断压缩包格式"""
        with open(filepath, 'rb') as f:
            magic = f.read(8)
            if magic.startswith(b'PK\x03\x04'): return 'zip'
            if magic.startswith(b'Rar!\x1A\x07'): return 'rar'
            if magic.startswith(b'7z\xBC\xAF\x27\x1C'): return '7z'
        return 'unknown'

    def parse_mp4_boxes(self, filepath):
        """解析 MP4 顶层 Box，检查是否有效以及是否包含 hide box"""
        boxes = []
        file_size = os.path.getsize(filepath)
        try:
            with open(filepath, 'rb') as f:
                offset = 0
                while offset < file_size:
                    f.seek(offset)
                    header = f.read(8)
                    if len(header) < 8: break
                    box_size, box_type = struct.unpack(">I4s", header)
                    
                    payload_offset = offset + 8
                    # 处理 64 位 Box Size
                    if box_size == 1:
                        large_size = struct.unpack(">Q", f.read(8))[0]
                        box_size = large_size
                        payload_offset = offset + 16
                    elif box_size == 0:
                        box_size = file_size - offset
                    
                    payload_size = box_size - (payload_offset - offset)
                    boxes.append({'type': box_type, 'payload_offset': payload_offset, 'payload_size': payload_size})
                    offset += box_size
            return boxes
        except Exception as e:
            return None # 解析失败，非有效 MP4

    def validate_shell_video(self, shell_path):
        """校验外壳视频是否有效且无 hide box"""
        if not os.path.isfile(shell_path):
            self.log(f"<span style='color:red;'>错误：外壳视频不存在 - {shell_path}</span>")
            return False
        boxes = self.parse_mp4_boxes(shell_path)
        if boxes is None or not any(b['type'] == b'ftyp' for b in boxes):
            self.log(f"<span style='color:red;'>错误：该文件不是有效的 MP4 视频。</span>")
            return False
        if any(b['type'] == HIDE_BOX_TYPE for b in boxes):
            self.log(f"<span style='color:red;'>错误：此外壳视频已包含 hide box，不可二次植入。</span>")
            return False
        return True

    def create_temp_zip(self, source, temp_dir, include_parent):
        """将文件或文件夹打包成 ZIP 存入缓存目录"""
        base_name = os.path.basename(source.rstrip('/\\'))
        temp_zip_path = self.get_unique_path(os.path.join(temp_dir, f"temp_{base_name}.zip"))
        
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.isfile(source):
                zf.write(source, arcname=base_name)
            elif os.path.isdir(source):
                for root, _, files in os.walk(source):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, source)
                        arcname = os.path.join(base_name, rel_path) if include_parent else rel_path
                        zf.write(file_path, arcname)
        return temp_zip_path

    # --- 3. 批量植入模块 ---
    def process_batch_injection(self, shell_video, target_list, temp_dir, output_dir, include_parent):
        #os.makedirs(temp_dir, exist_ok=True)
        #os.makedirs(output_dir, exist_ok=True)
        shell_video=self.remove_double_quotes(shell_video)
        temp_dir=self.remove_double_quotes(temp_dir)
        output_dir=self.remove_double_quotes(output_dir)
        #print(shell_video,type(shell_video))
        #print(temp_dir,type(temp_dir))
        #print(output_dir, type(output_dir))

        if os.path.exists(temp_dir)==False: os.makedirs(temp_dir)
        if os.path.exists(output_dir)==False: os.makedirs(output_dir)

        if not self.validate_shell_video(shell_video):
            return

        shell_size = os.path.getsize(shell_video)

        for target in target_list:
            #print('165'+target,type(target))
            target = self.remove_double_quotes(target)
            if not os.path.exists(target):
                self.log(f"警告：找不到路径跳过 - {target}")
                continue

            self.log(f"开始处理目标: {target}")
            payload_path = None
            is_temp_created = False

            # 逻辑1：判断是压缩包、文件还是目录
            if os.path.isfile(target) and target.lower().endswith('.zip'):
                if not self.is_zip_encrypted(target):
                    self.log("检测到无密码 ZIP，直接准备植入...")
                    payload_path = target
                else:
                    self.log("检测到加密 ZIP，无需重新打包，直接植入...")
                    payload_path = target
            else:
                self.log("非 ZIP 或为目录，正在缓存目录生成压缩包...")
                payload_path = self.create_temp_zip(target, temp_dir, include_parent)
                is_temp_created = True

            # 逻辑2：创建输出 MP4 路径
            base_target_name = os.path.basename(target.rstrip('/\\'))
            out_mp4_path = self.get_unique_path(os.path.join(output_dir, f"{base_target_name}_stego.mp4"))

            payload_size = os.path.getsize(payload_path)
            total_work = shell_size + payload_size
            written = 0

            # 逻辑3：二进制合并 (Shell + Box Header + Payload)
            try:
                with open(out_mp4_path, 'wb') as f_out:
                    # 复制原视频
                    with open(shell_video, 'rb') as f_shell:
                        while chunk := f_shell.read(CHUNK_SIZE):
                            f_out.write(chunk)
                            written += len(chunk)
                            self.progress(int(written / total_work * 100))
                    
                    # 写入 64位 hide box 头 (16字节)
                    box_total_size = payload_size + 16
                    f_out.write(struct.pack(">I4sQ", 1, HIDE_BOX_TYPE, box_total_size))
                    
                    # 写入 Payload
                    with open(payload_path, 'rb') as f_payload:
                        while chunk := f_payload.read(CHUNK_SIZE):
                            f_out.write(chunk)
                            written += len(chunk)
                            self.progress(int(written / total_work * 100))
                            
                self.log(f"<span style='color:lime;'>成功：植入完成 -> {out_mp4_path}</span>")
            except Exception as e:
                self.log(f"<span style='color:red;'>合并时出错: {e}</span>")
            finally:
                # 逻辑4：清理临时文件
                if is_temp_created and os.path.exists(payload_path):
                    os.remove(payload_path)

        self.progress(100)
        self.log("所有植入任务处理完毕！")

    # --- 4. 批量提取模块 ---
    def process_batch_extraction(self, target_list, output_dir):

        #os.makedirs(output_dir, exist_ok=True)
        # 使用缓存目录存放提取出来的 raw payload
        output_dir=self.remove_double_quotes(output_dir)
        if os.path.exists(output_dir)==False: os.makedirs(output_dir)
        temp_dir = os.path.abspath("./.temp")
        os.makedirs(temp_dir, exist_ok=True)

        for mp4_target in target_list:
            mp4_target = self.remove_double_quotes(mp4_target)
            if not os.path.isfile(mp4_target):
                self.log(f"警告：文件不存在跳过 - {mp4_target}")
                continue

            self.log(f"分析视频: {mp4_target}")
            boxes = self.parse_mp4_boxes(mp4_target)
            if boxes is None:
                self.log(f"<span style='color:red;'>错误：不是有效 MP4 - {mp4_target}</span>")
                continue

            hide_boxes = [b for b in boxes if b['type'] == HIDE_BOX_TYPE]
            if not hide_boxes:
                self.log("未发现任何 hide box 隐藏数据。")
                continue

            self.log(f"发现 {len(hide_boxes)} 个隐藏数据块，准备提取...")

            with open(mp4_target, 'rb') as f_in:
                for idx, hb in enumerate(hide_boxes):
                    # 1. 将 payload 提取到临时文件
                    temp_payload = os.path.join(temp_dir, f"raw_payload_{idx}.tmp")
                    f_in.seek(hb['payload_offset'])
                    bytes_to_read = hb['payload_size']
                    
                    with open(temp_payload, 'wb') as f_tmp:
                        while bytes_to_read > 0:
                            chunk = f_in.read(min(CHUNK_SIZE, bytes_to_read))
                            if not chunk: break
                            f_tmp.write(chunk)
                            bytes_to_read -= len(chunk)

                    # 2. 判断文件类型
                    arc_type = self.get_archive_type(temp_payload)
                    base_name = os.path.splitext(os.path.basename(mp4_target))[0]

                    if arc_type in ['rar', '7z']:
                        # 非 ZIP，直接移动到输出目录
                        out_file = self.get_unique_path(os.path.join(output_dir, f"{base_name}_extracted.{arc_type}"))
                        shutil.move(temp_payload, out_file)
                        self.log(f"<span style='color:lime;'>成功：分离出 {arc_type.upper()} 文件 -> {out_file}</span>")

                    elif arc_type == 'zip':
                        if self.is_zip_encrypted(temp_payload):
                            # 加密 ZIP，不解压，直接输出
                            out_file = self.get_unique_path(os.path.join(output_dir, f"{base_name}_extracted.zip"))
                            shutil.move(temp_payload, out_file)
                            self.log(f"<span style='color:lime;'>成功：分离出加密 ZIP -> {out_file}</span>")
                        else:
                            # 无密码 ZIP，解压里面内容
                            out_folder = self.get_unique_path(os.path.join(output_dir, f"{base_name}_contents"))
                            os.makedirs(out_folder)
                            try:
                                with zipfile.ZipFile(temp_payload, 'r') as zf:
                                    zf.extractall(out_folder)
                                self.log(f"<span style='color:lime;'>成功：解压无密码 ZIP -> {out_folder}</span>")
                            except Exception as e:
                                self.log(f"<span style='color:red;'>解压失败: {e}</span>")
                            finally:
                                os.remove(temp_payload)
                    else:
                        # 未知格式，当成 raw 数据抛出
                        out_file = self.get_unique_path(os.path.join(output_dir, f"{base_name}_unknown.dat"))
                        shutil.move(temp_payload, out_file)
                        self.log(f"警告：未知格式数据，已保存为 -> {out_file}")

        self.progress(100)
        self.log("所有提取任务处理完毕！")

if __name__ == '__main__':
    api = StegoApi()

    window = webview.create_window('PhantomMan MP4 Video Steganography Tool', 'gui.html', js_api=api, width=950, height=850)
    api.set_window(window)
    webview.start()