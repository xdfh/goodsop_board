package com.goodsop.devboard.rk3562;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.goodsop.devboard")
@MapperScan("com.goodsop.devboard.**.repository")
public class Rk3562ServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(Rk3562ServerApplication.class, args);
    }

}