# 集成测试说明

此目录包含 WebSocket 和 SSE 功能的集成测试。

## 测试文件说明

- `test_websocket_sse_integration.py` - 包含完整的 WebSocket 和 SSE 集成测试
- `test_sse_flow.py` - SSE 相关的集成测试
- `test_websocket_flow.py` - WebSocket 相关的集成测试

## 运行测试

### 运行所有集成测试
```bash
cd /path/to/project
source .venv/bin/activate  # 激活虚拟环境
python -m pytest tests/integration/ -v
```

### 运行特定的集成测试
```bash
# 运行 WebSocket-SSE 集成测试
python -m pytest tests/integration/test_websocket_sse_integration.py -v

# 运行 SSE 流程测试
python -m pytest tests/integration/test_sse_flow.py -v

# 运行 WebSocket 流程测试
python -m pytest tests/integration/test_websocket_flow.py -v
```

## 测试内容

### WebSocket-SSE 集成测试包括：

1. **完整流程测试** (`test_websocket_sse_full_flow`)
   - WebSocket 客户端连接到服务器
   - 通过 SSE API 发送消息
   - 验证消息通过 WebSocket 正确传递

2. **批量 SSE 测试** (`test_batch_sse_websocket_flow`)
   - 连接 WebSocket 客户端
   - 通过批量 SSE API 发送多条消息
   - 验证连接的用户收到消息，未连接的用户未收到消息

3. **健康和指标端点测试** (`test_health_and_metrics_endpoints_during_activity`)
   - 在 WebSocket 连接活跃时测试健康和指标端点
   - 验证连接计数准确性
   - 验证 SSE 消息传递不影响其他功能

4. **非存在用户测试** (`test_sse_to_nonexistent_user`)
   - 向未连接的用户发送 SSE 消息
   - 验证系统正确处理不存在的用户

## 注意事项

- 集成测试会在不同端口上启动临时服务器实例
- 每个测试完成后会自动清理服务器进程
- 测试可能会花费较长时间（每个测试约3-5秒），因为需要启动和停止服务器