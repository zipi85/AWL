#!/bin/bash
x=$(rpm -qa |grep awl-java|grep -v awl-java18|wc -l)
if (( $x > 0 ))
then
echo -n "remove " >/tmp/update_java
rpm -qa |grep awl-java|grep -v awl-java18 | grep -v extendedsupport |xargs -Ixx rpm -q xx --qf '%{name} '>> /tmp/update_java
echo >> /tmp/update_java
echo -n "install " >>/tmp/update_java
rpm -qa |grep awl-java |grep -v awl-java18|grep -v extendedsupport |xargs -Ixx rpm -q xx --qf '%{name} '|sed 's/-jre\|-jdk/-extendedsupport&/g'>> /tmp/update_java
echo >> /tmp/update_java
echo >> yum update awl-*-extendedsupport* --enablerepo=pvm-main
fi
x=$(rpm -qa |grep awl-java18|wc -l)
if (( $x > 0 ))
then
echo -n "update " >>/tmp/update_java
rpm -qa |grep awl-java18 |xargs -Ixx rpm -q xx --qf '%{name} ' >>/tmp/update_java
echo >> /tmp/update_java
fi
echo run >> /tmp/update_java
yum -y --enablerepo=pvm-main shell </tmp/update_java
rpm -qa --last |head
yum history info
