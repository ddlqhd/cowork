# WebSocket SSE Server 项目上下文

## 项目概述

这是一个基于 FastAPI 的 WebSocket 服务器，支持通过 SSE（Server-Sent Events）端点接收上游消息。该项目允许外部服务通过 HTTP API 发送消息到已连接的 WebSocket 客户端，实现了从 HTTP 请求到 WebSocket 推送的桥接功能。

## 架构与组件

### 核心组件
- **WebSocket 服务器**：处理 WebSocket 连接，提取用户 ID
- **SSE 端点**：HTTP 端点用于接收上游 SSE 消息
- **消息路由**：根据用户 ID 将消息路由到适当的 WebSocket 连接
- **连接管理器**：线程安全的连接管理，包含适当的清理机制
- **批量支持**：支持批量消息处理

### 主要文件结构
```
websocket-sse-server/
├── src/
│   └── websocket_sse_server/
│       ├── __init__.py
│       ├── main.py                    # FastAPI 应用程序
│       ├── config.py                  # 配置 (pydantic settings)
│       ├── models/
│       │   ├── __init__.py
│       │   └── message.py            # Pydantic 模型
│       ├── core/
│       │   ├── __init__.py
│       │   ├── connection_manager.py # WebSocket 连接管理器
│       │   └── sse_handler.py        # SSE 消息处理器
│       ├── api/
│       │   ├── __init__.py
│       │   ├── websocket_endpoints.py # WebSocket 路由
│       │   └── sse_endpoints.py      # SSE 端点
│       └── utils/
│           ├── __init__.py
│           ├── logger.py             # 日志配置
│           └── exceptions.py         # 自定义异常
├── tests/
│   ├── unit/
│   │   ├── test_connection_manager.py
│   │   └── test_sse_handler.py
│   └── integration/
│       ├── test_websocket_flow.py
│       ├── test_sse_flow.py
│       └── test_websocket_sse_integration.py
```

## 关键技术栈

- **FastAPI**：Web 框架
- **uvicorn**：ASGI 服务器
- **Pydantic**：数据验证和设置管理
- **loguru**：日志记录
- **websockets**：WebSocket 客户端测试
- **pytest**：测试框架

## 主要功能

### API 端点
1. **WebSocket 端点**：`ws://localhost:8080/ws?user_id=<user_id>`
2. **SSE 推送端点**：`POST /sse/push`
3. **SSE 批量推送端点**：`POST /sse/push/batch`
4. **健康检查**：`GET /health`
5. **指标**：`GET /metrics`

### 连接管理
- 使用 `ConnectionManager` 类管理 WebSocket 连接
- 通过用户 ID 索引连接
- 线程安全的连接操作
- 自动清理断开的连接

### 消息处理
- SSE 消息通过 HTTP API 接收
- 消息根据用户 ID 路由到对应的 WebSocket 连接
- 支持公共账号功能，用户可通过 @mention 向公共账号发送消息
- 支持批量消息处理
- 错误处理和日志记录

## 开发约定

### 测试实践
- **单元测试**：测试各个组件的独立功能（位于 `tests/unit/`）
- **集成测试**：测试组件间的交互和完整工作流（位于 `tests/integration/`）
- 所有测试必须通过，不得降低测试覆盖率
- 测试应覆盖正常流程和异常情况

### 代码风格
- 使用 Pydantic v2 的现代 API（如 `model_dump()` 替代 `dict()`）
- 配置类使用 `model_config` 而不是内部 `Config` 类
- 异步编程遵循最佳实践
- 错误处理和日志记录要适当

### 依赖管理
- 使用 `pyproject.toml` 管理项目依赖
- 生产依赖在 `[project]` 部分定义
- 开发依赖在 `[project.optional-dependencies.dev]` 部分定义

## 构建和运行

### 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 运行服务器
```bash
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080 --reload
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/
```

## 重要修复和改进

1. **性能优化**：修复了 `ConnectionManager` 中的锁竞争问题，避免了嵌套锁获取导致的测试超时
2. **弃用警告修复**：更新了 Pydantic API 使用，将 `.dict()` 替换为 `.model_dump()`，更新了配置类定义
3. **集成测试**：添加了全面的 WebSocket-SSE 集成测试，确保端到端功能正常
4. **错误处理**：改进了异常处理逻辑，避免了潜在的死锁情况
5. **公共账号功能**：增加了对公共账号的支持，允许用户通过 @mention 语法向公共账号（如CI机器人、邮件机器人等）发送消息

## 公共账号功能

系统支持公共账号（如CI机器人、邮件机器人等），用户可以通过 @mention 语法向这些公共账号发送消息。

### 实现细节
- 在 `src/websocket_sse_server/config/public_accounts.py` 中定义公共账号配置
- 在 `SSEHandler.process_sse_message` 方法中添加消息内容解析逻辑
- 使用正则表达式检测消息中的 @mention 模式
- 将匹配到的公共账号消息路由到对应的WebSocket连接
- 保留原始发送者信息，使公共账号知道消息来源

### 默认公共账号
- `ci_bot`
- `email_bot`
- `notification_bot`
- `system_bot`

### 环境配置
通过 `PUBLIC_ACCOUNTS` 环境变量可以添加自定义公共账号：
```
PUBLIC_ACCOUNTS=custom_bot1,custom_bot2,another_bot
```

### 使用示例
用户可以在消息中使用 @mention 语法：
```
"Please run tests on my branch @ci_bot"
```
这将把消息路由到 `ci_bot` 的WebSocket连接，同时保留原始发送者信息。

## 生产部署考虑

1. **负载均衡**：使用多个实例与 Redis 共享连接状态
2. **监控**：添加指标收集（Prometheus、Grafana）
3. **日志**：使用结构化日志（JSON 格式）
4. **SSL/TLS**：在生产环境中使用 HTTPS/WSS
5. **速率限制**：为 SSE 端点添加速率限制
6. **认证**：添加 JWT 或 OAuth2 认证