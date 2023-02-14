## 用途：
用于快速生成 cubefs ec 子系统的配置文件

## 步骤
1. group_info/202_sample.ini 为需要修改参数样列
1. 从 group_info/202_sample.ini 复制一份出来到 group_info/CLUSTER_ID.ini，进行修改
2. 运行 `python3 main.py config/CLUSTER_ID.ini`
3. 正常退出后会在统计 gen_config/CLUSTER_ID/ 下生成所有配置文件
4. proxy, access 和 blobstore 节点均可横向扩展，所以监听ip 需要在部署机器上进行替换
```
sed -i  's#IP#机器部署ip#'  上述节点配置文件
```
