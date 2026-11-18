define Child as Box<task_struct> [
    Text pid, comm
    Text ppid: real_parent.pid
]
define Parent as Box<task_struct> [
    Text pid, comm
    Link children -> @list
] where {
    list = List<task_struct.children>(@this.children).forEach |entry| {
        yield Child<task_struct.sibling>("child #{pid}": @entry)
    }
}
diag demo_process {
    plot Parent("parent": ${per_cpu_current_task(current_cpu())})
}
