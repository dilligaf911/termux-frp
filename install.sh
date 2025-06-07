###termux

pkg update 
pkg openssh  termux-services
passwd
sv-enable sshd
sv up sshd
pkg install frp 
mkdir $PREFIX/etc/frp

[////EDIT] $PREFIX/etc/frp/frpc.toml

serverAddr = "dilligaf.ru"
serverPort = 7000
auth.method = "token"
auth.token = "xxxx-xxxx-xxxx"


[[proxies]]
name = "android_termux_pixel"
type = "tcp"
localPort = 8022
remotePort = 33002
localIP = "127.0.0.1"

[///EDIT]

mkdir $PREFIX/var/service/frpc

[////EDIT] $PREFIX/var/service/frpc/run

#!/data/data/com.termux/files/usr/bin/sh
exec frpc -c $PREFIX/etc/frp/frpc.toml 2>&1

[////EDIT]

sv-enable frpc
sv up frpc