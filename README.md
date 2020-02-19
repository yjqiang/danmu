# danmu-abc

获取[哔哩哔哩](https://live.bilibili.com)、[斗鱼](https://www.douyu.com)、[虎牙](https://www.huya.com)以及 [个人项目 YjMonitor](https://github.com/yjqiang/YjMonitor) 自定义的弹幕推送。可选用 websocket 协议与 tcp 协议，其中 websocket 协议使用了 [aiohttp](https://github.com/aio-libs/aiohttp) 的 api。

## 接口：
1. [run_forever](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L78) 是程序核心，使用一个 `while` 循环实现掉线的自动重连（掉线后，`close` 掉现在的连接，重开一个新的）。每次的连接分三步，建立并 [`OAUTH`(即 \_one_hello)](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L41)、[心跳](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L45)和[接受](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L60)部分启动并永久执行直到异常或主动关闭、异常或主动关闭后的[清理工作](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L102-L111)。清理完后，重新开启新的连接。
1. [close_and_clean](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L128) 用于永久地关闭连接。
1. [pause](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L119) 用于暂停连接，暂停后，连接是[断开](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L84)的。直到 [resume](https://github.com/yjqiang/danmu/blob/9dc40b556709b895cbfc690e37d0b8e3fe57ffe2/client.py#L123) 唤醒。

## 版权问题：
1. 本代码 fork 自 [blivedm](https://github.com/xfgryujk/blivedm)，由于与原作者一些观点不同，并未走向一致，后由于一些原因，在于原作者[协商](https://github.com/xfgryujk/blivedm)后切断 fork 关系。LICENSE 也进行相应变动。