强化日语学习场景
<br>
<br>

# 功能
1. 通过*随机的例句*学习`“日语 -> 中文”`与`“中文 -> 日语”`
2. 不仅学习一个词的多种释义，也会掺入学习各种*用法*(习语、复合语等)
3. 对于一个单词所已熟练的释义/用法，可点击句子取消高亮，该释义/用法不会在本次学习的后续中出现   

<br>

##### (请下载最新的卡组并导入Anki，不会影响已有的学习进度)
> 更新日志:
> - 2024.4.21 新的cn->ja展现形式, 同时修复卡片翻转后部分空白的问题; 修复报错`Shogakukanjcv3.css`加载失败; 
> - 2024.2.5 去除一些无效卡片
> - 2023.12.23 "中文->日语"卡片支持考察习语、复合语等用法；加入自定义缩放因子以改变整体字体大小(如嫌字体小请参考下文的配置方法)；修复部分单词展示空白

#### DEMO
##### 卡片模板 - 日文->中文 (学习读)
1. 尝试把(随机的)日文例句翻译成中文  
a. _卡片正面_  
![jazh1_front](https://i.postimg.cc/zvxbFdSK/jazh1-front.png)  
b. _卡片背面_  
![jazh1_back](https://i.postimg.cc/L59gfdfm/jazh1-back.png)  
c. _在卡片正面双击例句临时展现中文释义_  
![jazh1a_front](https://i.postimg.cc/1RBqSthX/jazh1a-front.png)  
2. 当单词有多种释义时，同时展现  
a. _多释义卡片正面_  
![jazh2_front](https://i.postimg.cc/Prq85jT4/jazh2-front.png)  
b. _单击例句将已掌握的释义标记为移出本轮学习_  
![jazh2a_front](https://i.postimg.cc/jjyDFq4s/jazh2a-front.png)  
c. _在本轮学习中再次遇到该卡片时_  
![jazh2b_front](https://i.postimg.cc/3Jb0ycwH/jazh2b-front.png)  

##### 卡片模板 - 中文->日文 (学习写)
1. 尝试把(随机的)中文例句翻译成日文  
a. _卡片正面_  
![zhja1_front](https://i.postimg.cc/nhjjqGs9/zhja1-front.png)  
b. _卡片背面_  
![zhja1_back](https://i.postimg.cc/RZk3dJfs/zhja1-back.png)  

# 可配置项

#### 字太小/太大

1. Anki首页，点击“牌组”
2. 点击所要改变字体大小的牌组名称
3. 点击“浏览”
4. 点击右侧的"卡片..."按钮
5. 点击左侧的“样式”按钮
6. 找到`.root { `
7. 把`transform: scale(0.8)`中的`0.8`改成想要的缩放率(例. 放大1.5倍则改成1.5)
8. 点击右下的保存
