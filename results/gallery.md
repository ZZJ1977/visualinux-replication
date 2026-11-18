# 教材图索引

按论文表 2 的顺序列出。点击教材主题可放大原始对象图。对应快照的键是 JSON 里视图的名称。

| 表 2 序号 | 教材主题 | 图号 | 快照键 | 可以在图里查看什么 |
| --- | --- | --- | --- | --- |
| 1 | [进程父子关系](images/textbook_01_task_children.png) | 3-4 | `textbook_01_task_children` | 从 init_task 开始，沿 children 找直接子进程。对照子节点的 ppid 和父节点的 pid，再沿下一层分支向下。 |
| 2 | [PID 查找结构](images/textbook_02_pid_namespace.png) | 3-6 | `textbook_02_pid_namespace` | 先看命名空间的 level，再沿 ID 分配器查找 pid 对象。比较不同条目的 nr，理解一个命名空间怎样组织进程号。 |
| 3 | [IRQ 描述符](images/textbook_03_idt.png) | 4-5 | `textbook_03_idt` | 沿索引找到 irq_desc，检查 action 指针是否为空。有指针时，再沿它读取已注册处理程序的名字。 |
| 4 | [动态定时器](images/textbook_05_dyntimer.png) | 6-1 | `textbook_05_dyntimer` | 并看两个 timer_base 的时间轮。沿 vectors 找到非空桶，阅读各定时器的到期时间，区分桶本身和桶中的定时器。 |
| 5 | [CFS 运行队列](images/textbook_06_cfs_runqueue.png) | 7-1 | `textbook_06_cfs_runqueue` | 左侧方框是 CPU 0 的 CFS 运行队列。沿 tasks_timeline 进入红黑树，再比较左右子节点的 vruntime，观察调度器如何按虚拟运行时间排列任务。 |
| 6 | [伙伴分配器](images/textbook_07_buddy_system.png) | 8-2 | `textbook_07_buddy_system` | 先从内存节点找到分区，再在分区中展开 free_area。不同阶的空闲区保存不同大小的连续页块。 |
| 7 | [slab 对象缓存](images/textbook_0809_kmem_cache_examples.png) | 8-4 | `textbook_0809_kmem_cache_examples` | 从每个根对象的 name 区分缓存用途，再沿 CPU 局部缓存去找 slab。把进程描述符缓存与 inode 缓存并排比较。 |
| 8 | [进程地址空间](images/textbook_10_task_mm_mt.png) | 9-2 | `textbook_10_task_mm_mt` | 从任务的 mm 找到 Maple Tree，沿节点槽位到达 vm_area_struct。比较 vm_start 与 vm_end，读出一段虚拟地址范围。 |
| 9 | [信号处理](images/textbook_11_task_signal.png) | 11-1 | `textbook_11_task_signal` | 从任务的 pending 分支找已挂起的信号，再查看 sighand 分支中的处理配置。前者记录等待处理的事件，后者描述如何响应。 |
| 10 | [文件描述符表](images/textbook_13_fd_array.png) | 12-3 | `textbook_13_fd_array` | 沿任务的描述符数组找 file，再区分普通文件和套接字。看到 socket 时读取 state，即可判断这端是否已连接。 |
| 11 | [设备对象](images/textbook_14_kernfs_example.png) | 13-3 | `textbook_14_kernfs_example` | 在设备目录树中先找 dev，再区分 block 和 char 两个分支。沿子节点读取名字，可以把目录关系和内核对象对应起来。 |
| 12 | [块设备](images/textbook_15_bio_example.png) | 14-3 | `textbook_15_bio_example` | 从超级块列表开始找 s_bdev。沿非空指针可以到达块设备，再读取 gendisk 的 disk_name，定位文件系统所用磁盘。 |
| 13 | [页缓存](images/textbook_16_file_pagecache.png) | 15-1 | `textbook_16_file_pagecache` | 从文件跟到地址空间，比较各对象的 nrpages；沿 i_pages 能找到缓存页索引。图中收起索引后，页数仍可从字段读出。 |
| 14 | [文件映射](images/textbook_17_file_mapping.png) | 16-2 | `textbook_17_file_mapping` | 找到文件关联的映射树。非空分支指向 VMA；阅读其中的 vm_flags，观察读、写和共享属性如何组合。 |
| 15 | [匿名页反向映射](images/textbook_18_anon_rev.png) | 17-1 | `textbook_18_anon_rev` | 从任务地址空间选一段匿名 VMA，沿 anon_vma 进入反向映射结构。对照链节点，可以从匿名映射找回相关 VMA。 |
| 16 | [交换区](images/textbook_19_swap_area.png) | 17-6 | `textbook_19_swap_area` | 从系统交换区数组找到有效条目，再检查它的页数和底层设备。把 pages 换算成 KiB，可与客体的 /proc/swaps 交叉核对。 |
| 17、18 | [IPC 信号量、消息队列](images/textbook_20_ipc_ids.png) | 19-1、19-2 | `textbook_20_ipc_ids` | 从同一个 IPC 命名空间沿两条分支读图：先找信号量数组，再到消息队列读取 q_qnum。论文表 2 的两项在此共用一幅图。 |
| 19 | [工作队列](images/textbook_04_mm_percpu_wq.png) | 扩展示例 | `textbook_04_mm_percpu_wq` | 从工作队列沿 pwq 进入工作池，查看各池关联的 worker。工作队列组织要做的事，工作线程负责实际执行。 |
| 20 | [进程到 VFS](images/textbook_12_proc_vfs.png) | 扩展示例 | `textbook_12_proc_vfs` | 从进程的已打开文件沿指针找到目录项，阅读 d_iname。这样可以把用户程序使用的文件名对应到内核中的对象。 |
| 21 | [套接字连接](images/textbook_21_sockstack.png) | 扩展示例 | `textbook_21_sockstack` | 沿文件描述符找到 socket，再沿收发队列进入缓冲区。读取 sk_buff 的 len，能看到每个缓冲区里有多少字节。 |
