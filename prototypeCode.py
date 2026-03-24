import os
import struct
import shutil


def is_valid_zip(zip_path):
    """检查文件是否以 ZIP 文件头 PK\x03\x04 开头"""
    ZIP_MAGIC = b'\x50\x4b\x03\x04'
    with open(zip_path, 'rb') as f:
        header = f.read(4)
        return header == ZIP_MAGIC


def inject_zip_as_hide_box(mp4_src, zip_src, output_file):
    """
    将 ZIP 文件嵌入 MP4 末尾的一个自定义 'hide' Box 中
    """
    # 1. 安全校验
    if not os.path.exists(mp4_src) or not os.path.exists(zip_src):
        print("错误：找不到输入文件。")
        return

    if not is_valid_zip(zip_src):
        print("错误：待嵌入的文件不是有效的 ZIP 压缩包（未检测到 PK 头）。")
        return

    # 2. 计算尺寸
    zip_size = os.path.getsize(zip_src)
    # Box 头部：4字节(1) + 4字节(type) + 8字节(真实长度) = 16 字节
    header_size = 16
    total_box_size = zip_size + header_size

    print(f"[*] 准备植入...")
    print(f"[*] 目标 ZIP 大小: {zip_size / 1024 / 1024:.2f} MB")
    print(f"[*] 'hide' Box 总长度: {total_box_size} 字节")

    # 3. 开始流式处理
    try:
        with open(output_file, 'wb') as f_out:
            # 步骤 A: 复制原始 MP4 内容
            print("[1/3] 复制原始视频数据...")
            with open(mp4_src, 'rb') as f_mp4:
                shutil.copyfileobj(f_mp4, f_out)

            # 步骤 B: 写入自定义 'hide' Box 头部
            print("[2/3] 写入 'hide' Box 头部 (64-bit LargeSize)...")
            # 标志位: 1 (表示使用 64位 Size 字段)
            f_out.write(struct.pack('>I', 1))
            # 类型: 'hide'
            f_out.write(b'hide')
            # 真实长度: 64位无符号整数 (Big-Endian)
            f_out.write(struct.pack('>Q', total_box_size))

            # 步骤 C: 写入 ZIP 原始二进制流
            print("[3/3] 植入 ZIP 数据流...")
            with open(zip_src, 'rb') as f_zip:
                shutil.copyfileobj(f_zip, f_out)

        print(f"\n[!] 完成！隐写视频已生成: {output_file}")

    except Exception as e:
        print(f"\n[失败] 发生错误: {e}")


# --- 实例运行 ---
if __name__ == "__main__":
    # 请根据实际文件名修改
    source_video = r"D:\TEMP\29319432053-1-192.mp4"
    secret_zip = r"D:\TEMP\2017年12月英语六级真题(第2套).zip"
    final_video = r"D:\TEMP\stego_output.mp4"

    # 如果文件存在则执行
    if os.path.exists(source_video) and os.path.exists(secret_zip):
        inject_zip_as_hide_box(source_video, secret_zip, final_video)
    else:
        print("请确保目录下存在 original.mp4 和 data.zip")