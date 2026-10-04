# JSON 示例

这些文件使用同一组虚构标识，展示一次请求怎样从自建前端到官端，再回到原聊天。它们不是运行配置，不能替代真实鉴权、签名和配对。

## 离线最小代码

[minimal_context.py](minimal_context.py) 用 Python 标准库演示对话分组、一次虚构召回、冻结原始 JSON、单份正文和分页还原。可在 Python 3 中运行：

```sh
python examples/minimal_context.py
python examples/minimal_context.py --large
```

运行只打印摘要结果，不访问网络、数据库或模型。实际工程还要实现指南中的授权、事务、持久化、附件、配对、签名及回写。脚本中的 `next_offset` 是离线演示字段；实际接口使用不透明 `next_cursor`，不能直接信任客户端传入的任意偏移。

## 一次请求的字段

| 文件 | 内容 |
| --- | --- |
| [send-message.json](send-message.json) | 前端明确选择官端的消息 |
| [event.json](event.json) | 后端投递的请求引用，正文不在事件里 |
| [get-request-request.json](get-request-request.json) | 官端按请求编号读材料 |
| [get-request-result.json](get-request-result.json) | 小材料的工具响应，只有原始 JSON 一份正文 |
| [reply-request.json](reply-request.json) | 使用稳定关联标识回写答复 |
| [reply-result.json](reply-result.json) | 后端持久保存后的回执 |

`get-request-result.json` 的 `snapshot_json` 是一段 JSON 文本。先按原始 UTF-8 字节验证 `snapshot_sha256`，再解析阅读。这里的摘要和字节数按文件中的虚构正文真实计算。MCP 的 `content` 只返回简短说明，完整正文在 `structuredContent` 中，避免又复制一遍。

大材料的 `snapshot_json` 为 `null`，正文改用 `snapshot_json_part`；按不透明 `next_cursor` 读下一页，直到 `complete=true`。这些分页字段是教程的业务契约，需要自己的后端实现。

## 哪些字段属于平台协议

JSON-RPC 的 `jsonrpc`、`id`、`method`、`params`、MCP 工具调用的 `name` 与 `arguments`、工具结果的 `content` 与 `structuredContent`，以及 Events 的事件与订阅外层结构，遵循各自平台协议。

事件名 `chat.requested`、工具名 `get_request` 和 `reply`、路由 `chat-context`，以及业务参数中的 `request_id`、`binding_revision`、`recipient`、材料快照和召回字段，由本教程自行约定。`inline_snapshot` 和 `snapshot` 保留为空是兼容选择，不是官方字段要求。

实际订阅的 callback 和签名秘密由平台提供，不能把 Work 对话链接当成投递地址。发送 `event.json` 时，需要用该订阅的签名秘密对实际发送的原始请求体签名；此文件只展示应用事件正文。

## 标识关联

这组示例里的 `wreq_example_001`、`evt_example_001`、`sub_example_001` 分别是请求、事件和订阅的虚构标识。读取后按响应中的实际标识回写。相同请求重试时复用 `reply_example_001`；不要每次重试生成新回复标识。

前端示例里的 `mention.start`、`mention.end` 使用 UTF-16 code unit 计数，与 JavaScript 字符串索引一致。后端必须校验这个范围与实际标签匹配。
