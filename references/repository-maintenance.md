# 发布仓库维护约定

## 用户授权与边界

用户已要求将 lishi 上传至 `git@github.com:zhouyanyu/lishi-skill.git`，README 写清详细流程和使用方法，后续 skill 更新同步仓库，并通过 PowerShell 使用 SSH 上传。

- SSH：`git@github.com:zhouyanyu/lishi-skill.git`
- 浏览入口：`https://github.com/zhouyanyu/lishi-skill`
- 发布内容：`SKILL.md`、`agents/`、`references/`、`scripts/`、README，以及有必要的发布配置或验证代码。
- 排除：用户原书、提取正文、个人笔记、阅读进度、Wiki、私钥凭据、缓存和中间文件。

这是随 skill 修改执行的持续同步约定，不是后台监听或定时任务。普通读史和问答不触发发布。仓库名为 `lishi-skill`，安装目录和 frontmatter 名称仍为 `lishi`。其他使用者的 fork 或定制，只有其明确要求才改变目标，不自动向本仓库推送。

## PowerShell 与 SSH

使用 PowerShell 执行 Git，远端始终使用上述 SSH 地址。优先本机可用 SSH；Windows 若 Git 自带 SSH 无法使用系统代理，可对本 checkout 使用系统 OpenSSH：

```powershell
git -c 'core.sshCommand=C:/Windows/System32/OpenSSH/ssh.exe -o BatchMode=yes' ls-remote --symref 'git@github.com:zhouyanyu/lishi-skill.git' HEAD
```

有需要时在本仓库设置 `core.sshCommand`，不修改全局配置。可用系统 `ssh-add -l` 检查公开指纹，不读取私钥内容。保留正常主机密钥验证；主机密钥不匹配、认证失败或权限不足时报告具体阻碍，不能关闭校验、改用未经授权的发布目标或声称已经推送。

## 每次更新

1. 检查本地安装目录、交付副本及现有 checkout，确认此次改动与他人改动。优先复用可用 checkout，否则在当前任务工作目录克隆；过去聊天的路径不保证仍存在。
2. 获取远端最新状态、确认默认分支。已有远端正常快进或合并，空仓库可建立 `main`。不重置他人变更、不强制推送；冲突无法可靠解决时保留准备好的修改并报告。
3. 更新 skill，同步仓库根目录对应文件。行为、用法、输出、安装或依赖变化时相应更新 README，不把尚未实现的自动化写成已支持。
4. 运行可用的 skill 格式校验和内部链接检查；变动脚本运行相关验证，纯文档变更不用新增无关测试。检查 README 示例与实际流程一致。
5. 查看 diff，只暂存明确属于本次发布的文件；排除个人材料、临时文件、凭据及缓存。必要时核对安装副本与发布内容的一致性。
6. 创建清楚的提交，在 PowerShell 中通过 SSH 正常推送已确认分支。用户原始要求与本约定已授权此范围内的同步，无需逐次重复询问；工具权限仍按环境处理。
7. 用 `git ls-remote` 对比远端分支提交与本地 HEAD，只有一致才报告同步完成。失败时保留本地提交、交付文件与明确续接点。

不能自动给未来未知的变更预先创建提交，也不能把修改本 skill 扩展成发布用户的历史知识库。
