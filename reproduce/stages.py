"""GDB-side independent checks + upstream Visualinux export, one stop per stage."""
import json, os
from pathlib import Path
import gdb
from visualinux.core import core
from linux.cpus import get_current_cpu

here=Path(os.environ['VL_CLASSROOM'])
out=Path(os.environ['CAPTURE_DIR'])
gp=gdb.parse_and_eval
ptr=lambda v:hex(int(v))
region_hint=0x50000000
captured_mapping=None

class Mprotect(gdb.Breakpoint):
    def stop(self):
        global captured_mapping
        v=gp('$rdi').cast(gdb.lookup_type('struct vm_area_struct').pointer())
        if int(v['vm_start'])==region_hint and int(v['vm_end'])==region_hint+4096:
            captured_mapping=int(v)
        return False

class Checkpoint(gdb.Breakpoint):
    def stop(self):return True

# QEMU starts at reset with -S. Hardware breakpoints also work before the
# kernel's target virtual addresses are mapped.
Mprotect('*security_file_mprotect',type=gdb.BP_HARDWARE_BREAKPOINT,internal=True)
Checkpoint('*security_task_getsid',type=gdb.BP_HARDWARE_BREAKPOINT,internal=True)
# The core still performs the full extraction. Save NEWSTATE locally for browser
# replay in lieu of sending the intermediate stages to a shared web service.
received=[]
core.send=lambda payload:received.append(payload)
gdb.execute('macro define demo_receiver() (((struct socket*)per_cpu(current_task,0)->files->fdt->fd[4]->private_data)->sk)')
gdb.execute('macro define demo_mm() (per_cpu(current_task,0)->mm)')

def fields(box):
    return {k:m['value'] for k,m in box['absts']['default']['members'].items() if m['class']=='text'}

def children(parent):
    typ=gdb.lookup_type('struct task_struct').pointer()
    offs=int(gp('(unsigned long)&((struct task_struct*)0)->sibling'))
    head=parent['children']
    p=head['next'];result=[]
    while int(p)!=int(head.address):
        ch=gdb.Value(int(p)-offs).cast(typ)
        result.append(dict(pid=int(ch['pid']),ppid=int(ch['real_parent']['pid']),comm=ch['comm'].string()))
        assert len(result)<6
        p=p['next']
    return result

stages=[]
for stage in (1,2,3):
    gdb.execute('continue')
    parent=gp(f'per_cpu(current_task,{get_current_cpu()})')
    assert parent['comm'].string()=='vl-demo',parent['comm'].string()
    assert captured_mapping is not None
    vm=gdb.Value(captured_mapping).cast(gdb.lookup_type('struct vm_area_struct').pointer())
    assert int(vm['vm_mm'])==int(parent['mm']) and int(vm['vm_start'])==region_hint
    socket_obj=parent['files']['fdt']['fd'][4]['private_data'].cast(gdb.lookup_type('struct socket').pointer())
    sk=socket_obj['sk'];queue=sk['sk_receive_queue'];qlen=int(queue['qlen'])
    packets=[];n=queue['next']
    while int(n)!=int(queue.address):
        assert len(packets)<3
        packets.append(int(n['len']));n=n['next']
    assert packets==([5,11] if stage==2 else []) and len(packets)==qlen
    kids=children(parent)
    assert {p['comm'] for p in kids}==({'demo-anchor','demo-new'} if stage==2 else {'demo-anchor'})
    flags=int(vm['vm_flags'])
    assert bool(flags&2)==(stage==1)
    gdb.execute(f'macro define demo_mapping() ((struct vm_area_struct*){captured_mapping:#x})')
    row=dict(stage=stage,parent_pid=int(parent['pid']),children=kids,socket_addr=ptr(sk),socket_object_addr=ptr(socket_obj),qlen=qlen,packet_lengths=packets,
             mapping_addr=ptr(vm),vm_start=ptr(vm['vm_start']),vm_end=ptr(vm['vm_end']),vm_flags=hex(flags),views={})
    for name in ('process','queue','mapping'):
        received.clear();code=(here/'views'/(name+'.vcl')).read_text(encoding='utf8')
        core.sync(code)
        assert len(received)==1 and received[0]['command']=='NEWSTATE'
        view=received[0]['data']['demo_'+name];boxes=view['pool']['boxes']
        assert view['plot'] and all(k in boxes for k in view['plot']),(name,view)
        if name=='process':
            tasks=[fields(b) for b in boxes.values() if b['type']=='task_struct']
            assert {int(t['pid']) for t in tasks}=={row['parent_pid'],*(p['pid'] for p in kids)}
            assert {(int(t['pid']),int(t['ppid']),t['comm']) for t in tasks if 'ppid' in t}=={(p['pid'],p['ppid'],p['comm']) for p in kids}
        elif name=='queue':
            assert int(fields(boxes[view['plot'][0]])['qlen'])==qlen
            seen_lengths=sorted(int(fields(b)['len']) for b in boxes.values() if b['type']=='sk_buff')
            assert seen_lengths==sorted(packets),(stage,seen_lengths,packets)
        else:
            regs=[fields(b) for b in boxes.values() if b['type']=='vm_area_struct']
            assert len(regs)==1 and int(regs[0]['vm_flags'],16)==flags and int(regs[0]['vm_start'],16)==region_hint
        filename=f'stage-{stage}-{name}.json'
        (out/filename).write_text(json.dumps(received[0]['data'],ensure_ascii=False,indent=2),encoding='utf8')
        row['views'][name]=filename
    gdb.execute('macro undef demo_mapping')
    stages.append(row)
    print('STAGE',json.dumps(row),flush=True)
assert len({r['socket_addr'] for r in stages})==1 and len({r['parent_pid'] for r in stages})==1
(out/'demo-index.json').write_text(json.dumps({'kernel':gp('init_uts_ns.name.release').string(),'stages':stages},indent=2),encoding='utf8')
