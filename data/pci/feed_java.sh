#!/bin/bash
VERSION_OS=$(rpm -qa \*-release \*-release-server|grep -Ei 'centos|redhat'| xargs -Ixx rpm -q xx --queryformat '%{VERSION}'|cut -c1)
x=$(rpm -qa |grep awl-java|grep -vE 'awl-java18|extendedsupport'|wc -l)
if (( $x > 0 )); then
	echo -n "remove " >/tmp/update_java
	rpm -qa |grep awl-java|grep -vE 'awl-java18|extendedsupport' |xargs -Ixx rpm -q xx --qf '%{name} '>> /tmp/update_java
	echo >> /tmp/update_java
	echo -n "install " >>/tmp/update_java
	rpm -qa |grep awl-java |grep -vE 'awl-java18|extendedsupport' |xargs -Ixx rpm -q xx --qf '%{name} '|sed 's/-jre\|-jdk/-extendedsupport&/g'>> /tmp/update_java
	echo >> /tmp/update_java
else	
	echo "update awl-*-extendedsupport*" > /tmp/update_java
fi
x=$(rpm -qa |grep awl-java18|wc -l)
if (( $x > 0 )); then
	echo -n "update " >>/tmp/update_java
	rpm -qa |grep awl-java18 |xargs -Ixx rpm -q xx --qf '%{name} ' >>/tmp/update_java
	echo >> /tmp/update_java
fi
echo run >> /tmp/update_java
yum -y --enablerepo=pvm-main shell </tmp/update_java
rpm -qa --last |head
if (( $VERSION_OS > 5 )); then
	yum history info
fi
