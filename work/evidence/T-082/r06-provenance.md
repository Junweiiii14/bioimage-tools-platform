# R06 工具信任基准

2026-10-28；实现基线918598c，集成时HEAD已到05c1a16。以下来源核验先于锁新增条目，不是把任意当前二进制自动登记为可信。完整原始下载、成员对照和本机签名输出在ignored `.local/T082/r06-provenance/`；不提交工具二进制。

| 工具 | 已确认来源及摘要 | 本机对照 |
| --- | --- | --- |
| uv0.13.0 x64 Windows | [官方release](https://github.com/astral-sh/uv/releases/tag/0.13.0)，asset626003295；官方API digest `088962f9e7b7bd9ea740c04c650b2a21c8928c345bd99ac24350dc924dba656c` | 重新下载ZIP先比整个摘要，再读取uv.exe成员；现有WinGet uv文件与成员相同，`2bfbe53d3cc95799e98fa08323b04844fc01d4f8c87dd5c00089e43f6554f162` |
| CPython3.12.14 / BUILD20260825 | [Astral官方release](https://github.com/astral-sh/python-build-standalone/releases/tag/20260825)，`cpython-3.12.14+20260825-x86_64-pc-windows-msvc-install_only_stripped.tar.gz`；官方API digest `8e6aad12ef6fc9685e67ce66253f8f72d6e8fa02cb7187e5850bd4db5ecd9e2a` | 新下载归档摘要相同；2295个运行库文件逐字节相同，无缺失/变更，仅多uv生成的`Lib/EXTERNALLY-MANAGED`。固定文件名+摘要排序树散列`0ab3586b62ebbd26706b71c1f5d44febf70e7d4af9c43783a67b7f2814d7cf1c` |
| GCC15.2.0 / winlibs r6 | [原发布者release](https://github.com/brechtsanders/winlibs_mingw/releases/tag/15.2.0posix-13.0.0-msvcrt-r6)，asset360334926；官方API digest `d73d02c9caed172db0f3331fb4030e0a3b85947aefff9cc1da4dd81b7423c3a1` | 既存原ZIP摘要与官方一致；11602文件树散列`548b48719ff45f9ac17c00d343700d469deb53243e33722827cd0aeb7b7955a5`。gcc/windres与归档成员一致，分别`4c4b0bc1…d0a9f`、`70903d43…fcd91`（完整值在锁） |
| Inno6.7.3 | [官方下载页](https://jrsoftware.org/isdl.php)链接[官方tag](https://github.com/jrsoftware/issrc/releases/tag/is-6_7_3)，asset430321419；官方API digest `9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732` | T047原安装器摘要相同；安装器和ISCC.exe Authenticode Valid、Pyrsys B.V.、证书指纹E0AB19C8D38CBF9C44709925122A7A02F8C70CB7。其余编译器/支持二进制均Valid（旧压缩DLL由Martijn Laan签署）。四个未带Authenticode的Setup engine/loader有独立issig签名，已用官方tag的[def02公钥](https://github.com/jrsoftware/issrc/blob/is-6_7_3/def02.ispublickey)逐一验证OK；不以未签名为通过 |

Inno签名工具自身先验证Authenticode。`Setup.e32`、`SetupCustomStyle.e32`、`SetupLdr.e32`、`SetupLdr.e64`分别执行`ISSigTool --key-file=<从官方tag读取的公钥> verify <成员>`，4项exit0。预处理文件`ISPPBuiltins.iss`和默认语言`Default.isl`又与官方tag的Files目录内容完整比较相同，Git blob分别485edc32457ff686db8a21d2d6600e93d7f47560、925f95f594dac5e5cc4eaa238d6007840bc3bd61。运行入口逐项校验锁中的支持文件，而非仅校验薄ISCC启动器。

真实版本命令：uv0.13.0(4ecd0eff2)、GCC15.2.0/MSVCRT/POSIX/SEH r6、windres2.46.0.20260210、Inno engine6.7.3。ISCC的`/?`只有主版本，最终使用stdin中的明确`#error BIOIMAGE_VERSION_PROBE`读取engine版本，预期退出2且不生成安装器；预期错误不是成功编译。Python使用当前进程3.12.14和官方运行库全树双重核验。

运行库树排除与复制器一致的site-packages、__pycache__、pyc，以及uv的两个非代码管理标记BUILD/EXTERNALLY-MANAGED；复制后的运行库再次比对已验证树，不能用重新读取已变化源替代冻结基准。GCC检查完整官方归档树。来源URL、archive SHA、实际版本/路径/文件SHA及toolchain-lock SHA写入构建manifest。

第一次真实preflight读取旧wb-ui-system工具树时，一个文件在枚举后消失，入口拒绝继续；再次核验该树gcc.exe已不存在。执行者未删除该树，不推断外部删除原因。已核官方ZIP及`~/.cache/bioimage-nuitka`原树仍存在，切到该树后完整preflight exit0。Inno另复制至本轮ignored `.local/T082/r06-toolchain/inno-6.7.3`，不修改旧安装或注册表。旧T081 preflight只记录观察hash，不能替代本次来源与签名核验。

限制：固定来源与完整性核验不是对上游编译器源码、签名机构或供应商构建过程的安全审计；未声称可抵御拥有本机写权限的攻击者在校验后任意替换执行环境。构建身份固定后，真实候选安装及目标机验收仍由R07/R11执行。
