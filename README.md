# blivedm

获取哔哩哔哩、斗鱼以及 [YjMonitor](https://github.com/yjqiang/YjMonitor) 项目自定义的弹幕推送。可选用 websocket 协议与 tcp 协议，其中 websocket 协议 [aiohttp](https://github.com/aio-libs/aiohttp) 的 api 很方便，但是 tcp 的性能非常好，内存占用很低。

[哔哩哔哩弹幕websocket协议解释（来自项目上游源作者）](https://blog.csdn.net/xfgryujk/article/details/80306776)
