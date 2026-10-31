# MiraiHub 构建与验证

在 Windows x64 项目根目录双击 `build.bat`，或执行：

```powershell
.\build.bat --dry-run
.\build.bat --non-interactive
```

构建会使用当前工作目录的源码，包括未提交改动。`--dry-run` 仅检查工具并显示命令；`--non-interactive` 沿用当前版本，不等待输入。交互模式在 10 秒内未提交输入或直接回车，也沿用当前版本。

## 环境

需要 64 位 Python 3.10、JDK 17、Gradle 8.11.1、Android SDK 35 和 Build Tools 35.0.0。优先复用 `.desktop-build`、`build/android-tools/` 和 Gradle 缓存。其他安装位置可显式指定：

```powershell
.\build.bat --jdk C:\Tools\jdk-17 --sdk C:\Tools\android-sdk --gradle C:\Tools\gradle-8.11.1\bin\gradle.bat
```

版本唯一来源是 `desktop/version.json`（当前 `1.0.0`），更新源为 [新仓库](https://github.com/xiaofan6ya/MiraiHub)。需要修改版本时使用 `--version X.Y.Z`，三个部分必须为数字，次版本号和修订号小于 1000。构建不会自动拉取、提交、推送或发布。

## 产物

- Windows：`dist/` 下的 `*-windows-x64.zip` 与对应 `.zip.sha256`。zip 解开后根目录直接是 `*-windows-x64.exe` 与 `_internal/`，不再套一层文件夹。
- Android：`dist/android/` 下的 `*-android-arm64.apk` 与对应 `.apk.sha256`。
- 完整日志：`build/package-logs/`；两端成功后生成 `dist/build-版本号.json`。

安装包前缀统一为 `miraihub`，产品界面和版本资源使用同一名称。

Windows 采用 **onedir** 打包：程序依赖放在同目录的 `_internal/`，启动时不需要解包，因此没有 onefile 的 `_MEI*` 临时目录、启动更快，也不会在开机自启（工作目录常为 `System32`）时把临时文件写进系统目录。分发时把 zip 拷到目标位置解压即可。

运行期为便携模式：数据、日志、缓存、媒体资产与临时文件全部写在 EXE 所在目录，所以直接运行会往该目录写数据。冒烟和日常验证请用 `WORKBUDDY_DESKTOP_DATA` 指定独立空目录，避免污染产物目录。

升级方式：关闭程序后，解压新 zip 覆盖旧目录；`config.json`、`workbuddy.db`、`logs/`、`runtime/`、`webview/`、`agent_assets/` 等运行期文件保留即可。程序内置的「下载并安装更新」只替换单个 EXE，不适用于 onedir 产物，界面已改为引导到 Releases 下载 zip。

Android 签名保存在 `build/android-signing/`。迁移构建机时备份并恢复 `release.jks` 与 `signing.json`，不得提交到仓库或随安装包公开。

## 验证

打包前在临时空数据库上检查启动和接口参数。Android 使用 `android/requirements.txt` 的固定版本进行暂存源码启动检查，并执行 lint；这些检查不替代设备安装测试。

```powershell
Get-ChildItem dist\*-windows-x64.zip | Get-FileHash -Algorithm SHA256
Get-ChildItem dist\*.zip.sha256 | Get-Content
Get-ChildItem dist\android\*-android-arm64.apk | Get-FileHash -Algorithm SHA256
Get-ChildItem dist\android\*.apk.sha256 | Get-Content
```

逐一对照摘要与构建清单。实际程序还需在隔离空数据目录运行 `--smoke-test`，确认窗口、自动进入工作台、版本角标及结果 `ok: true`。隔离数据目录参数按当前源码设置，不使用本文中的脱敏占位符。

便携模式还需确认运行期产物全部落在 EXE 目录：解压 zip 到可写目录后启动，检查 `config.json`、`workbuddy.db`、`logs\`、`runtime\`、`webview\`、`agent_assets\`、`tmp\` 均已生成于同目录，且 `%TEMP%` 下没有新增 `_MEI*`。

## 发布

版本与仓库信息由 desktop/version.json 提供。按部署验证、双端构建与产物验证、公告、提交与标签、正式 Release 的顺序完成发布。正式 Release 应包含 Windows zip、APK 及各自的 SHA256 文件；Windows 和 Android 必须分别匹配正确平台包。

公开公告位于 `docs/RELEASE_NOTES_版本号.md`。不要发布内部分析、协议研究、取证资料、私有配置、凭据、签名或构建日志。公开范围见 [迁移约定](docs/PUBLICATION.md)。
