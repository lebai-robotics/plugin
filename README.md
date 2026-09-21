# 插件

## 简介

插件系统允许在机箱内运行任何可执行程序，可以通过[SDK](../sdk/index.md)控制机器人。

每个插件都可以包含3个组件： 可在网页端与用户交互的Web组件、开机自启并在后台持续运行的deamon组件、使用时调用一次的cmd组件。

## 目录结构

```bash
plugin  插件目录
├─plugin.json           插件配置信息
├─web                   Web组件目录
│  ├─index.html         Web组件入口文件
│  └─...                可随意存放各种前端文件（如js、css、图片、字体等）
├─bin                   可执行程序目录
│  ├─enable.exe         使能插件时运行一次（常用于安装项目依赖）
│  ├─disable.exe        禁用插件时运行一次（常用于清理项目数据）
│  ├─daemon.exe         deamon组件可执行程序
│  ├─cmd.exe            cmd组件可执行程序
│  └─...                可随意存放各种项目文件（如python源码等）
```

### plugin.json

```json
{
  "name": "claw",
  "author": "lebai.ltd",
  "description": "控制夹爪",
  "homepage": "https://help.lebai.ltd"
}
```

- name: 插件名称，必须与插件目录名一致
- author: 创作者
- description: 插件概述
- homepage: 项目网站，建议指向插件的使用说明
- auto_restart: daemon程序异常退出后，是否自动重启daemon程序

### Web

可以使用原生HTML，也可使用React、Vue等编译生成的HTML

### bin

可执行程序可以是C、Rust等编译生成的二进制文件，也可以是shell脚本。

## 开源插件

### camera

连接机箱摄像头并保存画面到文件系统

开源地址：<https://github.com/lebai-robotics/plugin/tree/main/camera>

### camera_calibrater

利用标定板进行相机标定

开源地址：<https://github.com/lebai-robotics/plugin/tree/main/camera_calibrater>

### apriltag

利用`camera_calibrater`的标定结果和`camera`的图像，计算AprilTag相对于基座的位姿

开源地址：<https://github.com/lebai-robotics/plugin/tree/main/apriltag>
