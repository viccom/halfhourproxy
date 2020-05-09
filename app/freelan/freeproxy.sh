#!/bin/bash

[ $(id -u) != "0" ] && { echo "${CFAILURE}Error: You must be root to run this script${CEND}"; exit 1; }

function install_freelan {
    echo "[INFO] install freelan"
    if [ ! -f "/bin/freelan" ]; then
        apt update
        apt install freelan -y
    fi

    sleep 2
    if [ -d "/etc/freelan/" ]; then
      rm -rf /etc/freelan/
    fi
    if [ -f "/etc/init.d/freelan" ]; then
      rm -f /etc/init.d/freelan
    fi
}

function start_freelan {
    echo "[INFO] start freelan"
    freelan --security.passphrase "freelan.passphrase" --tap_adapter.ipv4_address_prefix_length 192.168.212.2/24 --fscp.contact 47.244.5.11:443
    sleep 2
}


function generate_cleanfreelan {
echo "[INFO] Generating cleanfreelan"
cat <<EOF >/bin/cleanfreelan
#!/bin/bash
[[ \$(id -u) != "0" ]] && { echo "\${CFAILURE}Error: You must be root to run this script\${CEND}"; exit 1; }
curl -L freelan.freeioe.org/stop?key=gostpassword.passphrase  -X POST
echo
FREELANDEV=\`route -n|grep tap0\`
GATEWAY=\`cat /tmp/freeioevpn_oldgw\`
if [[ \$FREELANDEV ]]; then
route del default
route add default gw \$GATEWAY
pkill -9 freelan
sleep 1
sed -i 's/DNS=8.8.8.8/#DNS=/g' /etc/systemd/resolved.conf
fi
EOF
chmod +x /bin/cleanfreelan
}


function check_proxyip {
    sleep 1
    echo "[INFO] check proxyip"
    echo -e "\e[1;32;41m YOUR PROXY IP:: \e[0m"
    curl -L ifconfig.me/ip
    echo
    echo -e "\e[1;32;41m [INFO] 如果能看见 PROXY IP 说明代理成功！ \e[0m"
    echo -e "\e[1;32;41m [INFO] freelanvpn 将在30分钟后失效！ \e[0m"
    echo -e "\e[1;32;41m [INFO] 失效后将自动恢复网络！ \e[0m"
    echo -e "\e[1;32;41m [INFO] 也可手动执行 cleanfreelan 恢复网络！ \e[0m"
    echo -e "\e[1;32;41m [INFO] 如无法恢复网络，请重启系统！ \e[0m"
}

function add_iptables_rules {
    echo "[INFO] add iptables rules"
    NUM=1
    SUCC_COUNT=0
    while [ $NUM -le 10 ]; do
        if ping -c 1 192.168.212.1 > /dev/null; then
            echo "[INFO] 192.168.212.1 Ping is successful."
            let SUCC_COUNT++
            break
        else
            let NUM++
        fi
    done
    if [ $SUCC_COUNT -eq 0 ]; then
        echo -e "\e[1;33;41m [ERROR] 192.168.212.1 Ping is failure! \e[0m"
        echo -e "\e[1;33;41m [ERROR] freelan proxy start failure! \e[0m"
        echo -e "\e[1;33;41m [ERROR] 重试请再次运行命令： \e[0m"
        echo -e "\e[1;33;41m [ERROR] curl -L -s freelan.freeioe.org/start|bash \e[0m"
        curl -L freelan.freeioe.org/stop?key=gostpassword.passphrase -X POST
        pkill -9 freelan
    else
        GWDEV=`route -n|grep 0.0.0.0|grep UG|head -n 1|awk '{print $8}'`
        GATEWAY=`route -n|grep 0.0.0.0|grep UG|head -n 1|awk '{print $2}'`
        /bin/sed -i 's/#DNS=/DNS=8.8.8.8/g' /etc/systemd/resolved.conf
        /bin/systemctl restart systemd-resolved
        echo  $GATEWAY> /tmp/freeioevpn_oldgw
        generate_cleanfreelan
        MYIP=$(netstat -antp|grep ESTABLISHED|grep sshd|head -n 1|awk '{print $5}'|awk -F ':' '{print $1}')
        [ ${MYIP} ] && route add $MYIP/32 gw $GATEWAY
        route add 47.244.5.11/32 gw $GATEWAY
        NEWGATEWAY=192.168.212.1
        route del default
        route add default gw $NEWGATEWAY
        check_proxyip
        at now +30 minutes -f /bin/cleanfreelan
    fi

}


function main {
    install_freelan
    start_freelan
    add_iptables_rules

}

main