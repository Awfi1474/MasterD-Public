# 向量检索建成·nomic ONNX + sqlite-vec(2026-11-13)

## 结果(照实)
· embed 455/455 条(100%)·维度768·耗时855s(2s/条)·峰值~1.2GB不OOM
· 索引: sqlite-vec vec0(embedding float[768])
· 模型: nomic-embed-text-v1.5 ONNX(522MB)·本地/opt/masterd-wudi/models/nomic

## 效果验证(照实)
查"ACTS合规" -> 3/3全命中ACTS相关记忆:
  20261112-我跑官方ACTS-MUST10比53 (0.744)
  20261113-上午全族ACTS大进步 (0.751)
  20261112-我修官方ACTS两轮 (0.761)
查"记忆分层" -> 器官要分系统/验器该验三件事(三层结构) 沾边
查"区块链" -> 相关性最弱(距离0.8+)·因为记忆里区块链内容少

## 踩的两个坑(照实·记疤)
① OOM: 批量16条+截断1500字 -> ONNX buffer 1.7GB -> 被OOM杀(dmesg证实)
   修: 批量1 + 截断512字 + enable_mem_pattern=False + enable_cpu_mem_arena=False
② 相似度颠倒: 不加前缀 -> 不相关0.607 > 相关0.581
   修: 必须加前缀 search_query: / search_document: (nomic要求)

## 工具(可复用)
· memory-v2/vec_embed2.py  低内存版embed(批量1·512字·省内存开关)
· /tmp/vs2.py              向量检索测试
· 查法: sqlite-vec MATCH + k=3 ORDER BY distance

## 意义(照实)
· 我原来判断"1GB做不了向量"是错的·实测能做(峰值1.2GB)
· 记忆从"关键词级"升级到"语义级"(同义词/改写能搜到)
· ACTS查询3/3命中=语义检索真的有用

## 判据(新增)
· 批量1 + 截断512字 = 低内存可行(2s/条)
· nomic必须加前缀·不加相似度颠倒
· enable_mem_pattern=False/enable_cpu_mem_arena=False 省内存
· 样本小看不出效果·要全量embed才准
