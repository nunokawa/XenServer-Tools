#!/bin/sh

. /etc/xensource-inventory 

ethtool_py="/usr/local/sbin/ethtool.py"

XE=/opt/xensource/bin/xe
host_uuid=${INSTALLATION_UUID}

num=0
for i in `$XE pif-list params=uuid --minimal | sed 's/,/ /g'`
do
  uuid[$num]=$i

  set $(${XE} pif-list uuid=$i params=device,currently-attached,IP-configuration-mode,IP,netmask,gateway,DNS | awk -F: '{print $2}' | awk '{print $1}')
  device[$num]=$1
  attached[$num]=$2
  mode[$num]=$3
  ipaddr[$num]=$4
  netmask[$num]=$5
  gateway[$num]=$6
  dns[$num]=$7

  set $(ifconfig ${device[$num]} | grep HWaddr)
  while [ "$1" != "HWaddr" ];
  do
      shift
  done
  macaddr[$num]=$2

  tmp=`xe pif-list device=${device[$num]} params=other-config --minimal | sed 's/ //g' | sed 's/\;/ /g' | sed 's/:/=/g'`

  other[$num]=`echo $tmp | awk '{n = split($0, str, " ")} {for(j = 1; j <= n; j++) printf "other-config:" str[j] " "}'`

  num=`expr $num + 1`
done


while [ $num -gt 0 ]
do
  num=`expr $num - 1`

  echo "Setting ${device[$num]}: "

  ${XE} pif-forget uuid=${uuid[$num]}
  new_uuid=$(${XE} pif-introduce host-uuid=${host_uuid} device=${device[$num]} mac=${macaddr[$num]})

  case ${mode[$num]} in
    [Ss][Tt][Aa][Tt][Ii][Cc])
      ${XE} pif-reconfigure-ip uuid=${new_uuid} mode=${mode[$num]} IP=${ipaddr[$num]} netmask=${netmask[$num]} gateway=${gateway[$num]} DNS=${dns[$num]} ;
      [ "${attached[$num]}" = "true" ] &&  ${XE} pif-plug uuid=${new_uuid} ;
      echo "Device setting completed." ;;
    [Dd][Hh][Cc][Pp])
      ${XE} pif-reconfigure-ip uuid=${new_uuid} mode=${mode[$num]} ;
      [ "${attached[$num]}" = "true" ] &&  ${XE} pif-plug uuid=${new_uuid} ;
      echo "Device setting completed." ;;
    [Nn][Oo][Nn][Ee])
      [ "${attached[$num]}" = "true" ] &&  ${XE} pif-plug uuid=${new_uuid} ;
      echo "Device setting none." ;;
    '')
      [ "${attached[$num]}" = "true" ] &&  ${XE} pif-plug uuid=${new_uuid} ;
      echo "Device setting none." ;;
    *)
      echo "No specified device." ;;
  esac

  echo ""
  sleep 5
  ${XE} pif-param-set uuid=${new_uuid} ${other[$num]}
  sleep 5
  ${XE} pif-list uuid=${new_uuid} params=device,MAC,currently-attached,management,IP-configuration-mode,IP,netmask,gateway,DNS,carrier,speed,duplex,other-config

done

sleep 5
$ethtool_py

exit
