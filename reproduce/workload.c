/* x86-64 Linux, no libc. All resources are private to this guest process. */
static long sys(long n,long a,long b,long c,long d,long e,long f) {
    register long r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;
    __asm__ volatile("syscall":"+a"(n):"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");
    return n;
}
#define C(n,a,b,c) sys(n,(long)(a),(long)(b),(long)(c),0,0,0)
static void fatal(void) {
    C(1,2,"DEMO_FAILED\n",12);
    for(;;) C(34,0,0,0);
}
static long child(const char *name) {
    int syncfd[2];
    if(C(22,syncfd,0,0)<0) fatal();
    long pid=C(57,0,0,0);
    if(pid<0) fatal();
    if(pid==0) {
        sys(157,15,(long)name,0,0,0,0); /* prctl(PR_SET_NAME) */
        if(C(1,syncfd[1],"1",1)!=1) fatal();
        for(;;) C(34,0,0,0);
    }
    char ready;
    if(C(0,syncfd[0],&ready,1)!=1) fatal();
    C(3,syncfd[0],0,0);C(3,syncfd[1],0,0);
    return pid;
}
static void checkpoint(int stage,long pid) {
    char marker[]="DEMO_STAGE_0\n";
    marker[11]='0'+stage;
    C(1,1,marker,sizeof(marker)-1);
    if(C(124,pid,0,0)<0) fatal();
}
__attribute__((force_align_arg_pointer,noreturn)) void _start(void) {
    unsigned long cpu0=1;
    if(C(203,0,sizeof(cpu0),&cpu0)<0) fatal();
    long pid=C(39,0,0,0);
    long page=sys(9,0x50000000,4096,3,0x100022,-1,0); /* no replacement of existing VMAs */
    if(page!=0x50000000) fatal();
    *(volatile char*)page=7;
    int sockets[2];
    if(sys(53,1,2,0,(long)sockets,0,0)<0||sockets[0]!=3||sockets[1]!=4) fatal();
    child("demo-anchor");
    if(C(10,page,4096,3)<0) fatal(); /* records the address range at a normal LSM hook */
    checkpoint(1,pid);
    long extra=child("demo-new");
    if(C(1,sockets[0],"first",5)!=5 || C(1,sockets[0],"second-data",11)!=11) fatal();
    if(C(10,page,4096,1)<0) fatal();
    checkpoint(2,pid);
    char data[16];
    if(C(0,sockets[1],data,sizeof(data))!=5 || C(0,sockets[1],data,sizeof(data))!=11) fatal();
    if(C(62,extra,15,0)<0||sys(61,extra,0,0,0,0,0)!=extra) fatal();
    checkpoint(3,pid);
    for(;;) C(34,0,0,0);
}
