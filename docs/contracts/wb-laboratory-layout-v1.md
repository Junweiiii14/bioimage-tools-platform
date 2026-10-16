# 实验室版式与明确分段 v1

T-021实施契约。新增WBLayoutProject/schema7，保留schema1–6读取及原渲染；旧文档不自动升级。v7复用原图行/标注/结果/OCR/归一化，归档历史字段可为空或沿用v6证据，不生成外来本机运行。应用实验室版式是明确操作。

版式与原图行分开：FigureSlice记录原row_id、对应Fig、显示行号、段位置、原1基闭区间泳道范围。每原图行的全部1..N槽须恰好出现一次，顺序递增；不删除空泳道，不自动重排样本。分段坐标由原ROI和已冻结整数网格计算，逐段来源保存row/SHA/原ROI/原泳道/输出框。跨源或分段均有外置边框和至少2像素白色间距，不覆盖源像素。显示行合并为用户明确配置，同名蛋白不自动合并；同一显示行的蛋白文字必须一致。

同Fig各显示行的段列数、每段N和宽度一致以对齐；不同Fig宽度/N可不同。缺图段从同Fig对应实际段取得宽度，必须保留N，不能从缺失造零。同一显示行高度取实际ROI最大高，各段垂直居中且不拉伸；缺图默认高取模板crop_height。实际原ROI高允许2..4096像素；统一裁剪高仍是批量建议默认值，v7定量有效性与明确原ROI比较，不以其他行/模板高度撤销当前真实测量。几何/N/空位变更仍撤销审核和使旧结果失效。

FigureLayoutStyle保存独立Fig字号、段间距、标签对齐及逐排/独立列排布。FigureComposition保存分段和明确Fig列号；标签左右侧/基础字号/留白/行距/边框/DPI仍用FigureTemplate。列模式各列内部按figure_order纵排；行模式沿figure_order逐排，列数取模板columns。文本放不下明确报错，不裁切压缩。显示RGB8映射及3200万像素/32768单边预算保持。

render_figure对v7调用figure_segmented_geometry@1，旧v1–v6继续figure_original_geometry@1；旧项目/ZIP的像素、清单和字段不改变。直接TIFF/PNG、完整生成OCR和ZIP/恢复复用同一渲染。v7项目在恢复、表格、OCR/定量/归一化辅助更新后保留版式；改排版不改变原行/lane/band/run身份，不自动确认OCR关联。

UI显示可编辑的显示行/段顺序/原泳道范围/Fig列，支持按明确泳道分段、重建单行版式与预览。未完成或过期计划可以保存草稿，渲染前严格检查全部覆盖、身份与几何；错误给出具体Fig/行。删除/新增原图行后不得静默隐藏数据。

可复用模板仅包含FigureTemplate、FigureLayoutStyle及自定义字体，不带原图、row_id、Fig名称、OCR关联或测量结果。保存/导入新模板走后台、有界解析、摘要核验、无覆盖；从当前模板新建项目为空项目。独立.wbtemplate格式与旧版style=null兼容见wb-figure-template-v1.md。导入先保存当前项目，再将字体导入目的工作区并建立空项目；关闭/取消/代际变化拒绝晚到替换。

## 显式标准显示策略（T-041）

FigureLayoutStyle 新增版本化 `display_policy`：缺字段继续为 `native_samples@1`，原有原生宽度校验、像素及manifest表示保持；`standard_lane_ratio@1`允许同Fig各行原ROI宽高不同，段列数与对应泳道span仍须一致。`lane_unit`默认120，允许5..1200的5倍整数；显示段宽=span×lane_unit，所有显示行高=lane_unit×4/5（整数）。120用于预览；单Fig可选1200得到高960、宽1200N的显示区域。整个画布仍执行3200万像素/32768边长预算，不自动降质量或跳过行。

标准策略只对既有8位显示映射之后的RGB8图使用Pillow LANCZOS重采样，操作身份`figure_segmented_geometry@2`。manifest声明display_policy、lane_unit、row_height和`pillow_rgb8_lanczos@1`，每实际段保留原SHA/原ROI/原泳道范围、原ROI尺寸、output_box、display_output_size和输出RGB摘要；缺图仍为missing。`display_pixel_sha256`沿用重采样前单通道显示像素摘要，新增`display_rgb_sha256`指向实际输出RGB段。输出框和原ROI构成仿射回源映射，不能宣称显示像素为原样本。

定量、原值裁剪TIFF、原数组、位深与测量身份保持原样；显示TIFF读取保护识别@2。无新依赖。style schema见wb-layout-style-v1.schema.json；旧style缺两个新字段仍可读取，原生manifest不写新增默认style字段以保留已冻结历史字节。标准策略随项目和可复用模板保存，不由旧项目自动启用。

### 可选旋转显示框

FigureSlice.display_frame可空，DisplayFrame保存center_x/center_y/width/height/angle_degrees；全部有限，宽高>0，角度±30度。坐标使用原图像素边界坐标，正角度在图像xy方向顺时针；width方向为(cosθ,sinθ)。四角必须在该行原ROI与原图内，仅1e-7浮点计算容差，不扩展采样边界。原ROI仍为原图矩形定量/裁剪坐标，不由显示框替换。

仅standard_lane_ratio@1接受display_frame，native显式拒绝。旋转显示从原样本经既有8位显示映射，再以Pillow RGB8仿射双线性采样，声明pillow_rgb8_affine_bilinear@1；无frame仍LANCZOS。每实际标准显示段记录source_to_output 2×3矩阵（原图像素边界xy→完整画布xy）、display_frame（可空）及采样身份。矩阵支持显示点击回原图，不用于定量重采样。组合schema见wb-figure-composition-v1.schema.json；旧切片缺字段读作None。frame属于实验composition，不进入通用模板。Qt表单保存保留未编辑片段的frame和style策略/单位；改片段几何或分段清除对应frame，渲染仍验证有效性。
