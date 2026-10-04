# k-norm 投影算法说明 0.1

本文件保留算法推导与开发阶段验证记录。release 的安装与配置入口见 [README](../README.md)；release 校验默认只依赖随包快照。

本目录提供矩阵 Ky Fan k-范数**对偶球的 Frobenius 投影**，以及对应的近端映射。原 MATLAB 代码保留在原位置；`original_matlab/` 另存四个投影源文件的逐字节副本。

## 范围与文件

- `knorm_projection/baseline.py`：按原 `Projdualk → HKLineq → HKLeq` 路线建立的 Python 基线，保留完整约化 SVD、2q 个断点排序与二分查找、显式对角矩阵重构。补充参数验证、零半径、空输入和截断等式边界处理，不保留原来的边界报错。
- `knorm_projection/projection.py`：优化后的 0.1 实现，一般 k 与 k=2 有独立的计算路径。
- `tests/test_projection.py`：独立高精度参考、可行性、变分不等式、幂等性、Moreau/Fenchel 关系及边界测试。
- `benchmarks/benchmark.py`：相同输入、精度门限下的 Python 基线与优化版计时。
- `SOURCE_MANIFEST.json`：46 个原 MATLAB `.m` 文件的 SHA-256，以及四个快照文件名。
- `tools/validate.py`：运行完整测试及源文件保护检查，保存日志与证据记录。
- `results/`：每次运行产生独立目录。早期 quick 结果属于开发过程；本页指定的正式结果对应当前实现。

本版不移植 FMMC/ALM/PPA 外层求解器，不修改 MATLAB 文件，也不将 Python 基准解释为 MATLAB 加速结果。

## 数学定义

对 X∈C^(m×n)，q=min(m,n)，r≥0，整数 1≤k≤q，计算

\[
P=\operatorname*{argmin}_{Y}\frac12\|Y-X\|_F^2,
\qquad \|Y\|_2\le r,\quad \|Y\|_*\le kr.
\]

这是矩阵 Ky Fan k-范数的对偶球投影，**不是**投到 `sum(top-k singular values) <= r` 的原范数球。

若 X=U diag(s) V*，则 P=U diag(p) V*，其中

\[
p_i=\min(r,\max(s_i-\theta,0)),\qquad
\theta\ge0,quad \sum_i p_i\le kr,\quad
\theta(\sum_i p_i-kr)=0.
\]

`prox_ky_fan(X, r, k)` 计算 `prox_(r * ||.||_(k))(X)`，其中 `||.||_(k)` 为前 k 个奇异值之和。它直接用谱系数 `s-p` 重构，不先重构 P 再作 X-P。

## 一般 k 的优化

先截断 `p=min(s,r)`；若总量约束已满足，直接返回。活动情况下求解分段线性、单调的阈值方程。

令 s_k 为第 k 大奇异值。任一所需根可在以下区间选择：

\[
\max(0,s_k-r)\le\theta\le s_k.
\]

左端保证前 k 项均饱和，或等于未满足总量约束的 θ=0；右端只有至多 k-1 项可能为正。以 `theta=s_k+r*t` 平移并按半径缩放后，搜索区间落在 [-1,0]。远离该区间的谱差可以在不改变该区间内投影值的前提下截断，避免直接用巨大绝对阈值相减。

实现采用 Newton 步与区间保护，每三步至多使用一次强制二分；自由集为空或 Newton 步越界时也退回二分。活跃集稳定后，以最小自由谱值为基准重新解质量约束，验证上界、零分量和总量。未能在最多 96 步内验证一个有效浮点活跃集时抛出 `FloatingPointError`，不把迭代上限当作成功。

每步对向量作 O(q) 工作；已排序数据直接取 s_k，未排序数据用 `partition` 选择。迭代次数依赖输入，**不宣称一般 k 的总成本无条件为 O(q)**。相比基线，避免重新排序 2q 个断点及在移动活跃集上反复执行完整验证。

## k=2 的专用优化

奇异值降序排列时，先检查 `sum(min(s,r)) <= 2*r`。若不满足，令 Δ_c={x≥0:sum(x)=c}，计算 u=Π_(Δ_(2r))(s)：

\[
p=\begin{cases}
u,&u_1\le r,\\
(r,\Pi_{\Delta_r}(s_{2:q})),&u_1>r.
\end{cases}
\]

