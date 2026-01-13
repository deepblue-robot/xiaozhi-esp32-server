package xiaozhi.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Swagger配置
 * Copyright (c) 人人开源 All rights reserved.
 * Website: https://www.renren.io
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public GroupedOpenApi deviceApi() {
        return GroupedOpenApi.builder()
                .group("device")
                .pathsToMatch("/device/**")
                .build();
    }

    @Bean
    public GroupedOpenApi agentApi() {
        return GroupedOpenApi.builder()
                .group("agent")
                .pathsToMatch("/agent/**")
                .build();
    }

    @Bean
    public GroupedOpenApi modelApi() {
        return GroupedOpenApi.builder()
                .group("models")
                .pathsToMatch("/models/**")
                .build();
    }

    @Bean
    public GroupedOpenApi oatApi() {
        return GroupedOpenApi.builder()
                .group("ota")
                .pathsToMatch("/ota/**")
                .build();
    }

    @Bean
    public GroupedOpenApi timbreApi() {
        return GroupedOpenApi.builder()
                .group("timbre")
                .pathsToMatch("/ttsVoice/**")
                .build();
    }

    @Bean
    public GroupedOpenApi sysApi() {
        return GroupedOpenApi.builder()
                .group("admin")
                .pathsToMatch("/admin/**")
                .build();
    }

    @Bean
    public GroupedOpenApi userApi() {
        return GroupedOpenApi.builder()
                .group("user")
                .pathsToMatch("/user/**")
                .build();
    }

    @Bean
    public GroupedOpenApi configApi() {
        return GroupedOpenApi.builder()
                .group("config")
                .pathsToMatch("/config/**")
                .build();
    }

    @Bean
    public GroupedOpenApi merchantApi() {
        return GroupedOpenApi.builder()
                .group("merchant")
                .pathsToMatch("/merchant/**")
                .build();
    }


    @Bean
    public OpenAPI customOpenAPI() {
        // 1. 定义全局Header的安全方案（核心：OpenAPI 3 规范要求）
        String securitySchemeName = "tokenHeader";
        return new OpenAPI()
                // 文档基础信息
                .info(new Info()
                        .title("xiaozhi-esp32-manager-api")
                        .version("3.0")
                        .description("xiaozhi-esp32-manager-api文档"))
                // 2. 配置全局Header参数（SecurityScheme 是 OpenAPI 3 标准写法）
                .components(new io.swagger.v3.oas.models.Components()
                        .addSecuritySchemes(securitySchemeName,
                                new SecurityScheme()
                                        .name("Authorization")  // Header名称
                                        .type(SecurityScheme.Type.APIKEY)  // 类型为API KEY
                                        .in(SecurityScheme.In.HEADER)  // 位置在Header
                                        .description("访问令牌，格式：Bearer {token}")
                        )
                )
                // 3. 绑定安全方案到所有接口（关键：不绑定则不显示）
                .addSecurityItem(new SecurityRequirement().addList(securitySchemeName))
                .addSecurityItem(new SecurityRequirement().addList("appIdHeader"));
    }
}