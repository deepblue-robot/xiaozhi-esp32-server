CREATE TABLE `ai_merchant` (
  `id` bigint NOT NULL COMMENT 'id',
  `name` varchar(50) NOT NULL COMMENT '商户名称',
  `status` tinyint NOT NULL default '1' COMMENT '状态  0：停用   1：正常',
  `parent_id` bigint DEFAULT NULL COMMENT '父商户ID',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户表';

CREATE TABLE `ai_merchant_user` (
  `id` bigint NOT NULL COMMENT 'id',
  `merchant_id` bigint NOT NULL COMMENT '商户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(100) DEFAULT NULL COMMENT '密码',
  `super_admin` tinyint unsigned DEFAULT NULL COMMENT '超级管理员   0：否   1：是',
  `status` tinyint not null DEFAULT '1' COMMENT '状态  0：停用   1：正常',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户用户表';


CREATE TABLE `ai_merchant_config` (
   `id` bigint NOT NULL COMMENT 'id',
   `merchant_id` bigint NOT NULL COMMENT '商户ID',
   `logo_url` varchar(255) DEFAULT NULL COMMENT 'logo地址',
   `creator` bigint DEFAULT NULL COMMENT '创建者',
   `create_date` datetime DEFAULT NULL COMMENT '创建时间',
   `updater` bigint DEFAULT NULL COMMENT '更新者',
   `update_date` datetime DEFAULT NULL COMMENT '更新时间',
   PRIMARY KEY (`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户配置表';

CREATE TABLE `ai_merchant_agent` (
  `id` bigint NOT NULL COMMENT 'id',
  `merchant_id` bigint NOT NULL COMMENT '商户ID',
  `agent_id` bigint NOT NULL COMMENT '智能体ID',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商户智能体关联表';



CREATE TABLE `ai_mini_user` (
  `id` bigint NOT NULL COMMENT 'id',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(100) DEFAULT NULL COMMENT '密码',
  `open_id` varchar(50)  COMMENT 'openid',
  `status` tinyint DEFAULT NULL COMMENT '状态  0：停用   1：正常',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小程序用户';


alert table ai_device add COLUMN  `merchant_id` bigint NOT NULL COMMENT '商户ID' AFTER `id`;
alert table ai_device add COLUMN  `active_status` tinyint DEFAULT '0' COMMENT '设备激活状态(0未激活/1已激活)', AFTER `online`;