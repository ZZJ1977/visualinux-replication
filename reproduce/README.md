# 核验结果与重新采集

只想看效果，可以直接打开仓库的[离线演示](../demo/index.html)。下面的第一节适用于刚克隆仓库的组员；第二、三节适合想用自己的 Linux 6.1.25 客体重新采集内核对象的组员。

## 1. 从归档计算结果

在仓库根目录运行，使用 Python 3.10 或更新版本的标准库。

```sh
python reproduce/verify.py
```

程序检查 ViewQL 每一项预期与实际命中、表 4 的轮次和计时，然后将两次独立启动的 GDB 读数与各自的九份 ViewCL 对象图逐项比较。正常输出包含以下结果。

```text
ViewQL: 7/10 original cases match the archived graph criteria; IRQ 8/16.
QEMU: 60 samples, 17.9 to 530.4 ms.
Process tree: 119.3 ms mean over 3 trials.
```

后两行 `Capture ...: 3 checkpoints and 9 graphs verified.` 分别对应两个客体快照。7/10 采用归档图属性判据；页缓存的严格判据与两次补充核验见[实验结果](../results/README.md)。

## 2. 构建自写负载并启动新客体

[workload.c](workload.c) 是实际采集所用的 x86-64 Linux 用户程序。它创建子进程、发送两个 Unix 数据报，并为一页私有内存切换权限。QEMU 将它作为第一个用户进程启动。本机已用 Windows QEMU TCG、两个 vCPU、512 MiB 内存、按作者配置构建的 Linux 6.1.25 和带 Python 的 GDB 实际走通第三节，生成三阶段九幅新图。表 4 的主实验为客体分配了 1 GiB 内存，使用 128 MiB ext4 根磁盘。[主实验的计时](../results/table4.csv)

下面使用 Linux Bash 的命令。Windows 用户也可在 x86-64 Ubuntu 虚拟机或安装了相应 Linux 工具的 WSL2 中执行。直接在 Windows 看演示只需要浏览器。

**准备内核和符号。** 已有配套的 `bzImage`、带 DWARF 的 `vmlinux` 和对应的内核 GDB 辅助脚本时可以复用。若要从头构建，在仓库根目录打开 Bash。需要 Git、Linux 内核编译依赖（包括 GCC、make、flex、bison、bc、libelf 与 OpenSSL 开发包）、wget、Python 3，以及 QEMU x86。以下命令在临时目录内创建独立的官方 v1.0 工作副本。[作者的源码](https://github.com/icsnju/visualinux/tree/v1.0) · [对应的发布归档](https://doi.org/10.5281/zenodo.13710732)

```sh
export VL_CLASSROOM="$(pwd)/reproduce"
export VL_WORK="$(mktemp -d)"
git clone --depth 1 --branch v1.0 https://github.com/icsnju/visualinux.git "$VL_WORK/upstream"
cd "$VL_WORK/upstream"
bash scripts/build/get-kernel.sh 6.1.25
make -C kernel olddefconfig
make -C kernel -j4 bzImage vmlinux
make -C kernel scripts_gdb
```

**编译并打包课堂负载。** 下面使用 Zig 的 C 编译器；也可用 `clang -target x86_64-linux-gnu` 编译，再用 `ld.lld -m elf_x86_64 -static -e _start` 链接。打包程序会把 ELF 和串口设备节点写入压缩的 initramfs。

```sh
zig cc -target x86_64-linux-gnu -Os -ffreestanding -fno-stack-protector -fno-pie -nostdlib -static -Wl,-e,_start -s "$VL_CLASSROOM/workload.c" -o "$VL_WORK/vl-demo"
python3 "$VL_CLASSROOM/make_initramfs.py" "$VL_WORK/vl-demo" "$VL_WORK/demo.cpio.gz"
```

**启动 QEMU 并等待 GDB。** 把下面的命令留在当前终端运行。`-S` 会让客体停在启动前；在连接 GDB 前串口会保持空白。记下第二个终端要用的两个目录。

```sh
echo "$VL_CLASSROOM"
echo "$VL_WORK"
qemu-system-x86_64 -machine pc,accel=tcg -cpu max -m 512 -smp 2 \
  -kernel kernel/arch/x86/boot/bzImage -initrd "$VL_WORK/demo.cpio.gz" \
  -append 'rdinit=/bin/vl-demo nokaslr console=ttyS0' \
  -display none -vga none -serial mon:stdio -nic none -no-reboot \
  -S -gdb tcp:127.0.0.1:26002
```

## 3. 用 GDB 和 Visualinux 导出九幅新图

在第二个 Bash 终端，把头两行的目录替换成上一节打印的实际值。GDB 需要带 Python 3.10+；先比较 `gdb -batch -ex 'python import sys; print(sys.version)'` 和 `python3 --version` 的主、次版本，使安装包的解释器与 GDB 匹配。以下依赖安装在临时目录；采集在本地执行。

```sh
export VL_CLASSROOM="/path/to/your-clone/reproduce"
export VL_WORK="/path/printed/by/the/first/terminal"
cd "$VL_WORK/upstream"
python3 -m pip install --target "$VL_WORK/python-deps" -r scripts/build/py-requirements.txt requests
export PYTHONPATH="$PWD/kernel/scripts/gdb:$VL_WORK/python-deps${PYTHONPATH:+:$PYTHONPATH}"
export CAPTURE_DIR="$(mktemp -d "$VL_WORK/capture.XXXXXX")"
gdb -nx -q -batch kernel/vmlinux -x "$VL_CLASSROOM/capture.gdb"
python3 "$VL_CLASSROOM/verify.py" --capture "$CAPTURE_DIR"
```

QEMU 在串口打印 `DEMO_STAGE_1`、`DEMO_STAGE_2`、`DEMO_STAGE_3`。GDB 对三个断点分别执行[进程](views/process.vcl)、[队列](views/queue.vcl)和[地址映射](views/mapping.vcl)视图，将 `stage-*.json` 和 `demo-index.json` 保存到 `CAPTURE_DIR`。核验通过后，在 QEMU 终端按 `Ctrl+A`，松开后按 `X` 退出。

| 核验对象 | 第 1 个断点 | 第 2 个断点 | 第 3 个断点 |
| --- | --- | --- | --- |
| 父进程的子任务数 | 1 | 2 | 1 |
| 接收队列 | 空 | 两个包，分别为 5 和 11 字节 | 空 |
| 同一页的当前可写权限 | 可写 | 只读 | 只读 |

指针和子进程 PID 会随启动而变化。核验程序在同一次运行内比对对象身份、父子关系、报文长度和 `VM_WRITE` 位。这个轻量入口重采小组的三个补充实验；表 2 到表 4 的主实验使用作者的教材视图、`summation` 工作负载和 ext4 根盘。准备主实验可参阅[作者的教材实验说明](https://github.com/icsnju/visualinux/blob/v1.0/docs/archives/artifact-evaluation.md)以及[本组的实验条件与数据](../results/README.md)。
