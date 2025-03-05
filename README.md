# Web五子棋游戏

这是一个基于Web的五子棋游戏项目，由Cursor IDE和Claude-3.5-Sonnet AI助手协助开发。

## 项目特点

### 游戏功能
- 玩家执黑棋，AI执白棋
- 支持悔棋功能
- 自动判定胜负
- 支持平局判定
- 显示最后落子位置

### 视觉效果
- 精美的3D棋子渲染
- 木纹棋盘背景
- 星点标记
- 棋子落子动画
- 胜利烟花特效
- 棋子悬停预览
- 自适应布局

### 交互体验
- 音效反馈（可开关）
- 鼠标悬停预览
- 状态提示
- 一键重开

## 游戏截图
![游戏界面](https://raw.githubusercontent.com/boshi202/gomoku/master/screenshots/gameplay.png)
*游戏运行界面：展示了木纹棋盘、3D棋子效果、最后落子标记（红点）以及操作按钮*

## 技术栈
- 前端：HTML5, CSS3, JavaScript (Canvas API)
- 后端：Python, Flask
- AI：基于评分系统的五子棋AI

## 项目结构
```
web_gomoku/
├── app.py              # Flask后端服务
├── templates/          
│   └── index.html      # 游戏主页面
├── static/             # 静态资源
│   ├── images/         # 图片资源
│   └── sounds/         # 音效文件
└── logs/               # 日志目录
```

## 安装和运行

1. 确保已安装Python 3.x
2. 安装依赖：
```bash
pip install flask
```

3. 运行服务器：
```bash
python app.py
```

4. 在浏览器中访问：`http://localhost:6688`

## 游戏规则
- 玩家执黑棋先手
- 双方轮流在棋盘上落子
- 任意一方在横、竖、斜方向形成连续五子即获胜
- 棋盘下满未分出胜负则为平局

## 开发工具
- IDE: [Cursor](https://cursor.com/)
- AI助手: Claude-3.5-Sonnet

## 特别鸣谢
- 本项目由Cursor IDE和Claude-3.5-Sonnet AI助手协助开发
- 感谢Anthropic提供的Claude-3.5-Sonnet模型支持

## 许可证
MIT License

## 注意事项
- 建议使用现代浏览器（Chrome, Firefox, Safari等）以获得最佳体验
- 确保浏览器开启了JavaScript
- 如遇到音效无法播放，请检查浏览器的自动播放设置 