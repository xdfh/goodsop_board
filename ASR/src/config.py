# src/config.py
import os
from dynaconf import Dynaconf

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 显式文件加载逻辑 ---
ENV_VAR = "ENV_FOR_DYNACONF"
# 默认为 "dev01" 环境
active_env = os.environ.get(ENV_VAR, "dev01").lower()

print("-" * 50)
print(f"INFO: 检测到当前环境为: '{active_env}'")

# 总是先加载基础配置文件
files_to_load = [os.path.join(ROOT_DIR, 'config', 'default.py')]

# 然后根据环境，添加特定的配置文件
env_file_path = os.path.join(ROOT_DIR, 'config', f'{active_env}.py')
if os.path.exists(env_file_path):
    files_to_load.append(env_file_path)
    print(f"INFO: 准备加载配置文件: {env_file_path}")
else:
    # 这是一个安全保障，如果指定了不存在的环境，程序会警告
    print(f"警告: 未找到环境 '{active_env}' 的配置文件: {env_file_path}")
    print(f"INFO: 将仅使用 'default.py' 的配置。")
print("-" * 50)


settings = Dynaconf(
    # 设置环境变量的前缀为 "ASR"
    envvar_prefix="ASR",
    
    # 显式地提供要加载的文件列表，不再使用自动环境切换功能。
    settings_files=files_to_load,
)

# 使用示例:
# from src.config import settings
# print(settings.ASR_DEVICE)
# print(settings.PORT) 