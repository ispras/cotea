FROM python:3.10-bookworm

RUN apt update && apt install -y openssh-server sudo && rm -rf /var/lib/apt/lists/*
RUN echo 'root:amella' | chpasswd
RUN mkdir -p /run/sshd

COPY sshd_config /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
