# WB 独立版式模板 v1

`.wbtemplate` 是有界、无压缩 ZIP，`document_type=wb_figure_template/schema_version=1`。
只含 `settings.json`（最多64 KiB）与可选的一个 `font.ttf`、`font.otf` 或 `font.ttc`
（最多32 MiB），总文件最多34 MiB、最多两个成员。重复、额外、越界、加密、压缩或符号链接成员均拒绝；读取不解压到文件系统。

`PortableFigureTemplate` 保存 FigureTemplate（font 必须为空）、可空 FigureLayoutStyle、
可空 TemplateFont（固定文件名、SHA256、字节数）。旧版项目导出 layout_style=null，
不会升级旧渲染方式。新模板只携带通用样式，不携带行、段绑定、列的实验绑定、项目身份、
原图、ROI、定量、OCR、归一化或历史结果。未知字段、重复JSON键和未来schema明确失败。

字体导出核验原资产SHA/大小，再由 Pillow FreeType 从内存验证字体内容；导入同样验证。
源扩展从来源路径及 AssetRef.relative_path 确定；工作区资产无扩展时使用固定font.ttf，
格式仍由字体内容验证。LoadedFigureTemplate返回spec和font_data；宿主须把字体导入当前
工作区并替换为新的AssetRef，不复用旧工作区引用。字体是否获准再分发由用户的字体来源决定。

读取逐块受预算和取消控制，先取得有界快照再解析；不因文件读取期间增长突破预算。
导出同目录独占创建临时文件、关闭ZIP、flush/fsync、重新读取核验，再Windows rename/
POSIX link无覆盖发布。取消/失败只清理本次临时文件，保留已有目标。源及目标路径拒绝
symlink/junction。此检查不声称防御恶意进程在路径校验后替换父目录。

这些API是后台I/O；调用者负责GUI取消、过期结果和工作区资产提交，不在GUI线程调用。
文件损坏/参数不支持用ValueError，系统I/O错误用OSError；失败不返回成功模板。

实现依据：[Python3.12 zipfile](https://docs.python.org/3.12/library/zipfile.html)、
[Pillow ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)。
固定当前Pillow12.3.0，无新增依赖或数值算法变化。

T-041：layout_style保存显式display_policy和lane_unit；缺字段为native_samples@1与120。standard_lane_ratio@1仅改变显示渲染，不含实验绑定或定量语义；参数约束及schema见wb-laboratory-layout-v1.md和wb-layout-style-v1.schema.json。
