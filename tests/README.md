# 测试说明

本项目包含单元测试和集成测试，用于验证 WebSocket 和 SSE 服务器的功能。

## 目录结构

- `unit/` - 单元测试，测试各个组件的独立功能
- `integration/` - 集成测试，测试组件之间的交互和完整工作流

## 运行测试

### 安装依赖
```bash
# 确保已安装开发依赖
pip install -r requirements-dev.txt
```

### 运行所有测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行所有测试并显示覆盖率
python -m pytest tests/ --cov=src/ --cov-report=html
```

### 运行特定类型的测试
```bash
# 只运行单元测试
python -m pytest tests/unit/ -v

# 只运行集成测试
python -m pytest tests/integration/ -v
```

## 测试类型

### 单元测试
- `test_connection_manager.py` - 测试连接管理器的各种操作
- `test_sse_handler.py` - 测试 SSE 消息处理器

### 集成测试
- `test_websocket_flow.py` - 测试 WebSocket 连接流程
- `test_sse_flow.py` - 测试 SSE 消息推送流程
- `test_websocket_sse_integration.py` - 测试 WebSocket 和 SSE 的完整集成工作流

## 测试标准

- 所有测试必须在 CI 环境中通过
- 新功能必须包含相应的测试
- 重构代码时不得降低测试覆盖率
- 测试应覆盖正常流程和异常情况