# 仓库：lebai-robotics/plugin

乐白机器人系统多插件仓库。每个顶层目录是一个独立插件，拥有自己的 `plugin.json`。

## 插件结构

每个插件遵循固定布局：
- `plugin.json` — name 必须与目录名一致；可选字段：`boxs`、`auto_restart`
- `web/` — 可选 Web UI（纯 HTML/CSS/JS，无构建步骤）
- `bin/` — 可执行文件和源码
  - `enable.exe` — 脚本，插件启用时执行一次（通常执行 `lpip install -r requirements.txt`）
  - `disable.exe` — 脚本，插件禁用时执行一次（清理）
  - `daemon.exe` — 脚本，启动长期运行的后台进程
  - `cmd.exe` — 脚本或 Python 脚本，一次性命令
  - `src/` — 实际源码（Python、Rust 等）

**重要**：`bin/` 下的 `.exe` 文件是可执行文件，可以是 bash 脚本、Python 脚本或二进制程序，需要拥有可执行权限。二进制程序需要区分 CPU 架构，通常放在 `bin/x86_64/` 或 `bin/aarch64/` 子目录中，通过 bash 脚本的 `uname -m` 进行自动识别（如 modbus_rtu_slave）。

## 编程语言

- **Python**（占多数）：camera、camera_calibrater、apriltag、io_stop、yolo、claw。使用 `lebai_sdk` 进行机器人通信。
- **Rust**：modbus_rtu_slave。交叉编译目标：`x86_64-unknown-linux-gnu` 和 `aarch64-unknown-linux-gnu`。
- **Shell 脚本**：所有 enable/disable/daemon 入口点。

## CI/CD

- **CI 脚本**：`ci.sh` — 遍历插件目录，打包 `git ls-files`（或自定义 `list.sh`）列出的文件，通过 `ossutil` 上传到 S3。
- **GitHub Actions**：`.github/workflows/publish.yml` — 在 Docker 容器 `registry.cn-shanghai.aliyuncs.com/lebai/util:14.04` 中运行 `ci.sh`。
- 部分插件有 `list.sh`（如 modbus_rtu_slave），在 CI 打包前先构建二进制文件。
- CI 输出到 `.oss/` 目录（已 gitignore）。

## 关键命令

- 构建 Rust 插件：`cd modbus_rtu_slave/bin && cargo build --release --target x86_64-unknown-linux-gnu`
- 安装 Python 依赖：使用 `lpip`（不是 pip）— 在 enable.exe 脚本中使用
- 运行 Python 脚本：使用 `lpy` 命令（不是 python）— 在 daemon.exe 脚本中使用

## 约定

- 插件目录相互独立；插件间无共享代码，但 `lebai_sdk` 的使用模式相同。
- Python 插件使用 `lebai_sdk.init()` 和 `lebai_sdk.connect("127.0.0.1", True)` 与机器人通信。
- Web UI 通过机器人插件系统与插件通信，非直接 HTTP。
- Camera 相关插件共享 `camera/images/` 图片存储（yolo 从此读取）。
- 部分插件针对特定硬件（`plugin.json` 中 `"boxs": ["LA3"]`）。
- 跨平台构建产出架构特定二进制文件（x86_64、aarch64），移至以架构命名的目录。
