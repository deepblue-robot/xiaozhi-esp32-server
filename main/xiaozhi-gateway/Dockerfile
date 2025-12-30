# 基础镜像
FROM eclipse-temurin:21-jdk-alpine-3.23
# 维护者信息
MAINTAINER deepblueai/xiaozhi
# 设置容器时区为当前时区
RUN echo "Asia/Shanghai" > /etc/timezone

# 复制主机文件至镜像内，复制的目录需放置在 Dockerfile 文件同级目录下
ARG JAR_FILE=target/xiaozhi-gateway.jar
COPY ${JAR_FILE} /app.jar

# 容器启动执行命令
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC"
CMD exec java $JAVA_OPTS -Djava.security.egd=file:/dev/./urandom -jar app.jar
EXPOSE 8000
