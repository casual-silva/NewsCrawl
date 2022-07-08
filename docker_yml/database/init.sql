/*
 Navicat Premium Data Transfer

 Source Server         : 192.168.1.137
 Source Server Type    : MySQL
 Source Server Version : 50738
 Source Host           : 192.168.1.137:3306
 Source Schema         : news_crawl

 Target Server Type    : MySQL
 Target Server Version : 50738
 File Encoding         : 65001

 Date: 30/06/2022 18:24:59
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ce_news
-- ----------------------------
DROP TABLE IF EXISTS `ce_news`;
CREATE TABLE `ce_news`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uuid` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '新闻uuid',
  `title` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '新闻标题',
  `subtitle` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '新闻副标题',
  `summary` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '新闻摘要',
  `publish_date` datetime(0) NULL DEFAULT NULL COMMENT '新闻时间',
  `company_name` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '公司名称',
  `company_code` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '公司代码',
  `site_url` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '站点域名',
  `site_name` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '站点名称',
  `spider_time` datetime(0) NULL DEFAULT NULL COMMENT '创建时间',
  `article_source` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '文章来源',
  `author` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '文章作者',
  `created_time` datetime(0) NULL DEFAULT NULL COMMENT '写入时间',
  `classification` varchar(8) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '所属分类',
  `source_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '原文链接',
  `status` tinyint(2) NULL DEFAULT NULL COMMENT '提交状态: [0,1,2] > [\"未提交\", \"提交成功\", \"无效数据\"]',
  `other` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '其他',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `unique_uuid`(`uuid`) USING BTREE,
  INDEX `title`(`title`) USING BTREE,
  INDEX `publish_date`(`publish_date`) USING BTREE,
  INDEX `spider_time`(`spider_time`) USING BTREE,
  INDEX `site_url`(`site_url`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 117947 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ce_news_content
-- ----------------------------
DROP TABLE IF EXISTS `ce_news_content`;
CREATE TABLE `ce_news_content`  (
  `uuid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `content_text` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `created_time` datetime(0) NULL DEFAULT NULL,
  PRIMARY KEY (`uuid`) USING BTREE,
  INDEX `index_uuid`(`uuid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ce_news_html_content
-- ----------------------------
DROP TABLE IF EXISTS `ce_news_html_content`;
CREATE TABLE `ce_news_html_content`  (
  `uuid` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `html_text` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `created_time` datetime(0) NULL DEFAULT NULL,
  PRIMARY KEY (`uuid`) USING BTREE,
  INDEX `index_uuid`(`uuid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
