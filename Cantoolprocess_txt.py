import os
import re

global_workspacename = "I1_CAN_FD_VER02_01_01_MY_ECU_2"
special_strings = ["CRC", "ZCUF", "CL30", "CL15", "DCFC", "BMS", "CCu", "ACM"]
global_msg_name = ""

def process_line1(line):
    # 使用正則表達式擷取括弧內的內容（不包含 "*data" 部分）
    match = re.search(r'\(([^*]+)\s+\*data\)', line)
    if match:
        content = match.group(1).strip()
        # 將擷取到的內容替換成指定格式
        return f"{content} {content}_Data;"
    return None

def process_line2(line):
    match = re.search(r'(Rte_Read_[A-Za-z0-9_]+)\(([A-Za-z0-9_]+)\s+\*data\)', line)
    if match:
        full_signature = match.group(1)
        var_name = match.group(2)
        return f"{full_signature}(&{var_name}_Data);"
    return None

def process_line3(line):
    global global_msg_name
    global global_workspacename
    match = re.search(r'Rte_Read_CRC_([A-Za-z0-9_]+)_CRC_([A-Za-z0-9_]+)', line)
    if match:
        global_msg_name = match.group(1)
        string = convert_string(global_msg_name)
        msg_name = convert_string(global_msg_name)
        code_snippet = f"""
u8arrayTx[INDEX_APSS_CMD] = (uint8)APSS_WRITE_CMD;
u8arrayTx[INDEX_APSS_LEN] = (uint8)({global_workspacename}_{string.upper()}_LENGTH + 10);
u8arrayTx[INDEX_APSS_SEQ] = (uint8)((*Rte_Pim_MsgAlvCounter() & 0xFF00) >> 8);
u8arrayTx[INDEX_APSS_SEQ + 1] = (uint8)(*Rte_Pim_MsgAlvCounter() & 0x00FF);
u8arrayTx[INDEX_CAN_IF] = (uint8)(CAN_I1_Channel);
// u8arrayTx[INDEX_CAN_MSGID] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0xFF000000) >> 24);
// u8arrayTx[INDEX_CAN_MSGID + 1] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0x00FF0000) >> 16);
// u8arrayTx[INDEX_CAN_MSGID + 2] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0x0000FF00) >> 8);
// u8arrayTx[INDEX_CAN_MSGID + 3] = (uint8)({global_workspacename}_{string.upper()}_FRAME_ID & 0x000000FF);
u8arrayTx[INDEX_CAN_MSGID + 3] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0xFF000000) >> 24);
u8arrayTx[INDEX_CAN_MSGID + 2] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0x00FF0000) >> 16);
u8arrayTx[INDEX_CAN_MSGID + 1] = (uint8)(({global_workspacename}_{string.upper()}_FRAME_ID & 0x0000FF00) >> 8);
u8arrayTx[INDEX_CAN_MSGID] = (uint8)({global_workspacename}_{string.upper()}_FRAME_ID & 0x000000FF);
u8arrayTx[INDEX_CAN_DLC] = (uint8)({global_workspacename}_{string.upper()}_LENGTH);

struct {global_workspacename.lower()}_{msg_name.lower()}_t {msg_name.lower()};
"""
        return code_snippet.strip()
    return None

def process_line4(line):
    global global_msg_name
    match = re.search(r'\(([^*]+)\s+\*data\)', line)
    if match:
        content = match.group(1).strip()
        string = convert_string(content)
        msg_name = convert_string(global_msg_name)
        return f"{msg_name.lower()}.{string.lower()} = (uint8){content}_Data;"
    return None

def process_line5(line):
    global global_msg_name
    global global_workspacename
    match = re.search(r'Rte_Read_CRC_([A-Za-z0-9_]+)_CRC_([A-Za-z0-9_]+)', line)
    if match:
        msg_name = convert_string(global_msg_name)
        code_snippet = f"""
uint8_t dataArray[{global_workspacename}_{msg_name.upper()}_LENGTH] = {{0}};
if ({global_workspacename.lower()}_{msg_name.lower()}_pack(dataArray, &{msg_name.lower()}, {global_workspacename}_{msg_name.upper()}_LENGTH) == {global_workspacename}_{msg_name.upper()}_LENGTH)
    memcpy(&u8arrayTx[INDEX_CAN_DATA], dataArray, {global_workspacename}_{msg_name.upper()}_LENGTH);
    
uint32 crc_sum;
crc_sum = FlexCanApp_Calc_Crc32_test(&u8arrayTx, u8arrayTx[INDEX_APSS_LEN], 0);
u8arrayTx[u8arrayTx[INDEX_APSS_LEN]] = (uint8_t)((crc_sum & 0xFF000000) >> 24);
u8arrayTx[u8arrayTx[INDEX_APSS_LEN] + 1] = (uint8_t)((crc_sum & 0x00FF0000) >> 16);
u8arrayTx[u8arrayTx[INDEX_APSS_LEN] + 2] = (uint8_t)((crc_sum & 0x0000FF00) >> 8);
u8arrayTx[u8arrayTx[INDEX_APSS_LEN] + 3] = (uint8_t)(crc_sum & 0x000000FF);

Rte_Call_IF_IOHw_SPI_API_IoHwAbOperation_Communication(Master_To_APSS, &u8arrayTx, &u8arrayRx, APSS_NUM);
*Rte_Pim_MsgAlvCounter() = *Rte_Pim_MsgAlvCounter() + 1;
"""
        return code_snippet.strip()
    return None

