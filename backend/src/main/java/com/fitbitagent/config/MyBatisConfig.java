package com.fitbitagent.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.fitbitagent.repository")
public class MyBatisConfig {
}