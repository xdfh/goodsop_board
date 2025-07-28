cd /home
tar xvf docker-26.1.4.tar -C /userdata

2. ‌配置执行路径‌

ln -s /userdata/docker/* /usr/bin/
chmod +x /userdata/docker/*

3. ‌配置存储目录‌

mkdir /userdata/docker-data


nohup /usr/bin/dockerd --data-root=/userdata/docker-data > /var/log/docker.log 2>&1 &



docker version  # 检查版本输出

5. ‌开机自启配置‌