def process_file1(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line1(line)
            if processed_line:
                outfile.write(processed_line + '\n')
                
def process_file2(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line2(line)
            if processed_line:
                outfile.write(processed_line + '\n')

def process_file3(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line3(line)
            if processed_line:
                outfile.write(processed_line + '\n')

def process_file4(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line4(line)
            if processed_line:
                outfile.write(processed_line + '\n')
                     
def process_file5(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line5(line)
            if processed_line:
                outfile.write(processed_line + '\n')

def convert_string(s):
    # 查找所有大写字母的位置
    uppercase_positions = [m.start() for m in re.finditer(r'[A-Z]', s)]
    # 如果大写字母数量少于2，不做任何修改
    if len(uppercase_positions) < 2:
        return s.lower()
    # 跳过特殊字串的拆解
    for special in special_strings:
        s = s.replace(special, special.lower())
    # 从第二个大写字母位置开始，在每个大写字母前面加上下划线
    # 需要确保跳过特殊字串后的拆解
    def add_underscore(match):
        if match.group(0).upper() in special_strings:
            return match.group(0)
        else:
            return "_" + match.group(0).lower()
    # 处理特殊字串后的字符串
    processed_string = re.sub(r'(?<!^)([A-Z])', add_underscore, s)
    return processed_string  

# def merge_files(file1, file2, file3, file4, file5, output_file):
#     with open(output_file, 'w', encoding='utf-8') as outfile:
#         with open(file1, 'r', encoding='utf-8') as f1:
#             outfile.write(f1.read())
#         outfile.write('\n')  # 添加一行空行作為間隔
#         with open(file2, 'r', encoding='utf-8') as f2:
#             outfile.write(f2.read())
#         outfile.write('\n')  # 添加一行空行作為間隔
#         with open(file3, 'r', encoding='utf-8') as f3:
#             outfile.write(f3.read())
#         outfile.write('\n')  # 添加一行空行作為間隔
#         with open(file4, 'r', encoding='utf-8') as f4:
#             outfile.write(f4.read())
#         outfile.write('\n')  # 添加一行空行作為間隔
#         with open(file5, 'r', encoding='utf-8') as f5:
#             outfile.write(f5.read())
  
# def replace_double_underscores(filename):
#     with open(filename, 'r', encoding='utf-8') as file:
#         lines = file.readlines()
#     # 遍历每一行，替换双下划线为单下划线
#     modified_lines = [line.replace('__', '_') for line in lines]
#     with open(filename, 'w', encoding='utf-8') as file:
#         file.writelines(modified_lines)

# def print_file(filename):
#     with open(filename, 'r', encoding='utf-8') as file:
#         file_content = file.read()  
#     # 输出文件内容
#     print(file_content)  

def process_files_final(file1, file2, file3, file4, file5, output_file):
    # 合并文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for file in [file1, file2, file3, file4, file5]:
            with open(file, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write('\n')  # 添加一行空行作为间隔
    # 替换双下划线为单下划线
    with open(output_file, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('__', '_')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)
    # 打印最终文件内容
    print(content) 
       
if __name__ == "__main__":
    input_file = 'input2.txt'  # 請將此處替換為您的txt文件名
    output_file1 = 'output1.txt'  # 第一個輸出結果文件名
    output_file2 = 'output2.txt'  # 第二個輸出結果文件名
    output_file3 = 'output3.txt'  # 第三個輸出結果文件名
    output_file4 = 'output4.txt'  # 第四個輸出結果文件名
    output_file5 = 'output5.txt'  # 第五個輸出結果文件名
    final_output_file =  'final_output.txt' #'final_output.txt'  # 合併後的最終輸出結果文件名
 
    process_file1(input_file, output_file1)
    process_file2(input_file, output_file2)
    process_file3(input_file, output_file3)
    process_file4(input_file, output_file4)
    process_file5(input_file, output_file5)
    # merge_files(output_file1, output_file2, output_file3, output_file4, output_file5, final_output_file)
    # replace_double_underscores(final_output_file) 
    # print_file(final_output_file)
    process_files_final(output_file1, output_file2, output_file3, output_file4, output_file5, final_output_file)
    os.remove(output_file1)
    os.remove(output_file2)
    os.remove(output_file3)
    os.remove(output_file4)
    os.remove(output_file5)