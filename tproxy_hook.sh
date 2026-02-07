#!/bin/sh
# shellcheck disable=SC2015,SC3003,SC3060

NFT_TABLE='inet global_proxy'
NFT_BASEFILE="/etc/nikki/tproxy.nft"
ROUTE_TABLE=1200
ROUTE_PREF=10000
TPROXY_MARK=0x250

__update_nftset() {
  local set=$1
  local file=$2
  local url=$3

  mkdir -p "${file%/*}"

  local NEW_LIST=$(uclient-fetch -qO- "$url" | sed '/#/d')

  [[ -z "$NEW_LIST" ]] && logger -t tproxy "$set update failed" && exit 1

  {
    if [[ ! -f "$file" ]]; then
      echo "flush set $NFT_TABLE $set"
      echo "add element $NFT_TABLE $set { ${NEW_LIST//$'\n'/, } }"
    else
      local OLD_LIST=$(zcat "$file")
      local TO_ADD=$(comm -13 <(echo "$OLD_LIST") <(echo "$NEW_LIST"))
      local TO_DEL=$(comm -23 <(echo "$OLD_LIST") <(echo "$NEW_LIST"))

      [[ "$TO_ADD" ]] && echo "add element $NFT_TABLE $set { ${TO_ADD//$'\n'/, } }"
      [[ "$TO_DEL" ]] && echo "delete element $NFT_TABLE $set { ${TO_DEL//$'\n'/, } }"
    fi
  } | nft -f - && {
    echo "$NEW_LIST" | gzip > "$file"
    logger -t tproxy "$set update success"
  } || {
    logger -t tproxy "$set nothing changed"
  }
}

update_nftsets() {
  __update_nftset "chnroutes" "/var/tproxy_chnroutes.gz" "https://chnroutes2.cdn.skk.moe/chnroutes.txt"
  __update_nftset "chnroutes6" "/var/tproxy_chnroutes6.gz" "https://china-operator-ip.yfgao.com/china6.txt"
  __update_nftset "proxy_routes" "/var/tproxy_proxy_routes.gz" "https://gcore.jsdelivr.net/gh/A1ca7raz/rule-set@dist/ipset_proxy_ipv4.txt"
  __update_nftset "proxy_routes6" "/var/tproxy_proxy_routes6.gz" "https://gcore.jsdelivr.net/gh/A1ca7raz/rule-set@dist/ipset_proxy_ipv6.txt"
}

hook_start_tproxy() {
  ip -4 route add local default dev lo table $ROUTE_TABLE
  ip -4 rule add pref $ROUTE_PREF fwmark $TPROXY_MARK table $ROUTE_TABLE
  ip -6 route add local default dev lo table $ROUTE_TABLE
  ip -6 rule add pref $ROUTE_PREF fwmark $TPROXY_MARK table $ROUTE_TABLE
  nft -f $NFT_BASEFILE
  update_nftsets
}

hook_clean_tproxy() {
  ip -4 rule del table $ROUTE_TABLE > /dev/null 2>&1
  ip -4 route flush table $ROUTE_TABLE > /dev/null 2>&1
  ip -6 rule del table $ROUTE_TABLE > /dev/null 2>&1
  ip -6 route flush table $ROUTE_TABLE > /dev/null 2>&1
  nft delete table $NFT_TABLE > /dev/null 2>&1
  rm -f /var/tproxy_*
}
