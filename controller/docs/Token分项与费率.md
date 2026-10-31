# Token 分项与费率 / Token components and pricing

设备现在把未缓存输入、缓存读取、缓存写入、可见输出和推理分别显示数量与估价。推理是输出 Token 的子集，单独显示但只在总计中计算一次；OpenAI 文档说明 reasoning tokens 按 output tokens 计费。

费率配置支持 `custom` 与 `openai` 两种来源，均可乘本机 `multiplier`，默认 1。长上下文以单次请求输入（含缓存）是否严格大于 272,000 判档。缺少完整请求边界时不会把累计 Token 猜成一笔长请求。

The device shows uncached input, cached reads, cache writes, visible output and reasoning as separate counts and estimates. Reasoning is a subset of output: it is displayed separately but added once. Pricing supports custom or OpenAI baseline rates with a local multiplier (default 1). Long-context selection is per request, using cache-inclusive input strictly above 272,000 tokens.
