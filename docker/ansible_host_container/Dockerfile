FROM ubuntu:20.04

RUN apt update && apt install openssh-server sudo -y

RUN  echo 'root:root12345' | chpasswd

ADD src/ /home/ubuntu

RUN chmod a+x /home/ubuntu/add_key.sh

RUN /home/ubuntu/add_key.sh /home/ubuntu/anshostkey.pub /home/ubuntu/sshd_config > /home/ubuntu/ssh_setting.log

RUN service ssh start

EXPOSE 22

CMD ["/usr/sbin/sshd","-D"]
