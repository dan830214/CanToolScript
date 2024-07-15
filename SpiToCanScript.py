import os
import re

global_workspacename = "I1_CAN_FD_VER02_01_01_MY_ECU_2"
special_strings = ["CRC", "ZCUF", "CL30", "CL15", "DCFC", "BMS", "CCu", "ACM", "ASU", "ADAS", "FL", "FR", "RR", "RL", "CCU", "DCDC", "DCMD", "DCMP", "DCMRL", "DCMRR", "EBCM", "EPS", "HDLML", "HDLMR", "RWA", "SFA", "MCU", "MFS", "PSMD", "PSMP"]
global_struct_name = ""

# 添加特定字段转换规则
special_field_conversions = {
    "HVAC_CNTRL": "HvacCntrl",
    "ALV_CTR": "AlvCtr",
    "CCSF_VENT_OP_MODE_REQ": "Ccsf_VentOpModeReq",
    "CCS_RE_AC_USR_I_REQ": "Ccs_ReAcUsrIReq",
    "DEMIR_HEATG_SVMC_REQ": "Demir_HeatgSVMCReq",
    "CCS_RE_BLOWR_LV_USRL_REQ": "Ccs_ReBlowrLvUsrlReq",
    "DR_WNDW_CNTR": "DrWndw_Cntr",
    "DRV_DOOR_USR_AG_REQ": "DrvDoorUsrAgReq",
    "PASS_DOOR_USR_AG_REQ": "PassDoorUsrAgReq",
    "WNDW_UP_DWN_USR_REQ": "WndwUpDwnUsrReq",
    "LE_EXTND_RTRACT_REQ": "LeExtndRtractReq",
    "RI_EXTND_RTRACT_REQ": "RiExtndRtractReq",
    "PWD": "Pwd",
    "CEN": "Cen",
    "PWR_SD_ST": "PwrSdSt",
    "PWIND": "Pwind",
    "Cen_LOCK_AUDIO_VISUAL_CFG": "CenLock_AudioVisualCfg"
}

def remove_comments_from_struct(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    struct_lines = []
    inside_comment = False
    for line in lines:
        stripped_line = line.strip()
        # Check for start of comment block
        if stripped_line.startswith('/**'):
            inside_comment = True
            continue
        # Check for end of comment block
        if stripped_line.endswith('*/'):
            inside_comment = False
            continue
        # Skip lines inside comment block
        if inside_comment:
            continue
        # Add lines that are not comments
        struct_lines.append(line)
    # Remove extra newline characters
    struct_lines = [line for line in struct_lines if line.strip()]
    return ''.join(struct_lines)

def find_struct_name(lines):
    global global_struct_name
    # Construct the pattern based on global_workspacename
    relevant_part = global_workspacename.lower()
    pattern = fr'{relevant_part}_(\w+)_t'
    match = re.search(pattern, lines)
    if match:
        global_struct_name = match.group(1)
        global_struct_name = convert_string(global_struct_name)

def generate_case_text(lines):
    global global_workspacename
    global global_struct_name
    case_text = f"""case {global_workspacename.upper()}_{global_struct_name.upper()}_FRAME_ID:
struct {global_workspacename.lower()}_{global_struct_name.lower()}_t {global_struct_name.lower()};
uint8 u8arrayTemp[64] = {{0}};
memcpy(u8arrayTemp, &u8arrayRxDequeue[10], {global_workspacename.upper()}_{global_struct_name.upper()}_LENGTH);
if ({global_workspacename.lower()}_{global_struct_name.lower()}_unpack(&{global_struct_name.lower()}, u8arrayTemp, {global_workspacename.upper()}_{global_struct_name.upper()}_LENGTH) == 0)
{{"""
    return case_text

def process_struct_line(line):
    global global_workspacename
    global global_struct_name
    # Match lines like "int var;", "unsigned int var;", "char* var;", etc.
    match = re.match(r'\s*(\w[\w\s\*]*\w)\s+(\w+)\s*;', line)
    if match:
        variable_type = match.group(1).strip()
        variable_name = match.group(2).strip()
        # Ensure the type is formatted correctly
        variable_type = variable_type.replace(' ', '_').replace('*', 'ptr').upper()
        # Generate the required format
        data_line = f"        {variable_name.upper()} {variable_name.upper()}_Data = ({variable_name.upper()}){global_struct_name.lower()}.{variable_name.lower()};"
        return data_line
    return None

def process_struct_line_2(line):
    global global_workspacename
    global global_struct_name
    # Match lines like "int var;", "unsigned int var;", "char* var;", etc.
    match = re.match(r'\s*(\w[\w\s\*]*\w)\s+(\w+)\s*;', line)
    if match:
        variable_type = match.group(1).strip()
        variable_name = match.group(2).strip()
        # Ensure the type is formatted correctly
        variable_type = variable_type.replace(' ', '_').replace('*', 'ptr').upper()
        # Generate the required format
        data_line = f"        Rte_Write_{variable_name.upper()}_{variable_name.upper()}({variable_name.upper()}_Data);"
        return data_line
    return None

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

# 添加替换特定字段的函数
def replace_special_fields(text, conversions):
    for original, replacement in conversions.items():
        text = text.replace(original, replacement)
    return text

if __name__ == "__main__":
    input_file = 'input_spi.txt'
    final_output_file = "generated_text.txt"
    output = remove_comments_from_struct(input_file)
    
    # Save the simplified struct to a new file
    with open('output_spi.txt', 'w') as file:
        file.write(output)
    
    find_struct_name(output)
    
    generated_text = generate_case_text(output)
    
    # Process each line in the struct and append the data lines to the case text
    struct_lines = output.splitlines()
    for line in struct_lines:
        data_line = process_struct_line(line)
        if data_line:
            generated_text += "\n" + data_line
            
    for line in struct_lines:
        data_line = process_struct_line_2(line)
        if data_line:
            generated_text += "\n" + data_line
            
    # Close the case text block
    generated_text += "\n    }\n    break;"
    
    # 保护函数调用和宏名称
    protected_patterns = [
        fr'{global_workspacename.upper()}_{global_struct_name.upper()}_LENGTH',
        fr'{global_workspacename.lower()}_{global_struct_name.lower()}_unpack',
    ]

    placeholders = {pattern: f"PLACEHOLDER_{i}" for i, pattern in enumerate(protected_patterns)}

    for pattern, placeholder in placeholders.items():
        generated_text = generated_text.replace(pattern, placeholder)
    
    # 提取大括号内的部分进行替换
    case_body_start = generated_text.find("{")
    case_body_end = generated_text.rfind("}")
    case_body = generated_text[case_body_start + 1:case_body_end]
    
    # 在大括号内的部分进行特定字段的替换
    case_body = replace_special_fields(case_body, special_field_conversions)
    
    # 将替换后的大括号内的部分合并回去
    generated_text = generated_text[:case_body_start + 1] + case_body + generated_text[case_body_end:]
    
    # 还原保护的部分
    for pattern, placeholder in placeholders.items():
        generated_text = generated_text.replace(placeholder, pattern)
    
    # Write the generated text to a file
    with open(final_output_file, "w") as file:
        file.write(generated_text)
    
    # Optionally, remove the intermediate output file
    os.remove('output_spi.txt')
    
    # print(generated_text)