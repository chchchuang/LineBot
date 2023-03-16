# Accounting Linebot - 記帳機器人

> 讓記帳成為生活的一部份

> Author: chchchuang  
> Update: 2023/3/17  
> Contact: chchchuang@gmail.com

## architecture diagram

![linebot architecture diagram](https://github.com/chchchuang/linebot/blob/main/linebot%20architecture%20diagram.png)

## request message function

### write

記錄**人名**買了**品項**的**花費**

```
write 人名 品項 花費
```

### read

讀取完整記帳內容

```
read
```

### display

顯示完整表單網址

```
display
```

### sum

加總**人名**全部花費

```
sum 人名
```

### delete

刪除上一筆記帳

```
delete
```

### clear

清空全紀錄

```
clear
```

### 指令

顯示所有指令

```
指令
```
