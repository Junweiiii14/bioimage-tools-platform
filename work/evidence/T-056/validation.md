# E3/T056 验证（实施中）

base733ea17，Win11/Python3.12.14/Qt6.12.0，锁不变。

核心第一批：新增6项（含N=1…96的20例性质检验），连同既有E1/E2共21 passed/3.30s退出0。
覆盖全空不丢槽、不假坐标；已知Marker与五个样本中心；N冲突不臆造末端；
取消建议不安装、来源改变拒绝、嵌套slotID伪造拒绝、schema12保存重开、
明确人工矩形后从坐标编码原像素逐值核验TIFF、不覆盖与原图字节不变。

首轮新增断言错误：重复整个slot同时破坏position顺序，先被完整N检查拒绝；
改为保留position只伪造重复slotID以检验目标不变量，未放宽断言。
初期Pyright发现tifffile.imread未知重载类型，使用TiffFile/TiffPage原生读取核验，
无类型忽略/skip/容差/依赖/门禁修改。定向Pyright0；全仓静态、宿主、完整门禁/
隔离wheel和最终非作者独审未完成，E3不标done。真实科学留出缺口保留。
