define Packet as Box<sk_buff> [ Text len ]
define Receiver as Box<sock> [
    Text qlen: sk_receive_queue.qlen
    Link first -> @first
    Link last -> @last
] where {
    first = switch ${*@this.sk_receive_queue.qlen} {
        case ${0}: NULL
        otherwise: Packet("first packet": @this.sk_receive_queue.next)
    }
    last = switch ${*@this.sk_receive_queue.qlen} {
        case ${0}, ${1}: NULL
        otherwise: Packet("last packet": @this.sk_receive_queue.prev)
    }
}
diag demo_queue {
    plot Receiver("receiving socket": ${demo_receiver()})
}
