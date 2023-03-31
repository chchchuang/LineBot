# Accounting LineBot - Line記帳機器人

> 這是一個用Flask、串接LineBot API (Webhook)、連結Google Sheet並部署在 GCP 的記帳機器人
> 透過LineBot將帳目記錄在Google試算表, 並將函式部署雲端, 使用Line即可隨時輕鬆記帳

## Architecture Diagram 架構圖

![linebot architecture diagram](https://github.com/chchchuang/linebot/blob/main/linebot%20architecture%20diagram.png)

## Prerequisites 使用環境
* 後端: Python Flask
* LineBot: [Line Developers](https://developers.line.biz/zh-hant/) Messaging API
* 雲端部署: [Google Cloud Platform](https://console.cloud.google.com/?hl=zh-tw)(GCP) Cloud Function
* 資料庫: [Google Sheet](https://docs.google.com/spreadsheets/create?hl=zh-TW)

## Usage example 使用範例

### write

> 記錄``人名``買了``品項``的``花費``
```
write 人名 品項 花費
```
<img src="https://user-images.githubusercontent.com/111694502/228914578-be9f360b-1a1d-4ab5-a88b-9157bcf97004.jpg" width="500px" alt="LineBot-write">
<img src="https://user-images.githubusercontent.com/111694502/228915314-5f8996c4-91be-4bc5-b533-d4a4a65f86fe.png" width="500px" alt="GoogleSheet-record">


### read

> 讀取完整記帳內容
```
read
```
<img src="https://user-images.githubusercontent.com/111694502/228915967-187082ac-6386-4ac1-b822-325f446d55e1.JPG" width="500" alt="LineBot-read">


### display

> 顯示完整表單網址, 也可以進行修改
```
display
```
<img src="https://user-images.githubusercontent.com/111694502/228916612-79fc6b57-1af0-48e5-83e3-18d608e2e1e6.jpg" width="500" alt="LineBot-display">


### sum

> 加總``人名``全部花費
```
sum 人名
```
<img src="https://user-images.githubusercontent.com/111694502/228916939-9caf6a99-0ae6-4a8e-85d7-19ac0db6a7f3.jpg" width="500" alt="LineBot-sum">


### delete

> 刪除最後一筆記帳
```
delete
```
<img src="https://user-images.githubusercontent.com/111694502/228917217-a8d07d21-d823-4799-a247-ae641c523b53.jpeg" width="500" alt="LineBot-delete">


### clear

> 清空全紀錄
```
clear
```
<img src="https://user-images.githubusercontent.com/111694502/228917408-8d123c65-6c0f-4b7a-8fe1-4dda7631abdb.jpeg" width="500" alt="LineBot-clear">


### 指令

> 顯示所有``指令``
```
指令
```
<img src="https://user-images.githubusercontent.com/111694502/228917593-f0f99d7a-b4ac-4aed-bb31-a42e192894ea.jpg" width="500" alt="LineBot-tips">

## Authors 關於作者
* Author: **chchchuang**  
* Update: 2023-03-31  
* Contact: chchchuang@gmail.com