若 u_1>r，把第一项固定为 r 后，剩余质量从 `2r-u_1` 增至 r，尾部阈值只会下降，第一项仍满足上界活跃条件。尾部非负且总量为 r，自然不可能再超过单项上界 r。这给出精确的两次单纯形投影化简。

单纯形投影使用前缀和确定支撑，并再次平移以减少消减误差。已排序输入的这条路径为 O(q)；未排序向量会先排序。矩阵 SVD 路径的奇异值本来已排序。

**k=2 不等于秩为 2。** 例如 q>2 时，I 的投影为 `(2/q)*I`，仍是满秩。本版始终计算完整所需谱，不使用固定秩近似或部分 SVD。

## 矩阵计算与接口

- 一般实数/复数矩形矩阵：`numpy.linalg.svd(..., full_matrices=False)`。
- `hermitian=True`：显式启用 `eigh`，要求输入逐元素满足 X=X*。有小非对称误差时，应由调用者明确决定是否对称化。本程序不自动把任意输入换成它的对称部分。
- 重构用按列缩放，省去显式对角矩阵；只略过投影公式产生的零谱系数，不以容差删除小正值。
- 输入不被修改；输出为 float64 或 complex128。整数及低精度输入会转换到该精度。
- r=0 时投影为零、近端映射为 X；空矩阵保持原形状，允许任意正整数 k；非空输入要求 1≤k≤q。
- NaN、Inf、负半径、非法 k 和错误形状显式报错。分解返回非有限谱时也不返回假成功结果。
- `return_info=True` 返回 `(结果, 字典)`，记录实际方法、标量迭代/单纯形次数、总量约束状态、非零谱系数数目、归一化可行性残差及矩阵分解方法。可行性残差不等于完整投影误差，也不替代最优性验证。

NumPy 的约化 SVD、返回顺序与重构约定见 [SVD 官方文档](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)；Hermitian 特征值分解约定见 [eigh 官方文档](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)。

## 已执行的验证与性能结果

日期：2026-10-04。20 项 unittest 方法通过，覆盖小维度枚举的全部合法 k、独立 500 位 Decimal 阈值求解、重复谱与断点邻域、跨度极大的谱/半径、包含 10002 个分量的自由集、复数矩形矩阵、对称不定矩阵、幂等性、变分不等式和 Moreau/Fenchel 关系。另核对 46 个原 MATLAB 文件与 4 个快照的 SHA-256。

验证记录：[validation.json](../reports/validation_20261004T103153162134Z/validation.json)、[测试日志](../reports/validation_20261004T103153162134Z/tests.log)。

正式基准：[benchmark.json](../reports/benchmark_20261004T103212641128Z/benchmark.json)。种子 20261004，NumPy 2.3.5、OpenBLAS 0.3.30，BLAS 环境请求单线程，各方案预热后作 7 组计时，记录每次调用耗时的中位数。所有方案在相同输入、半径、k 和 1e-10 验证门限下比较；实际最大基线差约 6.05e-15，最大归一化可行性残差约 1.91e-14。分解、参数检查和重构都计入矩阵计时，额外的结果核验不计入。

| 测试对象 | Python 基线 | 0.1 对应路径 | 基线时间 / 0.1 时间 |
|---|---:|---:|---:|
| 向量 q=4096，k=2 | 235.0 μs | k2：86.4 μs | 2.72 |
| 向量 q=32768，k=2 | 1845.4 μs | k2：631.5 μs | 2.92 |
| 向量 q=4096，k=1024 | 233.7 μs | general：166.0 μs | 1.41 |
| 向量 q=32768，k=8192 | 1219.1 μs | general：1044.9 μs | 1.17 |
| 对称矩阵 384×384，k=2 | 38.16 ms | eigh + k2：18.56 ms | 2.06 |
| 对称矩阵 384×384，k=96 | 36.83 ms | eigh + general：20.44 ms | 1.80 |

结果并非全部提速：q=256、k=64 的 general 路径约慢 12%；256×192、k=2 的通用矩阵 SVD 路径约慢 9%。该批对称矩阵的 eigh 路径均有收益，通用矩形矩阵路径的收益较小或不稳定。不能把向量内核加速比例当作矩阵投影或外层求解器的加速比例。

这些是本机、有限合成输入上的 Python 测量，不包含 MATLAB 运行、FMMC 迭代实验、所有浮点输入的证明或跨平台性能保证。原 MATLAB 程序保留作为来源，独立 Decimal/几何检查用于避免只把旧实现当作正确性标准。
