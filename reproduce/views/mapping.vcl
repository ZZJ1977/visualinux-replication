define Region as Box<vm_area_struct> [
    Text<u64:x> vm_start, vm_end, vm_flags
    Text<bool> can_write: ${vma_is_writable(@this)}
]
define AddressSpace as Box<mm_struct> [
    Link region -> @region
] where {
    region = Region("one private page": ${demo_mapping()})
}
diag demo_mapping {
    plot AddressSpace("parent address space": ${demo_mm()})
}
