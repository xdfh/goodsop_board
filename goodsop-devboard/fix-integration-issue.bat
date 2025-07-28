@echo off
echo 正在清理 Maven 缓存和重新编译项目...
echo.

echo 1. 清理项目...
mvn clean

echo.
echo 2. 删除 target 目录...
for /d /r . %%d in (target) do @if exist "%%d" rd /s /q "%%d"

echo.
echo 3. 重新编译项目...
mvn compile

echo.
echo 4. 启动 RK3562 服务器...
mvn spring-boot:run -pl goodsop-rk3562-server

pause
